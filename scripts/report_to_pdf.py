"""Turn REPORT.md into a PDF for the sprint submission.

Pandoc converts the Markdown to a standalone HTML page with a simple
paper-like style, and a headless Chrome or Chromium prints that page to PDF.
HTML comments (our TODO notes) are dropped, so they never reach the PDF.

Needs: pandoc, and Chrome or Chromium. No Python packages beyond the standard
library.

    python scripts/report_to_pdf.py                  # REPORT.md -> REPORT.pdf
    python scripts/report_to_pdf.py REPORT.md -o out/report.pdf
    python scripts/report_to_pdf.py --html-only      # just write the HTML, to check it in a browser
    CHROME=/path/to/chrome python scripts/report_to_pdf.py

Generated PDFs and HTML are git-ignored (see .gitignore); attach the PDF to the
submission form rather than committing it.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CSS = """
@page { size: A4; margin: 2.2cm 2.2cm 2.4cm 2.2cm; }
html { font-size: 10.5pt; }
body {
  font-family: "Charter", "Georgia", "Times New Roman", serif;
  line-height: 1.4; color: #111; max-width: none; margin: 0;
}
h1, h2, h3, h4 { font-family: "Helvetica Neue", "Arial", sans-serif; line-height: 1.25; break-after: avoid; }
h1 { font-size: 1.7rem; text-align: center; margin: 0 0 0.8rem; }
h2 { font-size: 1.25rem; margin: 1.4rem 0 0.5rem; }
h3 { font-size: 1.08rem; margin: 1.1rem 0 0.4rem; }
h4 { font-size: 1rem; margin: 0.9rem 0 0.3rem; }
p { margin: 0.45rem 0; text-align: justify; hyphens: auto; }
ul, ol { margin: 0.4rem 0; padding-left: 1.4rem; }
li { margin: 0.15rem 0; }
table { border-collapse: collapse; width: 100%; margin: 0.8rem 0; font-size: 0.86rem; break-inside: avoid; }
th, td { border-top: 1px solid #bbb; border-bottom: 1px solid #bbb; padding: 0.25rem 0.4rem; text-align: left; vertical-align: top; }
thead th { border-bottom: 1.5px solid #333; }
code { font-family: "Menlo", "Consolas", monospace; font-size: 0.88em; }
pre { background: #f5f5f5; padding: 0.5rem; overflow-x: auto; font-size: 0.82rem; }
img, figure { max-width: 100%; break-inside: avoid; }
figcaption { font-size: 0.88rem; color: #333; text-align: center; }
a { color: #1a4fa0; text-decoration: none; }
blockquote { margin: 0.5rem 1rem; color: #333; }
.footnotes { font-size: 0.85rem; }
"""

CHROME_CANDIDATES = [
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]


def find_chrome() -> str:
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    # Playwright's headless shell first: it is made for printing and exits cleanly
    # in containers where full Chrome can hang.
    for base in [Path("/opt/pw-browsers"), Path.home() / ".cache/ms-playwright",
                 Path.home() / "Library/Caches/ms-playwright"]:
        for p in sorted(base.glob("chromium_headless_shell-*/chrome-*/chrome-headless-shell"), reverse=True):
            return str(p)
    for c in CHROME_CANDIDATES:
        path = shutil.which(c) or (c if os.path.isfile(c) else None)
        if path:
            return path
    sys.exit("No Chrome or Chromium found. Install one, or set CHROME=/path/to/chrome.")


def strip_comments(md: str) -> str:
    """Drop HTML comments, and list items or lines left empty by doing so."""
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    md = re.sub(r"(?m)^\s*(?:\d+\.|[-*])\s*$\n?", "", md)  # empty list items
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md


def to_html(md_path: Path, html_path: Path, keep_comments: bool) -> None:
    md = md_path.read_text(encoding="utf-8")
    if not keep_comments:
        md = strip_comments(md)
    title_match = re.search(r"(?m)^# (.+)$", md)
    title = title_match.group(1).strip() if title_match else md_path.stem
    with tempfile.TemporaryDirectory() as tmp:
        css_file = Path(tmp) / "report.css"
        css_file.write_text(CSS, encoding="utf-8")
        src = Path(tmp) / "report.md"
        src.write_text(md, encoding="utf-8")
        subprocess.run(
            ["pandoc", str(src), "--from", "gfm+footnotes", "--to", "html5",
             "--standalone", "--embed-resources", "--css", str(css_file),
             "--metadata", f"pagetitle={title}",
             "--resource-path", str(md_path.parent.resolve()),
             "--output", str(html_path)],
            check=True,
        )


def to_pdf(html_path: Path, pdf_path: Path) -> None:
    chrome = find_chrome()
    with tempfile.TemporaryDirectory() as profile:
        cmd = [chrome, "--headless", "--no-sandbox", "--disable-gpu", "--no-first-run",
               "--no-default-browser-check", f"--user-data-dir={profile}",
               "--no-pdf-header-footer", "--print-to-pdf-no-header",
               f"--print-to-pdf={pdf_path.resolve()}", html_path.resolve().as_uri()]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
        except subprocess.TimeoutExpired:
            sys.exit(f"{chrome} did not finish within 90 s. Try another browser with CHROME=..., "
                     "or use --html-only and print the HTML to PDF from a browser.")
    if not pdf_path.exists():
        sys.exit(f"Chrome ran but wrote no PDF ({chrome}).")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", nargs="?", default="REPORT.md", type=Path)
    ap.add_argument("-o", "--output", type=Path, help="PDF path (default: input with .pdf)")
    ap.add_argument("--html-only", action="store_true", help="write the HTML next to the PDF path and stop")
    ap.add_argument("--keep-comments", action="store_true", help="keep HTML comments (they stay invisible)")
    args = ap.parse_args()

    if not shutil.which("pandoc"):
        sys.exit("pandoc is not installed (e.g. `brew install pandoc` or `apt install pandoc`).")
    pdf = args.output or args.input.with_suffix(".pdf")
    pdf.parent.mkdir(parents=True, exist_ok=True)
    html = pdf.with_suffix(".html")
    to_html(args.input, html, args.keep_comments)
    if args.html_only:
        print(f"Wrote {html}")
        return
    to_pdf(html, pdf)
    html.unlink()
    print(f"Wrote {pdf} ({pdf.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
