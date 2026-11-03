# Client Proposal & Scope Document Generator

Turn basic project details into a clean client proposal: executive summary, scope of work,
timeline with milestones, and pricing. Edit everything live, then export.

## Run it (Windows)

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

Mac / Linux:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

The app opens at http://localhost:8501 with a sample already loaded, so you can demo it straight away.
Needs Python 3.10 or newer. No API key and no internet needed to generate (fonts in the HTML load from Google Fonts when online).

## How to use it

1. **Pick a sample** in the sidebar and press *Load sample*, or enter your own details.
   Use *Form* for separate boxes, or *Free-form paste* with lines like:
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
3. **Edit live.** Change any text in the *Edit content* tab, or edit milestones and prices in the
   *Timeline & pricing* tab. The preview updates as you type, and the timeline chart and totals follow.
4. You can also **click any text in the preview** and type over it. Those edits live in the preview
   only, so use the preview's own *Download HTML* button to keep them.
5. **Export** from the *Export* tab: HTML presentation or Word (.docx).
   For a PDF, open the HTML in a browser, press Ctrl+P and choose *Save as PDF* (the layout prints one section per page).

Pressing *Generate proposal* again replaces your edits with a fresh draft.

## What it makes

| Section | Source |
|---|---|
| Executive summary | Built from client, goals, deliverables, timeline and price |
| Scope of work | Your deliverables, plus standard inclusions, exclusions and assumptions for the project type |
| Timeline | Phases sized to your timeline (website, app, marketing, branding, or general) |
| Investment | Your price or range split across phases, with payment terms |

## Samples

Three demos live in `samples/` (website redesign, mobile app, marketing campaign).
Add your own by dropping another `.json` file in that folder using the same fields.

## Project layout

```
app.py                  Streamlit interface
proposal/generator.py   Parsing and proposal building
proposal/render.py      HTML rendering
proposal/docx_export.py Word export
templates/              The HTML proposal template
samples/                Demo inputs
tests/                  Run with: .venv\Scripts\python.exe -m pytest
```

## Notes

- The text is template based, so review and adjust it before sending to a client.
- All text you type is escaped in the HTML output, so pasted markup cannot run as code.
