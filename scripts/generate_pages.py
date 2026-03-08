#!/usr/bin/env python3
"""
generate_pages.py - UTF-8 safe fallback generator

This version avoids the corrupted comparison-table template and always builds
reviewable guide-style HTML directly from the planner output.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        for key in ("text", "content", "description", "body", "value", "answer", "title"):
            if value.get(key):
                return _clean_text(value.get(key))
        return " ".join(_clean_text(v) for v in value.values() if v)
    if isinstance(value, list):
        return " ".join(_clean_text(v) for v in value if v)
    text = str(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _slug_to_title(slug: str) -> str:
    slug = (slug or "").strip("/")
    if not slug:
        return "VPNの選び方ガイド"
    text = slug.replace("-", " ")
    words = [w for w in text.split() if w]
    mapping = {
        "vpn": "VPN",
        "for": "向け",
        "remote": "リモート",
        "work": "ワーク",
        "travel": "旅行",
        "wifi": "Wi-Fi",
        "public": "公共",
        "security": "セキュリティ",
        "privacy": "プライバシー",
    }
    converted = [mapping.get(w.lower(), w) for w in words]
    joined = "".join(converted)
    if "VPN" not in joined:
        joined = f"{joined}VPN" if joined else "VPN"
    return f"{joined}の選び方ガイド"


def _listify(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, dict):
                text = _clean_text(item)
            else:
                text = _clean_text(item)
            if text:
                out.append(text)
        return out
    if isinstance(value, dict):
        out = []
        for key in ("items", "points", "bullets", "list"):
            if key in value:
                out.extend(_listify(value[key]))
        if out:
            return out
        text = _clean_text(value)
        return [text] if text else []
    text = _clean_text(value)
    return [text] if text else []


def _paragraphs_from_points(points: list[str], fallback: list[str]) -> list[str]:
    source = [p for p in points if p] or fallback
    paragraphs: list[str] = []
    for point in source:
        base = _clean_text(point)
        if not base:
            continue
        paragraphs.append(
            f"{base}という場面がある場合は、使い始める前に確認する条件を整理しておくと判断しやすくなります。"
        )
        paragraphs.append(
            f"特定のサービス名を先に決めるよりも、接続のしやすさ、使う端末、サポートの確認しやすさを見るほうが選びやすくなります。"
        )
    return paragraphs


def _section(title: str, paragraphs: list[str], bullets: list[str] | None = None, css_class: str = "") -> str:
    class_attr = f' class="{_escape(css_class)}"' if css_class else ""
    parts = [f"<section{class_attr}>", f"  <h2>{_escape(title)}</h2>"]
    for paragraph in paragraphs:
        text = _clean_text(paragraph)
        if text:
            parts.append(f"  <p>{_escape(text)}</p>")
    if bullets:
        parts.append("  <ul>")
        for item in bullets:
            text = _clean_text(item)
            if text:
                parts.append(f"    <li>{_escape(text)}</li>")
        parts.append("  </ul>")
    parts.append("</section>")
    return "\n".join(parts)


def _checklist(items: list[str]) -> str:
    if not items:
        items = [
            "公共Wi-Fiを使う機会が多いか確認する",
            "仕事用端末と私用端末の両方で使うか確認する",
            "アプリで簡単に接続できるか確認する",
            "日本語サポートの有無を確認する",
            "返金保証や試用条件を確認する",
        ]
    lis = "\n".join(f"    <li>{_escape(item)}</li>" for item in items if _clean_text(item))
    return "\n".join([
        "<section>",
        "  <h2>導入前に確認するポイント</h2>",
        "  <p>比較表よりも、使う場面に合わせて確認したい点を先に整理すると選びやすくなります。</p>",
        '  <ul class="checklist">',
        lis,
        "  </ul>",
        "</section>",
    ])


def _faq_blocks(faq_items: list[Any]) -> str:
    normalized: list[tuple[str, str]] = []
    for item in faq_items:
        if isinstance(item, dict):
            q = _clean_text(item.get("q") or item.get("question") or item.get("title"))
            a = _clean_text(item.get("a") or item.get("answer") or item.get("content"))
        else:
            q = _clean_text(item)
            a = ""
        if q:
            if not a:
                a = "使う場面を先に整理し、端末対応とサポート体制を確認しておくと判断しやすくなります。"
            normalized.append((q, a))

    defaults = [
        (
            "無料のVPNでも十分ですか？",
            "無料サービスは接続先や使い方に制限がある場合があります。まずは何のために使うかを整理し、継続して使うなら導入しやすさとサポート体制も確認しておくと安心です。",
        ),
        (
            "仕事用の端末でも使いやすいですか？",
            "業務で使う場合は、接続のしやすさと設定変更の分かりやすさが大切です。社内ルールがある場合は、その条件に合うかを先に確認しておくと選びやすくなります。",
        ),
        (
            "スマートフォンでも使えますか？",
            "外出先で使うことが多いなら、パソコンだけでなくスマートフォンでも扱いやすいかを見ておくと便利です。普段使う端末で迷わず切り替えられるかを確認しておくと安心です。",
        ),
    ]
    while len(normalized) < 3:
        normalized.append(defaults[len(normalized)])

    blocks = []
    for question, answer in normalized[:5]:
        q = _clean_text(question)
        a = _clean_text(answer)
        if len(a) < 50:
            a = a + " 迷いやすい点は、使う場所と端末の組み合わせを先に整理しておくと見分けやすくなります。"
        blocks.append(
            "\n".join([
                "  <details>",
                f"    <summary>{_escape(q)}</summary>",
                f"    <div>{_escape(a)}</div>",
                "  </details>",
            ])
        )
    return "\n".join(blocks)


def build_safe_html(topic: dict[str, Any], plan: dict[str, Any]) -> str:
    slug = str(topic.get("slug") or topic.get("topic") or "").strip()
    h1 = _clean_text(plan.get("h1") or topic.get("title") or _slug_to_title(slug))
    if not h1:
        h1 = "VPNの選び方ガイド"
    # comparison wording cleanup
    h1 = h1.replace("比較", "判断軸")
    h1 = h1.replace("ランキング", "選び方")

    target_reader = _clean_text(plan.get("target_reader") or topic.get("target_reader") or "社外のネットワークを使う機会がある方")
    intro = _clean_text(plan.get("intro") or "社外のネットワークを使う場面では、通信の扱いを見直しておくと安心です。")

    selection_points = _listify(plan.get("selection_points") or plan.get("key_points") or plan.get("points"))
    who_choose = _listify(plan.get("who_choose") or plan.get("recommended_for"))
    who_avoid = _listify(plan.get("who_avoid") or plan.get("not_for"))
    mistakes = _listify(plan.get("mistakes") or plan.get("cautions") or plan.get("warnings"))
    checklist_items = _listify(plan.get("checklist") or plan.get("check_points"))
    faq_items = plan.get("faq") if isinstance(plan.get("faq"), list) else []

    if not selection_points:
        selection_points = [
            "外出先で接続することが多いか",
            "複数の端末で使いたいか",
            "設定に時間をかけたくないか",
            "困ったときに確認しやすい案内があるか",
        ]
    if not who_choose:
        who_choose = [
            "社外のネットワークを使う機会がある",
            "出張先や共有Wi-Fiで作業することがある",
            "仕事用と私用の端末を切り替えて使う",
        ]
    if not who_avoid:
        who_avoid = [
            "使う場面が決まっておらず、必要性の整理から始めたい",
            "接続先や端末の条件をまだ確認できていない",
        ]
    if not mistakes:
        mistakes = [
            "価格だけで決めて、普段使う端末に合うかを後回しにする",
            "外出先で使うのに、切り替えやすさを確認しないまま進める",
            "困ったときの確認手段を見ないまま導入する",
        ]

    intro_paragraphs = [
        f"{target_reader}にとって、通信環境の見直しは早めに整理しておきたいポイントです。",
        intro,
        "選ぶ際は、特定のサービス名を先に決めるよりも、使う場面と確認したい条件を先に整理すると判断しやすくなります。",
    ]

    scene_section = _section(
        "どんな場面で考えるか",
        _paragraphs_from_points(who_choose, ["外出先や共有Wi-Fiを使う機会がある"]),
        who_choose,
    )

    avoid_section = _section(
        "先に整理しておきたいこと",
        [
            "導入を急ぐ前に、どの端末で使うか、どこで接続するかを整理しておくと判断しやすくなります。",
            "使う場面が曖昧なままだと、選ぶ基準がぶれやすくなります。",
        ],
        who_avoid,
    )

    point_section = _section(
        "選ぶときの判断軸",
        [
            "外出先で迷わず使えるか、普段使う端末で切り替えやすいかを先に見ておくと、導入後の負担を抑えやすくなります。",
            "接続のしやすさ、案内の分かりやすさ、困ったときに確認できる情報があるかを順に確認していくと絞り込みやすくなります。",
        ],
        selection_points,
    )

    mistake_section = _section(
        "導入前に見ておきたい点",
        [
            "焦って決めるよりも、使う場面と確認項目を整理してから候補を見るほうが、あとで見直しが少なくなります。",
            "仕事で使うなら、普段の作業の流れを止めにくいかどうかも見ておくと安心です。",
        ],
        mistakes,
    )

    checklist_section = _checklist(checklist_items)

    faq_section = "\n".join([
        '<section class="faq-section">',
        "  <h2>よくある質問</h2>",
        _faq_blocks(faq_items),
        "</section>",
    ])

    html_parts = [
        '<div class="disclosure">広告を含みます</div>',
        f"<h1>{_escape(h1)}</h1>",
    ]
    html_parts.extend(f"<p>{_escape(p)}</p>" for p in intro_paragraphs if _clean_text(p))
    html_parts.extend([
        scene_section,
        avoid_section,
        point_section,
        checklist_section,
        '<div class="cta-block" data-cta="primary">{{CTA_PRIMARY}}</div>',
        mistake_section,
        faq_section,
        '<div class="cta-block" data-cta="secondary">{{CTA_SECONDARY}}</div>',
    ])
    return "\n".join(html_parts)


def generate_page(topic: dict[str, Any], plan: dict[str, Any]) -> str:
    """Return safe guide-style HTML built from the plan.

    The previous file was corrupted and produced broken comparison-table fallback
    HTML. This deterministic builder keeps the pipeline running until prompt- and
    model-based generation is stable again.
    """
    return build_safe_html(topic, plan)


if __name__ == "__main__":
    sample_topic = {"slug": "vpn-for-remote-work"}
    sample_plan = {
        "h1": "リモートワーク向けVPNの選び方ガイド",
        "target_reader": "社外のネットワークを使って作業する方",
        "intro": "外出先や共有Wi-Fiを使う場面では、通信の扱いを見直しておくと安心です。",
        "selection_points": [
            "接続のしやすさ",
            "普段使う端末との相性",
            "確認しやすい案内があるか",
        ],
    }
    print(build_safe_html(sample_topic, sample_plan))
