#!/usr/bin/env python3
"""Build the blog library from structured hub and article metadata."""

from __future__ import annotations

import html
import json
import math
from html.parser import HTMLParser
from pathlib import Path

from build_content_hubs import footer, header


ROOT = Path(__file__).resolve().parents[1] / "FlitKey HP"


class VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.words: list[str] = []
        self.suppressed = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "nav", "footer"}:
            self.suppressed += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "nav", "footer"} and self.suppressed:
            self.suppressed -= 1

    def handle_data(self, data: str) -> None:
        if not self.suppressed:
            self.words.extend(data.split())


HUBS = [
    ("/blogs/linux-text-expansion/", "LINUX", "Linux & Wayland", "Choose and troubleshoot text expansion across X11, Wayland, GNOME, KDE Plasma, and Hyprland."),
    ("/blogs/windows-text-expansion/", "WIN", "Windows", "Compare visual snippets, Windows automation, local storage, installer trust, and application behavior."),
    ("/blogs/migrations/", "MOVE", "Migrations", "Move supported snippets in reversible batches without pretending every script, form, or macro converts."),
    ("/blogs/comparisons/", "VS", "Comparisons", "Choose between FlitKey and established tools using platform, workflow, data, and maintenance requirements."),
    ("/blogs/snippet-templates/", "{…}", "Snippet packs", "Review reusable developer, support, sysadmin, productivity, and AI prompt examples before loading them."),
    ("/blogs/privacy-security/", "LOCK", "Privacy & security", "Understand keyboard access, local files, clipboard exposure, backups, and compliance boundaries."),
]


ARTICLES = [
    {
        "path": "wayland-text-expander.html", "url": "/wayland-text-expander", "badge": "Platform guide",
        "title": "Text Expanders on Wayland: What Actually Works in 2026",
        "summary": "Understand the X11 and Wayland capability difference, then test FlitKey's supported picker-and-clipboard workflow on the desktop you actually use.",
        "categories": ("linux",), "pills": ("Wayland limits", "X11 workflow", "GNOME, KDE & Hyprland"), "published": "July 25, 2026",
    },
    {
        "path": "espanso-migration-guide.html", "url": "/espanso-migration-guide", "badge": "Migration guide",
        "title": "How to Import Espanso YAML Snippets into FlitKey",
        "summary": "Back up both libraries, import supported static matches, review warnings, test real applications, and retain unsupported Espanso automation.",
        "categories": ("linux", "migration"), "pills": ("Supported YAML", "Rollback", "Unsupported cases"), "published": "July 27, 2026",
    },
    {
        "path": "blogs/comparisons/espanso-vs-flitkey/index.html", "url": "/espanso-vs-flitkey/", "badge": "Comparison",
        "title": "FlitKey vs Espanso: Visual GUI or YAML Workflow?",
        "summary": "Compare visual snippet management with Espanso's configurable workflow, including automation depth, migration boundaries, and Wayland behavior.",
        "categories": ("comparison", "linux"), "pills": ("Visual vs YAML", "Static import", "Choose Espanso when…"), "published": "July 27, 2026",
    },
    {
        "path": "blogs/comparisons/autohotkey-vs-flitkey/index.html", "url": "/autohotkey-vs-flitkey/", "badge": "Comparison",
        "title": "FlitKey vs AutoHotkey: Visual Snippets or Windows Automation?",
        "summary": "Separate plain hotstrings from executable Windows automation before deciding whether a focused visual snippet manager can replace part of a script.",
        "categories": ("comparison", "windows", "migration"), "pills": ("Hotstrings", "Windows automation", "Safe conversion"), "published": "July 27, 2026",
    },
    {
        "path": "blogs/comparisons/textexpander-vs-flitkey/index.html", "url": "/textexpander-vs-flitkey/", "badge": "Comparison",
        "title": "FlitKey vs TextExpander: Local Utility or Sync Service?",
        "summary": "Compare a local individual desktop utility with an account-based service offering synchronized and organizational workflows.",
        "categories": ("comparison", "windows", "privacy"), "pills": ("Local files", "Sync & teams", "Current vendor sources"), "published": "July 27, 2026",
    },
    {
        "path": "blogs/comparisons/atext-vs-flitkey/index.html", "url": "/atext-vs-flitkey/", "badge": "Comparison",
        "title": "FlitKey vs aText: Windows and Linux Comparison",
        "summary": "Compare two visual editing workflows by platform, content complexity, storage, migration risk, and the features that should keep users on aText.",
        "categories": ("comparison", "windows", "linux", "migration"), "pills": ("Visual editing", "CSV migration", "Platform fit"), "published": "July 27, 2026",
    },
    {
        "path": "blogs/comparisons/phraseexpress-vs-flitkey/index.html", "url": "/phraseexpress-vs-flitkey/", "badge": "Comparison",
        "title": "PhraseExpress vs FlitKey: Linux and Windows Fit",
        "summary": "Decide whether advanced commercial automation and team capabilities or a smaller local open-source snippet workflow better fits the job.",
        "categories": ("comparison", "windows", "linux", "migration"), "pills": ("Automation depth", "Team requirements", "Migration limits"), "published": "August 3, 2026",
    },
]


