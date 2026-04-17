from __future__ import annotations

import os
from typing import Dict, List

from duckduckgo_search import DDGS


def search_internet(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Return lightweight web search results for agents."""
    if not query.strip():
        return []

    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=max_results)
        return [
            {
                "title": item.get("title", ""),
                "href": item.get("href", ""),
                "body": item.get("body", ""),
            }
            for item in results
        ]


def send_telegram(message: str) -> str:
    """Placeholder notifier to avoid hard failures when token/chat id are not configured."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return "Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID."

    # External side effects are intentionally not executed here without explicit integration.
    return "Telegram delivery is configured but disabled in safe mode."
