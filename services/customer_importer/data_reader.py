"""
data_reader.py — 客户数据读取器

支持从 Excel (.xlsx) 和 CSV 文件读取客户数据。
自动检测文件格式和编码，返回统一的字典列表。
"""

from __future__ import annotations

import csv
import logging
import os
from pathlib import Path
from typing import Any, Generator

logger = logging.getLogger(__name__)

# ── 标准客户字段映射 ──────────────────────────────────────────────────────
# 读取时自动将常见中文/英文列名标准化为内部字段名
FIELD_ALIASES: dict[str, str] = {
    # 姓名
    "name": "name",
    "姓名": "name",
    "客户名称": "name",
    "企业名称": "name",
    "公司名称": "name",
    "联系人": "name",
    # 电话
    "phone": "phone",
    "电话": "phone",
    "手机": "phone",
    "手机号": "phone",
    "联系电话": "phone",
    "手机号码": "phone",
    # 邮箱
    "email": "email",
    "邮箱": "email",
    "邮件": "email",
    "E-mail": "email",
    "电子邮箱": "email",
    # 公司
    "company": "company",
    "公司": "company",
    "企业": "company",
    "单位": "company",
    "所属公司": "company",
    # 职位
    "title": "title",
    "职位": "title",
    "职务": "title",
    "头衔": "title",
    # 地址
    "address": "address",
    "地址": "address",
    "公司地址": "address",
    "详细地址": "address",
    # 备注
    "notes": "notes",
    "备注": "notes",
    "remark": "notes",
    "备注说明": "notes",
    # 行业
    "industry": "industry",
    "行业": "industry",
    "所属行业": "industry",
    # 微信
    "wechat": "wechat",
    "微信": "wechat",
    "微信号": "wechat",
    "微信ID": "wechat",
}


def _normalize_headers(headers: list[str]) -> dict[str, str]:
    """将原始表头映射到标准化字段名

    返回 {原始列名: 标准化字段名} 映射表。
    无法映射的列保留原名称并记录 warning。
    """
    mapping: dict[str, str] = {}
    for h in headers:
        stripped = h.strip()
        normalized = FIELD_ALIASES.get(stripped.lower())
        if normalized:
            mapping[h] = normalized
        else:
            logger.warning("未识别的列名「%s」— 按原样保留", h)
            mapping[h] = stripped
    return mapping


def _normalize_row(row: dict[str, str], header_map: dict[str, str]) -> dict[str, str]:
    """按 header_map 标准化一行数据"""
    out: dict[str, str] = {}
    for orig_col, value in row.items():
        std_col = header_map.get(orig_col, orig_col)
        out[std_col] = (value or "").strip()
    return out


# ── CSV 读取 ──────────────────────────────────────────────────────────────


