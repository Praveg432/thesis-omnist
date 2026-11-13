#!/usr/bin/env python3
"""Render a Markdown file to a print-quality PDF via styled HTML + headless Chrome.

Usage: md_to_pdf.py <input.md> <output.pdf> [--title "Doc Title"]

Standalone utility: no business logic, pure document conversion. Kept simple and
explicit so the output is reproducible and the styling is auditable.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import markdown  # provided by the local .pdfvenv

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Print stylesheet aligned to the IIT Patna thesis-manual spirit:
# serif body (Times-like), A4, 1-inch-ish margins, 1.15 line spacing for
# on-screen readability, clean bordered tables, no page-breaking inside tables.
CSS = """
@page { size: A4; margin: 2.2cm 2.0cm 2.2cm 2.5cm; }
* { box-sizing: border-box; }
body {
  font-family: "Times New Roman", Georgia, serif;
  font-size: 11.5pt; line-height: 1.5; color: #111; margin: 0;
}
h1 { font-size: 18pt; text-align: center; line-height: 1.3; margin: 0 0 0.3em; }
h2 { font-size: 14pt; border-bottom: 1.5px solid #333; padding-bottom: 3px;
     margin: 1.4em 0 0.5em; page-break-after: avoid; }
h3 { font-size: 12.5pt; margin: 1.1em 0 0.4em; page-break-after: avoid; }
h4 { font-size: 11.5pt; margin: 0.9em 0 0.3em; page-break-after: avoid; }
p, li { text-align: justify; }
table {
  border-collapse: collapse; width: 100%; margin: 0.8em 0;
  font-size: 10pt; page-break-inside: avoid;
}
th, td { border: 1px solid #999; padding: 5px 8px; text-align: left; vertical-align: top; }
th { background: #f0f0f0; font-weight: bold; }
code { font-family: "SFMono-Regular", Menlo, Consolas, monospace; font-size: 9.5pt;
       background: #f5f5f5; padding: 1px 3px; border-radius: 3px; }
pre { background: #f5f5f5; border: 1px solid #ddd; border-radius: 4px; padding: 10px;
      overflow-x: auto; font-size: 9pt; line-height: 1.35; page-break-inside: avoid; }
pre code { background: none; padding: 0; }
blockquote { border-left: 3px solid #bbb; margin: 0.8em 0; padding: 0.2em 0 0.2em 1em;
             color: #333; background: #fafafa; }
hr { border: none; border-top: 1px solid #ccc; margin: 1.6em 0; }
a { color: #0b4; text-decoration: none; }
strong { font-weight: bold; }
h2, h3, table, pre, blockquote { page-break-inside: avoid; }
"""

HTML_SHELL = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{title}</title>
<style>{css}</style></head><body>{body}</body></html>"""


def convert(md_path: Path, pdf_path: Path, title: str) -> None:
    text = md_path.read_text(encoding="utf-8")
    body = markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "toc", "sane_lists", "attr_list"],
    )
    html = HTML_SHELL.format(title=title, css=CSS, body=body)
    html_path = pdf_path.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")

    result = subprocess.run(
        [
            CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri(),
        ],
        capture_output=True, text=True, timeout=120,
    )
    if not pdf_path.exists():
        sys.stderr.write(result.stdout + result.stderr)
        raise SystemExit(f"PDF not produced: {pdf_path}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--title", default="Document")
    args = ap.parse_args()
    convert(Path(args.input), Path(args.output), args.title)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
