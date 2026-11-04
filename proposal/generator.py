"""Turn basic project details into a structured proposal (a plain dict).

Everything here is template based, so it works offline with no API key.
The dict it returns is what the editor, the HTML template and the DOCX
exporter all share.
"""

from __future__ import annotations

import json
import math
import re
from datetime import date, timedelta
from pathlib import Path

from .limits import MAX_AMOUNT, MAX_ITEM_CHARS, MAX_LIST_ITEMS, MAX_NAME_CHARS, MAX_WEEKS, clamp, clean_text
from .quotes import pick_quote

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"

# Input fields, in the order they appear in the form and in free-form text.
FIELDS = ("client_name", "project_type", "goals", "deliverables", "timeline", "pricing", "notes")

FIELD_LABELS = {
    "client_name": "Client",
    "project_type": "Project type",
    "goals": "Goals",
    "deliverables": "Deliverables",
    "timeline": "Timeline",
    "pricing": "Pricing",
    "notes": "Notes",
}

ALIASES = {
    "client_name": ("client", "client name", "company", "customer", "prepared for"),
    "project_type": ("project type", "type", "project"),
    "goals": ("goals", "goal", "objectives", "objective"),
    "deliverables": ("deliverables", "deliverable", "key deliverables", "scope"),
    "timeline": ("timeline", "duration", "deadline", "time frame", "timeframe"),
    "pricing": ("pricing", "price", "budget", "cost", "fee"),
    "notes": ("notes", "special notes", "note", "extras"),
}

# (name, share of time and budget, description)
PHASES = {
    "web": [
        ("Discovery & Planning", 0.15, "Kickoff call, content audit, sitemap and wireframes approved."),
        ("Design", 0.25, "Visual design of the key pages, with two rounds of revisions."),
        ("Development", 0.40, "Build, content entry, forms and integrations, tested on real devices."),
        ("Review & Launch", 0.20, "Client review, fixes, go-live and handover."),
    ],
    "app": [
        ("Discovery & Planning", 0.12, "Requirements workshop, user flows and technical plan signed off."),
        ("UX/UI Design", 0.22, "Clickable prototype and final screen designs approved."),
        ("Development", 0.46, "Sprint-based build with a working demo at the end of each sprint."),
        ("Testing & Launch", 0.20, "QA, bug fixing, store submission or deployment, and handover."),
    ],
    "marketing": [
        ("Strategy & Research", 0.20, "Audience research, channel plan and success metrics agreed."),
        ("Creative Production", 0.30, "Content, copy and visuals produced and approved."),
        ("Campaign Launch", 0.20, "Campaign goes live across the agreed channels."),
        ("Optimise & Report", 0.30, "Weekly tuning, plus a final results report with next steps."),
    ],
    "brand": [
        ("Discovery", 0.20, "Brand questionnaire, competitor review and creative direction."),
        ("Concepts", 0.30, "Initial concepts presented for feedback."),
        ("Refinement", 0.30, "Chosen concept refined through revision rounds."),
        ("Final Files & Guidelines", 0.20, "Final artwork, file formats and a short brand guide."),
    ],
    "general": [
        ("Discovery & Planning", 0.20, "Kickoff, requirements and an agreed plan."),
        ("Production", 0.50, "The main work, with regular progress updates."),
        ("Review & Delivery", 0.30, "Client review, final changes and handover."),
    ],
}

KIND_PATTERNS = (
    ("app", r"\bapps?\b|application|mobile|software|platform|saas"),
    ("web", r"web|site|landing|e-?commerce|shopify|wordpress|store"),
    ("marketing", r"market|campaign|seo|social|advert|\bads?\b|content|email"),
    ("brand", r"brand|logo|identity|design"),
)

EXCLUSIONS = {
    "web": [
        "Writing website copy and taking photography (unless listed above)",
        "Domain registration and hosting fees",
        "Paid plug-ins, stock images and third-party licences",
        "Work on pages or features not listed in the deliverables",
    ],
    "app": [
        "App store developer account fees",
        "Third-party service and server costs",
        "Features not listed in the deliverables",
        "Ongoing maintenance after the support period",
    ],
    "marketing": [
        "Paid advertising spend (billed directly to the client)",
        "Photography, video shoots and influencer fees",
        "Channels not named in the deliverables",
        "Work after the campaign end date",
    ],
    "brand": [
        "Trademark searches and legal registration",
        "Printing and production of physical items",
        "Stock images and font licences",
        "Applications of the brand not listed in the deliverables",
    ],
    "general": [
        "Work not listed in the deliverables",
        "Third-party costs and licences",
        "Ongoing support after delivery",
    ],
}

