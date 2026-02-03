from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

from .dedupe import filter_new, load_seen, save_seen
from .fetcher import fetch_items, rank_and_filter
from .feishu import build_post_payload, send_webhook
from .sources import get_sources
from .ai_helper import batch_generate_summaries


def ensure_enough_items(
    all_items,
    seen_set,
    target_count=8,
    category_limits=None
):
    """
    确保有足够数量的新内容
    
    策略：
    1. 优先使用高质量新内容
    2. 不足时从 7 天内补充
    3. 还不够从 1 个月内补充
    """
    from .fetcher import rank_and_filter
    from .dedupe import filter_new
    
    if category_limits is None:
        category_limits = {"ai": 4, "ux": 4}
    
    result = []
    seen_urls = set(seen_set)
    
    # 阶段 1：7 天内高优先级内容
    print(f"  阶段1: 从 7 天内内容筛选...")
    recent_7d = [
        it for it in all_items
        if it.published_at >= datetime.now(tz=timezone.utc) - timedelta(days=7)
    ]
    ranked_7d = rank_and_filter(recent_7d, max_items=20, category_limits=category_limits)
    
    for item in ranked_7d:
        if item.url not in seen_urls:
            result.append(item)
            seen_urls.add(item.url)
        if len(result) >= target_count:
            break
    
    print(f"  → 7天内新内容: {len(result)} 条")
    
    # 阶段 2：如果不足，从 1 个月内补充
    if len(result) < target_count:
        print(f"  阶段2: 内容不足，从 1 个月内补充...")
        recent_30d = [
            it for it in all_items
            if it.published_at >= datetime.now(tz=timezone.utc) - timedelta(days=30)
        ]
        ranked_30d = rank_and_filter(recent_30d, max_items=50, category_limits=category_limits)
        
        for item in ranked_30d:
            if item.url not in seen_urls:
                result.append(item)
                seen_urls.add(item.url)
            if len(result) >= target_count:
                break
        
        print(f"  → 补充后共: {len(result)} 条")
    
    # 阶段 3：如果还不足，放宽所有时间限制
    if len(result) < target_count:
        print(f"  阶段3: 仍不足，从所有内容补充...")
        ranked_all = rank_and_filter(all_items, max_items=100, category_limits=category_limits)
        
        for item in ranked_all:
            if item.url not in seen_urls:
                result.append(item)
                seen_urls.add(item.url)
            if len(result) >= target_count:
                break
        
        print(f"  → 最终共: {len(result)} 条")
    
    return result[:target_count]


def main() -> int:
    webhook = os.getenv("FEISHU_WEBHOOK_URL", "").strip()
    if not webhook:
        raise SystemExit("❌ Missing FEISHU_WEBHOOK_URL")

    target_count = 8  # 目标推送数量
    category_limits = {"ai": 4, "ux": 4}

    # 1. 抓取资讯
    sources = get_sources()
    print(f"📡 抓取资讯源（共 {len(sources)} 个）...")
    all_items = fetch_items(sources)
    print(f"✓ 抓取到 {len(all_items)} 条资讯")
    
    # 2. 加载历史去重数据
    state_path = Path("state/seen.json")
    seen = load_seen(state_path)
    print(f"📚 历史记录: {len(seen)} 条已推送")
    
    # 3. 智能筛选，确保数量充足
    print(f"🔍 智能筛选，目标 {target_count} 条...")
    selected_items = ensure_enough_items(
        all_items,
        seen,
        target_count=target_count,
        category_limits=category_limits
    )
    
    # 统计分类
    ai_count = len([i for i in selected_items if i.category == "ai"])
    ux_count = len([i for i in selected_items if i.category == "ux"])
    print(f"✓ 最终选择 {len(selected_items)} 条")
    print(f"  - AI: {ai_count} 条")
    print(f"  - UX: {ux_count} 条")

    # 4. 如果没有新内容（极端情况），停止推送
    if len(selected_items) == 0:
        print("⚠️ 没有新内容，跳过本次推送")
        return 0

    # 5. 转换为字典格式（用于 AI 处理）
    items_dict = []
    for item in selected_items:
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

    # 8. 更新去重数据（添加本次推送的 URL）
    from .dedupe import fingerprint
    for item in selected_items:
        fp = fingerprint(item)
        seen.add(fp)
    
    save_seen(state_path, seen)
    print(f"✓ 状态已保存（新增 {len(selected_items)} 条记录）")

    # 9. 检查结果
    if isinstance(result, dict) and str(result.get("code", "0")) not in ("0", 0):
        print("❌ 飞书 webhook 响应:", result)
        return 2
    
    print("✅ 推送成功!")
    print(f"   响应: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
