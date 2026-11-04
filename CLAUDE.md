# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Windows project; the venv is `.venv` in the repo root. Call its Python directly instead of activating it.

```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py            # app at http://localhost:8501
.venv\Scripts\python.exe -m pytest -q                       # all tests (pytest config is in pyproject.toml)
.venv\Scripts\python.exe -m ruff check . ; .venv\Scripts\python.exe -m ruff format --check . ; .venv\Scripts\python.exe -m mypy   # what CI runs
.venv\Scripts\python.exe -m pytest tests/test_generator.py -k price_items   # one test
```

`.claude/launch.json` defines a `proposal-app` server for the in-app browser preview. There is no build step. CI (`.github/workflows/ci.yml`) runs ruff, mypy, pytest with a coverage floor, `proposal.health` and pip-audit. Dependencies are pinned: edit `requirements.in` / `requirements-dev.in`, then recompile with pip-tools (see README).

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

- The proposal design is a modern web page (see `DESIGN.md`, `PRODUCT.md`): sticky nav, cobalt hero, navy Investment section, tangerine only on navy. It deliberately has NO paper, tab or folder look; the user rejected that. The cover shows a free Unsplash photo chosen by project kind (`proposal/imagery.py`, files in `proposal/assets/hero/`, credits in `CREDITS.md`), embedded as a data URI so exports are self-contained; with no photo it falls back to the cobalt cover. The summary section opens with a real, sourced quote chosen by project kind (`proposal/quotes.py`; stored as `p["quote"]`, switchable in the app's Edit tab). Only add quotes whose wording and source you have verified; quote sites are full of misattributions. The Terms section only exists when there are payment terms or notes, so the page count is 6 or 7. The motion script is an enhancement: keep the print rules (`@page { margin: 0 }`, one `.block` per page, `[data-m]` forced visible), keep tints as colours not opacities, and keep `tests/test_design.py` in step with any template change.

- Limits live in `proposal/limits.py`. `collect()` in `app.py` and `build_proposal` clean and cap everything, so any new user-editable field needs `limits.clean_text` and a `max_chars`. The rate limiters are module-level in `limits.py` (not `app.py`), because `app.py` is re-run on every click.
- Logging goes through `proposal/monitoring.py`. Never log client names, prices or proposal text; log counts and timings with `log_event` / `timed`. Unexpected errors go through `report_error`, which returns the error id shown to the user.
- `tests/conftest.py` turns the rate limits off; tests of the limits set their own values.

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
- `.claude/skills/frontend-design/` is Anthropic's official design skill (Apache-2.0, from github.com/anthropics/skills). `.claude/skills/gsap-core/`, `gsap-timeline/`, `gsap-scrolltrigger/` and `gsap-performance/` are GreenSock's official GSAP skills (MIT, from github.com/greensock/gsap-skills). `.claude/skills/motion-design/` is LottieFiles' motion skill (MIT, from github.com/LottieFiles/motion-design-skill). All are plain instruction files with no scripts. The proposal's motion uses the "Premium" personality from motion-design and GSAP 3.12.5 from cdnjs with integrity hashes; it is only an enhancement (see the template's script and `tests/test_design.py`).
- `.claude/skills/taste-skill/` is Leonxlnx's taste-skill (MIT, from github.com/Leonxlnx/taste-skill; its frontmatter name is `design-taste-frontend`). It is aimed at marketing sites and app screens, and its Node scripts (Node 22+) drive a local headless Chrome. `scripts/assets.mjs` downloads stock photos from public image APIs, which this product does not need.