STANDARD_INCLUSIONS = ("Two rounds of revisions per deliverable", "Regular progress updates")

ASSUMPTIONS = [
    "The client names one main contact who can give feedback and approvals.",
    "Feedback is shared within 3 working days. Late feedback may move the timeline.",
    "Content, logins and files the client agreed to supply arrive on time.",
    "Requests outside the scope above are quoted and agreed in writing before work starts.",
]

PAYMENT_TERMS = [
    "40% on signing, to book the project in.",
    "30% at the mid-point milestone.",
    "30% on final delivery.",
    "Invoices are payable within 14 days.",
]

NEXT_STEPS = [
    "Review this proposal and share any changes you would like.",
    "Sign off the scope, timeline and pricing.",
    "Pay the first invoice to reserve the start date.",
    "Join the kickoff call and begin Phase 1.",
]

_SYMBOL_BY_CODE = {"usd": "$", "gbp": "£", "eur": "€", "inr": "₹"}
_NOT_MONEY_RE = re.compile(
    r"\s*(?:%|(?:percent|months?|weeks?|days?|years?|yrs?|hours?|hrs?|pages?|phases?|payments?|installments?)\b)", re.I
)
_NUMBER_RE = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")
_BULLET_RE = re.compile(r"^\s*(?:[-*•–]|\d+[.)])\s*")
_LABEL_RE = re.compile(r"^\s*([A-Za-z][A-Za-z ]{1,24}?)\s*[:=]\s*(.*)$")


# ---------------------------------------------------------------- parsing


def to_list(value, split_commas: bool = False) -> list[str]:
    """Split text (or a list) into clean items. Bullets and numbering are removed."""
    if isinstance(value, (list, tuple)):
        raw = [str(v) for v in value]
    else:
        raw = [ln for ln in str(value or "").splitlines() if ln.strip()]
        if len(raw) == 1:
            pattern = r"\s*[;,]\s*" if split_commas else r"\s*;\s*"
            raw = re.split(pattern, raw[0])
    items = (clean_text(_BULLET_RE.sub("", r), MAX_ITEM_CHARS) for r in raw)
    return [i for i in items if i][:MAX_LIST_ITEMS]


def parse_freeform(text: str) -> dict[str, str]:
    """Read 'Label: value' lines (with bullet lines underneath) into input fields."""
    found: dict[str, list[str]] = {f: [] for f in FIELDS}
    current = None
    for line in str(text or "").splitlines():
        match = _LABEL_RE.match(line)
        field = _field_for(match.group(1)) if match else None
        if match and field:
            current = field
            rest = match.group(2).strip()
            if rest:
                found[field].append(rest)
        elif line.strip() and current:
            found[current].append(line.strip())
    return {f: "\n".join(v) for f, v in found.items()}


def _field_for(label: str) -> str | None:
    label = label.strip().lower()
    for field, names in ALIASES.items():
        if label in names:
            return field
    return None


def to_freeform(inputs: dict) -> str:
    """The reverse of parse_freeform. Used to show a sample as free-form text."""
    lines = []
    for field in FIELDS:
        value = str(inputs.get(field, "") or "").strip()
        if not value:
            continue
        items = to_list(value, split_commas=(field == "deliverables"))
        if field in ("goals", "deliverables", "notes") and len(items) > 1:
            lines.append(f"{FIELD_LABELS[field]}:")
            lines += [f"- {i}" for i in items]
        else:
            lines.append(f"{FIELD_LABELS[field]}: {value}")
    return "\n".join(lines)


