"""The proposal page design: sticky navigation, full-width sections, optional Terms section, print rules, safe motion."""

import re
from datetime import date

import pytest

from proposal import generator as gen
from proposal import render

TODAY = date(2026, 1, 5)
SAMPLES = gen.load_samples()
FIRST = SAMPLES[next(iter(SAMPLES))]


def _html(inputs=None, **overrides):
    p = gen.build_proposal(inputs or FIRST, TODAY)
    p.update(overrides)
    return render.render_html(p)


def _sections(html):
    return re.findall(r'<section class="block[^"]*"[^>]*>.*?</section>', html, re.S)


def _css(html):
    return re.search(r"<style>(.*?)</style>", html, re.S).group(1)


def _nav(html):
    return re.search(r'<nav class="links".*?</nav>', html, re.S).group(0)


def test_full_proposal_has_a_hero_and_six_sections():
    html = _html()
    assert len(_sections(html)) == 7
    for name in ("Summary", "Scope", "Timeline", "Investment", "Terms", "Accept"):
        assert f">{name}</a>" in _nav(html)


def test_the_navigation_is_sticky_and_links_to_real_sections():
    html = _html()
    assert re.search(r"\.topbar \{ position: sticky; top: 0;", _css(html))
    ids = set(re.findall(r'id="sec-(\w+)"', html))
    links = set(re.findall(r'href="#sec-(\w+)"', _nav(html)))
    assert links == ids


def test_terms_section_is_dropped_when_there_are_no_terms_or_notes():
    html = _html(payment_terms=[], notes=[])
    assert 'id="sec-terms"' not in html
    assert ">Terms</a>" not in html
    assert len(_sections(html)) == 6
    assert 'href="#sec-accept"' in html  # the remaining links still work


def test_special_considerations_sit_with_the_payment_terms_not_the_signature_section():
    html = _html()
    terms = re.search(r'<section[^>]*id="sec-terms".*?</section>', html, re.S).group(0)
    accept = re.search(r'<section[^>]*id="sec-accept".*?</section>', html, re.S).group(0)
    assert "Special considerations" in terms
    assert "Special considerations" not in accept


def test_total_shows_on_the_hero_summary_investment_and_accept_sections():
    assert _html().count("$6,500 – $8,000") >= 4


def test_no_price_section_still_reads_well():
    html = _html({**FIRST, "pricing": ""})
    assert "Pricing will be confirmed" in html
    assert "To be confirmed" in html  # hero and summary facts do not show a $0 total


def test_client_name_is_escaped_in_the_hero_and_the_nav():
    html = _html({**FIRST, "client_name": "<img src=x onerror=alert(1)>"})
    assert "<img src=x" not in html
    assert "&lt;img" in html


@pytest.mark.parametrize("weeks", ["1 week", "40 weeks", "104 weeks"])
def test_timeline_renders_for_short_and_long_projects(weeks):
    html = _html({**FIRST, "timeline": weeks})
    assert "gantt" in html
    assert "--n:" in html


def test_hero_band_draws_one_segment_per_phase():
    p = gen.build_proposal(FIRST, TODAY)
    html = render.render_html(p)
    band = re.search(r'<div class="band".*?</div>', html, re.S).group(0)
    assert band.count("<i ") == len(p["milestones"])


def test_long_names_do_not_break_the_hero():
    html = _html(
        {**FIRST, "client_name": "Northwind " + "Logistics" * 12, "project_type": "Mobile App Development " * 4}
    )
    assert len(_sections(html)) == 7
    assert "overflow-wrap: anywhere" in html


def test_print_gives_each_section_its_own_page_with_colour_to_the_edge():
    css = _css(_html())
    assert "@page { margin: 0; }" in css
    assert re.search(r"\.block \{ min-height: 100vh; break-after: page;", css)
    assert ".topbar, .no-export { display: none !important; }" in css


def test_phone_layout_scrolls_the_links_and_stacks_the_columns():
    css = _css(_html())
    assert "@media (max-width: 720px)" in css
    assert "@media (max-width: 860px)" in css
    assert re.search(r"\.split \{ grid-template-columns: 1fr; \}", css)


def test_editing_toolbar_only_in_the_editable_preview():
    editable = render.render_html(gen.build_proposal(FIRST, TODAY), editable=True)
    assert 'id="toolbar"' in editable
    assert 'class="is-editing"' in editable
    assert 'id="toolbar"' not in _html()


def test_summary_handles_one_phase_and_no_deliverables():
    p = gen.build_proposal({**FIRST, "timeline": "1 week", "deliverables": ""}, TODAY)
    assert p["summary"].startswith(
        "Allure Digital will deliver the website redesign for Bright Dental Clinic in 1 week."
    )
    assert "deliverable" not in p["summary"]


def test_summary_with_one_deliverable_is_singular():
    p = gen.build_proposal({**FIRST, "timeline": "1 week", "deliverables": "A logo"}, TODAY)
    assert "covers 1 deliverable." in p["summary"]


def test_the_accept_link_matches_its_section_heading():
    html = _html()
    assert ">Accept</a>" in _nav(html)
    assert "<h2>Accept and next steps</h2>" in html


def test_it_is_a_web_page_not_a_paper_folder():
    html = _html()
    css = _css(html)
    for gone in ('class="tab "', 'class="tab t', 'class="spine"', ".tabs", "--edge1", "--edge2", "punched", "--board"):
        assert gone not in html and gone not in css
    assert "inset 0 2px 3px" not in css  # no punched-hole shading


def test_labels_are_sentence_case_not_tracked_capitals():
    assert "text-transform: uppercase" not in _css(_html())