FILTERS = (
    ("all", "All"),
    ("comparison", "Comparisons"),
    ("linux", "Linux & Wayland"),
    ("windows", "Windows"),
    ("migration", "Migrations"),
    ("privacy", "Privacy"),
)


def reading_minutes(relative_path: str) -> int:
    parser = VisibleText()
    parser.feed((ROOT / relative_path).read_text(encoding="utf-8"))
    return max(1, math.ceil(len(parser.words) / 225))


def render_hubs() -> str:
    return "".join(
        f'<a class="topic-hub-card" href="{url}"><span class="topic-hub-icon" aria-hidden="true">{html.escape(icon)}</span><span class="topic-hub-copy"><strong>{html.escape(title)}</strong><span>{html.escape(description)}</span></span><span class="topic-hub-arrow" aria-hidden="true">&rarr;</span></a>'
        for url, icon, title, description in HUBS
    )


def render_articles() -> str:
    cards = []
    for article in ARTICLES:
        minutes = reading_minutes(article["path"])
        categories = " ".join(article["categories"])
        pills = "".join(f'<span class="blog-pill">{html.escape(pill)}</span>' for pill in article["pills"])
        search = " ".join((article["title"], article["summary"], *article["pills"], *article["categories"]))
        cards.append(
            f'<a class="blog-card" data-category="{categories}" data-search="{html.escape(search.lower(), quote=True)}" href="{article["url"]}">'
            f'<div class="blog-card-header"><span class="blog-badge">{html.escape(article["badge"])}</span><span class="blog-read-time">{minutes} min read</span></div>'
            f'<h3 class="blog-card-title">{html.escape(article["title"])}</h3><p class="blog-card-snippet">{html.escape(article["summary"])}</p>'
            f'<div class="blog-card-highlights">{pills}</div><div class="blog-card-footer"><span class="blog-author">Updated Aug 3, 2026</span>'
            f'<span class="blog-link-btn">Read article <span aria-hidden="true">&rarr;</span></span></div></a>'
        )
    return "".join(cards)


