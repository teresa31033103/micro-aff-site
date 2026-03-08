#!/usr/bin/env python3
"""
plan_topics.py - 企画AI
Ollamaを使ってトピックのページ構成を生成する
薄い記事になりにくいよう、企画段階で必須項目を厚めにそろえる
"""

import json
import re
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).parent.parent
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"


DEFAULT_SELECTION_POINTS = [
    ("料金と返金条件", "費用だけでなく、無料体験や返金条件まで見ると失敗しにくくなります。", ["月額・年額の差", "返金保証の有無", "無料体験の条件"]),
    ("使う場所との相性", "自宅・出張先・公衆Wi-Fiなど、使う場面によって重視点が変わります。", ["回線の安定性", "接続のしやすさ", "移動中の使いやすさ"]),
    ("端末と設定のしやすさ", "導入が難しいと継続しづらいため、初期設定のしやすさも重要です。", ["Windows・スマホ対応", "同時接続台数", "初期設定の分かりやすさ"]),
]

DEFAULT_FAQ = [
    ("無料版だけで十分ですか？", "用途が限定的なら無料版でも足りる場合がありますが、継続利用するなら制限や使い勝手まで確認した方が安全です。"),
    ("最初に見るべき比較ポイントは何ですか？", "料金だけでなく、使う場所との相性、設定のしやすさ、サポートの有無をあわせて見ると判断しやすくなります。"),
    ("初心者でも使えますか？", "導入手順が簡潔で、公式の案内が分かりやすいサービスを選べば、初心者でも使いやすくなります。"),
    ("迷ったときの決め方はありますか？", "まず利用シーンを1つに絞り、その用途で困りやすい点を先に確認すると選びやすくなります。"),
]


GENERIC_BAD_PATTERNS = [
    r"比較を提供します",
    r"おすすめを提供します",
    r"人々が知りたい",
    r"検索する人々",
    r"取り組む人々",
    r"最優秀選定",
    r"ご案内します",
    r"企業や個人が必要とする",
    r"プライバシーキャンセル",
    r"high-speed",
    r"Server",
]


def _clean_generic_string(value: str, fallback: str) -> str:
    value = str(value or "").strip()
    if not value:
        return fallback
    if any(re.search(pattern, value) for pattern in GENERIC_BAD_PATTERNS):
        return fallback
    return value


def load_prompt_template(name: str) -> str:
    path = ROOT / "prompts" / f"{name}.md"
    return path.read_text(encoding="utf-8")


def call_ollama(prompt: str, model: str = MODEL) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.35,
            "num_predict": 2600,
        },
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=180)
        resp.raise_for_status()
        return resp.json().get("response", "")
    except requests.exceptions.ConnectionError:
        print("  ❌ Ollamaに接続できません。`ollama serve` が起動しているか確認してください。")
        return ""
    except Exception as e:
        print(f"  ❌ Ollama APIエラー: {e}")
        return ""


def extract_json(text: str) -> dict[str, Any]:
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return {}


def infer_candidate_names(topic: dict[str, Any]) -> list[str]:
    affiliate_key = topic.get("affiliate_key", "")
    title = topic.get("title", "")
    if affiliate_key == "vpn-service" or "VPN" in title.upper():
        return ["固定IPを重視する人向け", "価格を抑えたい人向け", "公衆Wi-Fi利用が多い人向け"]
    if affiliate_key == "password-manager" or "パスワード" in title:
        return ["個人利用を重視する人向け", "家族共有を重視する人向け", "コスト重視の人向け"]
    if affiliate_key == "windows-backup" or "バックアップ" in title:
        return ["自動バックアップを重視する人向け", "写真保存を重視する人向け", "Windows標準機能も含めて比較したい人向け"]
    return ["候補A", "候補B", "候補C"]


