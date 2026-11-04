"""Client Proposal & Scope Document Generator.

Run with:  python -m streamlit run app.py
"""

from __future__ import annotations

import uuid

import pandas as pd
import streamlit as st

from proposal import docx_export, limits, pdf_export, render
from proposal import generator as gen
from proposal.monitoring import configure_logging, log_event, report_error, timed

st.set_page_config(page_title="Proposal Generator", page_icon="📄", layout="wide")
configure_logging()  # safe on every rerun: it only sets up logging the first time


@st.cache_data
def _load_samples() -> dict[str, dict]:
    return gen.load_samples()


SAMPLES = _load_samples()
FORM, FREE = "Form", "Free-form paste"

# Content widgets that hold one list item per line: widget key -> proposal key
LIST_AREAS = {
    "e_goals": "goals",
    "e_scope_in": "scope_in",
    "e_scope_out": "scope_out",
    "e_assumptions": "assumptions",
    "e_payment": "payment_terms",
    "e_notes": "notes",
    "e_steps": "next_steps",
}


INPUT_KEYS = ("in_client", "in_type", "in_goals", "in_deliv", "in_timeline", "in_pricing", "in_notes", "in_ff")


def _lines(items: list[str]) -> str:
    return "\n".join(items)


# ------------------------------------------------------------- state changes


def fill_inputs(inputs: dict) -> None:
    ss = st.session_state
    ss.in_client = inputs.get("client_name", "")
    ss.in_type = inputs.get("project_type", "")
    ss.in_prepared = inputs.get("prepared_by", ss.get("in_prepared", "Allure Digital"))
    ss.in_goals = inputs.get("goals", "")
    ss.in_deliv = inputs.get("deliverables", "")
    ss.in_timeline = inputs.get("timeline", "")
    ss.in_pricing = inputs.get("pricing", "")
    ss.in_notes = inputs.get("notes", "")
    ss.in_ff = gen.to_freeform(inputs)


def load_proposal(p: dict) -> None:
    """Copy a freshly generated proposal into the live editing widgets."""
    ss = st.session_state
    ss.ver = ss.get("ver", 0) + 1
    ss.pop("pdf", None)  # a PDF made from the previous proposal must not be offered again
    ss.currency = p["currency"]
    ss.e_title, ss.e_client, ss.e_by = p["title"], p["client"], p["prepared_by"]
    ss.e_date, ss.e_valid = p["prepared_on"], p["valid_until"]
    ss.e_summary = p["summary"]
    ss.quote = p.get("quote")  # the chosen quote; the checkbox in the Edit tab shows or hides it
    ss.e_quote_on = bool(p.get("quote"))
    ss.e_deliv = _lines(p["deliverables"])
    for key, field in LIST_AREAS.items():
        ss[key] = _lines(p[field])
    ss.ms_init = pd.DataFrame(p["milestones"])[["phase", "start", "end", "description"]]
    ss.price_init = pd.DataFrame(p["price_items"], columns=["item", "low", "high"])


def generate() -> None:
    ss = st.session_state
    ss.pop("notice", None)
    wait = limits.generate_limiter.hit(ss.sid)
    if wait:
        log_event("rate_limited", action="generate")
        ss.notice = f"Please wait {wait:.0f} second(s) before generating again."
        return
    if ss.in_mode == FREE:
        if len(ss.in_ff) > limits.MAX_FREEFORM_CHARS:
            ss.notice = f"The pasted text is too long. The limit is {limits.MAX_FREEFORM_CHARS:,} characters."
            return
        inputs = gen.parse_freeform(ss.in_ff)
        inputs["prepared_by"] = ss.in_prepared
    else:
        inputs = {
            "client_name": ss.in_client,
            "project_type": ss.in_type,
            "goals": ss.in_goals,
            "deliverables": ss.in_deliv,
            "timeline": ss.in_timeline,
            "pricing": ss.in_pricing,
            "notes": ss.in_notes,
            "prepared_by": ss.in_prepared,
        }
    check = limits.validate_inputs(inputs)
    if not check.ok:
        log_event("generate_rejected", mode=ss.in_mode, problems=len(check.errors))
        if ss.in_mode == FREE and not inputs["client_name"].strip():
            ss.notice = "No client name found. Start a line with 'Client:' so the generator can find it."
        else:
            ss.notice = " ".join(check.errors)
        return
    try:
        with timed("generate", mode=ss.in_mode) as info:
            proposal = gen.build_proposal(inputs)
            fill_inputs(inputs)  # keeps the form and the free-form text in step with each other
            load_proposal(proposal)
            info.update(
                weeks=max(m["end"] for m in proposal["milestones"]),
                price_items=len(proposal["price_items"]),
                warnings=len(check.warnings),
            )
    except Exception as exc:  # last line of defence: calm message for the user, details in the log
        error_id = report_error(exc, "generate")
        ss.notice = f"Something went wrong while generating. Please try again. (error id {error_id})"
        return
    if check.warnings:
        ss.notice = " ".join(check.warnings)
    ss.has_proposal = True


