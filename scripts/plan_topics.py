#!/usr/bin/env python3
"""
plan_topics.py - 企画AI
Ollamaを使ってトピックのページ構成を生成する
"""

import json
import re
import requests
from pathlib import Path

ROOT = Path(__file__).parent.parent
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"  # または mistral, phi3 など手元にあるモデル

def load_prompt_template(name: str) -> str:
    path = ROOT / "prompts" / f"{name}.md"
    return path.read_text(encoding="utf-8")

def call_ollama(prompt: str, model: str = MODEL) -> str:
    """Ollama APIを呼び出してテキストを生成する"""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 2000,
        }
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json().get("response", "")
    except requests.exceptions.ConnectionError:
        print("  ❌ Ollamaに接続できません。`ollama serve` が起動しているか確認してください。")
        return ""
    except Exception as e:
        print(f"  ❌ Ollama APIエラー: {e}")
        return ""

def extract_json(text: str) -> dict:
    """レスポンステキストからJSONを抽出する"""
    # コードブロック内のJSONを探す
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # コードブロックなしのJSONを探す
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return {}

def plan_topic(topic: dict) -> dict:
    """トピック情報からページ構成を生成する"""
    template = load_prompt_template("planner")

    # テンプレートに値を埋め込む
    prompt = template.replace("{topic_id}", topic.get("id", ""))
    prompt = prompt.replace("{title}", topic.get("title", ""))
    prompt = prompt.replace("{niche}", topic.get("niche", ""))
    prompt = prompt.replace("{intent}", topic.get("intent", ""))
    prompt = prompt.replace("{keywords}", ", ".join(topic.get("keywords", [])))

    response = call_ollama(prompt)
    if not response:
        return {}

    plan = extract_json(response)
    if not plan:
        print(f"  ⚠️  JSON抽出失敗。レスポンス先頭: {response[:200]}")
        return {}

    return plan

if __name__ == "__main__":
    # テスト実行
    test_topic = {
        "id": "windows-backup-tools",
        "title": "Windowsバックアップツール比較",
        "niche": "PC管理・効率化",
        "intent": "比較・選定",
        "keywords": ["windows バックアップ ソフト 無料", "windows バックアップ おすすめ"],
        "affiliate_key": "windows-backup"
    }
    result = plan_topic(test_topic)
    print(json.dumps(result, ensure_ascii=False, indent=2))
