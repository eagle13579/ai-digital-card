"""
AI数字名片 — 翻译核心服务 (Translation Service)
=================================================

从 auto_translate.py 中提取的核心翻译逻辑，供 Web 路由调用。
支持:
  - 列出所有翻译 key 及各语言状态
  - DeepSeek 自动翻译缺失 key
  - 人工修正单条翻译
  - 翻译覆盖率统计
"""

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ════════════════════════════════════════════════════════════
# 路径 & 常量
# ════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # D:/AI数智名片
BACKEND_I18N_DIR = PROJECT_ROOT / "backend" / "app" / "i18n"
BACKEND_I18N_FILE = BACKEND_I18N_DIR / "__init__.py"

ALL_LANGS = ["zh", "en", "ja", "ko", "es", "fr", "de", "pt", "ru", "ar", "th", "vi"]
NON_ZH_LANGS = [l for l in ALL_LANGS if l != "zh"]

LANG_NAMES = {
    "zh": "简体中文", "en": "English", "ja": "日本語", "ko": "한국어",
    "es": "Español", "fr": "Français", "de": "Deutsch", "pt": "Português",
    "ru": "Русский", "ar": "العربية", "th": "ไทย", "vi": "Tiếng Việt",
}

BATCH_SIZE = 20
MAX_RETRIES = 3
RETRY_DELAY_SEC = 5


# ════════════════════════════════════════════════════════════
# 数据结构
# ════════════════════════════════════════════════════════════


@dataclass
class TranslationEntry:
    """单个翻译条目"""
    key: str
    zh: str
    en: Optional[str] = None
    context: str = ""


@dataclass
class TranslationResult:
    """翻译结果统计"""
    total_keys: int = 0
    existing_keys: int = 0
    translated_keys: int = 0
    failed_keys: int = 0
    failed_details: list[str] = field(default_factory=list)
    elapsed: float = 0.0


# ════════════════════════════════════════════════════════════
# 解析器
# ════════════════════════════════════════════════════════════


class BackendI18nParser:
    """解析 backend/app/i18n/__init__.py 中的 TRANSLATIONS 字典"""

    SECTION_PATTERN = re.compile(r'# ── (.+?) ─')

    @classmethod
    def parse(cls, filepath: Path = BACKEND_I18N_FILE) -> dict[str, TranslationEntry]:
        """解析 i18n/__init__.py 返回 {key: TranslationEntry}"""
        if not filepath.exists():
            return {}

        content = filepath.read_text(encoding="utf-8")
        entries: dict[str, TranslationEntry] = {}
        current_section = ""

        for line in content.splitlines():
            m = cls.SECTION_PATTERN.search(line)
            if m:
                current_section = m.group(1).strip()

            match = re.match(
                r'\s*["\']([^"\']+)["\']\s*:\s*_fill_langs\(\{([^}]+)\}\).*,?\s*',
                line,
            )
            if not match:
                continue

            key = match.group(1)
            dict_body = match.group(2)
            zh_val = cls._extract_lang_value(dict_body, "zh")
            en_val = cls._extract_lang_value(dict_body, "en")

            if zh_val:
                entries[key] = TranslationEntry(
                    key=key, zh=zh_val, en=en_val, context=current_section,
                )

        return entries

    @staticmethod
    def _extract_lang_value(dict_body: str, lang: str) -> Optional[str]:
        m = re.search(rf'["\']{lang}["\']\s*:\s*["\']([^"\']*)["\']', dict_body)
        return m.group(1) if m else None


# ════════════════════════════════════════════════════════════
# 加载器
# ════════════════════════════════════════════════════════════


class BackendTranslationLoader:
    """从 i18n/__init__.py 加载指定语言的已有翻译"""

    @classmethod
    def load_existing(cls, filepath: Path, lang: str) -> dict[str, str]:
        """提取指定语言的所有已有翻译，返回 {key: translation}"""
        if not filepath.exists():
            return {}

        content = filepath.read_text(encoding="utf-8")
        existing: dict[str, str] = {}

        for line in content.splitlines():
            match = re.match(
                r'\s*["\']([^"\']+)["\']\s*:\s*_fill_langs\(\{([^}]+)\}\).*,?\s*',
                line,
            )
            if not match:
                continue
            key = match.group(1)
            dict_body = match.group(2)
            val = BackendI18nParser._extract_lang_value(dict_body, lang)
            if val:
                existing[key] = val

        return existing


# ════════════════════════════════════════════════════════════
# 统计
# ════════════════════════════════════════════════════════════


def get_translation_stats() -> dict:
    """计算翻译覆盖率统计，返回 {lang: {total, translated, missing_count, completion_pct}}"""
    source_entries = BackendI18nParser.parse()
    if not source_entries:
        return {}

    total = len(source_entries)
    stats = {}

    for lang in ALL_LANGS:
        existing = BackendTranslationLoader.load_existing(BACKEND_I18N_FILE, lang)
        translated = len(existing)
        missing_count = total - translated
        completion_pct = round(translated / total * 100, 1) if total > 0 else 0.0
        stats[lang] = {
            "lang_code": lang,
            "lang_name": LANG_NAMES.get(lang, lang),
            "total": total,
            "translated": translated,
            "missing_count": missing_count,
            "completion_pct": completion_pct,
        }

    return stats


