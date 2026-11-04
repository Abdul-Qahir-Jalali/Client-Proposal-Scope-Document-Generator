"""The opening quote: real, sourced, relevant to the project type, stable, and switchable."""

from datetime import date
from io import BytesIO
from pathlib import Path

import pytest
from docx import Document

from proposal import docx_export, quotes, render
from proposal import generator as gen

TODAY = date(2026, 1, 5)
SAMPLES = gen.load_samples()
FIRST = SAMPLES[next(iter(SAMPLES))]


@pytest.mark.parametrize("kind", list(gen.PHASES))
def test_every_project_kind_has_a_named_and_sourced_quote(kind):
    options = quotes.QUOTES[kind]
    assert options
    for q in options:
        assert q["text"].strip() and q["author"].strip() and q["role"].strip()
        assert len(q["text"]) < 200  # short enough to read as a pull-quote
        assert "\n" not in q["text"]


def test_no_quote_is_listed_twice_for_the_same_kind():
    for options in quotes.QUOTES.values():
        texts = [q["text"] for q in options]
        assert len(texts) == len(set(texts))


def test_pick_is_stable_for_one_proposal_and_can_differ_between_clients():
    first = quotes.pick_quote("web", "Acme|Website")
    assert quotes.pick_quote("web", "Acme|Website") == first
    picks = {quotes.pick_quote("web", f"Client {i}|Website")["author"] for i in range(40)}
    assert len(picks) == len(quotes.QUOTES["web"])  # both web quotes get used across many clients


def test_unknown_kind_falls_back_to_the_general_quotes():
    assert quotes.pick_quote("nonsense", "x")["text"] in {q["text"] for q in quotes.QUOTES["general"]}


@pytest.mark.parametrize(
    "project_type,kind",
    [
        ("Website Redesign", "web"),
        ("Mobile App", "app"),
        ("Marketing Campaign", "marketing"),
        ("Brand Identity", "brand"),
    ],
)
def test_the_quote_matches_the_project_type(project_type, kind):
    p = gen.build_proposal({**FIRST, "project_type": project_type}, TODAY)
    assert p["quote"]["text"] in {q["text"] for q in quotes.QUOTES[kind]}


def test_quote_is_shown_with_the_person_and_the_source_right_after_the_cover():
    p = gen.build_proposal(FIRST, TODAY)
    html = render.render_html(p)
    q = p["quote"]
    assert q["text"] in html and q["author"] in html and q["role"] in html
    assert html.index('class="quote"') < html.index("Executive summary")
    assert html.index('class="hero') < html.index('class="quote"')


def test_quote_can_be_switched_off():
    p = gen.build_proposal(FIRST, TODAY)
    html = render.render_html({**p, "quote": None})
    assert 'class="quote"' not in html.split("</style>")[1]


def test_quote_text_is_escaped():
    p = gen.build_proposal(FIRST, TODAY)
    p["quote"] = {"text": "<script>alert(1)</script>", "author": "A <b>", "role": "R", "source": ""}
    html = render.render_html(p)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_word_export_carries_the_quote():
    p = gen.build_proposal(FIRST, TODAY)
    text = "\n".join(par.text for par in Document(BytesIO(docx_export.build_docx(p))).paragraphs)
    assert p["quote"]["text"] in text and p["quote"]["author"] in text


def test_word_export_without_a_quote_still_works():
    p = {**gen.build_proposal(FIRST, TODAY), "quote": None}
    assert Document(BytesIO(docx_export.build_docx(p))).paragraphs


def test_app_offers_a_switch_for_the_quote():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(Path(__file__).resolve().parent.parent / "app.py"), default_timeout=60).run()
    [b for b in at.button if b.label == "Load sample"][0].click().run()
    assert not at.exception
    box = at.checkbox(key="e_quote_on")
    assert box.value is True
    assert "Show a quote at the start" in box.label
    box.uncheck().run()
    assert not at.exception