def parse_money(text: str, cap: bool = True) -> tuple[float, float, str]:
    """Return (low, high, currency symbol). Handles '$4,000', '3k-5k', '£2,500 to £3,500'.

    Amounts above MAX_AMOUNT are lowered to it, unless cap=False (used only to detect that).
    """
    text = str(text or "")
    currency = "$"
    for symbol in "$£€₹":
        if symbol in text:
            currency = symbol
            break
    else:
        code = re.search(r"\b(usd|gbp|eur|inr|pkr|aed|cad|aud)\b", text, re.I)
        if code:
            c = code.group(1).lower()
            currency = _SYMBOL_BY_CODE.get(c, c.upper() + " ")
    values = []
    for m in _NUMBER_RE.finditer(text):
        # Skip numbers that are not money: '50% upfront', '3 months', '10 pages'.
        if _NOT_MONEY_RE.match(text, m.end()):
            continue
        number = float(m.group(0).replace(",", ""))
        if text[m.end() : m.end() + 1].lower() == "k":
            number *= 1000
        values.append(number)
    if not values:
        return 0.0, 0.0, currency
    low, high = min(values[:2]), max(values[:2])
    if cap:
        low, high = min(low, MAX_AMOUNT), min(high, MAX_AMOUNT)
    return low, high, currency


def _amount(value) -> float | None:
    """A price cell as a float, or None when it is blank (None or NaN from an empty table cell)."""
    return None if value is None or math.isnan(float(value)) else float(value)


def clean_amounts(low, high) -> tuple[float, float]:
    """Make an editable price row safe: blank cells become 0 or copy the other end, and the
    numbers are kept between 0 and MAX_AMOUNT (no negative, infinite or absurd prices)."""
    low, high = _amount(low), _amount(high)
    if low is None and high is None:
        return 0.0, 0.0
    low = high if low is None else low
    high = low if high is None else max(high, low)
    return clamp(low, 0.0, MAX_AMOUNT), clamp(high, 0.0, MAX_AMOUNT)


def price_range_text(low, high, currency: str) -> str:
    """'$4,000' for a fixed price, '$3,000 – $5,000' for a range."""
    low, high = clean_amounts(low, high)
    if round(low) == round(high):
        return money(low, currency)
    return f"{money(low, currency)} – {money(high, currency)}"


def parse_weeks(text: str, default: int = 6, cap: bool = True) -> int:
    """'8 weeks' -> 8, '2 months' -> 9, '30 days' -> 5. Falls back to a default."""
    m = re.search(r"(\d+(?:\.\d+)?)\s*(day|week|wk|month|mo)", str(text or ""), re.I)
    if not m:
        return default
    n, unit = float(m.group(1)), m.group(2).lower()
    if unit.startswith("day"):
        weeks = math.ceil(n / 7)
    elif unit.startswith(("week", "wk")):
        weeks = math.ceil(n)
    else:
        weeks = math.ceil(n * 4.3)
    return max(1, min(weeks, MAX_WEEKS) if cap else weeks)


def money(value: float, currency: str = "$") -> str:
    return f"{currency}{value:,.0f}"


# ---------------------------------------------------------------- building


def project_kind(project_type: str) -> str:
    text = str(project_type or "").lower()
    for kind, pattern in KIND_PATTERNS:
        if re.search(pattern, text):
            return kind
    return "general"


def _allocate_weeks(total: int, weights: list[float]) -> list[int]:
    """Share `total` weeks across phases by weight, at least one week each."""
    n = len(weights)
    spare = total - n
    raw = [w * spare for w in weights]
    whole = [int(x) for x in raw]
    leftover = spare - sum(whole)
    for i in sorted(range(n), key=lambda i: raw[i] - whole[i], reverse=True)[:leftover]:
        whole[i] += 1
    return [1 + w for w in whole]


def build_milestones(kind: str, weeks: int) -> tuple[list[dict], list[float]]:
    phases = list(PHASES[kind])
    if weeks < len(phases):
        keep = max(weeks - 1, 0)
        tail = phases[keep:]
        phases = phases[:keep] + [
            ("Build & Delivery", sum(p[1] for p in tail), "Build, review and hand over the finished work.")
        ]
    lengths = _allocate_weeks(weeks, [p[1] for p in phases])
    milestones, cursor = [], 1
    for (name, _, description), length in zip(phases, lengths, strict=True):
        milestones.append({"phase": name, "start": cursor, "end": cursor + length - 1, "description": description})
        cursor += length
    return milestones, [p[1] for p in phases]


