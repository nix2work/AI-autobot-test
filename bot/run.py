from __future__ import annotations

import os
from pathlib import Path

from .dedupe import filter_new, load_seen, save_seen
from .fetcher import fetch_items, rank_and_filter
from .feishu import build_post_payload, send_webhook
from .sources import get_sources
from .ai_helper import batch_generate_summaries


def main() -> int:
    webhook = os.getenv("FEISHU_WEBHOOK_URL", "").strip()
    if not webhook:
        raise SystemExit("❌ Missing FEISHU_WEBHOOK_URL")

    # 1. 抓取资讯
    sources = get_sources()
    print(f"📡 抓取资讯源（共 {len(sources)} 个）...")
    items = fetch_items(sources)
    print(f"✓ 抓取到 {len(items)} 条资讯")
    
    # 2. 排序和过滤
    print(f"🔍 智能排序和过滤...")
    ranked = rank_and_filter(
        items,
        max_items=8,
        category_limits={
            "ai": 4,
            "ux": 4,
        }
    )
    print(f"✓ 排序后保留 {len(ranked)} 条")

    # 3. 去重（基于历史）
    state_path = Path("state/seen.json")
    seen = load_seen(state_path)
    new_items, updated_seen = filter_new(ranked, seen)
    print(f"✓ 去重后有 {len(new_items)} 条新内容")

    # 4. 如果没有新内容，使用 Top 3 作为保底
    to_send = new_items if new_items else ranked[:3]
    print(f"📝 准备处理 {len(to_send)} 条")

    # 5. 转换为字典格式（用于 AI 处理）
    items_dict = []
    for item in to_send:
        items_dict.append({
            "title": item.title,
            "description": item.description,
            "url": item.url,
            "source_name": item.source_name,
            "category": item.category,
        })
    
    # 6. 生成摘要和翻译（使用 AI）
    enhanced_items = batch_generate_summaries(items_dict)
    
    # 7. 构建飞书消息
    print(f"📤 准备推送到飞书...")
    payload = build_post_payload(enhanced_items)
    result = send_webhook(payload, webhook)

    # 8. 保存状态
    save_seen(state_path, updated_seen)
    print(f"✓ 状态已保存")

    # 9. 检查结果
    if isinstance(result, dict) and str(result.get("code", "0")) not in ("0", 0):
        print("❌ 飞书 webhook 响应:", result)
        return 2
    
    print("✅ 推送成功!")
    print(f"   响应: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
