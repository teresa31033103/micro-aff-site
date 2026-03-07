#!/usr/bin/env python3
"""
build_site.py - 公開AI（ビルド担当）
HTMLテンプレートにコンテンツ・CTAリンク・開示文を組み込んでdist/に出力する
サイトマップと一覧ページも更新する
"""

import html
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
TEMPLATE_PATH = ROOT / "site" / "templates" / "page.html"
DIST_DIR = ROOT / "dist"
AFFILIATE_MAP_PATH = ROOT / "data" / "affiliate_map.json"
SITE_DOMAIN = "akane123.github.io/micro-aff-site"  # ← GitHub Pages URLに変更


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_site_paths() -> tuple[str, str]:
    parts = SITE_DOMAIN.split("/", 1)
    base_path = ""
    if len(parts) == 2 and parts[1].strip("/"):
        base_path = "/" + parts[1].strip("/")
    return SITE_DOMAIN, base_path


def build_cta_html(aff_data: dict, cta_type: str) -> str:
    """CTAブロックのHTMLを生成する"""
    if cta_type == "primary":
        url = aff_data.get("primary_cta_url", "#")
        label = aff_data.get("primary_cta_label", "詳細を見る →")
        intro = "👇 詳しくはこちらから確認できます"
    else:
        url = aff_data.get("secondary_cta_url", "#")
        label = aff_data.get("secondary_cta_label", "公式サイトを見る →")
        intro = "📌 気になった方はこちらもどうぞ"

    return (
        '<div class="cta-block">\n'
        f'  <p>{html.escape(intro)}</p>\n'
        f'  <a href="{html.escape(url, quote=True)}" class="cta-btn" rel="noopener noreferrer sponsored" target="_blank">{html.escape(label)}</a>\n'
        '</div>'
    )


def render_template(*, page_title: str, meta_description: str, canonical_url: str, main_content: str) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    site_domain, base_path = get_site_paths()

    final_html = template.replace("{{PAGE_TITLE}}", html.escape(page_title))
    final_html = final_html.replace("{{META_DESCRIPTION}}", html.escape(meta_description))
    final_html = final_html.replace("{{SITE_DOMAIN}}", site_domain)
    final_html = final_html.replace("{{BASE_PATH}}", base_path)
    final_html = final_html.replace("{{CANONICAL_URL}}", canonical_url)
    final_html = final_html.replace("{{MAIN_CONTENT}}", main_content)
    return final_html


def build_page(topic: dict, plan: dict, html_content: str) -> Path:
    """最終HTMLをビルドしてdist/に出力する"""
    affiliate_map = load_json(AFFILIATE_MAP_PATH)
    aff_key = topic.get("affiliate_key", "")
    aff_data = affiliate_map.get(aff_key, {})

    page_title = plan.get("page_title", topic.get("title", ""))
    meta_description = plan.get("meta_description", "")
    page_slug = topic.get("id", "page")
    site_domain, base_path = get_site_paths()
    site_root = f"https://{site_domain}"

    content = html_content

    disclosure_text = aff_data.get("disclosure", "本ページには広告リンクが含まれる場合があります。")
    content = content.replace("{{DISCLOSURE}}", html.escape(disclosure_text))
    if "{{DISCLOSURE}}" not in html_content and 'class="disclosure"' not in content:
        content = f'<div class="disclosure">{html.escape(disclosure_text)}</div>\n' + content

    cta_primary_html = build_cta_html(aff_data, "primary")
    cta_secondary_html = build_cta_html(aff_data, "secondary")
    content = content.replace("{{CTA_PRIMARY}}", cta_primary_html)
    content = content.replace("{{CTA_SECONDARY}}", cta_secondary_html)

    page_meta = f'<p class="page-meta">最終更新: {datetime.now().strftime("%Y年%m月%d日")} | カテゴリ: {html.escape(topic.get("niche", ""))}</p>'
    full_content = f"{content}\n{page_meta}"
    canonical_url = f"{site_root}/pages/{page_slug}/"
    final_html = render_template(
        page_title=page_title,
        meta_description=meta_description,
        canonical_url=canonical_url,
        main_content=full_content,
    )

    page_dir = DIST_DIR / "pages" / page_slug
    page_dir.mkdir(parents=True, exist_ok=True)
    output_path = page_dir / "index.html"
    output_path.write_text(final_html, encoding="utf-8")
    print(f"  📄 出力: {output_path}")
    return output_path


