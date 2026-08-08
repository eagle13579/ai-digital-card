"""
出海时光机引擎 v3 — 世界银行数据采集器
========================================
从世界银行开放 API (api.worldbank.org) 采集全球各国环境指标。

数据源：世界银行公开数据（合法合规，免费开放）
指标：dimensions.py 中定义的 ENV_DIMENSIONS 各维度
缓存：data/time_machine_engine/wb_cache.json（避免重复请求）

用法：
  from time_machine_engine.collector import WorldBankCollector
  c = WorldBankCollector()
  c.refresh_cache(force=False)   # 全量刷新缓存
  df = c.get_indicators(country_iso3, indicators, years)  # 获取数据
"""

import json
import os
import time
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

from .dimensions import ENV_DIMENSIONS

# 缓存路径（相对 backend 根目录）
BACKEND_DIR = Path("/var/www/ai-digital-card/backend")
CACHE_FILE = BACKEND_DIR / "data" / "time_machine_engine" / "wb_cache.json"

BASE_URL = "https://api.worldbank.org/v2/country/all/indicator/{indicator}"
PAGE_SIZE = 1000  # 世界银行 API 单页上限
MAX_RETRY = 3
CACHE_TTL_HOURS = 168  # 缓存 7 天（世界银行数据月度更新）

# 需要采集的指标清单（从维度定义派生）
INDICATORS = {v["wb_indicator"]: k for k, v in ENV_DIMENSIONS.items()}


