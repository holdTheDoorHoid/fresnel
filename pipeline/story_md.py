"""Story Markdown -> safe HTML, with an in-page chapter list (DESIGN.md section 5).

Copied from Firefinder's pipeline/build_site_data.py (the same small, safe subset) and given
chapters: a story's `## ` headings are its chapters (The place, Building the light, The keepers,
...). `markdown_to_html()` gives each heading an id ("s-the-keepers"), and `chapters_of()`
lists the `## ` headings in order, so the page can show "In this history" links above the story.

Python 3.12, standard library only.
"""
from __future__ import annotations

import html
import re
from collections import Counter

# ---------------------------------------------------------------------------------------
# Markdown (a small, safe subset) -> HTML
# ---------------------------------------------------------------------------------------

_SAFE_SCHEMES = ("http", "https", "mailto")


def safe_href(url: str) -> str | None:
    """Return the URL if it is http(s), mailto, relative or a #fragment; else None."""
    url = url.strip()
    if not url:
        return None
    probe = re.sub(r"[\x00-\x20\x7f]+", "", url).lower()
    m = re.match(r"^([a-z][a-z0-9+.-]*):", probe)
    if m:
        return url if m.group(1) in _SAFE_SCHEMES else None
    return url


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


_FN_LABEL_RE = re.compile(r"[^a-z0-9-]+")


def _fn_slug(label: str) -> str:
    return _FN_LABEL_RE.sub("-", label.lower()).strip("-") or "note"


_EMPHASIS = [
    (re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*"), r"<strong>\1</strong>"),
    (re.compile(r"__(?=\S)(.+?)(?<=\S)__"), r"<strong>\1</strong>"),
    (re.compile(r"(?<![\w*])\*(?=\S)(.+?)(?<=\S)\*(?![\w*])"), r"<em>\1</em>"),
    (re.compile(r"(?<![\w_])_(?=\S)(.+?)(?<=\S)_(?![\w_])"), r"<em>\1</em>"),
]


def _emphasis(escaped: str) -> str:
    for pattern, repl in _EMPHASIS:
        escaped = pattern.sub(repl, escaped)
    return escaped


_INLINE_RE = re.compile(
    r"`(?P<code>[^`]+)`"
    r"|\[\^(?P<fn>[^\]\s]+)\]"
    r"|\[(?P<text>[^\]]+)\]\((?P<url>[^)\s]+)(?:\s+\"[^\"]*\")?\)"
    r"|<(?P<auto>https?://[^>\s]+)>"
    # a bare URL, as research footnotes write them; trailing punctuation stays outside
    r"|(?P<bare>https?://[^\s<>\"]*[^\s<>\".,;:!?)\]'])"
)

# External links in stories open in the same tab but pass no referrer or window handle.
EXTERNAL_REL = "noopener noreferrer"


def _link(href: str, label: str) -> str:
    rel = f' rel="{EXTERNAL_REL}"' if href.lower().startswith(("http://", "https://")) else ""
    return f'<a href="{_esc(href)}"{rel}>{label}</a>'


class _Notes:
    """Footnote numbering in order of first reference."""

    def __init__(self, definitions: dict[str, str]) -> None:
        self.definitions = definitions
        self.order: list[str] = []
        self.ref_counts: Counter[str] = Counter()

    def ref(self, label: str) -> str:
        if label not in self.definitions:
            return _esc(f"[^{label}]")
        if label not in self.order:
            self.order.append(label)
        self.ref_counts[label] += 1
        n = self.order.index(label) + 1
        slug = _fn_slug(label)
        count = self.ref_counts[label]
        ref_id = f"fnref-{slug}" + (f"-{count}" if count > 1 else "")
        return f'<sup id="{ref_id}" class="fnref"><a href="#fn-{slug}" aria-label="Note {n}">{n}</a></sup>'


def _inline(text: str, notes: _Notes | None, allow_links: bool = True) -> str:
    out: list[str] = []
    pos = 0
    last_fn_end = -1
    for m in _INLINE_RE.finditer(text):
        out.append(_emphasis(_esc(text[pos : m.start()])))
        pos = m.end()
        if m.group("code") is not None:
            out.append(f"<code>{_esc(m.group('code'))}</code>")
        elif m.group("fn") is not None:
            if notes and last_fn_end == m.start() and m.group("fn") in notes.definitions:
                out.append('<sup class="fnsep">,</sup>')  # "[^3][^1]" reads 3,1 and not 31
            out.append(notes.ref(m.group("fn")) if notes else _esc(m.group(0)))
            last_fn_end = m.end()
        elif m.group("text") is not None:
            label = _inline(m.group("text"), None, allow_links=False)
            href = safe_href(m.group("url")) if allow_links else None
            out.append(_link(href, label) if href else label)
        else:
            href = m.group("auto") or m.group("bare")
            out.append(_link(href, _esc(href)) if allow_links else _esc(href))
    out.append(_emphasis(_esc(text[pos:])))
    return "".join(out)


_FRONT_MATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.S)
_FN_DEF_RE = re.compile(r"^\[\^([^\]\s]+)\]:\s?(.*)$")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_HR_RE = re.compile(r"^(?:-{3,}|\*{3,}|_{3,})\s*$")
_UL_RE = re.compile(r"^[-*+]\s+(.*)$")
_OL_RE = re.compile(r"^\d{1,3}[.)]\s+(.*)$")