def build() -> str:
    canonical = "https://flitkey.xyz/blogs"
    def filter_count(key: str) -> int:
        if key == "all":
            return len(ARTICLES)
        return sum(key in article["categories"] for article in ARTICLES)

    filters = "".join(
        f'<button class="article-filter{" is-active" if key == "all" else ""}" type="button" data-filter="{key}" aria-controls="blog-grid" aria-pressed="{"true" if key == "all" else "false"}">{html.escape(label)} <span>{filter_count(key)}</span></button>'
        for key, label in FILTERS
    )
    blog_posts = []
    for article in ARTICLES:
        published = "2026-07-27"
        if article["path"] == "wayland-text-expander.html":
            published = "2026-07-25"
        elif "phraseexpress-vs-flitkey" in article["path"]:
            published = "2026-08-03"
        blog_posts.append({"@type": "BlogPosting", "headline": article["title"], "url": f'https://flitkey.xyz{article["url"]}', "datePublished": published, "dateModified": "2026-08-03"})
    schema = json.dumps({"@context": "https://schema.org", "@graph": [
        {"@type": "Blog", "@id": f"{canonical}#blog", "name": "FlitKey Blog & Technical Guides", "url": canonical, "description": "Evidence-led platform guides, migration walkthroughs, and software comparisons for desktop text expansion tools.", "blogPost": blog_posts},
        {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://flitkey.xyz/"}, {"@type": "ListItem", "position": 2, "name": "Blog", "item": canonical}]},
    ]}, separators=(",", ":"))
    return f'''<!doctype html><html lang="en" data-theme="light" data-accent="signal-red"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FlitKey Blog: Desktop Text Expander Guides and Comparisons</title><meta name="description" content="Evidence-led text expansion guides for Linux and Windows: Wayland behavior, migration instructions, product comparisons, privacy, and reusable snippets."><meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large"><link rel="canonical" href="{canonical}"><link rel="icon" href="../favicon.ico"><link rel="manifest" href="../site.webmanifest"><link rel="stylesheet" href="../styles.css"><meta property="og:type" content="website"><meta property="og:url" content="{canonical}"><meta property="og:title" content="FlitKey Blog & Technical Guides"><meta property="og:description" content="Evidence-led comparisons, migration walkthroughs, privacy guidance, and practical Windows, Linux, X11, and Wayland documentation."><meta property="og:image" content="https://flitkey.xyz/og-image.png"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="FlitKey Blog & Technical Guides"><meta name="twitter:description" content="Practical desktop text-expansion guides with explicit methods and limitations."><meta name="twitter:image" content="https://flitkey.xyz/og-image.png"><script type="application/ld+json">{schema}</script></head><body class="docs-body">{header()}<main class="blog-index-shell"><section class="blog-index-hero" aria-labelledby="blog-title"><span class="section-tag">FLITKEY FIELD GUIDES</span><h1 id="blog-title">Solve a text-expansion problem</h1><p>Choose a platform, migration path, or product decision. Every article leads with the answer, names its limitations, and links to the next useful step.</p><div class="blog-index-summary"><span><strong>{len(ARTICLES)}</strong> in-depth articles</span><span><strong>{len(HUBS)}</strong> topic hubs</span><span>Updated August 3, 2026</span></div></section><section class="blog-library-section" aria-labelledby="topic-heading"><div class="blog-section-heading"><span class="section-tag">BROWSE BY TOPIC</span><h2 id="topic-heading">Start with your goal</h2><p>Topic hubs organize the articles and supporting documentation into a guided path.</p></div><div class="topic-hub-grid">{render_hubs()}</div></section><section class="blog-library-section" aria-labelledby="article-heading"><div class="blog-section-heading"><span class="section-tag">ARTICLE LIBRARY</span><h2 id="article-heading">All published articles</h2><p id="article-results" aria-live="polite">Showing all {len(ARTICLES)} articles</p></div><div class="article-library-controls"><div class="article-filter-group" role="group" aria-label="Filter articles by topic">{filters}</div><div class="article-search"><label class="sr-only" for="blog-search">Search articles</label><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.35-4.35"></path></svg><input id="blog-search" type="search" placeholder="Search titles, tools, or workflows" autocomplete="off"><button id="blog-search-clear" type="button" hidden aria-label="Clear article search">&times;</button></div></div><div class="blog-empty-state" id="blog-empty-state" hidden><strong>No matching articles</strong><p>Try another topic or clear the search.</p><button class="btn btn-secondary" id="blog-reset" type="button">Show all articles</button></div><div class="blog-grid" id="blog-grid">{render_articles()}</div></section></main>{footer()}<script src="../script.js"></script><script>
(() => {{
  const cards = [...document.querySelectorAll('#blog-grid .blog-card')];
  const filters = [...document.querySelectorAll('.article-filter')];
  const search = document.getElementById('blog-search');
  const clear = document.getElementById('blog-search-clear');
  const reset = document.getElementById('blog-reset');
  const empty = document.getElementById('blog-empty-state');
  const results = document.getElementById('article-results');
  const params = new URLSearchParams(window.location.search);
  const requestedFilter = params.get('topic');
  const validFilters = new Set(filters.map(button => button.dataset.filter));
  let activeFilter = validFilters.has(requestedFilter) ? requestedFilter : 'all';
  search.value = params.get('q') || '';
  filters.forEach(item => {{
    const active = item.dataset.filter === activeFilter;
    item.classList.toggle('is-active', active);
    item.setAttribute('aria-pressed', String(active));
  }});
  function syncUrl(query) {{
    const next = new URLSearchParams();
    if (activeFilter !== 'all') next.set('topic', activeFilter);
    if (query) next.set('q', query);
    const suffix = next.toString();
    history.replaceState(null, '', window.location.pathname + (suffix ? '?' + suffix : ''));
  }}
  function applyFilters() {{
    const query = search.value.toLowerCase().trim();
    let visible = 0;
    cards.forEach(card => {{
      const categories = (card.dataset.category || '').split(/\\s+/);
      const matchesFilter = activeFilter === 'all' || categories.includes(activeFilter);
      const matchesSearch = !query || (card.dataset.search || '').includes(query);
      card.hidden = !(matchesFilter && matchesSearch);
      if (!card.hidden) visible += 1;
    }});
    const context = activeFilter === 'all' && !query ? 'all ' + cards.length : visible + ' of ' + cards.length;
    results.textContent = 'Showing ' + context + ' article' + (visible === 1 ? '' : 's');
    empty.hidden = visible !== 0;
    clear.hidden = !query;
    syncUrl(query);
  }}
  function selectFilter(button) {{
    activeFilter = button.dataset.filter;
    filters.forEach(item => {{
      const active = item === button;
      item.classList.toggle('is-active', active);
      item.setAttribute('aria-pressed', String(active));
    }});
    applyFilters();
  }}
  filters.forEach(button => button.addEventListener('click', () => selectFilter(button)));
  search.addEventListener('input', applyFilters);
  search.addEventListener('keydown', event => {{
    if (event.key === 'Escape' && search.value) {{ search.value = ''; applyFilters(); }}
  }});
  clear.addEventListener('click', () => {{ search.value = ''; search.focus(); applyFilters(); }});
  reset.addEventListener('click', () => {{
    search.value = '';
    selectFilter(filters.find(button => button.dataset.filter === 'all'));
    search.focus();
  }});
  applyFilters();
}})();
</script></body></html>'''


def main() -> None:
    destination = ROOT / "blogs" / "index.html"
    destination.write_text(build(), encoding="utf-8")
    print(destination)


if __name__ == "__main__":
    main()
