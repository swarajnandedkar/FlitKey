#!/usr/bin/env python3
"""Fail on broken local links, invalid JSON-LD, and high-risk marketing claims."""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree


SITE = Path(sys.argv[1] if len(sys.argv) > 1 else "FlitKey HP").resolve()
BANNED = {
    "unsupported compliance claim": re.compile(r"(?:hipaa|gdpr) compliant|complete hipaa|fully compliant", re.I),
    "unsupported performance claim": re.compile(r"(?:~\s*\d+\s*MB RAM|under \d+ milliseconds|zero latency)", re.I),
    "unsupported Wayland claim": re.compile(r"(?:native Wayland input|full native Wayland|Wayland Native)", re.I),
    "stale release URL": re.compile(r"releases/download/v0\.[0-4]\.", re.I),
    "unsupported legacy cursor marker": re.compile(r"\$\|\$"),
    "stale TextExpander price": re.compile(r"\$(?:39\.99|119\.88)|\$40\s+to\s+\$120", re.I),
}

# Reader-visible editorial minimums. Navigation, footer, styles, and structured
# data do not count. These values mirror the approved content briefs.
WORD_TARGETS = {
    "wayland-text-expander.html": 1800,
    "espanso-migration-guide.html": 1500,
    "blogs/comparisons/espanso-vs-flitkey/index.html": 2200,
    "blogs/comparisons/autohotkey-vs-flitkey/index.html": 2000,
    "blogs/comparisons/textexpander-vs-flitkey/index.html": 2000,
    "blogs/comparisons/atext-vs-flitkey/index.html": 1800,
    "blogs/comparisons/phraseexpress-vs-flitkey/index.html": 2000,
    "blogs/index.html": 350,
    "blogs/linux-text-expansion/index.html": 550,
    "blogs/windows-text-expansion/index.html": 550,
    "blogs/migrations/index.html": 550,
    "blogs/comparisons/index.html": 550,
    "blogs/snippet-templates/index.html": 550,
    "blogs/privacy-security/index.html": 550,
}
COMPARISON_SLUGS = (
    "phraseexpress-vs-flitkey",
    "atext-vs-flitkey",
    "textexpander-vs-flitkey",
    "espanso-vs-flitkey",
    "autohotkey-vs-flitkey",
)
PUBLIC_COMPARISON_ALIASES = {f"{slug}/index.html" for slug in COMPARISON_SLUGS}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.blog_card_links: list[str] = []
        self.resources: list[str] = []
        self.ids: set[str] = set()
        self.canonical: str | None = None
        self.in_json_ld = False
        self.json_ld: list[str] = []
        self._json_buffer: list[str] = []
        self._visible_buffer: list[str] = []
        self._suppressed_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "nav", "footer"}:
            self._suppressed_depth += 1
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"] or "")
        if tag == "a" and values.get("href"):
            self.links.append(values["href"] or "")
            classes = (values.get("class") or "").split()
            if "blog-card" in classes:
                self.blog_card_links.append(values["href"] or "")
        if tag in {"img", "script"} and values.get("src"):
            self.resources.append(values["src"] or "")
        if tag == "link" and values.get("rel") in {"stylesheet", "manifest", "icon"} and values.get("href"):
            self.resources.append(values["href"] or "")
        if tag == "link" and values.get("rel") == "canonical":
            self.canonical = values.get("href")
        if tag == "script" and values.get("type") == "application/ld+json":
            self.in_json_ld = True
            self._json_buffer = []

    def handle_data(self, data: str) -> None:
        if self.in_json_ld:
            self._json_buffer.append(data)
        if not self._suppressed_depth and data.strip():
            self._visible_buffer.append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.in_json_ld:
            self.json_ld.append("".join(self._json_buffer))
            self.in_json_ld = False
        if tag in {"script", "style", "nav", "footer"} and self._suppressed_depth:
            self._suppressed_depth -= 1

    @property
    def visible_word_count(self) -> int:
        return len(" ".join(self._visible_buffer).split())


