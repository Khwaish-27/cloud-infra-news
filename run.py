"""Daily pipeline entry point.

Run:  python run.py
Produces: index.html (open in a browser) and data/archive/YYYY-MM-DD.json
"""
from __future__ import annotations

import json
import os
from datetime import datetime

import fetch
import classify
import summarize
import render

RECENCY_HOURS = 48
SUMMARY_SENTENCES = 4
USE_SUMY = True


def log(msg: str) -> None:
    line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  {msg}"
    print(line)
    with open("run.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _strip_internal(articles: list[dict]) -> list[dict]:
    """Remove non-serializable / internal fields before saving as JSON."""
    cleaned = []
    for a in articles:
        cleaned.append({k: v for k, v in a.items() if not k.startswith("_")})
    return cleaned


def main() -> None:
    log("=== Pipeline start ===")

    # 1-4. Fetch, dedupe, recency filter
    sources = fetch.load_sources()
    articles = fetch.fetch_all(sources, log=log)
    log(f"Fetched {len(articles)} raw items")
    articles = fetch.dedupe(articles)
    articles = fetch.filter_recent(articles, hours=RECENCY_HOURS)
    log(f"{len(articles)} articles after dedupe + last {RECENCY_HOURS}h filter")

    # 5. Classify
    categories = classify.load_categories()
    articles = classify.classify_all(articles, categories)

    # 6. Summarize
    articles = summarize.summarize_all(
        articles, sentences=SUMMARY_SENTENCES, use_sumy=USE_SUMY, log=log
    )

    # 7. Persist data
    os.makedirs("data/archive", exist_ok=True)
    clean = _strip_internal(articles)
    with open("data/articles.json", "w", encoding="utf-8") as f:
        json.dump(clean, f, indent=2, ensure_ascii=False)
    stamp = datetime.now().strftime("%Y-%m-%d")
    with open(f"data/archive/{stamp}.json", "w", encoding="utf-8") as f:
        json.dump(clean, f, indent=2, ensure_ascii=False)

    # Category counts for the log
    counts: dict[str, int] = {}
    for a in articles:
        counts[a["categories"][0]] = counts.get(a["categories"][0], 0) + 1
    log("Category counts: " + ", ".join(f"{k}={v}" for k, v in counts.items()))

    # 8. Render dashboard
    path = render.render(articles, out_path="index.html")
    log(f"Dashboard written to {path}")
    log("=== Pipeline done ===\n")


if __name__ == "__main__":
    main()
