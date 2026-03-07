#!/usr/bin/env python3
"""
publish_git.py - 公開AI（Git担当）
生成されたファイルをGitコミット・プッシュする
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent

def run_git(args: list, cwd=None) -> tuple[int, str, str]:
    """gitコマンドを実行して結果を返す"""
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()

def git_push(generated_paths: list = None):
    """変更をコミットしてプッシュする"""
    print("\n📤 Git操作を開始します...")

    # git status確認
    code, out, err = run_git(["status", "--porcelain"])
    if not out:
        print("  ℹ️  変更なし。プッシュをスキップします。")
        return True

    # dist/ と data/ をステージング
    add_targets = ["dist/", "data/site_state.json", "data/topics_queue.json"]
    for target in add_targets:
        code, out, err = run_git(["add", target])
        if code != 0:
            print(f"  ⚠️  git add失敗: {target} - {err}")

    # コミットメッセージ生成
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    page_count = len(generated_paths) if generated_paths else 0
    commit_msg = f"auto: {page_count}ページ生成 [{timestamp}]"

    code, out, err = run_git(["commit", "-m", commit_msg])
    if code != 0:
        if "nothing to commit" in err or "nothing to commit" in out:
            print("  ℹ️  コミットする変更がありません。")
            return True
        print(f"  ❌ git commit失敗: {err}")
        return False

    print(f"  ✅ コミット完了: {commit_msg}")

    # プッシュ
    code, out, err = run_git(["push", "origin", "main"])
    if code != 0:
        # masterブランチを試す
        code2, out2, err2 = run_git(["push", "origin", "master"])
        if code2 != 0:
            print(f"  ❌ git push失敗: {err}")
            print(f"  ヒント: git remote -v でリモート設定を確認してください")
            return False

    print(f"  ✅ プッシュ完了 → GitHub Pages に自動デプロイされます")
    print(f"  🌐 数分後に https://{get_pages_url()} で確認できます")
    return True

def get_pages_url() -> str:
    """GitHub PagesのURLを推測する"""
    code, out, err = run_git(["remote", "get-url", "origin"])
    if code == 0 and "github.com" in out:
        # https://github.com/USER/REPO.git → USER.github.io/REPO
        parts = out.replace(".git", "").split("/")
        if len(parts) >= 2:
            user = parts[-2].replace("github.com:", "").replace("github.com/", "")
            repo = parts[-1]
            return f"{user}.github.io/{repo}"
    return "YOUR_GITHUB_PAGES_URL"

if __name__ == "__main__":
    git_push()
