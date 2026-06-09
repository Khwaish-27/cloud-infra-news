"""Summarize articles in 3-4 lines. No API keys.

Tier 1: use the feed's own summary text, trimmed to a few sentences.
Tier 2: if the text is long enough, run sumy (TextRank) for a cleaner extract.

If sumy / nltk data is unavailable, we fall back to tier 1 automatically.
"""
from __future__ import annotations

import re

# sumy is optional at import time; we degrade gracefully if it's missing.
try:
    from sumy.parsers.plaintext import PlaintextParser
    from sumy.nlp.tokenizers import Tokenizer
    from sumy.summarizers.text_rank import TextRankSummarizer
    _SUMY_AVAILABLE = True
except Exception:  # noqa: BLE001
    _SUMY_AVAILABLE = False


_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _first_sentences(text: str, n: int = 4) -> str:
    text = text.strip()
    if not text:
        return ""
    sentences = _SENTENCE_SPLIT.split(text)
    return " ".join(sentences[:n]).strip()


def _sumy_summary(text: str, sentences: int = 4) -> str:
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = TextRankSummarizer()
    picked = summarizer(parser.document, sentences)
    return " ".join(str(s) for s in picked).strip()


def summarize_text(text: str, sentences: int = 4, use_sumy: bool = True) -> str:
    text = (text or "").strip()
    if not text:
        return "No summary available."

    # Short text: just trim, sumy adds nothing.
    word_count = len(text.split())
    if use_sumy and _SUMY_AVAILABLE and word_count > 60:
        try:
            result = _sumy_summary(text, sentences)
            if result:
                return result
        except Exception:  # noqa: BLE001 - fall back on any nltk/tokenizer issue
            pass

    return _first_sentences(text, sentences)


def summarize_all(articles: list[dict], sentences: int = 4, use_sumy: bool = True,
                  log=print) -> list[dict]:
    for a in articles:
        a["summary"] = summarize_text(a.get("raw_text", ""), sentences, use_sumy)
    log(f"Summarized {len(articles)} articles "
        f"({'sumy' if (_SUMY_AVAILABLE and use_sumy) else 'feed-text'} mode)")
    return articles


if __name__ == "__main__":
    sample = (
        "A major cloud provider reported an outage affecting several regions. "
        "The incident lasted nearly three hours and disrupted enterprise workloads. "
        "Engineers traced the cause to a misconfigured network routing update. "
        "Services were restored after the change was rolled back. "
        "The company said it will publish a full post-incident report next week."
    )
    print(summarize_text(sample))
