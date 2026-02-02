from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    category: str


def default_sources() -> Dict[str, List[Source]]:
    # Keep this small + RSS-first (stable). Users can override via SOURCES_JSON.
    return {
        "ai": [
            Source(name="OpenAI", url="https://openai.com/blog/rss/", category="ai"),
            Source(name="Anthropic", url="https://www.anthropic.com/news/rss.xml", category="ai"),
            Source(name="Hugging Face", url="https://huggingface.co/blog/feed.xml", category="ai"),
            Source(name="Google AI Blog", url="https://blog.google/technology/ai/rss/", category="ai"),
        ],
        "ux": [
            Source(name="NNg", url="https://www.nngroup.com/feed/rss/", category="ux"),
            Source(name="UX Collective", url="https://uxdesign.cc/feed", category="ux"),
            Source(name="Smashing (UX)", url="https://www.smashingmagazine.com/category/ux/feed/", category="ux"),
        ],
        "product": [
            Source(name="Figma", url="https://www.figma.com/blog/rss/", category="product"),
            Source(name="Atlassian Design", url="https://atlassian.design/blog/feed/", category="product"),
        ],
    }


def load_sources_from_env() -> Optional[Dict[str, List[Source]]]:
    raw = os.getenv("SOURCES_JSON")
    if not raw:
        return None
    obj = json.loads(raw)
    out: Dict[str, List[Source]] = {}
    for category, items in obj.items():
        out[str(category)] = [
            Source(
                name=str(it.get("name", "Unnamed")),
                url=str(it["url"]),
                category=str(category),
            )
            for it in (items or [])
            if isinstance(it, dict) and it.get("url")
        ]
    return out


def get_sources() -> List[Source]:
    by_cat = load_sources_from_env() or default_sources()
    sources: List[Source] = []
    for cat, items in by_cat.items():
        for s in items:
            sources.append(Source(name=s.name, url=s.url, category=cat))
    return sources

