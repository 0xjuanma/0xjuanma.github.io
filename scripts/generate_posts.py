#!/usr/bin/env python3
"""
Scans posts/*.html, sorts by numeric prefix (descending = newest first),
takes up to MAX_POSTS, and patches the <!-- posts:start/end --> block in
index.html.

Post HTML files should include:
  <title>Post Title</title>
  <meta name="date" content="YYYY-MM-DD">          (required for date display)
  <meta name="description" content="Short teaser"> (optional; shown on expand)

If no posts are found, the section is removed (markers remain as injection point).
"""
import re
import sys
from pathlib import Path
from datetime import datetime

REPO_ROOT    = Path(__file__).resolve().parent.parent
POSTS_DIR    = REPO_ROOT / "posts"
INDEX_HTML   = REPO_ROOT / "index.html"
MAX_POSTS    = 3

START_MARKER = "        <!-- posts:start -->"
END_MARKER   = "        <!-- posts:end -->"

_TITLE_RE = re.compile(r"<title>([^<]+)</title>", re.I)
_DATE_RE  = re.compile(r'<meta\s+name=["\']date["\']\s+content=["\']([^"\']+)["\']', re.I)
_DESC_RE  = re.compile(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']', re.I)


def numeric_prefix(p: Path) -> int:
    m = re.match(r"^(\d+)", p.stem)
    return int(m.group(1)) if m else 0


def parse_post(path: Path) -> dict:
    text    = path.read_text(encoding="utf-8")
    title_m = _TITLE_RE.search(text)
    title   = title_m.group(1).strip() if title_m else path.stem
    date_m  = _DATE_RE.search(text)
    dt      = (datetime.strptime(date_m.group(1), "%Y-%m-%d") if date_m
               else datetime.fromtimestamp(path.stat().st_mtime))
    desc_m  = _DESC_RE.search(text)
    tagline = desc_m.group(1).strip() if desc_m else None
    return {"path": path, "title": title, "dt": dt, "tagline": tagline}


def fmt_date(dt: datetime) -> str:
    return dt.strftime("%b %Y")


_CHEVRON = (
    '<svg class="post-chevron" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2" aria-hidden="true">'
    '<polyline points="6 9 12 15 18 9"></polyline></svg>'
)
_LINK_ARROW = (
    '<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
    '<path d="M14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z'
    'm-2 16H5V5h7V3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2v-7h-2v7h-7z"/>'
    '</svg>'
)


def build_row(post: dict) -> str:
    rel     = f"posts/{post['path'].name}"
    title   = post["title"]
    tagline = post["tagline"]

    tagline_html = (
        f'                        <p class="post-tagline">{tagline}</p>\n'
        if tagline else ""
    )
    return (
        f'            <details class="post-row">\n'
        f'                <summary class="post-summary"'
        f' aria-label="{title} \u2014 expand for summary">\n'
        f'                    <span class="post-date">{fmt_date(post["dt"])}</span>\n'
        f'                    <span class="post-title">{title}</span>\n'
        f'                    {_CHEVRON}\n'
        f'                </summary>\n'
        f'                <div class="post-body">\n'
        f'                    <div class="post-body-inner">\n'
        f'{tagline_html}'
        f'                        <a href="{rel}" class="post-link"'
        f' aria-label="Read {title}">\n'
        f'                            Read post\n'
        f'                            {_LINK_ARROW}\n'
        f'                        </a>\n'
        f'                    </div>\n'
        f'                </div>\n'
        f'            </details>'
    )


def build_section(rows: list) -> str:
    return (
        '        <section class="posts-section" aria-labelledby="posts-heading">\n'
        '            <h2 class="posts-title" id="posts-heading">Posts</h2>\n\n'
        + "\n\n".join(rows) + "\n"
        '        </section>'
    )


def main():
    posts = sorted(
        [parse_post(p) for p in POSTS_DIR.glob("*.html")],
        key=lambda x: numeric_prefix(x["path"]),
        reverse=True,
    )[:MAX_POSTS]

    html    = INDEX_HTML.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
        re.DOTALL,
    )

    if not posts:
        replacement = f"{START_MARKER}\n{END_MARKER}"
    else:
        section     = build_section([build_row(p) for p in posts])
        replacement = f"{START_MARKER}\n{section}\n{END_MARKER}"

    patched = pattern.sub(replacement, html)
    if patched == html:
        print("No changes — index.html already up to date.")
        sys.exit(0)

    INDEX_HTML.write_text(patched, encoding="utf-8")
    print(f"index.html patched — {len(posts)} post(s) listed.")


if __name__ == "__main__":
    main()