def _plain(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def markdown_to_html(md: str, title: str | None = None) -> str:
    """Convert story Markdown to HTML.

    Supports paragraphs, # headings (shifted down one level: the page title is the h1),
    *emphasis*, **strong**, `code`, [links](https://...), <https://autolinks>, "-" and "1."
    lists, > blockquotes, --- rules and footnotes ([^1] with "[^1]: text" definitions).
    Everything else, including any raw HTML, is escaped and shown as text. Links keep only
    http(s), mailto, relative and #fragment URLs.
    """
    text = md.replace("\r\n", "\n").replace("\r", "\n")
    text = _FRONT_MATTER_RE.sub("", text, count=1)
    # A first line "# <the lookout's name>" repeats the page's own h1: drop it.
    first = re.match(r"\A\s*#(?!#)\s*([^\n]*)\n", text)
    if first and title and _plain(first.group(1)) and _plain(first.group(1)) in _plain(title):
        text = text[first.end():]
    lines = text.split("\n")

    # 1. Pull out footnote definitions (with indented continuation lines).
    definitions: dict[str, str] = {}
    body: list[str] = []
    i = 0
    while i < len(lines):
        m = _FN_DEF_RE.match(lines[i])
        if m:
            label, content = m.group(1), [m.group(2)]
            i += 1
            while i < len(lines) and (lines[i].startswith("    ") or lines[i].startswith("\t")):
                content.append(lines[i].strip())
                i += 1
            definitions.setdefault(label, " ".join(c for c in content if c))
            continue
        body.append(lines[i])
        i += 1

    notes = _Notes(definitions)
    out: list[str] = []

    # 2. Blocks.
    para: list[str] = []
    list_kind: str | None = None
    list_items: list[str] = []
    quote: list[str] = []

    def flush_para() -> None:
        if para:
            out.append(f"<p>{_inline(' '.join(s.strip() for s in para), notes)}</p>")
            para.clear()

    def flush_list() -> None:
        nonlocal list_kind
        if list_kind:
            items = "".join(f"<li>{_inline(it, notes)}</li>" for it in list_items)
            out.append(f"<{list_kind}>{items}</{list_kind}>")
            list_items.clear()
            list_kind = None

    def flush_quote() -> None:
        if quote:
            inner = " ".join(s.strip() for s in quote if s.strip())
            out.append(f"<blockquote><p>{_inline(inner, notes)}</p></blockquote>")
            quote.clear()

    def flush_all() -> None:
        flush_para()
        flush_list()
        flush_quote()

    for line in body:
        stripped = line.strip()
        if not stripped:
            flush_all()
            continue
        if stripped.startswith(">"):
            flush_para()
            flush_list()
            quote.append(stripped[1:])
            continue
        flush_quote()
        h = _HEADING_RE.match(stripped)
        if h:
            flush_all()
            level = min(len(h.group(1)) + 1, 4)
            content = _inline(h.group(2), notes)
            slug = _fn_slug(re.sub(r"<[^>]+>", "", h.group(2)))[:60]
            out.append(f'<h{level} id="s-{slug}">{content}</h{level}>')
            continue
        if _HR_RE.match(stripped):
            flush_all()
            out.append("<hr>")
            continue
        ul, ol = _UL_RE.match(stripped), _OL_RE.match(stripped)
        if ul or ol:
            flush_para()
            kind = "ul" if ul else "ol"
            if list_kind and list_kind != kind:
                flush_list()
            list_kind = kind
            list_items.append((ul or ol).group(1))  # type: ignore[union-attr]
            continue
        if list_kind and line.startswith(("  ", "\t")):
            list_items[-1] += " " + stripped
            continue
        flush_list()
        para.append(stripped)
    flush_all()

    # 3. Footnotes: referenced ones in order of first use, then any never referenced.
    labels = notes.order + [label for label in definitions if label not in notes.order]
    if labels:
        items = []
        for label in labels:
            slug = _fn_slug(label)
            content = _inline(definitions[label], None)
            back = ""
            if label in notes.order:
                back = f' <a href="#fnref-{slug}" class="fn-back" aria-label="Back to the text">↩</a>'
            items.append(f'<li id="fn-{slug}">{content}{back}</li>')
        out.append(
            '<section class="footnotes" aria-label="Notes and sources"><ol>' + "".join(items) + "</ol></section>"
        )
    return "\n".join(out)


# ---------------------------------------------------------------------------------------


def chapters_of(md: str) -> list[dict]:
    """The story's chapters: every `## ` heading, in order, as {"id", "title"} with the same id
    markdown_to_html() gives it (title as plain text, Markdown emphasis removed)."""
    text = _FRONT_MATTER_RE.sub("", md.replace("\r\n", "\n").replace("\r", "\n"), count=1)
    out: list[dict] = []
    seen: Counter[str] = Counter()
    for line in text.split("\n"):
        h = _HEADING_RE.match(line.strip())
        if not h or len(h.group(1)) != 2:
            continue
        raw = h.group(2)
        slug = _fn_slug(re.sub(r"<[^>]+>", "", _inline(raw, None)))[:60]
        seen[slug] += 1
        if seen[slug] > 1:
            continue  # a repeated heading links to its first use
        title = re.sub(r"[*_`]", "", re.sub(r"\[\^[^\]]+\]", "", raw)).strip()
        out.append({"id": f"s-{slug}", "title": title})
    return out
