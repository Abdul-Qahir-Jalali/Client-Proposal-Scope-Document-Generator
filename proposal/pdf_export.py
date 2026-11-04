"""Export the proposal HTML as a PDF using a locally installed Chrome or Edge (headless)."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from .limits import pdf_slots
from .monitoring import get_logger, timed

MAX_HTML_BYTES = 5_000_000  # a normal proposal is about 60 KB
SLOT_WAIT_SECONDS = 20

_WINDOWS_PATHS = (
    r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
    r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
    r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe",
    r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe",
)
_COMMANDS = ("google-chrome", "chromium", "chromium-browser", "chrome", "msedge", "microsoft-edge")
_MAC_PATHS = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
)


class PdfUnavailable(RuntimeError):
    """Raised when no browser is installed or it fails to produce a PDF."""


def find_browser() -> str | None:
    for template in _WINDOWS_PATHS + _MAC_PATHS:
        path = os.path.expandvars(template)
        if os.path.isfile(path):
            return path
    for name in _COMMANDS:
        found = shutil.which(name)
        if found:
            return found
    return None


def html_to_pdf(html: str, timeout: int = 60) -> bytes:
    """Print `html` to PDF. The page's print CSS gives one section per page.

    At most `limits.PDF_MAX_PARALLEL` browsers run at once. Others wait up to SLOT_WAIT_SECONDS,
    then get a "busy" message, so a burst of clicks cannot start dozens of Chrome processes.
    """
    browser = find_browser()
    if browser is None:
        get_logger("pdf").warning("pdf_unavailable reason=no_browser")
        raise PdfUnavailable("No Chrome or Edge found. Download the HTML and use Print > Save as PDF.")
    if len(html.encode("utf-8")) > MAX_HTML_BYTES:
        raise PdfUnavailable("This proposal is too large to turn into a PDF. Shorten some sections.")
    if not pdf_slots.acquire(timeout=SLOT_WAIT_SECONDS):
        get_logger("pdf").warning("pdf_busy")
        raise PdfUnavailable("Many PDFs are being made right now. Please try again in a minute.")
    try:
        with timed("pdf_export", html_bytes=len(html)) as info:
            pdf = _run_browser(browser, html, timeout)
            info["pdf_bytes"] = len(pdf)
            return pdf
    finally:
        pdf_slots.release()


def _run_browser(browser: str, html: str, timeout: int) -> bytes:
    # ignore_cleanup_errors: on Windows the browser can still hold profile files for a moment.
    with tempfile.TemporaryDirectory(prefix="proposal-pdf-", ignore_cleanup_errors=True) as tmp:
        source, target = Path(tmp) / "proposal.html", Path(tmp) / "proposal.pdf"
        source.write_text(html, encoding="utf-8")
        command = [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--user-data-dir={Path(tmp) / 'profile'}",
            "--virtual-time-budget=4000",
            f"--print-to-pdf={target}",
            source.as_uri(),
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, timeout=timeout)
        except (subprocess.SubprocessError, OSError) as exc:
            raise PdfUnavailable(f"The browser could not create the PDF ({exc.__class__.__name__}).") from exc
        if not target.is_file() or target.stat().st_size == 0:
            raise PdfUnavailable("The browser did not produce a PDF.")
        return target.read_bytes()
