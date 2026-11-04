"""Render a proposal dict to a standalone HTML presentation document."""

from __future__ import annotations

import math
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .generator import clean_amounts, money, price_range_text, price_text, pricing_totals, project_kind
from .imagery import hero_data_uri

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "j2"]),
)
_env.filters["money"] = money
_env.filters["price_range"] = lambda item, currency: price_range_text(item["low"], item["high"], currency)


def total_weeks(p: dict) -> int:
    return max((int(m["end"]) for m in p["milestones"]), default=0)


def week_label(m: dict) -> str:
    start, end = int(m["start"]), int(m["end"])
    return f"Week {start}" if start == end else f"Weeks {start}–{end}"


def short_week_label(m: dict) -> str:
    start, end = int(m["start"]), int(m["end"])
    return f"W{start}" if start == end else f"W{start}–{end}"


def gantt(p: dict) -> dict:
    """Place each milestone on a week grid. Labels thin out on long projects."""
    n = max(total_weeks(p), 1)
    every = math.ceil(n / 14)
    return {
        "n": n,
        "labels": [{"week": w, "show": (w - 1) % every == 0} for w in range(1, n + 1)],
        "rows": [
            {
                **m,
                "col_start": int(m["start"]),
                "col_end": int(m["end"]) + 1,
                "label": week_label(m),
                "short": short_week_label(m),
            }
            for m in p["milestones"]
        ],
    }


def filename_stem(p: dict) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", f"{p['client']} {p['title']}".lower()).strip("-")
    return slug or "proposal"


def render_html(p: dict, *, editable: bool = False) -> str:
    """editable=True adds the click-to-edit toolbar used in the app preview."""
    low, high = pricing_totals(p)
    return _env.get_template("proposal.html.j2").render(
        p=p,
        editable=editable,
        weeks=total_weeks(p),
        gantt=gantt(p),
        price_total=price_text(p),
        has_price=high > 0,
        range_prices=any(
            round(lo) != round(hi) for lo, hi in (clean_amounts(i["low"], i["high"]) for i in p["price_items"])
        ),
        file_stem=filename_stem(p),
        hero_image=hero_data_uri(project_kind(p.get("project_type", ""))),
    )
