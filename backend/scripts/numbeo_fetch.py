"""
Numbeo 房价收入比抓取脚本（反向时光机辅助数据源）
=================================================
抓取 https://www.numbeo.com/property-investment/rankings_by_country.jsp 的
Price To Income Ratio（房价收入比）→ 存 JSON 供 reverse_time_machine 使用。

数据说明:
  - 房价收入比 = 房价 / 家庭年收入，是判断房产泡沫的核心指标
  - 中国 17.35 / 香港 35.19 / 日本 11.69 (2026-08 抓取)
  - 参考: 全球健康区间 3-6, 泡沫警戒 > 10

用法:
  python3 numbeo_fetch.py            # 抓取并保存
  python3 numbeo_fetch.py --check    # 只读本地缓存
"""
import json
import os
import re
import sys
import time
import urllib.request

DATA_DIR = "/var/www/ai-digital-card/backend/data/time_machine_engine"
OUT_PATH = os.path.join(DATA_DIR, "numbeo_price_income.json")

URL = "https://www.numbeo.com/property-investment/rankings_by_country.jsp"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def fetch() -> dict:
    req = urllib.request.Request(URL, headers=UA)
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", errors="ignore")
    pairs = re.findall(r"\['([^']+)',\s*([\d.]+)\]", html)
    data = {name.strip(): float(v) for name, v in pairs}
    # 英文名 → ISO3 映射（反向时光机用 ISO3）
    EN2ISO = {
        "China": "CHN", "Japan": "JPN", "Hong Kong (China)": "HKG",
        "Taiwan": "TWN", "South Korea": "KOR", "Singapore": "SGP",
        "United States": "USA", "United Kingdom": "GBR", "Germany": "DEU",
        "France": "FRA", "Australia": "AUS", "Canada": "CAN",
        "Vietnam": "VNM", "Thailand": "THA", "Indonesia": "IDN",
        "Philippines": "PHL", "Malaysia": "MYS", "India": "IND",
        "Brazil": "BRA", "Mexico": "MEX", "Russia": "RUS",
        "Turkey": "TUR", "South Africa": "ZAF", "Egypt": "EGY",
        "Israel": "ISR", "Saudi Arabia": "SAU", "United Arab Emirates": "ARE",
        "Qatar": "QAT", "Kuwait": "KWT", "New Zealand": "NZL",
        "Netherlands": "NLD", "Sweden": "SWE", "Norway": "NOR",
        "Denmark": "DNK", "Finland": "FIN", "Switzerland": "CHE",
        "Italy": "ITA", "Spain": "ESP", "Portugal": "PRT",
        "Poland": "POL", "Czech Republic": "CZE", "Ireland": "IRL",
        "Belgium": "BEL", "Austria": "AUT", "Argentina": "ARG",
        "Chile": "CHL", "Colombia": "COL", "Peru": "PER",
        "Pakistan": "PAK", "Bangladesh": "BGD", "Sri Lanka": "LKA",
        "Nepal": "NPL", "Kazakhstan": "KAZ", "Nigeria": "NGA",
        "Kenya": "KEN", "Ethiopia": "ETH", "Morocco": "MAR",
        "Algeria": "DZA", "Greece": "GRC", "Romania": "ROU",
        "Hungary": "HUN", "Ukraine": "UKR", "Iran": "IRN",
        "Iraq": "IRQ", "Jordan": "JOR", "Lebanon": "LBN",
        "Cyprus": "CYP", "Panama": "PAN", "Costa Rica": "CRI",
        "Uruguay": "URY", "Paraguay": "PRY", "Bolivia": "BOL",
        "Ecuador": "ECU", "Dominican Republic": "DOM", "Croatia": "HRV",
        "Serbia": "SRB", "Slovenia": "SVN", "Slovakia": "SVK",
        "Lithuania": "LTU", "Latvia": "LVA", "Estonia": "EST",
        "Bulgaria": "BGR", "Azerbaijan": "AZE", "Georgia": "GEO",
        "Armenia": "ARM", "Belarus": "BLR", "Tanzania": "TZA",
        "Uganda": "UGA", "Ghana": "GHA", "Cameroon": "CMR",
        "Ivory Coast": "CIV", "Senegal": "SEN", "Tunisia": "TUN",
        "Oman": "OMN", "Bahrain": "BHR", "Kyrgyzstan": "KGZ",
        "Uzbekistan": "UZB", "Mongolia": "MNG", "Myanmar": "MMR",
        "Laos": "LAO", "Cambodia": "KHM", "Fiji": "FJI",
    }
    iso_data = {}
    mapped = 0
    for name, val in data.items():
        iso = EN2ISO.get(name)
        if iso:
            iso_data[iso] = val
            mapped += 1
    payload = {
        "source": "numbeo",
        "metric": "price_to_income_ratio",
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_raw": len(data),
        "total_iso": mapped,
        "values": iso_data,
    }
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    return payload


def check() -> dict:
    if not os.path.exists(OUT_PATH):
        print("本地无缓存，先 fetch")
        return {}
    with open(OUT_PATH, encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    if "--check" in sys.argv:
        p = check()
        if p:
            print(f"缓存: {p.get('fetched_at')} | {p.get('total_iso')} 国")
            for k in ["CHN", "HKG", "JPN", "KOR", "TWN", "SGP", "USA"]:
                print(f"  {k}: {p['values'].get(k, '-')}")
    else:
        p = fetch()
        print(f"抓取完成: {p['total_raw']} 原始 / {p['total_iso']} 映射ISO3")
        print(f"保存: {OUT_PATH}")
        for k in ["CHN", "HKG", "JPN", "KOR", "TWN", "SGP", "USA"]:
            print(f"  {k}: {p['values'].get(k, '-')}")
