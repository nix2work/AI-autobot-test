from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Iterable, List, Dict

import feedparser

from .sources import Source


@dataclass(frozen=True)
class Item:
    title: str
    url: str
    source_name: str
    category: str
    published_at: datetime


def _parse_dt(entry) -> datetime:
    # feedparser returns struct_time in published_parsed/updated_parsed
    st = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if st:
        return datetime.fromtimestamp(time.mktime(st), tz=timezone.utc)
    # Fallback: now (keeps pipeline moving)
    return datetime.now(tz=timezone.utc)


def fetch_items(sources: Iterable[Source]) -> List[Item]:
    items: List[Item] = []
    for src in sources:
        # Note: feedparser.parse() doesn't support timeout parameter
        feed = feedparser.parse(src.url, request_headers={"User-Agent": "aixux-digest-bot/1.0"})
        for e in feed.entries or []:
            title = (getattr(e, "title", "") or "").strip()
            link = (getattr(e, "link", "") or "").strip()
            if not title or not link:
                continue
            items.append(
                Item(
                    title=title,
                    url=link,
                    source_name=src.name,
                    category=src.category,
                    published_at=_parse_dt(e),
                )
            )
    return items


KEYWORDS = {
    "ai": [
        "llm",
        "agent",
        "agents",
        "transformer",
        "diffusion",
        "multimodal",
        "reasoning",
        "alignment",
        "openai",
        "anthropic",
        "gemini",
        "gpt",
        "claude",
        "huggingface",
    ],
    "ux": [
        "ux",
        "user research",
        "usability",
        "accessibility",
        "a11y",
        "hci",
        "design system",
        "design systems",
        "information architecture",
        "ia",
        "interaction design",
        "service design",
        "user experience",
        "user interface",
        "ui",
    ],
    "product": [
        "product design",
        "product management",
        "roadmap",
        "growth",
        "onboarding",
        "metrics",
        "activation",
        "retention",
        "experimentation",
        "pm",
        "product",
    ],
}

# 来源权重（基于你的需求定制）
SOURCE_WEIGHTS = {
    # AI 来源
    "OpenAI": 1.2,
    "Anthropic": 1.2,
    "Hugging Face": 1.2,
    "Google AI Blog": 1.1,
    
    # UX 来源（重点）
    "NNg": 1.3,  # Nielsen Norman Group - UX 权威
    "UX Collective": 1.2,
    "Smashing (UX)": 1.1,
    
    # Product 来源
    "Figma": 1.2,
    "Product Hunt": 1.2,
    "Atlassian Design": 1.1,
}


def _score_text(text: str, keywords: List[str]) -> int:
    """关键词匹配得分"""
    t = text.lower()
    return sum(1 for k in keywords if k in t)


def _calculate_score(item: Item) -> float:
    """
    综合评分 = 关键词匹配 × 0.4 + 时效性 × 0.4 + 来源权重 × 0.2
    
    针对 UX 内容给予额外加成，因为这是你的重点领域
    """
    # 1. 关键词匹配得分（仅匹配该分类的关键词）
    category_keywords = KEYWORDS.get(item.category, [])
    keyword_score = _score_text(item.title, category_keywords)
    
    # 2. 时效性得分（越新越高）
    now = datetime.now(tz=timezone.utc)
    age_hours = (now - item.published_at).total_seconds() / 3600
    # 24小时内=1.0, 48小时=0.5, 72小时=0.25
    recency_score = max(0, 1.0 - (age_hours / 72))
    
    # 3. 来源权重
    source_weight = SOURCE_WEIGHTS.get(item.source_name, 1.0)
    
    # 4. UX 分类加成（你是交互设计师，UX 内容更重要）
    category_bonus = 1.1 if item.category == "ux" else 1.0
    
    # 综合得分
    total_score = (
        keyword_score * 0.4 +
        recency_score * 0.4 +
        source_weight * 0.2
    ) * category_bonus
    
    return total_score


def rank_and_filter(
    items: Iterable[Item],
    max_items: int = 14,
    category_limits: Dict[str, int] = None
) -> List[Item]:
    """
    智能排序和过滤 - UX 重点配置
    
    Args:
        items: 所有抓取的资讯
        max_items: 总数限制（默认 14）
        category_limits: 每个分类的限制（默认 AI:4, UX:6, Product:4）
    
    Returns:
        排序后的资讯列表
    """
    # 默认分类限制：UX 重点配置
    if category_limits is None:
        category_limits = {
            "ai": 4,       # AI 工具和趋势
            "ux": 6,       # UX 设计重点
            "product": 4,  # Product 思维
        }
    
    # 过滤太旧的内容（保留 3 天内）
    cutoff_time = datetime.now(tz=timezone.utc) - timedelta(days=3)
    recent_items = [it for it in items if it.published_at >= cutoff_time]
    
    # 如果最近内容太少，扩展到 7 天
    if len(recent_items) < max_items:
        cutoff_time = datetime.now(tz=timezone.utc) - timedelta(days=7)
        recent_items = [it for it in items if it.published_at >= cutoff_time]
    
    # 按分类分组
    by_category: Dict[str, List[tuple[float, datetime, Item]]] = {
        "ai": [],
        "ux": [],
        "product": [],
    }
    
    for item in recent_items:
        if item.category in by_category:
            score = _calculate_score(item)
            by_category[item.category].append((score, item.published_at, item))
    
    # 每个分类内排序：先按分数，再按时间
    for category in by_category:
        by_category[category].sort(key=lambda x: (x[0], x[1]), reverse=True)
    
    # 从每个分类取 top N
    result: List[Item] = []
    seen_urls = set()
    
    for category, limit in category_limits.items():
        count = 0
        for score, pub_time, item in by_category.get(category, []):
            if item.url in seen_urls:
                continue
            result.append(item)
            seen_urls.add(item.url)
            count += 1
            if count >= limit:
                break
    
    # 如果总数不够，从剩余高分内容补充（优先 UX）
    if len(result) < max_items:
        all_remaining = []
        # 先添加 UX 剩余
        for score, pub_time, item in by_category.get("ux", []):
            if item.url not in seen_urls:
                all_remaining.append((score + 0.1, pub_time, item))  # UX 加成
        # 再添加其他
        for category in ["ai", "product"]:
            for score, pub_time, item in by_category[category]:
                if item.url not in seen_urls:
                    all_remaining.append((score, pub_time, item))
        
        all_remaining.sort(key=lambda x: (x[0], x[1]), reverse=True)
        
        for score, pub_time, item in all_remaining:
            if len(result) >= max_items:
                break
            result.append(item)
            seen_urls.add(item.url)
    
    return result[:max_items]