def resolve_local(page: Path, href: str) -> Path | None:
    parsed = urlparse(href)
    if parsed.scheme in {"http", "https", "mailto", "tel", "data"} or parsed.netloc:
        return None
    if not parsed.path:
        return page
    path = unquote(parsed.path)
    if path == "/":
        return SITE / "index.html"
    if path.startswith("/"):
        relative = Path(path.lstrip("/"))
    else:
        relative = page.relative_to(SITE).parent / path
    candidates = [SITE / relative]
    if path.endswith("/"):
        candidates.append(SITE / relative / "index.html")
    else:
        candidates.extend([SITE / f"{relative}.html", SITE / relative / "index.html"])
    return next((candidate.resolve() for candidate in candidates if candidate.is_file()), candidates[0].resolve())


def main() -> int:
    if not SITE.is_dir():
        print(f"site directory not found: {SITE}")
        return 2

    errors: list[str] = []
    canonicals: dict[str, Path] = {}
    pages = sorted(SITE.rglob("*.html"))
    parsed_pages: dict[Path, PageParser] = {}
    for page in pages:
        text = page.read_text(encoding="utf-8")
        parser = PageParser()
        parser.feed(text)
        parsed_pages[page.resolve()] = parser

        relative = page.relative_to(SITE).as_posix()
        if "vs-flitkey" in relative and re.search(r"<title>[^<]*benchmark", text, re.I):
            errors.append(f"{page}: comparison title claims a benchmark without a published dataset")
        if target := WORD_TARGETS.get(relative):
            if parser.visible_word_count < target:
                errors.append(
                    f"{page}: {parser.visible_word_count} visible words; editorial target is {target}"
                )
            required_markup = {
                "shared site header": '<header class="header"',
                "shared navigation links": 'id="nav-links"',
                "theme control": 'id="theme-toggle"',
                "mobile navigation control": 'id="mobile-menu-btn"',
                "download navigation CTA": "nav-cta",
                "shared stylesheet": "styles.css",
            }
            for label, fragment in required_markup.items():
                if fragment not in text:
                    errors.append(f"{page}: missing {label}")

        for index, payload in enumerate(parser.json_ld, 1):
            try:
                json.loads(payload)
            except json.JSONDecodeError as exc:
                errors.append(f"{page}: JSON-LD block {index}: {exc}")

        # Root comparison files are generated deployment aliases for the
        # clustered sources and intentionally share their canonical URL.
        if parser.canonical and relative not in PUBLIC_COMPARISON_ALIASES:
            previous = canonicals.get(parser.canonical)
            if previous and previous != page:
                errors.append(f"{page}: duplicate canonical {parser.canonical} (also {previous})")
            canonicals[parser.canonical] = page

        for label, pattern in BANNED.items():
            if match := pattern.search(text):
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{page}:{line}: {label}: {match.group(0)!r}")

    for page, parser in parsed_pages.items():
        for href in parser.links + parser.resources:
            target = resolve_local(page, href)
            if target is None:
                continue
            if not target.is_file():
                errors.append(f"{page}: broken local URL {href} -> {target}")
                continue
            fragment = unquote(urlparse(href).fragment)
            if fragment and target.suffix == ".html":
                target_parser = parsed_pages.get(target.resolve())
                if target_parser and fragment not in target_parser.ids:
                    errors.append(f"{page}: missing fragment #{fragment} in {target}")

    homepage = parsed_pages.get((SITE / "index.html").resolve())
    required_home_links = {
        "/blogs",
        "/blogs/linux-text-expansion/",
        "/blogs/windows-text-expansion/",
        "/blogs/migrations/",
        "/blogs/comparisons/",
        "/blogs/snippet-templates/",
        "/blogs/privacy-security/",
    }
    if homepage:
        missing = required_home_links.difference(homepage.links)
        for href in sorted(missing):
            errors.append(f"index.html: missing required content-hub link {href}")

    blog_index = parsed_pages.get((SITE / "blogs" / "index.html").resolve())
    expected_blog_cards = {
        "/wayland-text-expander",
        "/espanso-migration-guide",
        "/espanso-vs-flitkey/",
        "/autohotkey-vs-flitkey/",
        "/textexpander-vs-flitkey/",
        "/atext-vs-flitkey/",
        "/phraseexpress-vs-flitkey/",
    }
    expected_blog_hubs = {
        "/blogs/linux-text-expansion/",
        "/blogs/windows-text-expansion/",
        "/blogs/migrations/",
        "/blogs/comparisons/",
        "/blogs/snippet-templates/",
        "/blogs/privacy-security/",
    }
    if blog_index:
        card_links = set(blog_index.blog_card_links)
        for href in sorted(expected_blog_cards - card_links):
            errors.append(f"blogs/index.html: published article is missing a card: {href}")
        for href in sorted(card_links - expected_blog_cards):
            errors.append(f"blogs/index.html: unexpected or duplicate-source article card: {href}")
        if len(blog_index.blog_card_links) != len(card_links):
            errors.append("blogs/index.html: duplicate article cards")
        for href in sorted(expected_blog_hubs - set(blog_index.links)):
            errors.append(f"blogs/index.html: missing topic hub: {href}")
        blog_source = (SITE / "blogs" / "index.html").read_text(encoding="utf-8")
        for stale in ("1-Click", "benchmark", "Free Lifetime", "100% Local Storage"):
            if stale.lower() in blog_source.lower():
                errors.append(f"blogs/index.html: stale card language: {stale}")
        for control in ('id="blog-search"', 'id="blog-empty-state"', 'id="article-results"', 'data-filter="all"'):
            if control not in blog_source:
                errors.append(f"blogs/index.html: missing library control {control}")

    redirects = (SITE / "_redirects").read_text(encoding="utf-8")
    for slug in COMPARISON_SLUGS:
        article = SITE / "blogs" / "comparisons" / slug / "index.html"
        public_article = SITE / slug / "index.html"
        if not article.is_file():
            errors.append(f"comparison cluster: missing article {article}")
        if not public_article.is_file() or public_article.is_symlink() or public_article.parent.is_symlink():
            errors.append(f"comparison cluster: Netlify-safe public route is not a regular file: {public_article}")
        elif article.is_file():
            source_text = article.read_text(encoding="utf-8")
            expected_public = source_text.replace(
                'href="../../../styles.css"', 'href="../styles.css"'
            ).replace('src="../../../script.js"', 'src="../script.js"')
            if public_article.read_text(encoding="utf-8") != expected_public:
                errors.append(f"comparison cluster: generated public route is stale: {public_article}")
            source_assets = {
                path.name: path.read_bytes()
                for path in article.parent.iterdir()
                if path.is_file() and path.name != "index.html"
            }
            public_assets = {
                path.name: path.read_bytes()
                for path in public_article.parent.iterdir()
                if path.is_file() and path.name != "index.html"
            }
            if public_assets != source_assets:
                errors.append(f"comparison cluster: generated public assets are stale: {public_article.parent}")
        public_path = f"/{slug}/"
        parser = parsed_pages.get(article.resolve())
        if parser and parser.canonical != f"https://flitkey.xyz{public_path}":
            errors.append(f"{article}: canonical must preserve {public_path}")
        public_parser = parsed_pages.get(public_article.resolve())
        if public_parser and public_parser.canonical != f"https://flitkey.xyz{public_path}":
            errors.append(f"{public_article}: canonical must preserve {public_path}")
        if f"/blogs/comparisons/{slug}/*" not in redirects or f"/{slug}/:splat" not in redirects:
            errors.append(f"_redirects: missing duplicate-cluster redirect for {public_path}")

    for symlink in SITE.rglob("*"):
        if symlink.is_symlink():
            errors.append(f"Netlify publish tree contains a symlink: {symlink}")

    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap_index_tag = "{http://www.sitemaps.org/schemas/sitemap/0.9}sitemapindex"
    urlset_tag = "{http://www.sitemaps.org/schemas/sitemap/0.9}urlset"
    sitemap_urls: set[str] = set()
    visited_sitemaps: set[Path] = set()

    def collect_sitemap(sitemap_path: Path) -> None:
        sitemap_path = sitemap_path.resolve()
        if sitemap_path in visited_sitemaps:
            errors.append(f"sitemap index loop or duplicate child: {sitemap_path}")
            return
        visited_sitemaps.add(sitemap_path)
        if not sitemap_path.is_file():
            errors.append(f"sitemap index references missing file: {sitemap_path}")
            return

        try:
            root = ElementTree.parse(sitemap_path).getroot()
        except ElementTree.ParseError as exc:
            errors.append(f"{sitemap_path}: invalid XML: {exc}")
            return

        if root.tag == sitemap_index_tag:
            entries = root.findall("sm:sitemap", namespace)
            if not entries:
                errors.append(f"{sitemap_path}: empty sitemap index")
            for entry in entries:
                location = (entry.findtext("sm:loc", default="", namespaces=namespace)).strip()
                parsed = urlparse(location)
                if parsed.scheme != "https" or parsed.netloc != "flitkey.xyz" or not parsed.path.endswith(".xml"):
                    errors.append(f"{sitemap_path}: invalid child sitemap URL {location!r}")
                    continue
                collect_sitemap(SITE / parsed.path.lstrip("/"))
            return

        if root.tag != urlset_tag:
            errors.append(f"{sitemap_path}: expected sitemapindex or urlset root")
            return

        entries = root.findall("sm:url", namespace)
        if not entries:
            errors.append(f"{sitemap_path}: empty URL sitemap")
        for entry in entries:
            location = (entry.findtext("sm:loc", default="", namespaces=namespace)).strip()
            parsed = urlparse(location)
            if parsed.scheme != "https" or parsed.netloc != "flitkey.xyz":
                errors.append(f"{sitemap_path}: invalid page URL {location!r}")
                continue
            if location in sitemap_urls:
                errors.append(f"{sitemap_path}: duplicate sitemap URL {location}")
            sitemap_urls.add(location)
            target = resolve_local(SITE / "index.html", parsed.path)
            if target is not None and not target.is_file():
                errors.append(f"{sitemap_path}: broken URL {location}")

    collect_sitemap(SITE / "sitemap_index.xml")
    missing_sitemap_urls = set(canonicals).difference(sitemap_urls)
    unexpected_sitemap_urls = sitemap_urls.difference(canonicals)
    for location in sorted(missing_sitemap_urls):
        errors.append(f"sitemap index: missing canonical URL {location}")
    for location in sorted(unexpected_sitemap_urls):
        errors.append(f"sitemap index: non-canonical URL {location}")

    compatibility_sitemap = SITE / "sitemap.xml"
    canonical_sitemap_index = SITE / "sitemap_index.xml"
    if not compatibility_sitemap.is_file():
        errors.append("missing backward-compatible sitemap.xml")
    elif compatibility_sitemap.read_bytes() != canonical_sitemap_index.read_bytes():
        errors.append("sitemap.xml must match sitemap_index.xml")

    robots = (SITE / "robots.txt").read_text(encoding="utf-8")
    if "Sitemap: https://flitkey.xyz/sitemap_index.xml" not in robots:
        errors.append("robots.txt: missing canonical sitemap index declaration")

    script = (SITE / "script.js").read_text(encoding="utf-8")
    styles = (SITE / "styles.css").read_text(encoding="utf-8")
    if re.search(r"fonts\.(?:googleapis|gstatic)\.com", styles):
        errors.append("styles.css: external font dependency found; brand fonts must be served locally")
    for family in ("Plus Jakarta Sans", "JetBrains Mono"):
        if family not in styles:
            errors.append(f"styles.css: missing shared font family {family}")
    for font_file in (
        "assets/fonts/plus-jakarta-sans-latin.woff2",
        "assets/fonts/jetbrains-mono-latin.woff2",
    ):
        if not (SITE / font_file).is_file():
            errors.append(f"missing bundled brand font: {font_file}")
        if font_file not in styles:
            errors.append(f"styles.css: bundled brand font is not referenced: {font_file}")
    for page in pages:
        if re.search(r"fonts\.(?:googleapis|gstatic)\.com", page.read_text(encoding="utf-8")):
            errors.append(f"{page}: external font dependency found")
    required_events = {
        "article_download_windows",
        "article_download_linux",
        "migration_download",
        "snippet_pack_download",
        "benchmark_methodology_click",
        "outbound_github_release_click",
    }
    for event in sorted(required_events):
        if event not in script:
            errors.append(f"script.js: missing analytics event {event}")

    if errors:
        print("SITE AUDIT FAILED")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print(f"SITE AUDIT PASSED: {len(pages)} HTML pages, {len(canonicals)} canonical URLs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
