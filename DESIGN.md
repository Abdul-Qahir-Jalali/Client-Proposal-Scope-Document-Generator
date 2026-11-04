---
name: Client Proposal Web Page
description: A modern sticky-nav web page of full-width sections that change ground: cobalt hero, white and canvas sections, a navy Investment section with a tangerine total.
colors:
  cobalt: "#2B44FF"
  cobalt-deep: "#1B2BC8"
  navy: "#0A0F3C"
  tang: "#FF7A1A"
  peach: "#FFB27A"
  periwinkle: "#8294FF"
  lilac: "#D6DCFF"
  canvas: "#F5F6FB"
  surface: "#FFFFFF"
  tint: "#ECEFFF"
  ink: "#0E1230"
  muted: "#565C7A"
  line: "#E1E4F0"
  canvas-night: "#0A0D1F"
  surface-night: "#11152B"
  tint-night: "#171C3A"
  ink-night: "#ECEFFF"
  muted-night: "#A2A9C8"
  line-night: "#262C4A"
typography:
  display:
    fontFamily: "Familjen Grotesk, Segoe UI, system-ui, sans-serif"
    fontSize: "clamp(2.8rem, 9vw, 8rem)"
    fontWeight: 700
    lineHeight: 0.94
    letterSpacing: "-0.045em"
  headline:
    fontFamily: "Familjen Grotesk, Segoe UI, system-ui, sans-serif"
    fontSize: "clamp(2.4rem, 5.6vw, 4.2rem)"
    fontWeight: 600
    lineHeight: 1.05
    letterSpacing: "-0.03em"
  title:
    fontFamily: "Familjen Grotesk, Segoe UI, system-ui, sans-serif"
    fontSize: "clamp(1.45rem, 2.7vw, 2.1rem)"
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  total:
    fontFamily: "Familjen Grotesk, Segoe UI, system-ui, sans-serif"
    fontSize: "clamp(2.4rem, 6.6vw, 5rem)"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "-0.04em"
  body:
    fontFamily: "Hanken Grotesk, Segoe UI, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.65
  label:
    fontFamily: "Hanken Grotesk, Segoe UI, system-ui, sans-serif"
    fontSize: "0.9rem"
    fontWeight: 500
    lineHeight: 1.3
  step-numeral:
    fontFamily: "Familjen Grotesk, Segoe UI, system-ui, sans-serif"
    fontSize: "3rem"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "-0.04em"
rounded:
  panel: "24px"
  field: "16px"
  input: "14px"
  bar: "8px"
  pill: "999px"
spacing:
  wrap: "1120px"
  gutter: "clamp(20px, 5vw, 56px)"
  nav-height: "60px"
  section-padding: "clamp(72px, 10vw, 136px)"
  block-gap: "clamp(36px, 5vw, 64px)"
components:
  nav-bar:
    backgroundColor: "{colors.navy}"
    textColor: "{colors.surface}"
    height: "60px"
  nav-link:
    backgroundColor: "transparent"
    textColor: "{colors.lilac}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "9px 14px"
  nav-link-current:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.navy}"
    rounded: "{rounded.pill}"
  progress-line:
    backgroundColor: "{colors.tang}"
    height: "3px"
  hero:
    backgroundColor: "{colors.cobalt}"
    textColor: "{colors.surface}"
    typography: "{typography.display}"
  hero-circle:
    backgroundColor: "{colors.cobalt-deep}"
    rounded: "50%"
  phase-band:
    backgroundColor: "{colors.surface}"
    rounded: "6px"
    height: "20px"
  glance-panel:
    backgroundColor: "{colors.tint}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
    padding: "32px 36px"
  gantt-panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.panel}"
    padding: "22px 26px 8px"
  gantt-bar:
    backgroundColor: "{colors.cobalt}"
    textColor: "{colors.surface}"
    rounded: "{rounded.bar}"
    padding: "7px 11px"
  investment-section:
    backgroundColor: "{colors.navy}"
    textColor: "{colors.surface}"
  share-bar:
    backgroundColor: "{colors.tang}"
    rounded: "6px"
    height: "22px"
  ledger-total:
    textColor: "{colors.tang}"
    typography: "{typography.total}"
  step-numeral:
    textColor: "{colors.cobalt}"
    typography: "{typography.step-numeral}"
  deal-panel:
    backgroundColor: "{colors.tint}"
    rounded: "{rounded.panel}"
    padding: "30px 36px"
  signature-field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.field}"
    padding: "20px 24px 10px"
---

# Design System: Client Proposal Web Page

