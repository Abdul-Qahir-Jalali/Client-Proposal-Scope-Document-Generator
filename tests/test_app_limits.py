"""The app itself refuses oversized input and rapid repeat clicks."""

from pathlib import Path

import pandas as pd

from proposal import limits


def _app():
    from streamlit.testing.v1 import AppTest

    return AppTest.from_file(str(Path(__file__).resolve().parent.parent / "app.py"), default_timeout=60).run()


def _click(at, label):
    [b for b in at.button if b.label == label][0].click().run()


def test_second_generate_click_inside_the_wait_is_refused(monkeypatch):
    monkeypatch.setattr(limits.generate_limiter, "min_seconds", 60.0)
    at = _app()
    at.text_input(key="in_client").set_value("First Co").run()
    _click(at, "Generate proposal")
    assert at.text_input(key="e_client").value == "First Co"
    at.text_input(key="in_client").set_value("Second Co").run()
    _click(at, "Generate proposal")
    assert at.text_input(key="e_client").value == "First Co"  # not regenerated
    assert any("Please wait" in w.value for w in at.sidebar.warning)


def test_overlong_free_form_text_is_refused():
    at = _app()
    at.radio(key="in_mode").set_value("Free-form paste").run()
    at.text_area(key="in_ff").set_value("Client: Acme\n" + "x" * limits.MAX_FREEFORM_CHARS).run()
    _click(at, "Generate proposal")
    assert not at.exception and not at.session_state.has_proposal
    assert any("too long" in w.value for w in at.sidebar.warning)


def test_client_name_box_cuts_text_at_the_limit():
    """First layer: the text box itself stops at the limit, so a pasted 10,000-character name is cut."""
    at = _app()
    at.text_input(key="in_client").set_value("A" * (limits.MAX_NAME_CHARS + 50)).run()
    assert len(at.text_input(key="in_client").value) == limits.MAX_NAME_CHARS
    _click(at, "Generate proposal")
    assert not at.exception and len(at.text_input(key="e_client").value) == limits.MAX_NAME_CHARS


def test_huge_timeline_generates_with_a_notice():
    at = _app()
    at.text_input(key="in_client").set_value("Acme").run()
    at.text_input(key="in_timeline").set_value("999999 weeks").run()
    _click(at, "Generate proposal")
    assert not at.exception and at.session_state.has_proposal
    assert max(at.session_state.ms_init["end"]) <= limits.MAX_WEEKS
    assert any("week maximum" in w.value for w in at.sidebar.warning)


def test_collect_cleans_hostile_table_values():
    """Values typed straight into the editable tables are cleaned before preview and export."""
    import sys
    import types

    app_source = (Path(__file__).resolve().parent.parent / "app.py").read_text(encoding="utf-8")
    start = app_source.index("def _week(")
    end = app_source.index("# ------------------------------------------------------------------- startup")
    import streamlit as st

    from proposal import generator as gen

    module = types.ModuleType("collect_under_test")
    module.__dict__.update({"pd": pd, "st": st, "gen": gen, "limits": limits, "LIST_AREAS": {}})
    exec(compile(app_source[start:end], "app.py", "exec"), module.__dict__)  # noqa: S102 - our own file
    sys.modules.pop("collect_under_test", None)

    st.session_state.update(
        {
            "e_client": "Acme\x00",
            "in_type": "Web",
            "e_title": "T" * 500,
            "e_by": "",
            "e_date": "1 Jan",
            "e_valid": "1 Feb",
            "e_summary": "S",
            "e_deliv": "",
            "currency": "$",
        }
    )
    ms = pd.DataFrame({"phase": ["Build"] * 50, "start": [-5] * 50, "end": [10**9] * 50, "description": ["d"] * 50})
    prices = pd.DataFrame({"item": ["Work"] * 60, "low": [float("nan")] * 60, "high": [10**15] * 60})
    p = module.collect(ms, prices)
    assert p["client"] == "Acme" and len(p["title"]) == limits.MAX_NAME_CHARS
    assert len(p["milestones"]) == limits.MAX_MILESTONES
    assert p["milestones"][0]["start"] == 1 and p["milestones"][0]["end"] == limits.MAX_WEEKS
    assert len(p["price_items"]) == limits.MAX_PRICE_ITEMS
    assert p["price_items"][0]["high"] == limits.MAX_AMOUNT
