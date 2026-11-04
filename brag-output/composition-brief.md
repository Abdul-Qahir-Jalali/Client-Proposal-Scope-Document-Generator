# Hyperframes Composition Brief: Client Proposal & Scope Document Generator

## Objective
Create a short launch-style brag video for the Client Proposal & Scope Document Generator.

## Output
- Composition directory: `brag-output/composition/`
- Rendered video: `brag-output/brag.mp4`
- Format: landscape, 1920x1080
- Duration: 24 seconds

## Source Material
- Project root: this repository
- Primary files read: README.md, CLAUDE.md, templates/proposal.html.j2, samples/01_dental_website.json
- Product name: Client Proposal & Scope Document Generator
- Strongest claims (verbatim from the README): "Edit every word live, then export to HTML, Word or PDF." and "It needs no API key and no internet to generate a proposal."
- Key UI moments: the form fields, then real renders of the proposal (cover, quote, timeline, investment) in `assets/shots/`
- Copy that must appear verbatim:
  - A few project details.
  - Edit every word live.
  - No API key. No internet to generate a proposal.

## Creative Direction
- Tone preset: polished
- Creative direction: quiet premium product film
- Hook: headline plus a form that types itself
- Outro: three export pills, then the name and the no-API-key line
- Avoid: generic SaaS language, abstract filler, any claim not in the project

## Visual Identity
- Colours: navy #0A0F3C, cobalt #2B44FF, canvas #F5F6FB, ink #0E1230, tangerine #FF7A1A (on navy only)
- Fonts: Familjen Grotesk (display), Hanken Grotesk (body), saved locally in `assets/fonts/`

## Storyboard
See `brag-plan.md`. Scenes: Details in (4.10s), Proposal out (4.12s), The quote (3.25s), The timeline (3.26s), The price (3.28s), Export (2.73s), Outro (3.26s).

## Audio
- Role: warm bed with sparse professional accents
- Music: happy-beats-business-moves-vol-10 (CC BY 4.0, credit "Music: Sascha Ende, ende.app (CC BY 4.0)")
- Cue guidance: bundled preset. Scene cuts on beats 4.10, 8.22, 11.47, 14.73; strong cues 18.01 and 20.74.
- Audio-reactive treatment: none (helper unavailable; documented)
- SFX: keypress (typing), click2 (Generate), impactSoft_medium_001 (strong cues), click_003 (pills), bong_001 (cover reveal)
- Audio files: in `composition/assets/music/` and `composition/assets/sfx/`

## Hyperframes Instructions
Native HyperFrames conventions: paused GSAP timeline registered on `window.__timelines["root"]`, `data-start`/`data-duration` clips, local assets only. Run `hyperframes check` before render.
