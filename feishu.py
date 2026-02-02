from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime
from typing import Dict, List

import requests

from .dedupe import canonicalize_url
from .fetcher import Item


def _utc_date_str() -> str:
    # Use local date in runner timezone (GitHub Actions is UTC). We include date only for readability.
    return datetime.now().strftime("%Y-%m-%d")


def build_post_payload(items: List[Item]) -> Dict:
    keyword = os.getenv("FEISHU_KEYWORD", "").strip()
    title = f"AI×UX Daily Digest · {_utc_date_str()}"
    if keyword:
        title = f"{title} · {keyword}"

    content: List[List[Dict]] = []
    content.append([{"tag": "text", "text": "Top picks (AI × UX)\n"}])

    for it in items:
        url = canonicalize_url(it.url)
        line = [
            {"tag": "text", "text": f"[{it.category.upper()}] "},
            {"tag": "a", "text": it.title, "href": url},
            {"tag": "text", "text": f"  · {it.source_name}\n"},
        ]
        content.append(line)

    return {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": title,
                    "content": content,
                }
            }
        },
    }


def sign_if_needed(headers: Dict[str, str], payload: Dict) -> Dict:
    secret = os.getenv("FEISHU_SECRET", "").strip()
    if not secret:
        return payload

    timestamp = str(int(time.time()))
    string_to_sign = f"{timestamp}\n{secret}"
    h = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
    sign = base64.b64encode(h).decode("utf-8")

    # Feishu v2 webhook supports sign + timestamp at top-level
    out = dict(payload)
    out["timestamp"] = timestamp
    out["sign"] = sign
    return out


def send_webhook(payload: Dict, webhook_url: str, timeout: int = 20) -> Dict:
    headers = {"Content-Type": "application/json; charset=utf-8"}
    final_payload = sign_if_needed(headers, payload)
    resp = requests.post(webhook_url, headers=headers, data=json.dumps(final_payload, ensure_ascii=False).encode("utf-8"), timeout=timeout)
    try:
        return resp.json()
    except Exception:
        return {"status_code": resp.status_code, "text": resp.text}

