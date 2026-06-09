"""Fetch and normalize articles from RSS feeds and Google News keyword searches.

No API keys required. Everything goes through feedparser.
"""
from __future__ import annotations

import urllib.parse
from datetime import datetime, timezone, timedelta

import feedparser
import yaml
from bs4 import BeautifulSoup


def _clean_html(raw: str) -> str:
    """Strip HTML tags and collapse whitespace."""
    if not raw:
        return ""
    text = BeautifulSoup(raw, "html.parser").get_text(separator=" ")
    return " ".join(text.split())


def _parse_date(entry) -> datetime | None:
    """Best-effort published date as a timezone-aware datetime (UTC)."""
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except (TypeError, ValueError):
                pass
    return None


def _normalize(entry, source_name: str) -> dict:
    summary = _clean_html(entry.get("summary", "") or entry.get("description", ""))
    title = _clean_html(entry.get("title", "")) or "(untitled)"
    published = _parse_date(entry)
    return {
        "title": title,
        "url": entry.get("link", "").strip(),
        "source": source_name,
        "published": published.isoformat() if published else None,
        "_published_dt": published,          # used internally for filtering
        "raw_text": summary,                 # feed's own summary text
    }


def _google_news_url(query: str, locale: str) -> str:
    q = urllib.parse.quote(query)
    return f"https://news.google.com/rss/search?q={q}&{locale}"


def load_sources(path: str = "sources.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch_all(sources: dict, log=print) -> list[dict]:
    """Fetch every source and return a flat list of normalized articles."""
    articles: list[dict] = []

    # 1. Direct publisher RSS feeds
    for feed in sources.get("rss_feeds", []):
        name, url = feed["name"], feed["url"]
        try:
            parsed = feedparser.parse(url)
            count = len(parsed.entries)
            for entry in parsed.entries:
                articles.append(_normalize(entry, name))
            log(f"[RSS]  {name:<22} {count:>3} items")
        except Exception as e:  # noqa: BLE001
            log(f"[RSS]  {name:<22} ERROR: {e}")

    # 2. Google News keyword searches (free, no key)
    locale = sources.get("google_news_locale", "hl=en-US&gl=US&ceid=US:en")
    for q in sources.get("google_news", []):
        name, query = q["name"], q["query"]
        url = _google_news_url(query, locale)
        try:
            parsed = feedparser.parse(url)
            count = len(parsed.entries)
            for entry in parsed.entries:
                articles.append(_normalize(entry, f"Google News: {name}"))
            log(f"[GNews] {name:<22} {count:>3} items")
        except Exception as e:  # noqa: BLE001
            log(f"[GNews] {name:<22} ERROR: {e}")

    return articles


def dedupe(articles: list[dict]) -> list[dict]:
    """Drop duplicates by URL, then by near-identical title."""
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    out: list[dict] = []
    for a in articles:
        url = a.get("url", "")
        title_key = "".join(c for c in a["title"].lower() if c.isalnum())[:80]
        if url and url in seen_urls:
            continue
        if title_key and title_key in seen_titles:
            continue
        seen_urls.add(url)
        seen_titles.add(title_key)
        out.append(a)
    return out


def filter_recent(articles: list[dict], hours: int = 48) -> list[dict]:
    """Keep articles published within the last `hours`. Undated items are kept."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    out = []
    for a in articles:
        dt = a.get("_published_dt")
        if dt is None or dt >= cutoff:
            out.append(a)
    return out


if __name__ == "__main__":
    src = load_sources()
    items = fetch_all(src)
    items = dedupe(items)
    items = filter_recent(items, hours=48)
    print(f"\nTotal after dedupe + recency filter: {len(items)} articles\n")
    for a in items[:10]:
        print(f"- [{a['source']}] {a['title']}")
