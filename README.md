# Client Proposal & Scope Document Generator

Turn a few project details into a finished client proposal: executive summary, scope of work,
timeline and pricing. Edit every word live, then export to HTML, Word or PDF.

![The app: project details on the left, editable content in the middle, live proposal preview on the right](docs/assets/app.png)

## A finished proposal

![A six-section proposal: cover, executive summary, scope of work, timeline, investment, next steps](docs/assets/proposal-tour.gif)

The proposal is one modern HTML page: a sticky navigation bar, a photo cover (chosen automatically from the project type) that draws the project's phases as a
band, then full-width sections for the summary, scope, timeline, a dark Investment section with the total as the largest
figure, terms, and a clear Accept section with signature fields. It follows your system light or dark theme, works on a
phone, animates gently as you scroll (and not at all if you prefer reduced motion), and prints one section per page.
[`docs/sample-proposal.html`](docs/sample-proposal.html) is a real export. Download it and open it in a browser.

## Run it

You need Python 3.11 or newer.

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

On Mac or Linux, use `.venv/bin/pip` and `.venv/bin/python` in place of the `.venv\Scripts\` paths.

The app opens at http://localhost:8501 empty, ready for your details. Press *Load sample* in the sidebar
to see a finished proposal straight away. It needs no API key and no internet to generate a proposal. The HTML loads its fonts from Google Fonts when online.

## How to use it

1. **Pick a sample** in the sidebar and press *Load sample*, or type your own details.
   Use *Form fields* for separate boxes, or *Free-form text* with lines like this:
   ```
   Client: Acme Co
   Project type: Website
   Goals: more leads; a faster site
   Deliverables:
   - 5-page website
   - Contact form
   Timeline: 6 weeks
   Pricing: $4k - $6k
   Notes: Launch before March
   ```
2. Press **Generate proposal**.
3. **Edit live.** Change any text in *Edit content*, or change milestones and prices in *Timeline & pricing*.
   The preview, the timeline chart and the totals update as you type.
4. You can also **click straight into the preview** and type over the text. Those edits stay in the preview,
   so use the preview's own *Download HTML* button to keep them.
5. **Export** from the *Export* tab as HTML, Word (.docx) or PDF.

Pressing *Generate proposal* again replaces your edits with a fresh draft.

## What it writes

| Section | Built from |
|---|---|
| Executive summary | Client, goals, deliverables, timeline and price |
| Scope of work | Your deliverables, plus standard inclusions, exclusions and assumptions for the project type |
| Timeline and milestones | Phases sized to your timeline, for websites, apps, marketing, branding or general projects |
| Investment | Your price or range split across the phases, with payment terms |

The text is template based, so read it and adjust it before it goes to a client.

## Exporting

| Format | How |
|---|---|
| HTML | Download from the *Export* tab. A single file you can email or host. |
| Word | Download the .docx from the *Export* tab. Fully editable. |
| PDF | Press *Create PDF*. It uses Chrome or Edge already on your computer and takes a few seconds. With neither installed, open the HTML and use Print, then Save as PDF. |

## Samples

Three demos live in `samples/`: a website redesign, a mobile app and a marketing campaign.
To add your own, drop another `.json` file in that folder with the same fields.

## Project layout

```
app.py                   Streamlit interface and live-editing state
proposal/generator.py    Parsing, phase and price templates, proposal builder
proposal/render.py       HTML rendering
proposal/docx_export.py  Word export
proposal/pdf_export.py   PDF export through headless Chrome or Edge
proposal/limits.py       Input limits, validation and rate limiting
proposal/monitoring.py   Logging, error tracking (Sentry, optional) and timing
proposal/health.py       Self-check: python -m proposal.health
templates/               The HTML proposal template
samples/                 Demo inputs
tests/                   Test suite
docs/                    README images and a sample export
```

## Development

Install the exact pinned versions, then run the same checks that CI runs on every push:

```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format --check .
.venv\Scripts\python.exe -m mypy
.venv\Scripts\python.exe -m pytest --cov
```

To change or upgrade a package, edit `requirements.in` (or `requirements-dev.in`), then rebuild the pinned files:

```bash
.venv\Scripts\python.exe -m piptools compile --strip-extras --no-header --annotation-style=line -o requirements.txt requirements.in
```

## Limits

Text length, the number of list lines, table rows, weeks (104) and amounts (1,000,000,000) are limited, and
"Generate proposal" and "Create PDF" have a short wait between clicks. All numbers are in `proposal/limits.py`.

## Logging, errors and health

Settings are environment variables (see `.env.example`): `LOG_LEVEL`, `LOG_FORMAT` (`text` or `json`),
`LOG_FILE` (default `logs/app.log`, rotates at 1 MB) and `SENTRY_DSN` (optional crash reports; needs `sentry-sdk`).
Logs hold counts and timings only, never client names or prices.
When something unexpected fails, the user sees an *error id*. Search the log or Sentry for that id.

Health check (exit code 0 = healthy): `python -m proposal.health`. The Streamlit server also answers `/_stcore/health`.

## Safe by design

Everything you type is escaped in the HTML output, so pasted markup cannot run as code. A test covers this.
