import re
from datetime import date
from io import BytesIO
from pathlib import Path

import pytest
from docx import Document

from proposal import docx_export, generator as gen, pdf_export, render

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


@pytest.mark.parametrize("text,expected", [
    ("$6,500 (50% upfront)", (6500, 6500)),
    ("$4,000 per month for 3 months", (4000, 4000)),
    ("$3,000 - $5,000 over 8 weeks", (3000, 5000)),
])
def test_parse_money_ignores_non_money_numbers(text, expected):
    assert gen.parse_money(text)[:2] == expected


@pytest.mark.parametrize("low,high,expected", [
    (float("nan"), float("nan"), (0, 0)),
    (500, float("nan"), (500, 500)),
    (float("nan"), 700, (700, 700)),
    (900, 400, (900, 900)),
    (None, None, (0, 0)),
])
def test_clean_amounts(low, high, expected):
    assert gen.clean_amounts(low, high) == expected


def test_totals_and_render_survive_blank_price_cells():
    p = gen.build_proposal(SAMPLES[next(iter(SAMPLES))], TODAY)
    p["price_items"].append({"item": "Extra", "low": float("nan"), "high": float("nan")})
    assert gen.pricing_totals(p)[1] > 0
    assert "Extra" in render.render_html(p)
    assert Document(BytesIO(docx_export.build_docx(p)))


def test_price_range_text():
    assert gen.price_range_text(4000, 4000, "$") == "$4,000"
    assert gen.price_range_text(3000, 5000, "£") == "£3,000 – £5,000"


def test_summary_keeps_proper_nouns():
    assert gen._lower_first("Google Ads setup") == "Google Ads setup"
    assert gen._lower_first("SEO audit") == "SEO audit"
    assert gen._lower_first("Increase online bookings") == "increase online bookings"


def _app():
    from streamlit.testing.v1 import AppTest
    return AppTest.from_file(str(Path(__file__).resolve().parent.parent / "app.py"), default_timeout=60).run()


def _click(at, label):
    [b for b in at.button if b.label == label][0].click().run()


def test_app_starts_empty():
    at = _app()
    assert not at.exception
    assert at.text_input(key="in_client").value == "" and at.text_area(key="in_goals").value == ""
    assert not at.session_state.has_proposal
    assert not at.tabs and "Start a proposal" in "".join(m.value for m in at.markdown)


def test_generate_needs_a_client_name():
    at = _app()
    _click(at, "Generate proposal")
    assert not at.exception and not at.session_state.has_proposal
    assert any("client name" in w.value.lower() for w in at.sidebar.warning)


def test_load_sample_and_manual_entry_show_a_proposal():
    at = _app()
    _click(at, "Load sample")
    assert not at.exception and at.session_state.has_proposal
    assert at.text_input(key="e_client").value == at.text_input(key="in_client").value != ""
    at.text_input(key="in_client").set_value("Manual Co").run()
    _click(at, "Generate proposal")
    assert not at.exception and at.text_input(key="e_client").value == "Manual Co"


def test_app_survives_switching_input_style():
    at = _app()
    _click(at, "Load sample")
    client = at.text_input(key="in_client").value
    at.radio(key="in_mode").set_value("Free-form paste").run()
    at.run()
    assert not at.exception
    at.radio(key="in_mode").set_value("Form").run()
    assert not at.exception and at.text_input(key="in_client").value == client


def test_pdf_reports_missing_browser(monkeypatch):
    monkeypatch.setattr(pdf_export, "find_browser", lambda: None)
    with pytest.raises(pdf_export.PdfUnavailable):
        pdf_export.html_to_pdf("<p>x</p>")


@pytest.mark.skipif(pdf_export.find_browser() is None, reason="needs Chrome or Edge")
def test_pdf_is_created_with_one_page_per_section():
    p = gen.build_proposal(SAMPLES[next(iter(SAMPLES))], TODAY)
    data = pdf_export.html_to_pdf(render.render_html(p))
    assert data.startswith(b"%PDF-")
    assert len(re.findall(rb"/Type\s*/Page[^s]", data)) == 6


def test_no_eyebrow_labels_in_html():
    html = render.render_html(gen.build_proposal(SAMPLES[next(iter(SAMPLES))], TODAY))
    assert 'class="eyebrow"' not in html


def test_docx_opens_and_has_content():
    p = gen.build_proposal(SAMPLES[next(iter(SAMPLES))], TODAY)
    doc = Document(BytesIO(docx_export.build_docx(p)))
    text = "\n".join(par.text for par in doc.paragraphs)
    assert "Bright Dental Clinic" in text and "Executive summary" in text
    assert len(doc.tables) == 2
