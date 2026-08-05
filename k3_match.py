#!/usr/bin/env python3
"""AI数智名片 × K3 匹配增强 — 1M上下文一次性理解企业全部资料
用法: python k3_match.py <企业资料文件>
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "baize_libs"))
from kimi_k3_service import KimiK3Client, KimiK3Router

PROMPT = """你是一个企业供需匹配专家。
请分析以下企业资料，输出：

## 一、企业画像
- 主营业务、规模、行业地位
- 核心能力/资源
- 当前痛点/需求

## 二、匹配机会
- 适合对接的供应商/客户类型
- 跨境合作可能性（韩国/中国）
- 匹配优先级排序

## 三、一句话推荐语（用于数字名片展示）

企业资料：
---
{content}
---"""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python k3_match.py <企业资料文件>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    print(f"[K3匹配] 企业资料: {os.path.basename(filepath)} ({len(content)}字)")
    
    client = KimiK3Client()
    router = KimiK3Router()
    
    if router.should_use_k3("analysis", len(content)):
        result = client.chat_completion(PROMPT.format(content=content[:500000]))
    else:
        print("[路由] 内容较短，建议用deepseek处理")
        result = PROMPT.format(content=content[:500000])
    
    output = filepath.replace(".", "_K3匹配报告.")
    with open(output, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"匹配报告: {output}")
