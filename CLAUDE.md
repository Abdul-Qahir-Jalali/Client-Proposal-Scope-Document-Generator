# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Windows project; the venv is `.venv` in the repo root. Call its Python directly instead of activating it.

```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py            # app at http://localhost:8501
.venv\Scripts\python.exe -m pytest -q                       # all tests
.venv\Scripts\python.exe -m pytest tests/test_generator.py -k price_items   # one test
```

`.claude/launch.json` defines a `proposal-app` server for the in-app browser preview. There is no linter or build step.

## Architecture

A Streamlit app that turns project details into a proposal. Everything revolves around one plain **proposal dict** (keys: `client`, `title`, `summary`, `goals`, `deliverables`, `scope_in`, `scope_out`, `assumptions`, `milestones`, `price_items`, `currency`, `payment_terms`, `notes`, `next_steps`, ...). Its shape is defined only by `build_proposal()` in `proposal/generator.py`; `render.py`, `docx_export.py` and `app.py` all read it by key, so changing a key means changing all four.

- `proposal/generator.py`: input parsing (`parse_freeform`, `parse_money`, `parse_weeks`), phase/price templates per project kind (`PHASES`, `EXCLUSIONS`, chosen by `project_kind` regex), and `build_proposal`. Template-based, no AI or network. `to_freeform` is the inverse of `parse_freeform` and the round-trip is tested, so keep them in sync (`FIELDS`, `ALIASES`, `FIELD_LABELS`).
- `proposal/render.py` + `templates/proposal.html.j2`: one Jinja template produces both outputs. `editable=True` adds the toolbar and `contenteditable` for the in-app preview; `False` gives the clean export. Totals, weeks and the Gantt grid are derived at render time, never stored in the dict.
- `proposal/docx_export.py`: `python-docx` export built from the same dict and the same derived helpers.
- `app.py`: owns all UI state.

### Live-editing flow in `app.py`

The app starts empty: `has_proposal` is False, all `in_*` inputs are `""`, and the script ends with `st.stop()` after an empty-state card. Only `generate()` (which refuses a blank client name) or `load_sample()` sets `has_proposal`, so nothing below the `st.stop()` can assume a proposal exists before that.

Widgets are keyed (`in_*` for sidebar inputs, `e_*` for edit-tab content). `generate()` and `load_sample()` are button callbacks: they build a dict and `load_proposal()` copies it into the `e_*` keys and two DataFrames (`ms_init`, `price_init`). On every rerun `collect()` rebuilds the dict from the widgets, and the preview and downloads render from that. The `st.data_editor` keys include `ss.ver`, which is bumped on each generate so the tables reset; do not drop it. Widget state must be set in callbacks or before the widget is created.

Edits typed directly in the preview iframe are not sent back to Streamlit. They live in the iframe until its own Download HTML button is used. This is by design.

`docs/sample-proposal.html`, `docs/assets/app.png` and `docs/assets/proposal-tour.gif` are generated README assets, not source. After changing `templates/proposal.html.j2` or the UI, re-render the sample (`render_html(build_proposal(sample))`) and recapture the images so the README does not show an old design.

## Gotchas

- Streamlit caches imported modules: after editing anything in `proposal/`, restart the server or the old code keeps running (this caused a stale-template bug).
- The preview uses `st.iframe`, not `st.components.v1.html`, which was removed after 2026-06-01. That iframe is same-origin with the app and runs scripts. All user text is escaped by Jinja autoescape; never use `|safe` or build HTML by string concatenation (`test_user_text_is_escaped` covers this).
- PDF export (`proposal/pdf_export.py`) prints the non-editable HTML with a locally installed headless Chrome or Edge, one section per page via the template's print CSS. WeasyPrint was dropped because it needs GTK libraries on Windows. With no browser found it raises `PdfUnavailable`, and the user falls back to Print to PDF on the downloaded HTML.
- Streamlit deletes the state of widgets that are not drawn in a run. Both sidebar input groups are therefore always drawn (inside expanders); do not put them behind an `if`.
- Editable price cells arrive as NaN when blank. `generator.clean_amounts` sanitises them and `pricing_totals` / `price_range_text` call it, so use those instead of reading `low` / `high` directly.
- Samples are any `samples/*.json` file with the input fields plus `sample_name`; they are discovered by `load_samples()`.

## Vendored skills

Both are third-party; do not edit them.

- `.claude/skills/impeccable/` is the Impeccable design skill (Apache-2.0, from github.com/pbakaus/impeccable). Its launcher downloads a checksum-verified engine binary on first run.
- `.claude/skills/brag/` and `brag-slim/` are the brag skills (MIT, from github.com/latent-spaces/brag). They turn the project into a short launch video via `npx hyperframes`, which downloads an npm package when run. The bundled music in `brag/assets/music` is CC BY 4.0 and needs the credit "Music: Sascha Ende, ende.app (CC BY 4.0)" in anything that uses it.
- `.claude/skills/taste-skill/` is Leonxlnx's taste-skill (MIT, from github.com/Leonxlnx/taste-skill; its frontmatter name is `design-taste-frontend`). It is aimed at marketing sites and app screens, and its Node scripts (Node 22+) drive a local headless Chrome. `scripts/assets.mjs` downloads stock photos from public image APIs, which this product does not need.
