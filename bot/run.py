from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

from .dedupe import fingerprint, load_seen, save_seen
from .fetcher import fetch_items, rank_and_filter
from .feishu import build_post_payload, send_webhook
from .sources import get_sources
from .ai_helper import batch_generate_summaries


def ensure_enough_items(all_items, seen_fingerprints, target_count=8, category_limits=None):
    """
    确保有足够数量的新内容，严格去重
    
    Args:
        all_items: 所有抓取的文章
        seen_fingerprints: 历史推送的 fingerprint 集合
        target_count: 目标数量
        category_limits: 分类限制
    
    Returns:
        去重后的文章列表
    """
    from .fetcher import rank_and_filter
    
    if category_limits is None:
        category_limits = {"ai": 4, "ux": 4}
    
    result = []
    seen_fps = set(seen_fingerprints)  # 复制一份，避免修改原集合
    
    # 阶段 1：7 天内内容
    print(f"  阶段1: 从 7 天内内容筛选...")
    recent_7d = [
        it for it in all_items
        if it.published_at >= datetime.now(tz=timezone.utc) - timedelta(days=7)
    ]
    ranked_7d = rank_and_filter(recent_7d, max_items=30, category_limits=category_limits)
    
    for item in ranked_7d:
        fp = fingerprint(item)  # 计算 fingerprint
        if fp in seen_fps:
            continue  # 已推送过，跳过
        
        result.append(item)
        seen_fps.add(fp)  # 添加到临时 seen 集合
        
        if len(result) >= target_count:
            break
    
    print(f"  → 7天内新内容: {len(result)} 条")
    
    # 阶段 2：1 个月内内容
    if len(result) < target_count:
        print(f"  阶段2: 内容不足，从 1 个月内补充...")
        recent_30d = [
            it for it in all_items
            if it.published_at >= datetime.now(tz=timezone.utc) - timedelta(days=30)
        ]
        ranked_30d = rank_and_filter(recent_30d, max_items=60, category_limits=category_limits)
        
        for item in ranked_30d:
            fp = fingerprint(item)
            if fp in seen_fps:
                continue
            
            result.append(item)
            seen_fps.add(fp)
            
            if len(result) >= target_count:
                break
        
        print(f"  → 补充后共: {len(result)} 条")
    
    # 阶段 3：所有内容
    if len(result) < target_count:
        print(f"  阶段3: 仍不足，从所有内容补充...")
        ranked_all = rank_and_filter(all_items, max_items=100, category_limits=category_limits)
        
        for item in ranked_all:
            fp = fingerprint(item)
            if fp in seen_fps:
                continue
            
            result.append(item)
            seen_fps.add(fp)
            
            if len(result) >= target_count:
                break
        
        print(f"  → 最终共: {len(result)} 条")
    
    # 如果还不够（极端情况）
    if len(result) < target_count:
        print(f"  ⚠️ 警告: 即使扩展到所有时间范围，去重后仍只有 {len(result)} 条")
        print(f"  → 这可能表示 RSS 源更新频率太低，建议添加更多源")
    
    return result[:target_count]


def main() -> int:
    webhook = os.getenv("FEISHU_WEBHOOK_URL", "").strip()
    if not webhook:
        raise SystemExit("❌ Missing FEISHU_WEBHOOK_URL")

    target_count = 8
    category_limits = {"ai": 4, "ux": 4}

    # 1. 抓取所有资讯
    sources = get_sources()
    print(f"📡 抓取资讯源（共 {len(sources)} 个）...")
    all_items = fetch_items(sources)
    print(f"✓ 抓取到 {len(all_items)} 条资讯")
    
    # 2. 加载历史记录（fingerprint 集合）
    state_path = Path("state/seen.json")
    seen = load_seen(state_path)
    print(f"📚 历史记录: {len(seen)} 条已推送")
    
    # 3. 智能筛选 + 严格去重
    print(f"🔍 智能筛选，目标 {target_count} 条...")
    selected_items = ensure_enough_items(
        all_items,
        seen,  # 传入 fingerprint 集合
        target_count=target_count,
        category_limits=category_limits
    )
    
    # 4. 统计分类
    ai_count = len([i for i in selected_items if i.category == "ai"])
    ux_count = len([i for i in selected_items if i.category == "ux"])
    print(f"✓ 最终选择 {len(selected_items)} 条（已去重）")
    print(f"  - AI: {ai_count} 条")
    print(f"  - UX: {ux_count} 条")

    # 5. 如果没有新内容
    if len(selected_items) == 0:
        print("⚠️ 没有新内容可推送")
        print("💡 建议：添加更多 RSS 源，或等待现有源更新")
        return 0

    # 6. 转换为字典格式
    items_dict = []
    for item in selected_items:
        items_dict.append({
            "title": item.title,
            "description": item.description,
            "url": item.url,
            "source_name": item.source_name,
            "category": item.category,
        })
    
    # 7. AI 生成摘要和翻译
    enhanced_items = batch_generate_summaries(items_dict)
    
    # 8. 推送到飞书
    print(f"📤 准备推送到飞书...")
    payload = build_post_payload(enhanced_items)
    result = send_webhook(payload, webhook)

    # 9. 更新历史记录（添加本次推送的 fingerprint）
    for item in selected_items:
        fp = fingerprint(item)
        seen.add(fp)
    
    save_seen(state_path, seen)
    print(f"✓ 状态已保存（新增 {len(selected_items)} 条记录）")

    # 10. 检查推送结果
    if isinstance(result, dict) and str(result.get("code", "0")) not in ("0", 0):
        print("❌ 飞书 webhook 响应:", result)
        return 2
    
    print("✅ 推送成功!")
    print(f"   响应: {result}")
    
    # 11. 打印一些调试信息
    print(f"\n📊 统计信息:")
    print(f"  - 本次推送: {len(selected_items)} 条")
    print(f"  - 历史总计: {len(seen)} 条")
    print(f"  - 去重率: {(1 - len(selected_items) / len(all_items)) * 100:.1f}%")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
