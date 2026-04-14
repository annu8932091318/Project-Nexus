from typing import Callable, Dict

from src.tools.browser import search_internet, send_telegram


def get_tool_registry() -> Dict[str, Callable]:
    return {
        "search_internet": search_internet,
        "send_telegram": send_telegram,
    }
