---
version: 1
slug: "templates-proposal-html-j2"
primary_target: "templates/proposal.html.j2"
related_targets: []
---

# Surface brief: client proposal (templates/proposal.html.j2)

Mode: Read (a page the client reads to understand scope and price, then decides to sign). Code-led build.
Audience: a small-business client on a laptop or phone, sometimes a PDF or printed copy.
User-pinned direction (beats any roll): a modern, great-looking WEB page, NOT a paper or folder metaphor; the user asked for the best colour scheme and high-quality visuals; content unchanged. The earlier "Tabbed Dossier" (paper sheets, index tabs, binding holes) is rejected and replaced.
Constraints: no new data fields or copy; every variable render.py passes stays; light and dark; phone at 390px; print one section per page (full-bleed colour sections); the editable toolbar and download script stay.

## Direction contract

THESIS: A proposal that reads like a premium product site: a sticky navigation bar that always shows where you are, full-width sections that change ground (cobalt hero, white, tint, navy price section), and big confident type. It refuses the paper/folder metaphor and the generic stack of identical cards.

OWN-WORLD: Cobalt #2B44FF (brand and hero ground), deep navy #0A0F3C (nav bar and the Investment section), tangerine #FF7A1A used only on navy (the total, one key figure), cool canvas #F5F6FB and white, tint #ECEFFF, ink #0E1230. Cobalt is the only accent colour on light grounds. Familjen Grotesk display with tight tracking, Hanken Grotesk text, sentence-case labels, tabular figures. Radii by role: panels 24px, fields 14px, bars 8px, pills 999px. Shadows only soft and offset. Hero art is data-made: the project's phases drawn as a proportional band across the hero, plus one tone-on-tone circle; no stock imagery, no gradients, no icons.

STORY: The client lands on a bold cover that already shows the shape of the project, reads goals first, sees scope in and out, watches the timeline as bars, meets the price on a dark full-width section with the total as the largest figure on the page, reads terms, and ends on a clear Accept section with steps and signature fields.

FIRST VIEWPORT: Navy bar (client name left, section links right, thin tangerine scroll-progress line). Below it a cobalt hero filling the viewport: the client name at poster scale in white, the title in a soft tint, the proportional phase band with a legend, and the five facts in a row at the bottom; one large darker-cobalt circle bleeds off the right edge. Primary action: scroll or click any section link.

FORM: Sticky-nav web page of full-width sections, user-pinned (no roll). seed: none (unavailable)

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