def build_price_items(milestones: list[dict], weights: list[float], low: float, high: float) -> list[dict]:
    """Split the budget across phases. The last phase absorbs rounding."""
    if high <= 0:
        return []
    step = 10 if high >= 1000 else 1
    items, used_low, used_high = [], 0.0, 0.0
    for i, (m, w) in enumerate(zip(milestones, weights, strict=True)):
        last = i == len(milestones) - 1
        lo = low - used_low if last else round(low * w / step) * step
        hi = high - used_high if last else round(high * w / step) * step
        used_low, used_high = used_low + lo, used_high + hi
        items.append({"item": m["phase"], "low": lo, "high": hi})
    return items


def _lower_first(text: str) -> str:
    """Lowercase the first letter to fit mid-sentence, unless it looks like a name or acronym
    ('SEO audit', 'Google Ads setup')."""
    has_proper_noun = any(w[:1].isupper() for w in text.split()[1:])
    if not text or text[:2].isupper() or has_proper_noun:
        return text
    return text[:1].lower() + text[1:]


def _lower_words(text: str) -> str:
    """'Website Redesign' -> 'website redesign', but keep 'iOS' and 'SEO' as typed."""
    return " ".join(w.lower() if w.istitle() else w for w in text.split())


def pricing_totals(p: dict) -> tuple[float, float]:
    amounts = [clean_amounts(i.get("low"), i.get("high")) for i in p["price_items"]]
    return sum(a[0] for a in amounts), sum(a[1] for a in amounts)


def price_text(p: dict) -> str:
    low, high = pricing_totals(p)
    return price_range_text(low, high, p["currency"]) if high > 0 else "To be confirmed"


def build_proposal(inputs: dict, today: date | None = None) -> dict:
    today = today or date.today()
    client = clean_text(inputs.get("client_name"), MAX_NAME_CHARS) or "Your Client"
    ptype = clean_text(inputs.get("project_type"), MAX_NAME_CHARS) or "Project"
    by = clean_text(inputs.get("prepared_by"), MAX_NAME_CHARS) or "Our team"
    goals = to_list(inputs.get("goals"))
    deliverables = to_list(inputs.get("deliverables"), split_commas=True)
    notes = to_list(inputs.get("notes"))

    kind = project_kind(ptype)
    weeks = parse_weeks(str(inputs.get("timeline") or ""))
    low, high, currency = parse_money(str(inputs.get("pricing") or ""))
    milestones, weights = build_milestones(kind, weeks)

    p = {
        "client": client,
        "project_type": ptype,
        "title": f"{ptype} Proposal",
        "prepared_by": by,
        "prepared_on": today.strftime("%d %B %Y").lstrip("0"),
        "valid_until": (today + timedelta(days=30)).strftime("%d %B %Y").lstrip("0"),
        "goals": goals,
        "deliverables": deliverables,
        "scope_in": deliverables + list(STANDARD_INCLUSIONS),
        "scope_out": list(EXCLUSIONS[kind]),
        "assumptions": list(ASSUMPTIONS),
        "milestones": milestones,
        "currency": currency,
        "price_items": build_price_items(milestones, weights, low, high),
        "payment_terms": list(PAYMENT_TERMS) if high > 0 else [],
        "notes": notes,
        "next_steps": list(NEXT_STEPS),
        "quote": pick_quote(kind, f"{client}|{ptype}"),
    }
    p["summary"] = _summary(p, weeks)
    return p


def _summary(p: dict, weeks: int) -> str:
    """Two or three plain sentences. The goals, price and dates are shown elsewhere on the page,
    so the summary does not repeat them."""
    plural = "s" if weeks != 1 else ""
    parts = [
        f"{p['prepared_by']} will deliver the {_lower_words(p['project_type'])} for {p['client']} in {weeks} week{plural}."
    ]
    phases, count = p["milestones"], len(p["deliverables"])
    covers = f"covers {count} deliverable{'s' if count != 1 else ''}" if count else ""
    if len(phases) > 1:
        runs = f"The work runs in {len(phases)} phases, from {phases[0]['phase']} to {phases[-1]['phase']}"
        parts.append(f"{runs}, and {covers}." if covers else f"{runs}.")
    elif covers:
        parts.append(f"The work {covers}.")
    parts.append(
        "This document sets out the scope, timeline and pricing so both sides agree on the work before it starts."
    )
    return " ".join(parts)


def load_samples(directory: Path = SAMPLES_DIR) -> dict[str, dict]:
    samples = {}
    for path in sorted(directory.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        samples[data.pop("sample_name", path.stem)] = data
    return samples
