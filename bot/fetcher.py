from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List, Optional

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


def fetch_items(sources: Iterable[Source], timeout: int = 20) -> List[Item]:
    items: List[Item] = []
    for src in sources:
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
    ],
}


def _score_text(text: str, keywords: List[str]) -> int:
    t = text.lower()
    return sum(1 for k in keywords if k in t)


def rank_and_filter(items: Iterable[Item], max_items: int = 8) -> List[Item]:
    scored = []
    for it in items:
        kw = KEYWORDS.get(it.category, []) + KEYWORDS.get("ai", []) + KEYWORDS.get("ux", [])
        score = _score_text(it.title, kw)
        scored.append((score, it.published_at, it))

    # Keep anything with score>0; if too sparse, fall back to freshest.
    positives = [t for t in scored if t[0] > 0]
    pool = positives if len(positives) >= 3 else scored

    pool.sort(key=lambda x: (x[0], x[1]), reverse=True)
    out: List[Item] = []
    seen_urls = set()
    for _, __, it in pool:
        if it.url in seen_urls:
            continue
        out.append(it)
        seen_urls.add(it.url)
        if len(out) >= max_items:
            break
    return out

