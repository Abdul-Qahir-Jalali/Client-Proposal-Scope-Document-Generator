"""Self-check for monitoring. Run:  python -m proposal.health

Exit code 0 = healthy, 1 = something that must work is broken. A monitor, a Docker HEALTHCHECK or
a cron job can run this and alert on a non-zero exit code. Streamlit also serves its own
"is the server up" endpoint at /_stcore/health.
"""

from __future__ import annotations

import json
import sys
import time

from . import docx_export, generator, pdf_export, render


def run_checks() -> dict[str, dict[str, object]]:
    """Each check returns {"ok": bool, "detail": str, "required": bool}."""
    results: dict[str, dict[str, object]] = {}

    def check(name: str, required: bool, fn) -> None:
        start = time.perf_counter()
        try:
            detail = fn()
            ok = True
        except Exception as exc:  # a health check must report any failure, not raise it
            detail, ok = f"{exc.__class__.__name__}: {exc}", False
        results[name] = {
            "ok": ok,
            "required": required,
            "detail": detail,
            "ms": round((time.perf_counter() - start) * 1000),
        }

    def samples() -> str:
        found = generator.load_samples()
        if not found:
            raise RuntimeError("no samples found")
        return f"{len(found)} samples"

    def build_and_render() -> str:
        sample = next(iter(generator.load_samples().values()))
        proposal = generator.build_proposal(sample)
        html = render.render_html(proposal)
        if proposal["client"] not in html:
            raise RuntimeError("client name missing from rendered HTML")
        return f"{len(html):,} bytes of HTML"

    def word_export() -> str:
        sample = next(iter(generator.load_samples().values()))
        data = docx_export.build_docx(generator.build_proposal(sample))
        return f"{len(data):,} bytes"

    def browser() -> str:
        found = pdf_export.find_browser()
        if not found:
            raise RuntimeError("no Chrome or Edge found (PDF export is unavailable)")
        return found

    check("samples", True, samples)
    check("generate_and_render", True, build_and_render)
    check("word_export", True, word_export)
    check("pdf_browser", False, browser)  # optional: users can still print the HTML to PDF
    return results


def main() -> int:
    results = run_checks()
    healthy = all(r["ok"] or not r["required"] for r in results.values())
    print(json.dumps({"healthy": healthy, "checks": results}, indent=2))
    return 0 if healthy else 1


if __name__ == "__main__":
    sys.exit(main())
