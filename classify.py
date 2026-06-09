"""Keyword-based classification into topic categories.

Transparent, free, no ML. An article can belong to multiple categories.
"""
from __future__ import annotations

import yaml


def load_categories(path: str = "categories.yaml") -> dict[str, list[str]]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    # lowercase every keyword for case-insensitive matching
    return {cat: [kw.lower() for kw in kws] for cat, kws in data.items()}


def classify_one(article: dict, categories: dict[str, list[str]]) -> dict:
    """Add 'categories' (list) and 'matched_keywords' (dict) to the article."""
    haystack = f"{article.get('title', '')} {article.get('raw_text', '')}".lower()

    matched: dict[str, list[str]] = {}
    for cat, keywords in categories.items():
        hits = [kw for kw in keywords if kw in haystack]
        if hits:
            matched[cat] = hits

    if matched:
        # rank categories by number of keyword hits (descending)
        ranked = sorted(matched.keys(), key=lambda c: len(matched[c]), reverse=True)
        article["categories"] = ranked
    else:
        article["categories"] = ["Uncategorised"]

    article["matched_keywords"] = matched
    return article


def classify_all(articles: list[dict], categories: dict[str, list[str]]) -> list[dict]:
    return [classify_one(a, categories) for a in articles]


if __name__ == "__main__":
    import fetch

    cats = load_categories()
    src = fetch.load_sources()
    items = fetch.filter_recent(fetch.dedupe(fetch.fetch_all(src)))
    items = classify_all(items, cats)
    for a in items[:15]:
        print(f"{', '.join(a['categories']):<40} {a['title'][:60]}")
