# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack
Existing codebase: a Streamlit app (`app.py`) that renders one Jinja HTML template (`templates/proposal.html.j2`, inline CSS, no build step) to the on-screen preview, a standalone HTML download, a Word file and a PDF printed by headless Chrome.

## Users
Two audiences, inferred from the repository and the user's briefing (not interviewed in depth):
- **Author:** a small digital agency (default name "Allure Digital") that turns project details into a proposal in minutes and edits it live.
- **Reader:** the agency's client, usually a small-business owner, who reads the proposal on a laptop or phone, or as a printed or PDF copy, to decide whether to sign. They are not designers or developers.

## Product Purpose
Produce a client proposal and scope document (summary, goals, scope included and excluded, assumptions, timeline, pricing, payment terms, next steps) that is clear enough to prevent scope disputes and good enough to win the job. Success: the client understands scope and price without a call, and knows how to accept.

## Positioning
Template-based, offline, no API key: the agency types a few facts and gets a complete, consistent, editable proposal that exports to HTML, Word and PDF from the same data.

## Operating Context
- One proposal dict feeds the HTML, Word and PDF outputs; HTML is a single self-contained file the client opens or prints.
- The PDF is one section per page (print CSS), made with locally installed headless Chrome or Edge.
- The app preview embeds the same template in an iframe with click-to-edit enabled.
- Fonts currently load from Google Fonts; an emailed or offline copy falls back to system fonts.

## Capabilities and Constraints
- Content is fixed by `build_proposal()`: client, title, summary, goals, deliverables, scope in/out, assumptions, milestones (weeks), price items (low/high), currency, payment terms, notes, next steps, dates, "prepared by". No logo, contact details or brand colour exist yet; the user decided NOT to add new data fields for this pass.
- Totals, weeks and the timeline grid are derived at render time.
- All user text is escaped by Jinja autoescape; never use `|safe`.
- Must keep: light and dark themes, phone layout, print one section per page, the `editable` toolbar and its script, and every variable `render.py` passes to the template.
- Open: whether agencies need their own logo and brand colour later (deferred by the user).

## Brand Commitments
None binding. The current teal cover and Bricolage Grotesque / Public Sans pairing are not commitments; the user asked for a fresh premium look.

## Evidence on Hand
Three sample proposals in `samples/*.json` (a dental clinic website, a logistics driver app, an organic grocer campaign) and their renders in `docs/`. No client logos, testimonials, case studies or photography exist; none may be invented.

## Product Principles
1. The price and the way to accept are the two moments that decide the deal; they get the most clarity.
2. Content must survive any length: long titles, 30-week plans, many scope items, no price at all.
3. One source, three outputs: a design must degrade gracefully into print and into the Word export's simpler form.
4. No invented claims: nothing the generator does not know (testimonials, guarantees, prices) appears in the design.

## Accessibility & Inclusion
Text contrast at least WCAG AA (current palette passes). Meaning is never carried by colour alone. Readable on a phone at 390px without sideways page scroll.