def load_sample() -> None:
    fill_inputs(SAMPLES[st.session_state.sample_choice])
    generate()


def _week(value, default: int) -> int:
    """A milestone week as a whole number from 1 to MAX_WEEKS (blank, NaN and huge values are handled)."""
    if value is None or pd.isna(value):
        return default
    return int(limits.clamp(float(value), 1, limits.MAX_WEEKS))


def collect(ms_df: pd.DataFrame, price_df: pd.DataFrame) -> dict:
    """Build the current proposal from whatever is in the editing widgets.

    Everything is cleaned here (control characters removed, lengths and row counts limited), so
    the preview and all three exports only ever see safe values.
    """
    ss = st.session_state
    name = limits.MAX_NAME_CHARS
    p = {
        "client": limits.clean_text(ss.e_client, name) or "Your Client",
        "project_type": limits.clean_text(ss.in_type, name),
        "title": limits.clean_text(ss.e_title, name) or "Proposal",
        "prepared_by": limits.clean_text(ss.e_by, name) or "Our team",
        "prepared_on": limits.clean_text(ss.e_date, 40),
        "valid_until": limits.clean_text(ss.e_valid, 40),
        "summary": limits.clean_text(ss.e_summary, limits.MAX_EDIT_CHARS),
        "deliverables": gen.to_list(ss.e_deliv),
        "currency": ss.currency,
        "quote": ss.get("quote") if ss.get("e_quote_on") else None,
    }
    for key, field in LIST_AREAS.items():
        p[field] = gen.to_list(ss[key])
    p["milestones"] = []
    for row in ms_df.dropna(subset=["phase"]).itertuples():
        phase = limits.clean_text(row.phase, limits.MAX_ITEM_CHARS)
        if not phase or len(p["milestones"]) >= limits.MAX_MILESTONES:
            continue
        start = _week(row.start, 1)
        end = max(start, _week(row.end, start))
        description = (
            limits.clean_text(row.description, limits.MAX_ITEM_CHARS) if isinstance(row.description, str) else ""
        )
        p["milestones"].append({"phase": phase, "start": start, "end": end, "description": description})
    p["price_items"] = []
    for r in price_df.dropna(subset=["item"]).itertuples():
        item = limits.clean_text(r.item, limits.MAX_ITEM_CHARS)
        if item and len(p["price_items"]) < limits.MAX_PRICE_ITEMS:
            low, high = gen.clean_amounts(r.low, r.high)
            p["price_items"].append({"item": item, "low": low, "high": high})
    return p


# ------------------------------------------------------------------- startup

if "has_proposal" not in st.session_state:
    # Start empty: nothing is generated until the user enters details or loads a sample.
    st.session_state.has_proposal = False
    st.session_state.sid = uuid.uuid4().hex  # random id for rate limiting; not linked to the person
    st.session_state.in_mode = FORM
    st.session_state.in_prepared = "Allure Digital"
    st.session_state.sample_choice = next(iter(SAMPLES))
    for _key in INPUT_KEYS:
        st.session_state[_key] = ""

# ------------------------------------------------------------------- sidebar

