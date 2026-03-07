#!/usr/bin/env python3
"""
generate_pages.py - 生成AI
企画データをもとにHTML本文を生成する
"""

import json
import requests
from pathlib import Path

ROOT = Path(__file__).parent.parent
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"

def load_prompt_template(name: str) -> str:
    path = ROOT / "prompts" / f"{name}.md"
    return path.read_text(encoding="utf-8")

def call_ollama(prompt: str, model: str = MODEL) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.4,
            "num_predict": 4000,
        }
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

def generate_page(topic: dict, plan: dict) -> str:
    """企画データからHTML本文を生成する"""
    template = load_prompt_template("writer")

    plan_json = json.dumps(plan, ensure_ascii=False, indent=2)
    affiliate_key = topic.get("affiliate_key", "")
    cta_placement = plan.get("cta_placement", "mid")

    prompt = template.replace("{plan_json}", plan_json)
    prompt = prompt.replace("{affiliate_key}", affiliate_key)
    prompt = prompt.replace("{cta_placement}", cta_placement)

    response = call_ollama(prompt)
    return response

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from plan_topics import plan_topic

    test_topic = {
        "id": "windows-backup-tools",
        "title": "Windowsバックアップツール比較",
        "niche": "PC管理・効率化",
        "intent": "比較・選定",
        "keywords": ["windows バックアップ ソフト 無料"],
        "affiliate_key": "windows-backup"
    }
    plan = plan_topic(test_topic)
    html = generate_page(test_topic, plan)
    print(html[:500])
