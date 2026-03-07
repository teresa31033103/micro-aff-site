#!/usr/bin/env python3
"""
run_pipeline.py - メインオーケストレータ
使い方: python scripts/run_pipeline.py [--topic TOPIC_ID] [--all]
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# パスの設定
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from plan_topics import plan_topic
from generate_pages import generate_page
from review_pages import review_page
from build_site import build_page, build_index, build_static_pages, update_sitemap
from publish_git import git_push

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def run_for_topic(topic: dict, dry_run: bool = False):
    """1トピックを企画→生成→審査→ビルドまで処理する"""
    topic_id = topic["id"]
    print(f"\n{'='*60}")
    print(f"📋 処理開始: {topic_id}")
    print(f"{'='*60}")

    # 1. 企画AI
    print("\n[1/4] 企画AI: ページ構成を生成中...")
    plan = plan_topic(topic)
    if not plan:
        print(f"  ❌ 企画失敗: {topic_id}")
        return False
    print(f"  ✅ 企画完了: {plan.get('page_title', '')}")

    # 2. 生成AI
    print("\n[2/4] 生成AI: HTML本文を生成中...")
    html_content = generate_page(topic, plan)
    if not html_content:
        print(f"  ❌ 生成失敗: {topic_id}")
        return False
    print(f"  ✅ 生成完了: {len(html_content)}文字")

    # 3. 審査AI
    print("\n[3/4] 審査AI: 品質チェック中...")
    review = review_page(html_content, topic.get("affiliate_key", ""))
    if not review:
        print(f"  ❌ 審査エラー: {topic_id}")
        return False

    print(f"  審査結果: {review.get('status')} | 文字数: {review.get('word_count', 0)}")

    if review.get("status") == "FAIL":
        print(f"  ❌ 審査FAIL: {review.get('fail_reasons')}")
        return False

    if review.get("warnings"):
        for w in review["warnings"]:
            print(f"  ⚠️  警告: {w}")

    print(f"  ✅ 審査通過")

    if dry_run:
        print("\n  [DRY RUN] ビルド・Gitスキップ")
        return True

    # 4. ビルド（HTML組み立て）
    print("\n[4/4] ビルド: 最終HTMLを組み立て中...")
    output_path = build_page(topic, plan, html_content)
    if not output_path:
        print(f"  ❌ ビルド失敗: {topic_id}")
        return False
    print(f"  ✅ ビルド完了: {output_path}")

    return output_path

def main():
    parser = argparse.ArgumentParser(description="AI自動コンテンツパイプライン")
    parser.add_argument("--topic", help="特定のトピックIDを処理")
    parser.add_argument("--all", action="store_true", help="queueの全pendingトピックを処理")
    parser.add_argument("--push", action="store_true", help="完了後にGitへpush")
    parser.add_argument("--dry-run", action="store_true", help="ビルド・Gitをスキップしてテスト実行")
    args = parser.parse_args()

    queue_path = ROOT / "data" / "topics_queue.json"
    state_path = ROOT / "data" / "site_state.json"

    queue_data = load_json(queue_path)
    state = load_json(state_path)

    topics_to_process = []

    if args.topic:
        # 指定トピックのみ
        matched = [t for t in queue_data["queue"] if t["id"] == args.topic]
        if not matched:
            print(f"❌ トピックが見つかりません: {args.topic}")
            sys.exit(1)
        topics_to_process = matched
    elif args.all:
        # 全pendingトピック
        topics_to_process = [t for t in queue_data["queue"] if t["status"] == "pending"]
        if not topics_to_process:
            print("✅ 処理待ちのトピックはありません")
            sys.exit(0)
    else:
        # デフォルト: 最初のpendingトピック1件
        pending = [t for t in queue_data["queue"] if t["status"] == "pending"]
        if not pending:
            print("✅ 処理待ちのトピックはありません")
            sys.exit(0)
        topics_to_process = [pending[0]]

    success_count = 0
    generated_paths = []

    for topic in topics_to_process:
        result = run_for_topic(topic, dry_run=args.dry_run)

        if result:
            # queueのstatusを更新
            for t in queue_data["queue"]:
                if t["id"] == topic["id"]:
                    t["status"] = "done"
                    t["completed_at"] = datetime.now().isoformat()

            # site_state更新
            state["total_pages_generated"] += 1
            state["pages"].append({
                "id": topic["id"],
                "slug": topic["id"],
                "title": topic["title"],
                "generated_at": datetime.now().isoformat()
            })
            state["last_run"] = datetime.now().isoformat()

            if isinstance(result, (str, Path)):
                generated_paths.append(str(result))

            success_count += 1
        else:
            print(f"\n⚠️  スキップ: {topic['id']}")

    # 状態ファイル保存
    save_json(queue_path, queue_data)
    save_json(state_path, state)

    # 一覧・固定ページ・サイトマップを最新状態で再生成
    if not args.dry_run:
        build_index()
        build_static_pages()
        update_sitemap()

    print(f"\n{'='*60}")
    print(f"✅ 完了: {success_count}/{len(topics_to_process)} 件成功")
    print(f"{'='*60}")

    # Gitへpush
    if args.push and generated_paths and not args.dry_run:
        print("\n📤 Gitへpush中...")
        git_push(generated_paths)

if __name__ == "__main__":
    main()