with st.sidebar:
    st.header("Project details")
    st.selectbox("Sample project", list(SAMPLES), key="sample_choice")
    st.button("Load sample", on_click=load_sample, width="stretch")
    st.divider()
    st.radio("Input style", [FORM, FREE], key="in_mode", horizontal=True)
    st.text_input("Prepared by (your company)", key="in_prepared", max_chars=limits.MAX_NAME_CHARS)
    # Both groups are drawn on every run, even when collapsed. Streamlit deletes the state of any
    # widget that is not drawn, which would wipe the form when switching to free-form text.
    with st.expander("Form fields", expanded=st.session_state.in_mode == FORM):
        st.text_input("Client name", key="in_client", max_chars=limits.MAX_NAME_CHARS)
        st.text_input(
            "Project type",
            key="in_type",
            max_chars=limits.MAX_NAME_CHARS,
            help="For example: website, mobile app, marketing campaign, branding",
        )
        st.text_area("Goals (one per line)", key="in_goals", height=100, max_chars=limits.MAX_TEXT_CHARS)
        st.text_area("Key deliverables (one per line)", key="in_deliv", height=130, max_chars=limits.MAX_TEXT_CHARS)
        st.text_input(
            "Timeline",
            key="in_timeline",
            max_chars=limits.MAX_SHORT_CHARS,
            help="For example: 8 weeks, 3 months, 30 days",
        )
        st.text_input(
            "Pricing or range",
            key="in_pricing",
            max_chars=limits.MAX_SHORT_CHARS,
            help="For example: $4,000 or $3k - $5k",
        )
        st.text_area("Special notes (one per line)", key="in_notes", height=90, max_chars=limits.MAX_TEXT_CHARS)
    with st.expander("Free-form text", expanded=st.session_state.in_mode == FREE):
        st.text_area(
            "Paste project details",
            key="in_ff",
            height=420,
            max_chars=limits.MAX_FREEFORM_CHARS,
            help="Use lines like 'Client: ...', 'Goals: ...', 'Timeline: ...'. Bullet lines under a label belong to it.",
        )
    st.button("Generate proposal", type="primary", on_click=generate, width="stretch")
    if st.session_state.get("notice"):
        st.warning(st.session_state.notice)
    st.caption("Generating again replaces your edits with a fresh draft.")

# --------------------------------------------------------------------- main

st.title("Client Proposal & Scope Document Generator")

if not st.session_state.has_proposal:
    with st.container(border=True):
        st.markdown(
            "#### Start a proposal\n"
            "1. Enter the client and project details in the sidebar, then press **Generate proposal**.\n"
            "2. Or pick a sample project in the sidebar and press **Load sample**.\n\n"
            "Your proposal appears here, and you can edit it live before exporting."
        )
    st.stop()

st.caption("Edit any field on the left. The proposal on the right updates as you type.")

left, right = st.columns([5, 7], gap="large")