def make_default_plan(topic: dict[str, Any]) -> dict[str, Any]:
    title = topic.get("title", "比較記事")
    niche = topic.get("niche", "")
    intent = topic.get("intent", "比較・選定")
    keywords = topic.get("keywords", [])
    kw_text = "、".join(keywords[:2]) if keywords else title
    candidates = infer_candidate_names(topic)

    if topic.get("affiliate_key") == "vpn-service":
        comparison_items = [
            {
                "name": "固定IPを重視する人向け",
                "strengths": ["仕事用アクセスを安定させやすい", "接続先を絞って運用しやすい"],
                "cautions": ["料金が上がりやすい", "個人利用では機能を持て余すことがある"],
                "pricing_hint": "固定IPや追加機能は別料金になりやすい",
                "best_for": "社内アクセスや接続元管理を重視する人",
            },
            {
                "name": "価格を抑えたい人向け",
                "strengths": ["月額負担を抑えやすい", "初めて試しやすい"],
                "cautions": ["返金条件や機能制限を見落としやすい", "サポートが簡素な場合がある"],
                "pricing_hint": "長期契約で単価が下がることが多い",
                "best_for": "まずVPNを試したい個人のリモートワーク利用",
            },
            {
                "name": "公衆Wi-Fi利用が多い人向け",
                "strengths": ["外出先での安全性を確保しやすい", "アプリ設定が簡単な製品を選びやすい"],
                "cautions": ["速度より安定性重視で見る必要がある", "無料枠だけでは足りない場合がある"],
                "pricing_hint": "短期利用では月額プランの条件を確認",
                "best_for": "ホテルやカフェ、空港Wi-Fiを仕事で使う人",
            },
        ]
        selection_points = [
            {"point": "仕事用通信との相性", "why_it_matters": "社内ツールや会議アプリを使うなら、速度だけでなく接続の安定性が重要です。", "check_items": ["Web会議が切れにくいか", "社内ツールへの接続で困らないか", "混雑時間帯でも使いやすいか"]},
            {"point": "公衆Wi-Fiでの使いやすさ", "why_it_matters": "ホテルやカフェでは設定の手間が少ないほど実際に使い続けやすくなります。", "check_items": ["初回設定が分かりやすいか", "スマホとPCの両方で使えるか", "接続先の切り替えがしやすいか"]},
            {"point": "料金と契約条件", "why_it_matters": "月額の安さだけで決めると、返金条件や追加料金で想定より負担が増えることがあります。", "check_items": ["月額と年額の差", "返金保証の条件", "固定IPや追加機能の有無"]},
        ]
        faq = [
            {"q": "リモートワークでVPNは必須ですか？", "a": "社内システムや共有Wi-Fiを使うなら、通信を保護する手段として検討価値があります。特に外出先で仕事をする人は優先度が上がります。"},
            {"q": "料金の安いVPNでも大丈夫ですか？", "a": "価格だけでは判断しにくいため、返金条件、設定のしやすさ、仕事用通信との相性を一緒に確認するのが安全です。"},
            {"q": "固定IPは必要ですか？", "a": "社内アクセス制限や接続元管理がある環境では役立つことがありますが、個人利用では不要な場合もあります。用途から逆算して判断してください。"},
            {"q": "出張先やカフェWi-Fiでも同じ選び方でいいですか？", "a": "外出先では接続のしやすさと安定性の優先度が上がります。自宅利用だけで選ぶより、公衆Wi-Fiでの使いやすさも確認した方が安心です。"},
        ]
        sections = [
            {"heading": "まず結論", "purpose": "用途を先に決めてから選ぶ重要性を示します。", "key_points": ["料金だけで選ばない", "使う場所を先に決める", "契約条件まで確認する"]},
            {"heading": "選び方のポイント", "purpose": "比較前に確認したい観点を整理します。", "key_points": ["仕事用通信との相性", "公衆Wi-Fiでの使いやすさ", "料金と契約条件"]},
            {"heading": "比較表で確認したい点", "purpose": "候補を横並びで見るときの基準をまとめます。", "key_points": ["安定性", "設定の手間", "追加料金の有無"]},
            {"heading": "失敗しやすいポイント", "purpose": "知名度や価格だけで選ばないための注意点を示します。", "key_points": ["長期契約の条件を見落とす", "固定IPの要否を考えない", "外出先利用を想定しない"]},
        ]
    else:
        comparison_items = []
        selection_points = [
            {
                "point": point,
                "why_it_matters": why,
                "check_items": checks,
            }
            for point, why, checks in DEFAULT_SELECTION_POINTS
        ]
        faq = [{"q": q, "a": a} for q, a in DEFAULT_FAQ]
        sections = [
            {
                "heading": "まず結論",
                "purpose": "検索意図に対する短い結論を最初に示します。",
                "key_points": [
                    f"{title}は、用途を決めてから比較すると選びやすくなります。",
                    f"{kw_text}のような検索では、料金だけでなく使う場面との相性が重要です。",
                    "最終判断の前に公式情報で最新条件を確認してください。",
                ],
            },
            {
                "heading": "選び方のポイント",
                "purpose": "比較前に見るべき観点を整理します。",
                "key_points": [sp[0] for sp in DEFAULT_SELECTION_POINTS],
            },
            {
                "heading": "比較表で確認したい点",
                "purpose": "候補を横並びで確認するための視点をまとめます。",
                "key_points": [
                    "料金・無料体験・返金条件",
                    "用途との相性",
                    "設定のしやすさとサポート",
                ],
            },
            {
                "heading": "失敗しやすいポイント",
                "purpose": "比較時に見落としやすい点を先回りして示します。",
                "key_points": [
                    "価格だけで選んで使う場所との相性を見落とす",
                    "初期設定のしやすさを確認しない",
                    "サポートや返金条件を読まずに契約する",
                ],
            },
        ]

    for idx, name in enumerate(candidates[:3], start=1):
        comparison_items.append(
            {
                "name": name,
                "strengths": [
                    f"{title}の観点で比較しやすい代表候補です",
                    "用途ごとの向き不向きを整理しやすいです",
                ],
                "cautions": [
                    "最新の価格や仕様は公式情報で再確認が必要です",
                    "利用環境によって使い勝手が変わる場合があります",
                ],
                "pricing_hint": "料金体系は公式サイトで確認",
                "best_for": f"{title}を比較しながら候補を絞りたい人",
            }
        )


    return {
        "page_title": title,
        "meta_description": f"{title}について、{niche}の観点から比較ポイントを整理しました。用途別に選びやすい形でまとめています。",
        "h1": title,
        "audience_summary": f"{title}を検討しており、複数候補を比べながら失敗を減らしたい人向けの記事です。",
        "search_intent_summary": f"{intent}の検索意図に合わせて、比較軸と向き不向きを先に把握したい読者を想定しています。",
        "quick_answer": ("仕事でVPNを使うなら、料金の安さだけでなく、接続の安定性、設定のしやすさ、契約条件まで並べて確認すると失敗しにくくなります。" if topic.get("affiliate_key") == "vpn-service" else f"{title}では、まず利用シーンを決めてから料金、設定しやすさ、用途との相性を比べるのが基本です。{kw_text}のような検索では、単に知名度で選ばず、自分の使い方で困りにくい候補を残すと失敗しにくくなります。"),
        "who_should_choose": (["在宅勤務でVPNの選び方を整理したい人", "外出先のWi-Fi利用も想定して候補を絞りたい人", "料金と使いやすさのバランスを見たい人"] if topic.get("affiliate_key") == "vpn-service" else [f"{title}の候補を2〜3個まで絞り込みたい人", "料金だけでなく使い勝手も重視したい人", "初めて比較記事を読んで候補整理をしたい人"]),
        "who_should_avoid": (["すでに導入するサービスが決まっている人", "最新の公式条件を確認せずに申込みたい人"] if topic.get("affiliate_key") == "vpn-service" else ["1つのサービスに決め打ちしていて比較が不要な人", "最新価格や最新仕様を公式で確認する前提がない人"]),
        "selection_points": selection_points,
        "comparison_items": comparison_items,
        "common_mistakes": [
            "用途を決めずに知名度だけで選ぶ",
            "料金しか見ず、導入や運用のしやすさを確認しない",
            "無料体験や返金条件を読まずに申し込む",
        ],
        "faq": faq,
        "sections": sections,
        "cta_placement": "mid",
    }


