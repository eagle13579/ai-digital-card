"""Baidu search for Xiaohongshu food compliance resources"""
import subprocess, sys, re, json

def search_baidu(query):
    """Search Baidu and return results"""
    url = f"https://www.baidu.com/s?wd={query}"
    cmd = ["curl", "-s", url, "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.stdout

def parse_baidu_results(html):
    """Extract search results from Baidu HTML"""
    results = []
    # Match titles and snippets
    # Baidu uses various formats
    # Method 1: h3 tags
    for m in re.finditer(r'<h3[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL):
        url = m.group(1)
        title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        if title and ('小红书' in title or 'xiaohongshu' in url.lower() or 'xhs' in title.lower() or '食品' in title):
            results.append({'title': title, 'url': url})
    
    # Method 2: div with class c-abstract
    for m in re.finditer(r'<span[^>]*class="content-right_[^"]*"[^>]*>(.*?)</span>', html, re.DOTALL):
        text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        if text:
            results.append({'snippet': text[:200]})
    
    return results

if __name__ == "__main__":
    queries = [
        "小红书 食品合规 博主",
        "小红书 食品安全 热门博主",
        "小红书 食品标签 合规 知识博主",
        "site:xiaohongshu.com 食品合规",
        "小红书 食品检测 认证 博主",
        "小红书 食品法规 知乎 博主"
    ]
    
    all_results = []
    for q in queries:
        print(f"\n=== 搜索: {q} ===")
        try:
            html = search_baidu(q)
            results = parse_baidu_results(html)
            for r in results[:5]:
                print(f"  {r.get('title', r.get('snippet', ''))[:120]}")
                if 'url' in r:
                    print(f"    {r['url'][:100]}")
            all_results.extend(results)
        except Exception as e:
            print(f"  ❌ 搜索失败: {e}")
    
    # Deduplicate
    seen = set()
    deduped = []
    for r in all_results:
        key = r.get('title', r.get('snippet', ''))[:50]
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    
    print(f"\n\n总计获取 {len(deduped)} 条结果")
    
    # Save results
    with open(r'D:\AI数智名片\backend\scripts\xhs_search_results.json', 'w', encoding='utf-8') as f:
        json.dump(deduped, f, ensure_ascii=False, indent=2)
    print(f"已保存到 xhs_search_results.json")
