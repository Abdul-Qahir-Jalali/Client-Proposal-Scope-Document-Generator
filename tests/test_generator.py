from datetime import date
from io import BytesIO

import pytest
from docx import Document

from proposal import docx_export, generator as gen, render

SAMPLES = gen.load_samples()
TODAY = date(2026, 1, 5)


def test_three_samples_available():
    assert len(SAMPLES) == 3


@pytest.mark.parametrize("text,expected", [
    ("$4,000", (4000, 4000, "$")),
    ("$3,000 - $5,000", (3000, 5000, "$")),
    ("around $9k", (9000, 9000, "$")),
    ("£2.5k to £3.5k", (2500, 3500, "£")),
    ("1500 EUR", (1500, 1500, "€")),
    ("TBD", (0, 0, "$")),
])
def test_parse_money(text, expected):
    assert gen.parse_money(text) == expected


@pytest.mark.parametrize("text,weeks", [
    ("8 weeks", 8), ("3 months", 13), ("30 days", 5), ("soon", 6), ("1 week", 1),
])
def test_parse_weeks(text, weeks):
    assert gen.parse_weeks(text) == weeks


def test_freeform_round_trip():
    for inputs in SAMPLES.values():
        parsed = gen.parse_freeform(gen.to_freeform(inputs))
        assert parsed["client_name"] == inputs["client_name"]
        assert gen.to_list(parsed["goals"]) == gen.to_list(inputs["goals"])
        assert gen.to_list(parsed["deliverables"], True) == gen.to_list(inputs["deliverables"], True)
        assert parsed["timeline"] == inputs["timeline"]


def test_freeform_messy_input():
    parsed = gen.parse_freeform("client: Acme Co\nBudget: 5k\nGoals: more leads; better brand\nDuration: 4 weeks")
    assert parsed["client_name"] == "Acme Co"
    assert gen.to_list(parsed["goals"]) == ["more leads", "better brand"]


@pytest.mark.parametrize("weeks", [1, 2, 3, 4, 8, 14, 26])
def test_milestones_cover_every_week_without_gaps(weeks):
    for kind in gen.PHASES:
        milestones, weights = gen.build_milestones(kind, weeks)
        assert milestones[0]["start"] == 1
        assert milestones[-1]["end"] == weeks
        for a, b in zip(milestones, milestones[1:]):
            assert b["start"] == a["end"] + 1
        assert len(weights) == len(milestones)


@pytest.mark.parametrize("name", list(SAMPLES))
def test_price_items_add_up_to_the_quote(name):
    p = gen.build_proposal(SAMPLES[name], TODAY)
    low, high, _ = gen.parse_money(SAMPLES[name]["pricing"])
    assert gen.pricing_totals(p) == (low, high)


def test_no_price_gives_no_price_items():
    p = gen.build_proposal({"client_name": "X", "project_type": "Website"}, TODAY)
    assert p["price_items"] == [] and p["payment_terms"] == []
    assert gen.price_text(p) == "To be confirmed"


@pytest.mark.parametrize("project_type,kind", [
    ("Website Redesign", "web"), ("Mobile App Development", "app"),
    ("Marketing Campaign", "marketing"), ("Brand identity", "brand"), ("Consulting", "general"),
])
def test_project_kind(project_type, kind):
    assert gen.project_kind(project_type) == kind


def test_html_contains_all_sections():
    p = gen.build_proposal(SAMPLES[next(iter(SAMPLES))], TODAY)
    html = render.render_html(p)
    for text in ("Executive summary", "Scope of work", "Timeline", "Investment", "Next steps", "Bright Dental Clinic"):
        assert text in html
    assert 'contenteditable="true" spellcheck' not in html and 'id="toolbar"' not in html


def test_editable_html_has_toolbar():
    html = render.render_html(gen.build_proposal({"client_name": "A"}, TODAY), editable=True)
    assert 'contenteditable="true" spellcheck' in html and "btn-download" in html


def test_user_text_is_escaped():
    p = gen.build_proposal({"client_name": "<script>alert(1)</script>", "goals": "<img src=x onerror=1>"}, TODAY)
    html = render.render_html(p)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html and "<img src=x" not in html


def test_summary_reads_naturally():
    p = gen.build_proposal(SAMPLES[next(iter(SAMPLES))], TODAY)
    assert "a website redesign for Bright Dental Clinic over 8 weeks" in p["summary"]
    assert "$6,500 – $8,000" in p["summary"]


def test_docx_opens_and_has_content():
    p = gen.build_proposal(SAMPLES[next(iter(SAMPLES))], TODAY)
    doc = Document(BytesIO(docx_export.build_docx(p)))
    text = "\n".join(par.text for par in doc.paragraphs)
    assert "Bright Dental Clinic" in text and "Executive summary" in text
    assert len(doc.tables) == 2