def read_customers_from_csv(
    file_path: str | Path,
    encoding: str | None = None,
    chunk_size: int = 100,
) -> Generator[list[dict[str, str]], None, dict[str, Any]]:
    """从 CSV 文件读取客户数据（生成器，支持大文件分块）

    Args:
        file_path: CSV 文件路径
        encoding: 文件编码（None=自动检测）
        chunk_size: 每批返回的记录数（默认 100）

    Yields:
        每一批客户字典列表

    Returns:
        摘要信息 dict: {total, success, failed, columns}
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV 文件不存在: {path}")

    # 自动检测编码
    if encoding is None:
        encoding = _detect_encoding(path)

    total = 0
    columns: list[str] = []
    header_map: dict[str, str] = {}

    with open(path, encoding=encoding, newline="") as f:
        # 尝试跳过 BOM
        sample = f.read(8192)
        f.seek(0)

        # 检测分隔符
        dialect = csv.Sniffer().sniff(sample)
        reader = csv.DictReader(f, dialect=dialect)

        # 标准化表头
        header_map = _normalize_headers(reader.fieldnames or [])
        columns = sorted(set(header_map.values()))

        batch: list[dict[str, str]] = []
        for row in reader:
            total += 1
            batch.append(_normalize_row(row, header_map))
            if len(batch) >= chunk_size:
                yield batch
                batch = []

        if batch:
            yield batch

    return {"total": total, "columns": columns}


# ── Excel 读取 ────────────────────────────────────────────────────────────


def read_customers_from_excel(
    file_path: str | Path,
    sheet_name: str | int = 0,
    chunk_size: int = 100,
) -> Generator[list[dict[str, str]], None, dict[str, Any]]:
    """从 Excel (.xlsx) 文件读取客户数据（生成器）

    Args:
        file_path: Excel 文件路径
        sheet_name: 工作表名或索引 (默认 0=第一个)
        chunk_size: 每批返回的记录数

    Yields:
        每一批客户字典列表

    Returns:
        摘要信息 dict
    """
    try:
        import openpyxl
    except ImportError:
        raise ImportError("读取 Excel 需要 openpyxl 库: pip install openpyxl")

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Excel 文件不存在: {path}")

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)

    if isinstance(sheet_name, int):
        ws = wb.worksheets[sheet_name]
    else:
        ws = wb[sheet_name]

    rows = ws.iter_rows(values_only=True)

    # 第一行作为表头
    try:
        raw_headers = [str(c) if c is not None else "" for c in next(rows)]
    except StopIteration:
        return {"total": 0, "columns": []}

    header_map = _normalize_headers(raw_headers)
    columns = sorted(set(header_map.values()))

    total = 0
    batch: list[dict[str, str]] = []

    for cell_values in rows:
        # 如果整行为空则跳过
        if all(v is None or str(v).strip() == "" for v in cell_values):
            continue

        total += 1
        row_dict: dict[str, str] = {}
        for i, val in enumerate(cell_values):
            if i < len(raw_headers):
                raw_col = raw_headers[i]
                std_col = header_map.get(raw_col, raw_col)
                row_dict[std_col] = str(val).strip() if val is not None else ""

        batch.append(row_dict)
        if len(batch) >= chunk_size:
            yield batch
            batch = []

    if batch:
        yield batch

    wb.close()
    return {"total": total, "columns": columns}


# ── 统一读取入口 ──────────────────────────────────────────────────────────


def read_customers(
    file_path: str | Path,
    **kwargs: Any,
) -> Generator[list[dict[str, str]], None, dict[str, Any]]:
    """自动检测文件格式并读取客户数据

    支持 .csv / .xlsx 格式。通过文件扩展名自动选择读取器。

    Args:
        file_path: 文件路径
        **kwargs: 传递给具体读取器的额外参数

    Yields:
        每一批客户字典列表

    Returns:
        摘要信息 dict
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".csv":
        yield from read_customers_from_csv(path, **kwargs)
    elif ext in (".xlsx", ".xls"):
        yield from read_customers_from_excel(path, **kwargs)
    else:
        raise ValueError(f"不支持的文件格式: {ext}（仅支持 .csv / .xlsx）")


# ── 辅助函数 ──────────────────────────────────────────────────────────────


def _detect_encoding(path: Path) -> str:
    """自动检测文件编码"""
    try:
        import chardet
        raw = path.read_bytes()
        result = chardet.detect(raw)
        encoding = result.get("encoding", "utf-8")
        # chardet 有时返回 None
        if encoding is None:
            encoding = "utf-8"
        # utf-8 / utf-16 等
        return encoding.lower().replace(" ", "-")
    except ImportError:
        # 没有 chardet 时尝试常见编码
        for enc in ("utf-8-sig", "utf-8", "gbk", "gb2312", "latin-1"):
            try:
                path.read_text(encoding=enc)
                return enc
            except (UnicodeDecodeError, UnicodeError):
                continue
        return "utf-8"


def summarize_columns(columns: list[str]) -> dict[str, str]:
    """返回列名到中文描述的映射，方便用户理解"""
    descriptions: dict[str, str] = {
        "name": "客户名称 / 姓名",
        "phone": "联系电话",
        "email": "电子邮箱",
        "company": "公司 / 企业",
        "title": "职位",
        "address": "地址",
        "notes": "备注",
        "industry": "行业",
        "wechat": "微信号",
    }
    return {col: descriptions.get(col, col) for col in columns}