with left:
    tab_edit, tab_time, tab_export = st.tabs(["Edit content", "Timeline & pricing", "Export"])

    with tab_edit:
        c1, c2 = st.columns(2)
        c1.text_input("Document title", key="e_title", max_chars=limits.MAX_NAME_CHARS)
        c2.text_input("Client", key="e_client", max_chars=limits.MAX_NAME_CHARS)
        c1.text_input("Prepared by", key="e_by", max_chars=limits.MAX_NAME_CHARS)
        if st.session_state.get("quote"):
            q = st.session_state.quote
            st.checkbox(f"Show a quote at the start ({q['author']})", key="e_quote_on")
        c2.text_input("Date", key="e_date", max_chars=40)
        st.text_area("Executive summary", key="e_summary", height=190, max_chars=limits.MAX_EDIT_CHARS)
        st.text_area("Goals (one per line)", key="e_goals", height=100, max_chars=limits.MAX_EDIT_CHARS)
        st.text_area("Key deliverables (one per line)", key="e_deliv", height=130, max_chars=limits.MAX_EDIT_CHARS)
        st.text_area("Scope: included", key="e_scope_in", height=150, max_chars=limits.MAX_EDIT_CHARS)
        st.text_area("Scope: not included", key="e_scope_out", height=130, max_chars=limits.MAX_EDIT_CHARS)
        st.text_area("Assumptions", key="e_assumptions", height=120, max_chars=limits.MAX_EDIT_CHARS)
        st.text_area("Special considerations", key="e_notes", height=90, max_chars=limits.MAX_EDIT_CHARS)
        st.text_area("Next steps", key="e_steps", height=110, max_chars=limits.MAX_EDIT_CHARS)

    with tab_time:
        ver = st.session_state.ver
        st.markdown("**Milestones.** Add, remove or change rows. Weeks start at 1.")
        ms_df = st.data_editor(
            st.session_state.ms_init,
            key=f"ms_{ver}",
            num_rows="dynamic",
            hide_index=True,
            width="stretch",
            column_config={
                "phase": st.column_config.TextColumn("Phase", required=True),
                "start": st.column_config.NumberColumn(
                    "Start week", min_value=1, max_value=limits.MAX_WEEKS, step=1, format="%d"
                ),
                "end": st.column_config.NumberColumn(
                    "End week", min_value=1, max_value=limits.MAX_WEEKS, step=1, format="%d"
                ),
                "description": st.column_config.TextColumn("What happens", width="large"),
            },
        )
        st.markdown(f"**Pricing** ({st.session_state.currency}). Set low and high the same for a fixed price.")
        price_df = st.data_editor(
            st.session_state.price_init,
            key=f"price_{ver}",
            num_rows="dynamic",
            hide_index=True,
            width="stretch",
            column_config={
                "item": st.column_config.TextColumn("Line item", required=True),
                "low": st.column_config.NumberColumn(
                    "Low", min_value=0, max_value=limits.MAX_AMOUNT, step=10, format="%.0f"
                ),
                "high": st.column_config.NumberColumn(
                    "High", min_value=0, max_value=limits.MAX_AMOUNT, step=10, format="%.0f"
                ),
            },
        )
        st.text_area("Payment terms (one per line)", key="e_payment", height=110, max_chars=limits.MAX_EDIT_CHARS)

proposal = collect(ms_df, price_df)

with left, tab_export:
    stem = render.filename_stem(proposal)
    st.markdown("Download the finished proposal.")

    def _html_file() -> str:
        log_event("export", format="html")
        return render.render_html(proposal)

    def _word_file() -> bytes:
        log_event("export", format="docx")
        return docx_export.build_docx(proposal)

    # Callables: the file is built only when the button is clicked, not on every keystroke.
    st.download_button(
        "Download HTML presentation",
        _html_file,
        f"{stem}.html",
        "text/html",
        width="stretch",
        type="primary",
        on_click="ignore",
    )
    st.download_button(
        "Download Word document (.docx)",
        _word_file,
        f"{stem}.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        width="stretch",
        on_click="ignore",
    )
    export_html = render.render_html(proposal)
    if st.button("Create PDF", width="stretch", help="Uses Chrome or Edge on this computer. Takes a few seconds."):
        pdf = st.session_state.get("pdf")
        if pdf is None or pdf[0] != export_html:  # skip the browser run when nothing changed
            wait = limits.pdf_limiter.hit(st.session_state.sid)
            if wait:
                log_event("rate_limited", action="pdf")
                st.warning(f"Please wait {wait:.0f} second(s) before creating another PDF.")
            else:
                try:
                    with st.spinner("Creating PDF..."):
                        st.session_state.pdf = (export_html, pdf_export.html_to_pdf(export_html))
                except pdf_export.PdfUnavailable as exc:
                    st.session_state.pop("pdf", None)
                    st.error(str(exc))
                except Exception as exc:
                    st.session_state.pop("pdf", None)
                    st.error(f"The PDF could not be created. (error id {report_error(exc, 'pdf')})")
    if "pdf" in st.session_state:
        made_from, pdf_bytes = st.session_state.pdf
        st.download_button(
            "Download PDF",
            pdf_bytes,
            f"{stem}.pdf",
            "application/pdf",
            width="stretch",
            type="primary",
            on_click="ignore",
        )
        if made_from != export_html:
            st.caption("You have edited the proposal since this PDF was made. Press Create PDF again to update it.")
    st.caption(
        "You can also click directly on text in the preview and edit it there. "
        "Use the preview's own Download HTML button to keep those edits."
    )

with right:
    # Safe to embed: render_html escapes every piece of user text (see tests/test_generator.py).
    st.iframe(render.render_html(proposal, editable=True), height=900)
