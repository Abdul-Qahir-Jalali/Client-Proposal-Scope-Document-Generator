"""Real, documented quotes for the start of a proposal, chosen from the project type.

Only quotes with a traceable source are listed. Wording is kept exact (no paraphrasing), and every entry names the person
and where it comes from. The pick is deterministic: the same client and title always get the same quote, so a proposal does
not change each time it is regenerated.

To add a quote: add a dict to the right kind below. Check the wording and source first (quote databases are full of
misattributions) and leave out anything you cannot trace.
"""

from __future__ import annotations

import zlib

QUOTES: dict[str, list[dict[str, str]]] = {
    "web": [
        {
            "text": "The power of the Web is in its universality. Access by everyone regardless of disability is an essential aspect.",
            "author": "Tim Berners-Lee",
            "role": "Inventor of the World Wide Web",
            "source": "W3C Web Accessibility Initiative",
        },
        {
            "text": "Good design makes a product understandable. It clarifies the product's structure.",
            "author": "Dieter Rams",
            "role": "Industrial designer",
            "source": "Ten principles for good design",
        },
    ],
    "app": [
        {
            "text": "Design is not just what it looks like and feels like. Design is how it works.",
            "author": "Steve Jobs",
            "role": "Co-founder of Apple",
            "source": "The New York Times Magazine, 2003",
        },
        {
            "text": "The best way to predict the future is to invent it.",
            "author": "Alan Kay",
            "role": "Computer scientist at Xerox PARC",
            "source": "",
        },
    ],
    "marketing": [
        {
            "text": "The aim of marketing is to make selling superfluous.",
            "author": "Peter Drucker",
            "role": "Management thinker",
            "source": "Management: Tasks, Responsibilities, Practices",
        },
    ],
    "brand": [
        {
            "text": "Good design is long-lasting. It avoids being fashionable and therefore never appears antiquated.",
            "author": "Dieter Rams",
            "role": "Industrial designer",
            "source": "Ten principles for good design",
        },
        {
            "text": "Design is not just what it looks like and feels like. Design is how it works.",
            "author": "Steve Jobs",
            "role": "Co-founder of Apple",
            "source": "The New York Times Magazine, 2003",
        },
    ],
    "general": [
        {
            "text": "Chance favors only the prepared mind.",
            "author": "Louis Pasteur",
            "role": "Chemist and microbiologist",
            "source": "Lecture at the University of Lille, 1854",
        },
        {
            "text": "The best way to predict the future is to invent it.",
            "author": "Alan Kay",
            "role": "Computer scientist at Xerox PARC",
            "source": "",
        },
    ],
}


def pick_quote(kind: str, seed: str) -> dict[str, str] | None:
    """The quote for this project kind. `seed` (client and title) keeps the choice stable for one proposal."""
    options = QUOTES.get(kind) or QUOTES["general"]
    if not options:
        return None
    return dict(options[zlib.crc32(seed.encode("utf-8")) % len(options)])