def list_all_keys_with_status() -> list[dict]:
    """列出所有翻译 key 及每个语言的状态"""
    source_entries = BackendI18nParser.parse()
    if not source_entries:
        return []

    # 为每个语言加载已有翻译
    existing_per_lang: dict[str, dict[str, str]] = {}
    for lang in ALL_LANGS:
        existing_per_lang[lang] = BackendTranslationLoader.load_existing(
            BACKEND_I18N_FILE, lang
        )

    result = []
    for key, entry in source_entries.items():
        lang_status = {}
        for lang in ALL_LANGS:
            val = existing_per_lang[lang].get(key)
            lang_status[lang] = val if val else ""
        result.append({
            "key": key,
            "zh": entry.zh,
            "en": entry.en or "",
            "context": entry.context,
            "languages": lang_status,
        })

    return result


# ════════════════════════════════════════════════════════════
# 翻译引擎
# ════════════════════════════════════════════════════════════


class DeepSeekTranslator:
    """DeepSeek API 翻译引擎"""

    API_URL = "https://api.deepseek.com/v1/chat/completions"
    MODEL = "deepseek-chat"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def translate_batch(
        self,
        entries: list[TranslationEntry],
        target_lang: str,
    ) -> list[tuple[str, str]]:
        """批量翻译一批条目，返回 [(key, translated_text), ...]"""
        if not entries:
            return []

        target_name = LANG_NAMES.get(target_lang, target_lang)
        source_lang_name = LANG_NAMES.get("zh", "简体中文")

        texts = [f"[{e.key}] {e.zh}" for e in entries]
        texts_str = "\n".join(texts)

        system_prompt = (
            f"你是一个专业的翻译专家。请将以下从 {source_lang_name} 到 {target_name} 的翻译任务完成。\n"
            f"要求：\n"
            f"1. 保持专业、自然的语气\n"
            f"2. 保持占位符 {{variable}} 不变，不要翻译它们\n"
            f"3. 保持原有的标点符号风格\n"
            f"4. 返回 JSON 格式: {{\"translations\": [{{\"key\": \"...\", \"translation\": \"...\"}}, ...]}}\n"
            f"5. 不要改变 key 值，只翻译翻译文本部分\n"
            f"6. 每行格式为 [key] 原文，请在翻译结果中保持 key 不变"
        )

        user_prompt = f"请将以下内容翻译成 {target_name}：\n\n{texts_str}"

        payload = {
            "model": self.MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 4096,
            "response_format": {"type": "json_object"},
        }

        result = self._call_api(payload)
        return self._parse_result(result, entries)

    def _call_api(self, payload: dict) -> Optional[dict]:
        """调用 DeepSeek API"""
        import urllib.request as request_lib

        data = json.dumps(payload).encode("utf-8")
        req = request_lib.Request(
            self.API_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        for attempt in range(MAX_RETRIES):
            try:
                with request_lib.urlopen(req, timeout=60) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except Exception as e:
                print(f"  [WARN] API 调用失败 (第 {attempt + 1}/{MAX_RETRIES} 次): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY_SEC)
                else:
                    return None

    def _parse_result(
        self, api_result: Optional[dict], entries: list[TranslationEntry]
    ) -> list[tuple[str, str]]:
        """解析 API 返回结果"""
        if not api_result:
            return [(e.key, "") for e in entries]

        try:
            content = api_result["choices"][0]["message"]["content"]
            data = json.loads(content)
            translations = data.get("translations", [])
            result_map = {item["key"]: item["translation"] for item in translations}
            return [(e.key, result_map.get(e.key, "")) for e in entries]
        except (KeyError, json.JSONDecodeError, TypeError):
            return self._fallback_parse(api_result, entries)

    def _fallback_parse(
        self, api_result: dict, entries: list[TranslationEntry]
    ) -> list[tuple[str, str]]:
        """备用解析：直接从 content 文本中读取"""
        try:
            content = api_result.get("choices", [{}])[0].get("message", {}).get("content", "")
            results = []
            for entry in entries:
                m = re.search(rf'\[{re.escape(entry.key)}\].*?["\']?([^"\'\n]+)', content)
                results.append((entry.key, m.group(1).strip() if m else ""))
            return results
        except Exception:
            return [(e.key, "") for e in entries]


# ════════════════════════════════════════════════════════════
# 写入器
# ════════════════════════════════════════════════════════════


class BackendTranslationWriter:
    """更新 backend/app/i18n/__init__.py 中的 TRANSLATIONS 字典"""

    @classmethod
    def write(
        cls,
        filepath: Path,
        source_entries: dict[str, TranslationEntry],
        target_lang: str,
        translations: dict[str, str],
        incremental: bool = True,
    ) -> int:
        """将翻译合并到 i18n/__init__.py 文件中，返回更新的行数"""
        if not filepath.exists():
            return 0

        content = filepath.read_text(encoding="utf-8")
        lines = content.splitlines()
        updated_count = 0
        new_lines = []

        for line in lines:
            match = re.match(
                r'\s*["\']([^"\']+)["\']\s*:\s*_fill_langs\(\{([^}]*)\}\).*,?\s*',
                line,
            )
            if match:
                key = match.group(1)
                if key in translations:
                    dict_body = match.group(2)
                    old_val = BackendI18nParser._extract_lang_value(dict_body, target_lang)

                    # 如果已有翻译且 incremental=True，跳过
                    if incremental and old_val:
                        new_lines.append(line)
                        continue

                    new_val = translations[key]
                    if not new_val:
                        new_lines.append(line)
                        continue

                    # 如果该语言已存在，替换值
                    if target_lang in dict_body:
                        new_dict = re.sub(
                            rf'["\']{target_lang}["\']\s*:\s*["\'][^"\']*["\']',
                            f'"{target_lang}": "{new_val}"',
                            dict_body,
                        )
                    else:
                        new_dict = dict_body.rstrip().rstrip(",")
                        new_dict += f', "{target_lang}": "{new_val}"'

                    indent = re.match(r'(\s*)', line).group(1)
                    new_line = f'{indent}"{key}": _fill_langs({{{new_dict}}}),'
                    new_lines.append(new_line)
                    updated_count += 1
                    continue

            new_lines.append(line)

        filepath.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        return updated_count


# ════════════════════════════════════════════════════════════
# 主管道
# ════════════════════════════════════════════════════════════


def auto_translate(
    target_langs: Optional[list[str]] = None,
    incremental_only: bool = True,
    dry_run: bool = False,
) -> dict[str, TranslationResult]:
    """运行自动翻译管道（后端模式），返回 {lang: TranslationResult}

    Args:
        target_langs: 目标语言列表，默认所有非 zh 语言
        incremental_only: 仅翻译缺失 key，不覆盖已有翻译
        dry_run: 预览模式，不调用 API 也不写入

    Returns:
        {lang_code: TranslationResult}
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key and not dry_run:
        raise ValueError("环境变量 DEEPSEEK_API_KEY 未设置")

    target_langs = target_langs or NON_ZH_LANGS

    translator = DeepSeekTranslator(api_key) if api_key else None

    source_entries = BackendI18nParser.parse()
    if not source_entries:
        return {}

    results: dict[str, TranslationResult] = {}

    for lang in target_langs:
        result = TranslationResult(total_keys=len(source_entries))
        existing = BackendTranslationLoader.load_existing(BACKEND_I18N_FILE, lang)
        result.existing_keys = len(existing)

        missing_entries = []
        for key, entry in source_entries.items():
            if key not in existing or not existing[key]:
                missing_entries.append(entry)
            elif not incremental_only:
                missing_entries.append(entry)

        if not missing_entries:
            result.translated_keys = 0
            results[lang] = result
            continue

        translations: dict[str, str] = {}
        start_time = time.time()

        if dry_run:
            result.translated_keys = len(missing_entries)
        else:
            for i in range(0, len(missing_entries), BATCH_SIZE):
                batch = missing_entries[i : i + BATCH_SIZE]
                batch_results = translator.translate_batch(batch, lang)
                for key, val in batch_results:
                    if val:
                        translations[key] = val
                        result.translated_keys += 1
                    else:
                        result.failed_keys += 1
                        result.failed_details.append(key)

                if i + BATCH_SIZE < len(missing_entries):
                    time.sleep(1)

        result.elapsed = time.time() - start_time

        # 写入文件
        if not dry_run and translations:
            BackendTranslationWriter.write(
                BACKEND_I18N_FILE,
                source_entries,
                lang,
                translations,
                incremental=incremental_only,
            )

        results[lang] = result

    return results


def update_single_translation(key: str, lang: str, value: str) -> bool:
    """人工修正某条翻译，更新到 i18n/__init__.py

    Args:
        key: 翻译键名
        lang: 目标语言代码
        value: 新的翻译文本

    Returns:
        是否成功更新
    """
    content = BACKEND_I18N_FILE.read_text(encoding="utf-8")
    lines = content.splitlines()
    new_lines = []
    updated = False

    for line in lines:
        match = re.match(
            r'\s*["\']([^"\']+)["\']\s*:\s*_fill_langs\(\{([^}]*)\}\).*,?\s*',
            line,
        )
        if match and match.group(1) == key:
            dict_body = match.group(2)
            escaped_val = value.replace("\\", "\\\\").replace('"', '\\"')

            if lang in dict_body:
                new_dict = re.sub(
                    rf'["\']{lang}["\']\s*:\s*["\'][^"\']*["\']',
                    f'"{lang}": "{escaped_val}"',
                    dict_body,
                )
            else:
                new_dict = dict_body.rstrip().rstrip(",")
                new_dict += f', "{lang}": "{escaped_val}"'

            indent = re.match(r'(\s*)', line).group(1)
            new_line = f'{indent}"{key}": _fill_langs({{{new_dict}}}),'
            new_lines.append(new_line)
            updated = True
        else:
            new_lines.append(line)

    if updated:
        BACKEND_I18N_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    return updated