## Overview

**Creative North Star: "The Product Page"**

The proposal reads like a premium product site, not a paper document. A sticky navy bar always shows where you are; below it, full-width sections change ground as the client scrolls: a cobalt hero, white and canvas reading sections, tint panels, a deep navy Investment section and a final Accept section. There are no tabs, binding holes, page edges, board covers or foil. Type is big and confident, colour is flat, and every decision moment gets its own ground.

Density is generous. Each section is one full-width band with a 1120px reading column and clamp(72px, 10vw, 136px) of vertical air, so the structure of the deal is legible at a glance. The two decisive moments, the price and the way to accept, get the strongest treatment: the navy section whose tangerine total is the largest figure on the page, and the Accept section with four big cobalt step numerals and signature fields.

The system rejects the category default: identical rounded cards on a grey canvas with a single teal accent. Here the ground itself changes between sections, and the hero art is made from the project's own data.

**Key Characteristics:**
- Sticky navy navigation bar with the client name, pill section links (the current one filled white) and a tangerine scroll-progress line.
- Cobalt #2B44FF hero with one tone-on-tone circle (#1B2BC8) bleeding off the right edge, a data-made phase band with legend, and five facts.
- Sections alternate white and canvas (#F5F6FB); tint panels (#ECEFFF) carry glance facts, assumptions and the deal line.
- Navy #0A0F3C Investment section with a proportional share bar and the total in tangerine as the largest figure.
- Two grotesques: Familjen Grotesk for display and figures that matter, Hanken Grotesk for text and tables; figures are tabular.
- No gradients, icons or stock imagery. Print: one section per page, colour to the paper edge.

## Colors

A cobalt brand colour on a cool neutral ground, with deep navy for the bar and price, and tangerine reserved for the navy.

### Primary
- **Cobalt** (`cobalt`, #2B44FF): the hero ground, Gantt bars, Accept step numerals and the accent on light grounds.
- **Cobalt Deep** (`cobalt-deep`, #1B2BC8): the hero circle only (tone on tone).
- **Navy** (`navy`, #0A0F3C): the navigation bar and the Investment section.
- **Tangerine** (`tang`, #FF7A1A): the total (the only tangerine figure on the page), the scroll-progress line, text selection and the focus ring.

### Secondary
- **Phase ramp** (white, #C4CCFF, #97A6FF, #6D80FF): one order-of-phases colour language used on the cobalt hero band and legend and on the navy share bar and ledger swatches (the pattern repeats every four). The Gantt bars follow the same order in cobalt, #1F33D6, #1626A8 and #0F1C80 so white labels keep their contrast. Lilac (#D6DCFF) is `--hero-soft`, the hero title, legend and fact labels. Periwinkle (#8294FF) is `--accent` in dark mode. In dark mode the Investment section uses #111A5E so it stays a distinct dark band.
- **Hero band tints** (#FFFFFF, #C4CCFF, #97A6FF, #6D80FF): the phase band segments and legend swatches, repeating every four.

### Neutral
- **Canvas** (`canvas`, #F5F6FB; dark #0A0D1F) and **Surface** (`surface`, #FFFFFF; dark #11152B): the alternating reading grounds.
- **Tint** (`tint`, #ECEFFF; dark #171C3A): panels.
- **Ink** (`ink`, #0E1230; dark #ECEFFF): body text and heavy rules.
- **Muted** (`muted`, #565C7A; dark #A2A9C8): secondary text, h3 labels, table headers.
- **Line** (`line`, #E1E4F0; dark #262C4A): hairlines and Gantt gridlines.

### Named Rules
**The Tangerine-On-Navy Rule.** Tangerine appears only on navy (the total), plus the progress line, text selection and focus ring. It never sits on a light ground.

**The One-Accent Rule.** On light grounds cobalt is the only accent. In dark mode `--accent` becomes periwinkle #8294FF so marks stay legible.

**The Ground-Change Rule.** Hierarchy comes from sections changing ground (cobalt, white, canvas, navy), not from boxes inside a single ground.

## Typography

**Display Font:** Familjen Grotesk (with Segoe UI, system-ui, sans-serif)
**Body Font:** Hanken Grotesk (with Segoe UI, system-ui, sans-serif)

**Character:** A slightly quirky grotesque with tight tracking for names and numbers, set against a neutral, open text grotesque. Fonts load from Google Fonts; offline copies fall back to Segoe UI or the system face.

### Hierarchy
- **Display** (700, clamp(2.8rem, 9vw, 8rem), 0.94, -0.045em): the client name in the hero, max 14ch, `overflow-wrap: anywhere`. The hero title is 500, clamp(1.3rem, 2.8vw, 2rem) in lilac.
- **Headline** (600, clamp(2.4rem, 5.6vw, 4.2rem), tight tracking): each section's h2.
- **Title** (500, clamp(1.45rem, 2.7vw, 2.1rem), 1.2, -0.02em): goals (max 30ch); also `.none`, the Accept deal line and 1.5rem h3 column headings.
- **Total** (700, clamp(2.4rem, 6.6vw, 5rem), 1, -0.04em): the Investment total only, in tangerine. It is the largest figure on the page after the hero name.
- **Step numerals** (Familjen Grotesk 700, 3rem, accent: cobalt, periwinkle in dark): the four Accept steps.
- **Body** (Hanken Grotesk 400, 17px, 1.65): lead paragraph is 1.3rem.
- **Label** (Hanken Grotesk 500 to 600, 0.82rem to 0.95rem, sentence case, no tracking): nav links, table headers, hero fact labels, signature headings. There are no tracked all-caps labels.

### Named Rules
**The Tabular Figures Rule.** Every figure column, date, week count, price and Gantt label uses tabular numerals.

**The One-Face-Per-Job Rule.** Display face for names, headings, goals, glance figures and the total; text face for running text, tables and labels.

## Layout

A stack of full-width sections inside a 1120px wrap with a clamp(20px, 5vw, 56px) gutter and clamp(36px, 5vw, 64px) between blocks. A 60px sticky navy bar sits on top, with the client name at the left (max 32ch, ellipsised) and the pill section links at the right.

The hero is cobalt, min-height min(100vh - 60px, 860px), content aligned to the bottom: client name, title, the phase band (one segment per phase, 20px high, 4px gaps) with its legend, then up to five facts (Prepared by, Date, Valid until, Timeline, Investment) in an auto-fit row (min 150px) under a hairline. Summary is a two-column split (5fr and 7fr: lead and glance panel beside the goals). Scope uses auto-fit columns (min 280px) with h3 headings over a 2px ink rule, and an assumptions tint panel. Timeline is a bordered 24px panel holding the Gantt (name column minmax(96px, 200px)), then the milestones table. Investment is the navy section: ledger rows with colour swatches, the share bar above and the total at the foot. Terms are twin columns of ruled rows. Accept has four steps over a 2px ink rule, the deal line in a tint panel, and two signature fields.

**Breakpoints:**
- **860px:** the two-column summary split stacks.
- **720px (phone):** the navigation links scroll horizontally with an edge fade and the brand is hidden; section padding drops to 56px; the hero shrinks to min(100vh - 60px, 720px); the Gantt shows no bar text and every fourth week label; the milestones table becomes stacked rows; steps go to two columns (one below 420px); panel radii drop to 20px.

**Print:** `@page { margin: 0 }`, one section per page (`min-height: 100vh`, `break-after: page`), colour to the paper edge, 20mm side padding, navigation hidden, `[data-m]` forced visible, Gantt and tables unclipped, hero facts in three columns.

**Dark mode:** by `prefers-color-scheme` unless `data-theme="light"`, or forced with `data-theme="dark"`. Canvas, surface, tint, ink, muted and line invert (#0A0D1F, #11152B, #171C3A, #ECEFFF, #A2A9C8, #262C4A); `--accent` becomes #8294FF. Cobalt, navy and tangerine stay as they are.

## Elevation & Depth

Flat. Depth comes from ground changes, tone-on-tone shapes and 1px lines, not shadows: the hero circle (#1B2BC8 on cobalt), the bordered Gantt panel, tint panels and ink-ruled signature fields. Any shadow is soft and offset, and print has none. The sticky bar rides above the sections by z-index (30); the editing toolbar (preview only) sits above it (40).

### Named Rules
**The Tone-On-Tone Rule.** Decoration is one shape in a deeper shade of its own ground. No gradients, no icons, no stock imagery.

## Shapes

Radii are by role: panels (glance, assumptions, deal, Gantt) 24px; signature fields 16px; inputs and fields 14px; Gantt bars 8px; phase and share segments 6px; swatches 3px; pills and buttons 999px; the hero circle is round. Panels step down to 20px on phones. List markers are 0.5rem squares (filled for Included, hollow outline for Not included, a short dash for Assumptions).

## Components

### Navigation Bar
- **Shape:** 60px navy bar, sticky, client name at the left, pill links at the right (999px radius, 9px 14px padding, Hanken Grotesk 500 at 0.92rem).
- **State:** links are lilac-tinted on navy; hover lifts to a 10% white wash; the current link is filled white with navy text. A 3px tangerine line along the bottom edge scales with scroll progress. On phones the links scroll with an edge fade and the brand hides.

### Hero
Cobalt ground, name at poster scale in white, title in lilac, the phase band with legend, five facts with lilac labels over a 28%-white hairline, and one darker cobalt circle bleeding off the top-right.

### Summary Blocks
The lead paragraph at 1.3rem, goals as hairline-ruled title-face lines (no bullets), and the glance panel (Timeline, Investment, Valid until) as a tint panel with 24px radius and 1.55rem figures.

### Gantt and Milestones
A bordered 24px panel on the surface ground. Bars are cobalt with white 0.8rem tabular text and 8px radius; gridlines are hairline. The milestones table has muted headers, and becomes stacked rows on phones.

### Investment Ledger
On navy: phase rows over faint white hairlines, each with a swatch matching its share-bar segment (the phase ramp). The share bar is proportional to each phase's amount, 22px high with 4px gaps. The foot shows a 'Total' label in light periwinkle-white and the figure in tangerine at the total size, the largest on the page. With no prices the section shows a single sentence in the title face.

### Terms Rows
Twin columns of ruled rows with no markers, hairline top, last row also bottom.

### Accept and Signature Fields
Four steps, each under a 2px ink rule with a large cobalt numeral; the deal line in a tint panel; then two signature fields (surface ground, 1.5px ink border, 16px radius) with a 54px signature line and a date line.

### Editing Toolbar (preview only)
A sticky ink bar with three pill buttons (Download HTML primary, Save as PDF, Reset); hover turns tangerine on navy text. Editable text shows a dashed outline on hover and a solid one on focus. In editing mode the navigation bar is static. Not exported.

## Motion

Personality: Premium. GSAP 3.12.5 and ScrollTrigger load from cdnjs with integrity hashes. Ease is `power2.out` throughout, with no overshoot or bounce. It is an enhancement only: CSS hides nothing except a 1.8s release-guarded hold (`.m-wait`) on the hero, so reduced motion, print and offline (GSAP not loaded) all show the complete static page. In print `[data-m]` is forced visible and the hold is released.

- **Hero sequence:** the client name rises over 0.7s, the title over 0.5s, the phase band segments are wiped in with clip-path (0.6s, 0.1s stagger), then the legend items and the facts follow with short staggers.
- **Restraint:** headings, goals and steps do not animate; the data drawing itself (band, bars, share bar, total) is the one orchestrated reveal. The scroll-progress line and the current-link highlight follow the scroll, and on phones the current link scrolls into view.
- **Gantt bars and share bar:** wiped in with clip-path.
- **Total:** fades up last, when the Investment section is reached.
- **Navigation:** the progress line scales with scroll and the current-link highlight follows the section in view.

## Do's and Don'ts

### Do:
- **Do** change the ground between sections (cobalt, white, canvas, navy) and keep the nav bar sticky.
- **Do** keep cobalt as the only accent on light grounds.
- **Do** keep the total in tangerine on navy as the largest figure of the Investment section.
- **Do** build the hero band and share bar from the proposal's own phases and amounts.
- **Do** choose radii by role (panels 24, fields 16 and 14, bars 8, pills 999).
- **Do** keep labels sentence case with tabular numerals, and `overflow-wrap: anywhere` on client-supplied names.
- **Do** keep one section per printed page with colour to the paper edge (`@page { margin: 0 }`).
- **Do** keep user text escaped through Jinja autoescape.

### Don't:
- **Don't** use tangerine on light grounds (only the progress line, selection and focus ring are exceptions).
- **Don't** use gradients, icons or stock imagery; decoration is tone on tone.
- **Don't** bring back paper, tabs, binding holes, page edges, a board cover or foil.
- **Don't** hide anything with CSS waiting for motion beyond the guarded 1.8s hero hold; the page must be complete without GSAP.
- **Don't** rely on colour alone for the current section; the filled white pill also changes shape against the others.
- **Don't** invent a logo, contact block or brand colour: no data fields for them exist.

## Deliberate Deviations from the Direction Contract

- **No logo or contact data.** The generator exposes no fields for either, so the design has no logo slot and no contact block; none may be invented.
- **Hero art is the phase band.** The contract's data-made art is built as a proportional band plus legend, with one circle; there is no further illustration.
- **Total sits second to the hero name.** The hero name is the biggest type on the page; the total is the largest figure.
