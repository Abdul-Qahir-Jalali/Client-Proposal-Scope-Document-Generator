"""Client Proposal & Scope Document Generator.

Run with:  python -m streamlit run app.py
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from proposal import docx_export, generator as gen, render

st.set_page_config(page_title="Proposal Generator", page_icon="📄", layout="wide")

SAMPLES = gen.load_samples()
FORM, FREE = "Form", "Free-form paste"

# Content widgets that hold one list item per line: widget key -> proposal key
LIST_AREAS = {
    "e_goals": "goals", "e_scope_in": "scope_in", "e_scope_out": "scope_out",
    "e_assumptions": "assumptions", "e_payment": "payment_terms",
    "e_notes": "notes", "e_steps": "next_steps",
}


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
    ss.currency = p["currency"]
    ss.e_title, ss.e_client, ss.e_by = p["title"], p["client"], p["prepared_by"]
    ss.e_date, ss.e_valid = p["prepared_on"], p["valid_until"]
    ss.e_summary = p["summary"]
    ss.e_deliv = _lines(p["deliverables"])
    for key, field in LIST_AREAS.items():
        ss[key] = _lines(p[field])
    ss.ms_init = pd.DataFrame(p["milestones"])[["phase", "start", "end", "description"]]
    ss.price_init = pd.DataFrame(p["price_items"], columns=["item", "low", "high"])


def generate() -> None:
    ss = st.session_state
    if ss.in_mode == FREE:
        inputs = gen.parse_freeform(ss.in_ff)
        inputs["prepared_by"] = ss.in_prepared
        fill_inputs(inputs)
    else:
        inputs = {
            "client_name": ss.in_client, "project_type": ss.in_type, "goals": ss.in_goals,
            "deliverables": ss.in_deliv, "timeline": ss.in_timeline, "pricing": ss.in_pricing,
            "notes": ss.in_notes, "prepared_by": ss.in_prepared,
        }
        ss.in_ff = gen.to_freeform(inputs)
    load_proposal(gen.build_proposal(inputs))


def load_sample() -> None:
    fill_inputs(SAMPLES[st.session_state.sample_choice])
    generate()


def collect(ms_df: pd.DataFrame, price_df: pd.DataFrame) -> dict:
    """Build the current proposal from whatever is in the editing widgets."""
    ss = st.session_state
    p = {
        "client": ss.e_client.strip() or "Your Client",
        "project_type": ss.in_type,
        "title": ss.e_title.strip() or "Proposal",
        "prepared_by": ss.e_by.strip() or "Our team",
        "prepared_on": ss.e_date, "valid_until": ss.e_valid,
        "summary": ss.e_summary.strip(),
        "deliverables": gen.to_list(ss.e_deliv),
        "currency": ss.currency,
    }
    for key, field in LIST_AREAS.items():
        p[field] = gen.to_list(ss[key])
    p["milestones"] = []
    for row in ms_df.dropna(subset=["phase"]).itertuples():
        if not str(row.phase).strip():
            continue
        start = max(1, int(row.start)) if pd.notna(row.start) else 1
        end = max(start, int(row.end)) if pd.notna(row.end) else start
        p["milestones"].append({"phase": str(row.phase).strip(), "start": start, "end": end,
                                "description": "" if pd.isna(row.description) else str(row.description)})
    p["price_items"] = [
        {"item": str(r.item), "low": float(r.low or 0), "high": float(max(r.high or 0, r.low or 0))}
        for r in price_df.dropna(subset=["item"]).itertuples() if str(r.item).strip()
    ]
    return p


# ------------------------------------------------------------------- startup

if "ver" not in st.session_state:
    st.session_state.in_mode = FORM
    st.session_state.in_prepared = "Allure Digital"
    st.session_state.sample_choice = next(iter(SAMPLES))
    load_sample()

# ------------------------------------------------------------------- sidebar

with st.sidebar:
    st.header("Project details")
    st.selectbox("Sample project", list(SAMPLES), key="sample_choice")
    st.button("Load sample", on_click=load_sample, width="stretch")
    st.divider()
    st.radio("Input style", [FORM, FREE], key="in_mode", horizontal=True)
    st.text_input("Prepared by (your company)", key="in_prepared")
    if st.session_state.in_mode == FORM:
        st.text_input("Client name", key="in_client")
        st.text_input("Project type", key="in_type", help="For example: website, mobile app, marketing campaign, branding")
        st.text_area("Goals (one per line)", key="in_goals", height=100)
        st.text_area("Key deliverables (one per line)", key="in_deliv", height=130)
        st.text_input("Timeline", key="in_timeline", help="For example: 8 weeks, 3 months, 30 days")
        st.text_input("Pricing or range", key="in_pricing", help="For example: $4,000 or $3k - $5k")
        st.text_area("Special notes (one per line)", key="in_notes", height=90)
    else:
        st.text_area("Paste project details", key="in_ff", height=420,
                     help="Use lines like 'Client: ...', 'Goals: ...', 'Timeline: ...'. Bullet lines under a label belong to it.")
    st.button("Generate proposal", type="primary", on_click=generate, width="stretch")
    st.caption("Generating again replaces your edits with a fresh draft.")

# --------------------------------------------------------------------- main

st.title("Client Proposal & Scope Document Generator")
st.caption("Edit any field on the left. The proposal on the right updates as you type.")

if not st.session_state.in_client.strip() and st.session_state.in_mode == FREE:
    st.warning("No client name found. Start a line with 'Client:' so the generator can find it.")

left, right = st.columns([5, 7], gap="large")

with left:
    tab_edit, tab_time, tab_export = st.tabs(["Edit content", "Timeline & pricing", "Export"])

    with tab_edit:
        c1, c2 = st.columns(2)
        c1.text_input("Document title", key="e_title")
        c2.text_input("Client", key="e_client")
        c1.text_input("Prepared by", key="e_by")
        c2.text_input("Date", key="e_date")
        st.text_area("Executive summary", key="e_summary", height=190)
        st.text_area("Goals (one per line)", key="e_goals", height=100)
        st.text_area("Key deliverables (one per line)", key="e_deliv", height=130)
        st.text_area("Scope: included", key="e_scope_in", height=150)
        st.text_area("Scope: not included", key="e_scope_out", height=130)
        st.text_area("Assumptions", key="e_assumptions", height=120)
        st.text_area("Special considerations", key="e_notes", height=90)
        st.text_area("Next steps", key="e_steps", height=110)

    with tab_time:
        ver = st.session_state.ver
        st.markdown("**Milestones.** Add, remove or change rows. Weeks start at 1.")
        ms_df = st.data_editor(
            st.session_state.ms_init, key=f"ms_{ver}", num_rows="dynamic", hide_index=True, width="stretch",
            column_config={
                "phase": st.column_config.TextColumn("Phase", required=True),
                "start": st.column_config.NumberColumn("Start week", min_value=1, step=1, format="%d"),
                "end": st.column_config.NumberColumn("End week", min_value=1, step=1, format="%d"),
                "description": st.column_config.TextColumn("What happens", width="large"),
            },
        )
        st.markdown(f"**Pricing** ({st.session_state.currency}). Set low and high the same for a fixed price.")
        price_df = st.data_editor(
            st.session_state.price_init, key=f"price_{ver}", num_rows="dynamic", hide_index=True, width="stretch",
            column_config={
                "item": st.column_config.TextColumn("Line item", required=True),
                "low": st.column_config.NumberColumn("Low", min_value=0, step=10, format="%.0f"),
                "high": st.column_config.NumberColumn("High", min_value=0, step=10, format="%.0f"),
            },
        )
        st.text_area("Payment terms (one per line)", key="e_payment", height=110)

proposal = collect(ms_df, price_df)

with left:
    with tab_export:
        stem = render.filename_stem(proposal)
        st.markdown("Download the finished proposal.")
        st.download_button("Download HTML presentation", render.render_html(proposal), f"{stem}.html",
                           "text/html", width="stretch", type="primary")
        st.download_button("Download Word document (.docx)", docx_export.build_docx(proposal), f"{stem}.docx",
                           "application/vnd.openxmlformats-officedocument.wordprocessingml.document", width="stretch")
        st.info("For a PDF: open the downloaded HTML in your browser, press Ctrl+P and choose Save as PDF. "
                "The layout is set up for printing, one section per page.")
        st.caption("You can also click directly on text in the preview and edit it there. "
                   "Use the preview's own Download HTML button to keep those edits.")

with right:
    # Safe to embed: render_html escapes every piece of user text (see tests/test_generator.py).
    st.iframe(render.render_html(proposal, editable=True), height=900)