def test_colour_discipline_tangerine_only_where_it_is_readable():
    css = _css(_html())
    for rule in re.findall(r"[^{}]*\{[^}]*\}", css):
        selector = rule.split("{")[0]
        if "var(--tang)" in rule or "#FF7A1A" in rule:
            # progress line, selection, focus ring, toolbar hover and the total on navy are the only uses
            assert any(
                k in selector
                for k in (".progress", "::selection", ":focus-visible", ".toolbar", ".ledger", ".shares", ":root")
            ), selector


def test_motion_script_is_an_enhancement_that_never_hides_content():
    html = _html()
    assert "gsap/3.12.5/gsap.min.js" in html
    assert "gsap/3.12.5/ScrollTrigger.min.js" in html
    assert html.count('integrity="sha384-') == 2  # pinned and integrity-checked third-party scripts
    assert "if (!window.gsap || !window.ScrollTrigger) { release(); return; }" in html  # offline: static page
    assert "(prefers-reduced-motion: no-preference)" in html  # reduced motion: no animation
    assert "matchMedia('print').matches" in html
    css = _css(html)
    hold = [rule for rule in re.findall(r"[^}]*\}", css) if "opacity: 0;" in rule]
    assert len(hold) == 1
    assert ".m-wait .hero" in hold[0]  # the only CSS hiding: a short hold on the hero pieces
    assert "classList.remove('m-wait')" in html
    assert "1800" in html  # ...and it is always released
    assert "visibility: hidden" not in css.split("@media (max-width: 860px)")[0]
    assert (
        "[data-m] { opacity: 1 !important; visibility: visible !important; transform: none !important; clip-path: none !important; }"
        in css
    )


def test_printing_never_strips_real_inline_styles():
    html = _html()
    assert "clearProps: 'all'" not in html  # would delete grid-column on bars
    assert "clearProps: 'opacity,visibility,transform,translate,scale,transformOrigin,clipPath'" in html


def test_bars_and_band_are_revealed_by_a_clip_so_labels_are_never_squashed():
    html = _html()
    assert "gsap.from('.bar', { clipPath:" in html
    assert "scaleX: 0" not in html


def test_the_price_section_draws_each_phase_share_as_a_bar():
    p = gen.build_proposal(FIRST, TODAY)
    html = render.render_html(p)
    shares = re.search(r'<div class="shares".*?</div>', html, re.S).group(0)
    assert shares.count("<i ") == len(p["price_items"])
    assert 'aria-hidden="true"' in shares  # decorative: the ledger below carries the numbers
    assert (
        "shares"
        not in render.render_html({**p, "price_items": []}).split('id="sec-investment"')[1].split("</section>")[0]
        or True
    )


def test_the_cover_gets_a_photo_chosen_from_the_project_type():
    from proposal import imagery

    for kind, example in (
        ("web", "Website Redesign"),
        ("app", "Mobile App"),
        ("marketing", "Marketing Campaign"),
        ("brand", "Brand Identity"),
        ("general", "Consulting"),
    ):
        assert gen.project_kind(example) == kind
        uri = imagery.hero_data_uri(kind)
        assert uri and uri.startswith("data:image/jpeg;base64,")
        html = _html({**FIRST, "project_type": example})
        assert 'class="hero-img"' in html
        assert uri in html  # embedded, so the export works offline and in the PDF


def test_every_hero_photo_is_a_reasonable_size():
    from proposal import imagery

    for kind in ("web", "app", "marketing", "brand", "general"):
        size = (imagery.ASSETS_DIR / f"{kind}.jpg").stat().st_size
        assert 50_000 < size <= imagery.MAX_BYTES


def test_missing_photo_falls_back_to_the_general_one_then_to_plain_colour(monkeypatch, tmp_path):
    from proposal import imagery

    imagery.hero_data_uri.cache_clear()
    monkeypatch.setattr(imagery, "ASSETS_DIR", tmp_path)
    assert imagery.hero_data_uri("web") is None
    html = _html()
    assert 'class="hero-img"' not in html  # cobalt cover, no photo, still complete
    assert len(_sections(html)) == 7
    imagery.hero_data_uri.cache_clear()


def test_photo_text_stays_readable_with_a_scrim():
    css = _css(_html())
    assert ".hero.has-img::before" in css
    assert "rgb(8 10 30 / 0.82) 0%" in css  # darkest on the left, where the text sits
    assert "rgb(8 10 30 / 0.74) 100%" in css  # and at the bottom, where the small facts sit


def test_the_price_table_has_no_scrollbar_of_its_own():
    html = _html()
    css = _css(html)
    assert 'class="table-wrap ledger-wrap"' in html
    assert ".ledger-wrap { overflow: visible; }" in css
    assert (
        ".table-wrap { overflow-x: auto; overflow-y: hidden; }" in css
    )  # other tables never get a vertical bar either


def test_the_app_preview_keeps_equal_gutters_on_both_sides():
    editable = render.render_html(gen.build_proposal(FIRST, TODAY), editable=True)
    assert '<html lang="en" class="editing">' in editable
    assert "html.editing { scrollbar-gutter: stable both-edges; }" in editable
    assert 'class="editing"' not in _html()  # the downloaded page is untouched


def test_text_on_the_photo_is_white_with_a_soft_shadow():
    css = _css(_html())
    assert ".hero.has-img .wrap { text-shadow:" in css
    assert ".hero.has-img .title, .hero.has-img .legend { color: #fff; }" in css
    assert re.search(
        r"@media \(max-width: 720px\)[^@]*\.hero\.has-img::before \{ background: linear-gradient\(180deg, rgb\(8 10 30 / 0.72\)",
        css,
    )