def update_sitemap():
    """サイトマップXMLを更新する"""
    state_path = ROOT / "data" / "site_state.json"
    with open(state_path, encoding="utf-8") as f:
        state = json.load(f)

    site_domain, base_path = get_site_paths()
    base_url = f"https://{site_domain}"

    sitemap_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap_lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    sitemap_lines.append(f"""  <url>
    <loc>{base_url}/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>""")

    for page in state.get("pages", []):
        slug = page.get("slug", "")
        updated = page.get("generated_at", datetime.now().isoformat())[:10]
        sitemap_lines.append(f"""  <url>
    <loc>{base_url}/pages/{slug}/</loc>
    <lastmod>{updated}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""")

    for slug in ["privacy", "about", "contact"]:
        sitemap_lines.append(f"""  <url>
    <loc>{base_url}/{slug}/</loc>
    <changefreq>yearly</changefreq>
    <priority>0.3</priority>
  </url>""")

    sitemap_lines.append("</urlset>")
    sitemap_path = DIST_DIR / "sitemap.xml"
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    sitemap_path.write_text("\n".join(sitemap_lines), encoding="utf-8")
    print(f"  🗺️  サイトマップ更新: {sitemap_path}")


def build_index():
    """トップページ（記事一覧）を生成する"""
    state_path = ROOT / "data" / "site_state.json"
    with open(state_path, encoding="utf-8") as f:
        state = json.load(f)

    _, base_path = get_site_paths()

    pages_html = ""
    for page in state.get("pages", []):
        slug = page.get("slug", "")
        title = html.escape(page.get("title", ""))
        date = html.escape(page.get("generated_at", "")[:10])
        pages_html += (
            '<article class="article-card">\n'
            f'  <a href="{base_path}/pages/{slug}/">\n'
            f'    <h2>{title}</h2>\n'
            f'    <p class="page-meta">{date}</p>\n'
            '  </a>\n'
            '</article>\n'
        )

    content = (
        '<h1>AIが選ぶ、あなたに合ったツール比較</h1>\n'
        '<p>AIが自動生成・審査した、実用的なツール比較・解説記事です。</p>\n'
        '<style>\n'
        '.article-card { background: white; border: 1px solid var(--border); border-radius: var(--radius); padding: 20px 24px; margin-bottom: 16px; }\n'
        '.article-card a { text-decoration: none; color: inherit; }\n'
        '.article-card h2 { font-size: 18px; color: var(--accent); margin-bottom: 6px; }\n'
        '.article-card:hover { box-shadow: var(--shadow); }\n'
        '</style>\n'
        f'{pages_html if pages_html else "<p>記事を準備中です。</p>"}'
    )

    canonical_url = f"https://{SITE_DOMAIN}/"
    final_html = render_template(
        page_title="AIツールラボ - ツール比較・解説",
        meta_description="AIが自動生成した実用的なツール比較・解説記事をまとめています。",
        canonical_url=canonical_url,
        main_content=content,
    )

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    index_path = DIST_DIR / "index.html"
    index_path.write_text(final_html, encoding="utf-8")
    print(f"  🏠 インデックス更新: {index_path}")


def build_static_pages():
    """最低限の固定ページを生成する"""
    pages = {
        "privacy": {
            "title": "プライバシーポリシー",
            "desc": "プライバシーポリシー",
            "body": "<h1>プライバシーポリシー</h1><p>当サイトではアクセス解析や広告リンクの計測のため、必要最小限の情報が利用される場合があります。</p><p>実運用時は、利用しているASPや分析ツールに合わせて内容を更新してください。</p>",
        },
        "about": {
            "title": "このサイトについて",
            "desc": "このサイトについて",
            "body": "<h1>このサイトについて</h1><p>このサイトは、AIが生成・審査した比較記事を公開するためのマイクロサイトです。</p><p>最終的な掲載判断と法務対応は運営者が行います。</p>",
        },
        "contact": {
            "title": "お問い合わせ",
            "desc": "お問い合わせ",
            "body": "<h1>お問い合わせ</h1><p>お問い合わせ先は、実運用時にメールアドレスまたはフォームURLへ差し替えてください。</p>",
        },
    }
    site_domain, base_path = get_site_paths()
    site_root = f"https://{site_domain}"
    for slug, page in pages.items():
        page_dir = DIST_DIR / slug
        page_dir.mkdir(parents=True, exist_ok=True)
        canonical_url = f"{site_root}/{slug}/"
        html_text = render_template(
            page_title=page["title"],
            meta_description=page["desc"],
            canonical_url=canonical_url,
            main_content=page["body"],
        )
        (page_dir / "index.html").write_text(html_text, encoding="utf-8")
        print(f"  📄 固定ページ更新: {page_dir / 'index.html'}")


if __name__ == "__main__":
    build_index()
    build_static_pages()
    update_sitemap()
    print("✅ ビルド完了")
