from langchain_community.tools import DuckDuckGoSearchRun
import apprise


def search_internet(query: str) -> str:
    """Call this when the agent needs current info."""
    search = DuckDuckGoSearchRun()
    return search.run(query)


def send_telegram(message: str, telegram_url: str = "tgram://bottoken/ChatID") -> bool:
    """Send status updates to a Telegram bot endpoint via Apprise."""
    apobj = apprise.Apprise()
    apobj.add(telegram_url)
    return apobj.notify(body=message, title="Nexus Update")
