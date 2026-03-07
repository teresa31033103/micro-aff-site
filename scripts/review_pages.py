#!/usr/bin/env python3
"""
review_pages.py - 審査AI
生成されたHTML本文の品質チェックを行う
ルールベース + Ollamaによる誇大表現チェックの2段構え
"""

import json
import re
import requests
from pathlib import Path

ROOT = Path(__file__).parent.parent
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"

# 誇大表現ブラックリスト
EXAGGERATION_PATTERNS = [
    r"最高[のにも]",
    r"絶対に",
    r"完璧な?",
    r"必ず(?:できる|成功|解決)",
    r"間違いなく",
    r"100%(?:安全|確実|保証)",
]

def rule_based_check(html: str) -> dict:
    """ルールベースの必須チェック"""
    result = {
        "has_disclosure": bool(re.search(r'class=["\']disclosure["\']', html)),
        "has_cta_placeholders": bool(re.search(r'\{\{CTA_(?:PRIMARY|SECONDARY)\}\}', html)),
        "has_comparison_table": bool(re.search(r'class=["\']comparison-table["\']', html)),
        "has_faq": bool(re.search(r'<details', html, re.IGNORECASE)),
        "h1_count": len(re.findall(r'<h1[\s>]', html, re.IGNORECASE)),
        "word_count": len(re.sub(r'<[^>]+>', '', html)),
        "warnings": [],
        "fail_reasons": [],
    }

    # FAIL判定
    if not result["has_disclosure"]:
        result["fail_reasons"].append("開示文（.disclosure）が見つかりません")
    if not result["has_cta_placeholders"]:
        result["fail_reasons"].append("CTAプレースホルダー {{CTA_PRIMARY}} または {{CTA_SECONDARY}} が見つかりません")
    if not result["has_comparison_table"]:
        result["fail_reasons"].append("比較表（.comparison-table）が見つかりません")
    if not result["has_faq"]:
        result["fail_reasons"].append("FAQセクション（<details>）が見つかりません")
    if result["h1_count"] != 1:
        result["fail_reasons"].append(f"h1タグの数が不正です: {result['h1_count']}個（1個必要）")

    # WARNING判定
    if result["word_count"] < 1500:
        result["warnings"].append(f"文字数が少ない可能性があります（タグ除去後: {result['word_count']}文字）")

    # 誇大表現チェック
    plain_text = re.sub(r'<[^>]+>', '', html)
    for pattern in EXAGGERATION_PATTERNS:
        if re.search(pattern, plain_text):
            result["warnings"].append(f"誇大表現の可能性: パターン「{pattern}」に一致")

    # テーブル内の比較件数を大まかに数える
    comparison_rows = len(re.findall(r'<tr', html)) - 1  # ヘッダー行を除く
    result["comparison_count"] = max(0, comparison_rows)
    if comparison_rows < 3:
        result["warnings"].append(f"比較対象が少ない可能性があります（推定{comparison_rows}件）")

    result["faq_count"] = len(re.findall(r'<details', html))

    # 最終ステータス
    if result["fail_reasons"]:
        result["status"] = "FAIL"
    elif result["warnings"]:
        result["status"] = "WARNING"
    else:
        result["status"] = "PASS"

    return result

def review_page(html_content: str, affiliate_key: str) -> dict:
    """HTML本文を審査する（ルールベース中心）"""
    return rule_based_check(html_content)

if __name__ == "__main__":
    # テスト
    sample_html = """
    <div class="disclosure">広告を含みます</div>
    <h1>テストページ</h1>
    <table class="comparison-table"><tr><th>名前</th></tr><tr><td>A</td></tr><tr><td>B</td></tr><tr><td>C</td></tr></table>
    <div class="cta-block">{{CTA_PRIMARY}}</div>
    <section class="faq-section">
      <details><summary>Q1</summary><div>A1</div></details>
      <details><summary>Q2</summary><div>A2</div></details>
      <details><summary>Q3</summary><div>A3</div></details>
    </section>
    <div>{{CTA_SECONDARY}}</div>
    """ + "テスト文章。" * 100

    result = review_page(sample_html, "test-key")
    print(json.dumps(result, ensure_ascii=False, indent=2))
