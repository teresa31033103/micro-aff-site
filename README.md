# 🔬 micro-aff-site

**ローカルAI × GitHub Pages × アフィリエイト**の自律コンテンツ生成パイプライン

追加月額費用ゼロで、AIが企画→生成→審査→公開を自動実行します。

---

## アーキテクチャ

```
[Ollama（ローカルAI）]
    │
    ├─ 企画AI (plan_topics.py)    → ページ構成JSON生成
    ├─ 生成AI (generate_pages.py) → HTML本文生成
    ├─ 審査AI (review_pages.py)   → 品質・規約チェック
    └─ ビルドAI (build_site.py)   → 最終HTML組み立て
         │
         ▼
    [dist/ フォルダ]
         │
    git push
         │
         ▼
    [GitHub Actions]
         │
         ▼
    [GitHub Pages] → 🌐 公開
```

---

## セットアップ（初回のみ・人間が行う作業）

### 1. Ollamaをインストール
```
https://ollama.com からWindows版をダウンロード・インストール
```

### 2. モデルをダウンロード
```bash
ollama pull llama3.2
# または: ollama pull mistral
```

### 3. GitHubリポジトリを作成
1. GitHub にログイン
2. 新しいリポジトリを作成（Public必須）
3. このフォルダをpush:
```bash
git init
git remote add origin https://github.com/YOUR_USERNAME/micro-aff-site.git
git add .
git commit -m "initial commit"
git push -u origin main
```

### 4. GitHub Pages を有効化
1. リポジトリの Settings → Pages
2. Source: **GitHub Actions** を選択
3. 保存

### 5. アフィリエイトリンクを登録
`data/affiliate_map.json` の `YOUR_AFFILIATE_LINK_HERE` を実際のリンクに置き換える

### 6. サイトドメインを更新
`scripts/build_site.py` の `SITE_DOMAIN` を自分のGitHub PagesのURLに変更:
```python
SITE_DOMAIN = "yourusername.github.io/micro-aff-site"
```

### 7. まとめて初期セットアップ（推奨）
```bat
install.cmd YOUR_GITHUB_USERNAME micro-aff-site llama3.2
```

これで以下をまとめて実行します。
- Python依存のインストール
- Ollamaモデル確認と不足時の `ollama pull`
- `scripts/build_site.py` の `SITE_DOMAIN` 自動更新
- 初期ビルド

手動で行う場合:
```bash
pip install -r requirements.txt
```

---

## 使い方

### パイプライン実行（1件）
```bat
launch.cmd --push
launch.cmd --topic windows-backup-tools --push
launch.cmd --all --push
```

手動で行う場合:
```bash
python scripts/run_pipeline.py --push
python scripts/run_pipeline.py --topic windows-backup-tools --push
python scripts/run_pipeline.py --all --push
```

### テスト実行（ビルド・Gitのみスキップ）
```bat
launch.cmd --dry-run
```

手動で行う場合:
```bash
python scripts/run_pipeline.py --dry-run
```
※ `--dry-run` でも企画AI・生成AIの呼び出しは行うため、Ollama は必要です。

### 新しいトピックを追加
`data/topics_queue.json` の `queue` 配列に追加:
```json
{
  "id": "unique-topic-id",
  "title": "ページタイトル",
  "niche": "ジャンル",
  "intent": "比較・選定",
  "keywords": ["キーワード1", "キーワード2"],
  "affiliate_key": "affiliate_map.jsonのキー名",
  "status": "pending"
}
```

---

## ディレクトリ構成

```
micro-aff-site/
├─ data/
│  ├─ topics_queue.json   # 生成待ちトピック一覧
│  ├─ affiliate_map.json  # アフィリエイトリンク登録
│  └─ site_state.json     # 生成済みページ状態
├─ prompts/
│  ├─ planner.md          # 企画AIへの指示
│  ├─ writer.md           # 生成AIへの指示
│  └─ reviewer.md         # 審査AIへの指示
├─ scripts/
│  ├─ run_pipeline.py     # メインオーケストレータ
│  ├─ plan_topics.py      # 企画AI
│  ├─ generate_pages.py   # 生成AI
│  ├─ review_pages.py     # 審査AI（ルールベース）
│  ├─ build_site.py       # HTMLビルド・サイトマップ
│  └─ publish_git.py      # Git commit/push
├─ site/
│  └─ templates/
│     └─ page.html        # HTMLテンプレート
├─ dist/                  # 公開ファイル（GitHub Pagesが読む）
├─ .github/
│  └─ workflows/
│     └─ deploy.yml       # GitHub Actions設定
└─ requirements.txt
```

---

## コスト内訳

| 項目 | 費用 |
|------|------|
| Ollama（ローカルLLM） | 無料 |
| GitHub（公開リポジトリ） | 無料 |
| GitHub Pages | 無料 |
| GitHub Actions（public repo） | 無料 |
| アフィリエイトASP登録 | 無料 |
| **合計** | **¥0/月** |

収益が発生した場合のコスト: 売上の一定%(ASP手数料のみ)

---

## 規約遵守について

- 全ページに開示文を自動挿入（`data/affiliate_map.json`で設定）
- リンクの隠蔽・中継リダイレクト・JS動的置換はしない
- 審査AIが誇大表現・開示漏れを自動検出

---

## ライセンス

MIT