class WorldBankCollector:
    """世界银行数据采集器（带磁盘缓存）"""

    def __init__(self, cache_file: Path | str | None = None):
        self.cache_file = Path(cache_file) if cache_file else CACHE_FILE
        self._cache = self._load_cache()

    # ── 缓存 ──────────────────────────────────────────────

    def _load_cache(self) -> dict:
        if self.cache_file.exists():
            try:
                cache = json.loads(self.cache_file.read_text(encoding="utf-8"))
                # 注入地区补充数据（台湾等世界银行缺失地区）
                from .region_supplement import inject_supplement
                cache["data"] = inject_supplement(cache.get("data", {}))
                return cache
            except Exception:
                pass
        return {"fetched_at": None, "data": {}}

    def _save_cache(self):
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(
            json.dumps(self._cache, ensure_ascii=False), encoding="utf-8"
        )

    def _cache_fresh(self) -> bool:
        ts = self._cache.get("fetched_at")
        if not ts:
            return False
        try:
            age_h = (time.time() - ts) / 3600
            return age_h < CACHE_TTL_HOURS
        except Exception:
            return False

    # ── HTTP ──────────────────────────────────────────────

    def _http_get_json(self, url: str, timeout: int = 20) -> dict | list | None:
        """带重试的 GET 请求"""
        for attempt in range(MAX_RETRY):
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) TimeMachine/3.0",
                    "Accept": "application/json",
                })
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return json.loads(resp.read().decode("utf-8", errors="ignore"))
            except Exception as e:
                if attempt < MAX_RETRY - 1:
                    time.sleep(2 * (attempt + 1))
                else:
                    print(f"  ⚠️ 请求失败 {url[:80]}: {e}")
        return None

    # ── 采集 ──────────────────────────────────────────────

    def fetch_indicator(self, indicator: str, start_year: int = 2000,
                        end_year: int | None = None) -> dict:
        """抓取单个指标全部国家的数据
        返回 {iso3: {year: value}}
        """
        end_year = end_year or datetime.now().year
        result: dict = {}
        page = 1
        total_pages = 1
        while page <= total_pages:
            url = (BASE_URL.format(indicator=indicator)
                   + f"?date={start_year}:{end_year}&format=json"
                   + f"&per_page={PAGE_SIZE}&page={page}")
            data = self._http_get_json(url)
            if not data or len(data) < 2 or not isinstance(data[1], list):
                break
            meta = data[0] if isinstance(data[0], dict) else {}
            total_pages = meta.get("pages", 1)
            for item in data[1]:
                iso3 = item.get("countryiso3code")
                year = item.get("date")
                value = item.get("value")
                if not iso3 or not year or value is None:
                    continue
                result.setdefault(iso3, {})[int(year)] = value
            page += 1
            if page > 1 and total_pages > 1:
                time.sleep(0.3)  # 温和限速
        return result

    def refresh_cache(self, force: bool = False, verbose: bool = True) -> dict:
        """全量刷新缓存（每个维度指标拉一遍）"""
        if self._cache_fresh() and not force:
            if verbose:
                print("缓存仍有效，跳过刷新（--force 可强制）")
            return self._cache

        if verbose:
            print(f"开始采集 {len(INDICATORS)} 个指标...")
        for i, (indicator, dim_key) in enumerate(INDICATORS.items(), 1):
            if verbose:
                print(f"  [{i}/{len(INDICATORS)}] {dim_key} ({indicator})...")
            data = self.fetch_indicator(indicator)
            self._cache["data"][dim_key] = data
            if verbose:
                print(f"    → {sum(len(v) for v in data.values())} 条记录")
            time.sleep(0.5)

        self._cache["fetched_at"] = time.time()
        self._save_cache()
        if verbose:
            print(f"✅ 缓存已更新: {self.cache_file}")
        return self._cache

    # ── 查询 ──────────────────────────────────────────────

    def get_country_series(self, iso3: str, dim_key: str,
                           years: list[int] | None = None) -> dict:
        """获取某国某维度的年度序列 {year: value}
        注意: 世界银行 API 返回的 date 是字符串，缓存 JSON 后 int 会变 str，
        查询时统一做 int 兼容。
        """
        data = self._cache.get("data", {}).get(dim_key, {})
        series = data.get(iso3, {})
        if years:
            years_set = {int(y) for y in years}
            series = {int(y): v for y, v in series.items() if int(y) in years_set}
        else:
            series = {int(y): v for y, v in series.items()}
        return series

    def get_country_avg(self, iso3: str, dim_key: str,
                        years: list[int] | None = None) -> float | None:
        """获取某国某维度的均值（可指定年份区间）"""
        series = self.get_country_series(iso3, dim_key, years)
        vals = [v for v in series.values() if v is not None and v != ""]
        if not vals:
            return None
        return round(sum(vals) / len(vals), 4)

    def percentile_of(self, iso3: str, dim_key: str,
                      years: list[int] | None = None) -> float | None:
        """某国某维度值在全球分布的百分位 (0-1)
        百分位匹配 = 发展阶段相似性（消除绝对量纲/国别差异）
        """
        target = self.get_country_avg(iso3, dim_key, years)
        if target is None:
            return None
        all_vals = []
        for ciso in self.available_countries():
            v = self.get_country_avg(ciso, dim_key, years)
            if v is not None:
                all_vals.append(v)
        if not all_vals:
            return None
        below = sum(1 for v in all_vals if v < target)
        return round(below / len(all_vals), 4)

    def percentile_map(self, dim_key: str,
                       years: list[int] | None = None) -> dict[str, float]:
        """所有国家某维度的百分位映射 {iso3: percentile}"""
        result = {}
        all_vals = {}
        for ciso in self.available_countries():
            v = self.get_country_avg(ciso, dim_key, years)
            if v is not None:
                all_vals[ciso] = v
        if not all_vals:
            return result
        sorted_vals = sorted(all_vals.values())
        n = len(sorted_vals)
        for ciso, v in all_vals.items():
            below = sum(1 for x in sorted_vals if x < v)
            result[ciso] = round(below / n, 4)
        return result

    def available_countries(self, min_dims: int = 5) -> list[str]:
        """返回数据覆盖足够维度的国家列表（排除世界银行聚合区）"""
        from .dimensions import EXCLUDE_AGGREGATES
        counts: dict = {}
        for dim_key, cdata in self._cache.get("data", {}).items():
            for iso3 in cdata:
                counts[iso3] = counts.get(iso3, 0) + 1
        return sorted(
            iso3 for iso3, n in counts.items()
            if n >= min_dims and iso3 not in EXCLUDE_AGGREGATES
        )

    def cache_summary(self) -> dict:
        """缓存概览"""
        data = self._cache.get("data", {})
        summary = {
            "fetched_at": self._cache.get("fetched_at"),
            "dimensions": len(data),
            "per_dimension": {k: sum(len(v) for v in d.values()) for k, d in data.items()},
            "countries_with_data": len(self.available_countries()),
        }
        return summary