def normalize_plan(topic: dict[str, Any], raw_plan: dict[str, Any]) -> dict[str, Any]:
    base = make_default_plan(topic)
    plan = base | {k: v for k, v in raw_plan.items() if v not in (None, "", [], {})}

    def ensure_string(key: str) -> None:
        if not isinstance(plan.get(key), str) or not plan.get(key, "").strip():
            plan[key] = base[key]
            return
        plan[key] = _clean_generic_string(plan.get(key, ""), base[key])

    for key in ["page_title", "meta_description", "h1", "audience_summary", "search_intent_summary", "quick_answer", "cta_placement"]:
        ensure_string(key)

    def ensure_string_list(key: str, minimum: int, fallback: list[str]) -> None:
        value = plan.get(key)
        if not isinstance(value, list):
            plan[key] = fallback
            return
        cleaned = [str(x).strip() for x in value if str(x).strip()]
        if len(cleaned) < minimum:
            for item in fallback:
                if item not in cleaned:
                    cleaned.append(item)
                if len(cleaned) >= minimum:
                    break
        plan[key] = cleaned

    ensure_string_list("who_should_choose", 3, base["who_should_choose"])
    ensure_string_list("who_should_avoid", 2, base["who_should_avoid"])
    ensure_string_list("common_mistakes", 3, base["common_mistakes"])

    selection_points = plan.get("selection_points")
    if not isinstance(selection_points, list):
        selection_points = []
    normalized_selection = []
    for item in selection_points:
        if not isinstance(item, dict):
            continue
        point = str(item.get("point", "")).strip()
        why = str(item.get("why_it_matters", "")).strip()
        checks = item.get("check_items", [])
        if not isinstance(checks, list):
            checks = []
        checks = [str(x).strip() for x in checks if str(x).strip()]
        if point and why and checks:
            normalized_selection.append({"point": point, "why_it_matters": why, "check_items": checks[:4]})
    if len(normalized_selection) < 3:
        normalized_selection = base["selection_points"]
    plan["selection_points"] = normalized_selection[:4]

    comparison_items = plan.get("comparison_items")
    if not isinstance(comparison_items, list):
        comparison_items = []
    normalized_items = []
    for item in comparison_items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        strengths = item.get("strengths", item.get("pros", []))
        cautions = item.get("cautions", item.get("cons", []))
        if not isinstance(strengths, list):
            strengths = []
        if not isinstance(cautions, list):
            cautions = []
        strengths = [str(x).strip() for x in strengths if str(x).strip()]
        cautions = [str(x).strip() for x in cautions if str(x).strip()]
        pricing_hint = str(item.get("pricing_hint", item.get("price", ""))).strip() or "料金体系は公式サイトで確認"
        best_for = str(item.get("best_for", "")).strip() or "比較しながら候補を絞りたい人"
        if name and strengths and cautions:
            normalized_items.append(
                {
                    "name": name,
                    "strengths": strengths[:3],
                    "cautions": cautions[:3],
                    "pricing_hint": pricing_hint,
                    "best_for": best_for,
                }
            )
    if len(normalized_items) < 3:
        normalized_items = base["comparison_items"]
    plan["comparison_items"] = normalized_items[:5]

    faq = plan.get("faq")
    if not isinstance(faq, list):
        faq = []
    normalized_faq = []
    for item in faq:
        if not isinstance(item, dict):
            continue
        q = str(item.get("q", "")).strip()
        a = str(item.get("a", "")).strip()
        if q and a:
            normalized_faq.append({"q": q, "a": a})
    if len(normalized_faq) < 4:
        normalized_faq = base["faq"]
    plan["faq"] = normalized_faq[:6]

    sections = plan.get("sections")
    if not isinstance(sections, list):
        sections = []
    normalized_sections = []
    for item in sections:
        if not isinstance(item, dict):
            continue
        heading = str(item.get("heading", "")).strip()
        purpose = str(item.get("purpose", "")).strip()
        key_points = item.get("key_points", [])
        if not isinstance(key_points, list):
            key_points = []
        key_points = [str(x).strip() for x in key_points if str(x).strip()]
        if heading and purpose and key_points:
            normalized_sections.append({"heading": heading, "purpose": purpose, "key_points": key_points[:5]})
    if len(normalized_sections) < 4:
        normalized_sections = base["sections"]
    plan["sections"] = normalized_sections[:6]

    if plan.get("cta_placement") not in {"mid", "end"}:
        plan["cta_placement"] = "mid"

    return plan


def plan_topic(topic: dict[str, Any]) -> dict[str, Any]:
    template = load_prompt_template("planner")
    prompt = template.replace("{topic_id}", topic.get("id", ""))
    prompt = prompt.replace("{title}", topic.get("title", ""))
    prompt = prompt.replace("{niche}", topic.get("niche", ""))
    prompt = prompt.replace("{intent}", topic.get("intent", ""))
    prompt = prompt.replace("{keywords}", ", ".join(topic.get("keywords", [])))

    response = call_ollama(prompt)
    raw_plan = extract_json(response) if response else {}
    if response and not raw_plan:
        print(f"  ⚠️  JSON抽出失敗。レスポンス先頭: {response[:200]}")

    return normalize_plan(topic, raw_plan)


if __name__ == "__main__":
    test_topic = {
        "id": "windows-backup-tools",
        "title": "Windowsバックアップツール比較",
        "niche": "PC管理・効率化",
        "intent": "比較・選定",
        "keywords": ["windows バックアップ ソフト 無料", "windows バックアップ おすすめ"],
        "affiliate_key": "windows-backup",
    }
    result = plan_topic(test_topic)
    print(json.dumps(result, ensure_ascii=False, indent=2))
