"""Render the dashboard (index.html) from the classified + summarized articles."""
from __future__ import annotations

import os
from datetime import datetime

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Display order for category sections
CATEGORY_ORDER = [
    "Cloud Infrastructure",
    "Networks",
    "Cybersecurity",
    "GRC",
    "Data Centres",
    "Uncategorised",
]


def group_by_category(articles: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {c: [] for c in CATEGORY_ORDER}
    for a in articles:
        primary = a["categories"][0] if a.get("categories") else "Uncategorised"
        groups.setdefault(primary, []).append(a)
    # drop empty sections, preserve order
    return {c: groups[c] for c in CATEGORY_ORDER if groups.get(c)}


def render(articles: list[dict], out_path: str = "index.html",
           template_dir: str = "templates") -> str:
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("index.html")

    grouped = group_by_category(articles)
    html = template.render(
        grouped=grouped,
        categories=list(grouped.keys()),
        total=len(articles),
        updated=datetime.now().strftime("%A, %d %B %Y at %H:%M"),
    )

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return os.path.abspath(out_path)
