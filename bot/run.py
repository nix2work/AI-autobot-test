from __future__ import annotations

import os
from pathlib import Path

from .dedupe import filter_new, load_seen, save_seen
from .fetcher import fetch_items, rank_and_filter
from .feishu import build_post_payload, send_webhook
from .sources import get_sources


def main() -> int:
    webhook = os.getenv("FEISHU_WEBHOOK_URL", "").strip()
    if not webhook:
        raise SystemExit("Missing FEISHU_WEBHOOK_URL")

    sources = get_sources()
    items = fetch_items(sources)
    ranked = rank_and_filter(items, max_items=8)

    state_path = Path("state/seen.json")
    seen = load_seen(state_path)
    new_items, updated_seen = filter_new(ranked, seen)

    # If everything is duplicate, still send something small (to show liveness),
    # but do not spam: send top 3 as fallback.
    to_send = new_items if new_items else ranked[:3]

    payload = build_post_payload(to_send)
    result = send_webhook(payload, webhook)

    save_seen(state_path, updated_seen)

    # Basic error signal for CI logs
    if isinstance(result, dict) and str(result.get("code", "0")) not in ("0", 0):
        print("Feishu webhook response:", result)
        return 2
    print("Feishu webhook response:", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

