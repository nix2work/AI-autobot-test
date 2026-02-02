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
    print(f"📡 抓取资讯源...")
    items = fetch_items(sources)
    print(f"✓ 抓取到 {len(items)} 条资讯")
    
    # UX 重点配置：AI(4) + UX(6) + Product(4) = 14 条
    ranked = rank_and_filter(
        items,
        max_items=14,
        category_limits={
            "ai": 4,
            "ux": 6,
            "product": 4,
        }
    )
    print(f"✓ 排序后保留 {len(ranked)} 条")
    print(f"  - AI: {len([i for i in ranked if i.category == 'ai'])} 条")
    print(f"  - UX: {len([i for i in ranked if i.category == 'ux'])} 条")
    print(f"  - Product: {len([i for i in ranked if i.category == 'product'])} 条")

    state_path = Path("state/seen.json")
    seen = load_seen(state_path)
    new_items, updated_seen = filter_new(ranked, seen)
    print(f"✓ 去重后有 {len(new_items)} 条新内容")

    # If everything is duplicate, still send something small (to show liveness),
    # but do not spam: send top 3 as fallback.
    to_send = new_items if new_items else ranked[:3]
    print(f"📤 准备推送 {len(to_send)} 条到飞书")

    payload = build_post_payload(to_send)
    result = send_webhook(payload, webhook)

    save_seen(state_path, updated_seen)
    print(f"✓ 状态已保存")

    # Basic error signal for CI logs
    if isinstance(result, dict) and str(result.get("code", "0")) not in ("0", 0):
        print("❌ 飞书 webhook 响应:", result)
        return 2
    print("✅ 飞书 webhook 响应:", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
