#!/usr/bin/env python3
"""
review_pages.py - 審査AI（選び方ガイド形式・強化版）
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent

# 根拠のない断定・誇大表現
EXAGGERATION_PATTERNS = [
    (r"最高[のにも]",       "根拠のない最上級「最高」"),
    (r"最速",               "根拠のない最上級「最速」"),
    (r"No\.?1\b",           "根拠のない「No.1」"),
    (r"業界最安",           "根拠のない「業界最安」"),
    (r"絶対に",             "断定表現「絶対に」"),
    (r"完璧な?[ーにも]",    "断定表現「完璧」"),
    (r"必ず(?:できる|成功|解決)", "断定表現「必ず」"),
    (r"100%(?:安全|確実|保証)", "断定表現「100%〜」"),
    (r"最優秀",             "根拠のない「最優秀」"),
]

# AI生成特有の不自然語（Ollamaが出しやすいパターン）
UNNATURAL_PATTERNS = [
    (r"高[-‐]speed",            "不自然な英語混在「高-speed」"),
    (r"[Ss]erver機能",          "不自然な英語混在「Server機能」"),
    (r"プライバシーキャンセル",  "意味不明な造語「プライバシーキャンセル」"),
    (r"[Ss]ecurity機能",        "不自然な英語混在「Security機能」"),
    (r"高[-‐]performance",      "不自然な英語混在「高-performance」"),
    (r"テレワークを取り組む",    "不自然な表現「テレワークを取り組む」"),
    (r"企業や個人(?:が|の)(?:テレワーク|リモート)", "不自然な主語構文"),
    (r"ご案内します",           "過剰な敬語「ご案内します」"),
    (r"提供します(?:ので|から)", "AI的な言い回し「提供しますので」"),
    (r"人々(?:が|の|に)",       "不自然な文語「人々」"),
]

# 具体的な価格・料金
PRICE_PATTERNS = [
    (r"月額\s*[\d,]+\s*円",         "根拠のない具体価格（月額〇〇円）"),
    (r"年額\s*[\d,]+\s*円",         "根拠のない具体価格（年額〇〇円）"),
    (r"¥\s*[\d,]+",                 "根拠のない価格（¥〇〇）"),
    (r"\$\s*[\d.]+\s*(?:/月|/年|per month)", "根拠のない価格（$〇〇）"),
    (r"[\d,]+\s*円[/／]月",         "根拠のない価格（〇〇円/月）"),
]

# 速度・性能の数値
SPEED_PATTERNS = [
    (r"\d+\s*[MGT]bps",     "根拠のない速度数値（〇〇Mbps等）"),
    (r"\d+\s*GB[/／](?:月|日)", "根拠のない容量数値（〇〇GB/月等）"),
    (r"99\.?\d*%(?:稼働|アップタイム)", "根拠のない稼働率数値"),
]


def rule_based_check(html: str) -> dict:
    """選び方ガイド形式の審査"""
    plain_text = re.sub(r'<[^>]+>', '', html)

    result = {
        "has_disclosure":      bool(re.search(r'class=["\']disclosure["\']', html)),
        "has_cta_placeholders": bool(re.search(r'\{\{CTA_(?:PRIMARY|SECONDARY)\}\}', html)),
        "has_checklist":       bool(re.search(r'class=["\']checklist["\']', html)),
        "has_faq":             bool(re.search(r'<details', html, re.IGNORECASE)),
        "has_comparison_table": bool(re.search(r'class=["\']comparison-table["\']', html)),
        "h1_count":            len(re.findall(r'<h1[\s>]', html, re.IGNORECASE)),
        "word_count":          len(plain_text),
        "faq_count":           len(re.findall(r'<details', html)),
        "warnings":            [],
        "fail_reasons":        [],
    }

    # --- FAIL判定 ---
    if not result["has_disclosure"]:
        result["fail_reasons"].append("開示文（.disclosure）が見つかりません")
    if not result["has_cta_placeholders"]:
        result["fail_reasons"].append("CTAプレースホルダー {{CTA_PRIMARY}} または {{CTA_SECONDARY}} が見つかりません")
    if not result["has_checklist"]:
        result["fail_reasons"].append("チェックリスト（.checklist）が見つかりません")
    if not result["has_faq"]:
        result["fail_reasons"].append("FAQセクション（<details>）が見つかりません")
    if result["h1_count"] != 1:
        result["fail_reasons"].append(f"h1タグの数が不正: {result['h1_count']}個（1個必要）")
    # 比較表はガイド形式では FAIL
    if result["has_comparison_table"]:
        result["fail_reasons"].append("比較表（.comparison-table）が含まれています。選び方ガイド形式では使用禁止です")

    # --- WARNING判定 ---
    if result["word_count"] < 1500:
        result["warnings"].append(f"文字数不足（タグ除去後: {result['word_count']}文字、目安1500文字以上）")

    for pattern, label in EXAGGERATION_PATTERNS:
        if re.search(pattern, plain_text):
            result["warnings"].append(f"誇大・断定表現: {label}")

    for pattern, label in UNNATURAL_PATTERNS:
        if re.search(pattern, plain_text):
            result["warnings"].append(f"不自然表現: {label}")

    for pattern, label in PRICE_PATTERNS:
        if re.search(pattern, plain_text):
            result["warnings"].append(f"根拠のない価格表記: {label}")

    for pattern, label in SPEED_PATTERNS:
        if re.search(pattern, plain_text):
            result["warnings"].append(f"根拠のない数値表記: {label}")

    # --- ステータス確定 ---
    if result["fail_reasons"]:
        result["status"] = "FAIL"
    elif result["warnings"]:
        result["status"] = "WARNING"
    else:
        result["status"] = "PASS"

    return result


def review_page(html_content: str, affiliate_key: str) -> dict:
    return rule_based_check(html_content)


if __name__ == "__main__":
    print("=== テスト1: 正常なガイド形式 ===")
    good = """
    <div class="disclosure">広告を含みます</div>
    <h1>VPNの選び方ガイド</h1>
    <section>
      <h2>選ぶときのポイント</h2>
      <ul class="checklist">
        <li>暗号化方式をAES-256対応か確認する</li>
        <li>ノーログポリシーを公式で確認する</li>
        <li>返金保証・無料トライアルがあるか確認する</li>
        <li>接続サーバーの国数を確認する</li>
        <li>同時接続台数を確認する</li>
      </ul>
    </section>
    <div>{{CTA_PRIMARY}}</div>
    <section class="faq-section">
      <details><summary>Q1</summary><div>A1</div></details>
      <details><summary>Q2</summary><div>A2</div></details>
      <details><summary>Q3</summary><div>A3</div></details>
    </section>
    <div>{{CTA_SECONDARY}}</div>
    """ + "選び方の解説文章です。" * 100
    r = review_page(good, "vpn-service")
    print(json.dumps(r, ensure_ascii=False, indent=2))

    print("\n=== テスト2: 旧形式（比較表・価格・不自然語あり） ===")
    bad = """
    <div class="disclosure">広告を含みます</div>
    <h1>VPN比較</h1>
    <table class="comparison-table">
      <tr><th>名前</th><th>価格</th></tr>
      <tr><td>NordVPN 最高のセキュリティ 月額1,500円</td><td>高-speed</td></tr>
      <tr><td>ExpressVPN 最速 完璧な暗号化</td><td>100%安全</td></tr>
    </table>
    <ul class="checklist"><li>確認事項</li></ul>
    <div>{{CTA_PRIMARY}}</div>
    <section class="faq-section">
      <details><summary>Q1</summary><div>テレワークを取り組む企業や個人にご案内します</div></details>
      <details><summary>Q2</summary><div>A2</div></details>
      <details><summary>Q3</summary><div>A3</div></details>
    </section>
    <div>{{CTA_SECONDARY}}</div>
    """ + "文章。" * 100
    r2 = review_page(bad, "vpn-service")
    print(json.dumps(r2, ensure_ascii=False, indent=2))
