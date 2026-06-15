#!/usr/bin/env python3
"""Validate public launch readiness for static site indexing and trust."""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "https://aielectronicchips.com"
ALLOWED_SKIP_TARGETS = {"#main"}

RISKY_TERMS = [
    "sovereignty score",
    "ranking",
    "benchmark",
    "certification",
    "guarantee",
    "guaranteed",
    "checkout",
    "price",
    "pricing",
    "affiliate",
    "product review",
    "best AI chips",
    "best HBM",
    "investment advice",
    "legal advice",
    "procurement advice",
    "national-security advice",
    "national security advice",
    "sponsored conclusion",
    "predetermined conclusion",
]

BOUNDARY_DATA_FILES = {"strategic-offerings.json", "chip-dependency-model.json"}
GOVERNANCE_FILES = {
    "STRATEGIC_AVAILABILITY_TRUST_GATE.md",
    "COMMERCIAL_TRUST_AUDIT.md",
    "STRATEGIC_AVAILABILITY_PROTOCOL.md",
    "PREMIUM_BRIEF_BOUNDARY.md",
    "MONETIZATION_BOUNDARY.md",
    "COMPUTE_SOVEREIGNTY_STANDARD.md",
    "COMPUTE_SOVEREIGNTY_ONTOLOGY.md",
    "CHIP_DEPENDENCY_MAP_PROTOCOL.md",
    "SOURCE_REGISTRY_PROTOCOL.md",
    "SOURCE_POLICY.md",
    "CLAIM_POLICY.md",
    "CATEGORY_THESIS.md",
    "BUYER_LOGIC.md",
    "MODEL_COHERENCE_AUDIT.md",
    "DECISION_LOG.md",
    "README.md",
    "ASSET_INTELLIGENCE_FACTORY_PLAN.md",
    "PUBLIC_LAUNCH_READINESS_CHECKLIST.md",
    "INDEXATION_HARDENING_AUDIT.md",
}

PROHIBITED_OUTPUT_TOKEN = re.compile(
    r'^\s*"(?:[a-z_]*(?:score|ranking|benchmark|certification|guarantee|checkout|price|affiliate|advice|conclusion)[a-z_]*)",?\s*$',
    re.IGNORECASE,
)
PROHIBITION_MARKERS = re.compile(
    r"(?:"
    r"\bnot\b|\bno\b|\bnon-|\bcannot\b|\bcan't\b|\bmust not\b|\bdoes not\b|\bdo not\b|"
    r"\bwithout\b|\bprohibited\b|\bexcluded\b|\bboundary\b|\blimitation\b|"
    r"\brequires\b|\bexpects\b|\bseeks\b|\bThe client\b|\bThe party\b|\bThe request\b|"
    r"Cannot purchase|No public|No predetermined|product-review|predetermin|"
    r"prohibited_outputs|not_suitable_when|trust_constraints|deliverable_boundary|"
    r"MUST NOT|must not include|Excluded Models|Prohibited"
    r")",
    re.IGNORECASE,
)

REQUIRED_META = {
    "title": re.compile(r"<title>(?P<value>[^<]+)</title>", re.IGNORECASE),
    "description": re.compile(
        r'<meta\s+name="description"\s+content="(?P<value>[^"]+)"',
        re.IGNORECASE,
    ),
    "robots": re.compile(
        r'<meta\s+name="robots"\s+content="(?P<value>[^"]+)"',
        re.IGNORECASE,
    ),
    "canonical": re.compile(
        r'<link\s+rel="canonical"\s+href="(?P<value>[^"]+)"',
        re.IGNORECASE,
    ),
    "og_type": re.compile(
        r'<meta\s+property="og:type"\s+content="(?P<value>[^"]+)"',
        re.IGNORECASE,
    ),
    "og_site_name": re.compile(
        r'<meta\s+property="og:site_name"\s+content="(?P<value>[^"]+)"',
        re.IGNORECASE,
    ),
    "og_title": re.compile(
        r'<meta\s+property="og:title"\s+content="(?P<value>[^"]+)"',
        re.IGNORECASE,
    ),
    "og_description": re.compile(
        r'<meta\s+property="og:description"\s+content="(?P<value>[^"]+)"',
        re.IGNORECASE,
    ),
    "og_url": re.compile(
        r'<meta\s+property="og:url"\s+content="(?P<value>[^"]+)"',
        re.IGNORECASE,
    ),
}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str | None]] = []
        self.images: list[tuple[str | None, str | None]] = []
        self._current_link_href: str | None = None
        self._current_link_text: list[str] = []
        self._current_link_aria: str | None = None
        self._capture_link_text = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k: v for k, v in attrs if k}
        if tag == "a":
            self._current_link_href = attr_map.get("href")
            self._current_link_aria = attr_map.get("aria-label")
            self._current_link_text = []
            self._capture_link_text = True
        elif tag == "img":
            self.images.append((attr_map.get("src"), attr_map.get("alt")))

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._capture_link_text:
            text = re.sub(r"\s+", " ", "".join(self._current_link_text)).strip()
            self.links.append((self._current_link_href or "", self._current_link_aria or text or None))
            self._capture_link_text = False
            self._current_link_href = None
            self._current_link_aria = None
            self._current_link_text = []

    def handle_data(self, data: str) -> None:
        if self._capture_link_text:
            self._current_link_text.append(data)


def public_html_pages() -> list[Path]:
    pages = [ROOT / "index.html"]
    pages.extend(sorted(ROOT.glob("*/index.html")))
    return pages


def page_to_route(path: Path) -> str:
    if path == ROOT / "index.html":
        return f"{DOMAIN}/"
    rel = path.parent.relative_to(ROOT).as_posix()
    return f"{DOMAIN}/{rel}/"


def route_to_file(route: str) -> Path:
    parsed = urlparse(route)
    if parsed.netloc and parsed.netloc != "aielectronicchips.com":
        raise ValueError(route)
    path = parsed.path.strip("/")
    if not path:
        return ROOT / "index.html"
    return ROOT / path / "index.html"


def parse_sitemap_routes() -> list[str]:
    tree = ET.parse(ROOT / "sitemap.xml")
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [loc.text.strip() for loc in tree.findall(".//sm:loc", ns) if loc.text]


def is_prohibition_context(line: str, path: Path, previous_line: str = "") -> bool:
    if path.name in GOVERNANCE_FILES or path.name in BOUNDARY_DATA_FILES:
        return True
    combined = f"{previous_line} {line}"
    if PROHIBITION_MARKERS.search(combined):
        return True
    if path.suffix == ".json" and PROHIBITED_OUTPUT_TOKEN.match(line):
        return True
    if path.suffix == ".json" and any(
        marker in line
        for marker in (
            "prohibited",
            "boundary",
            "not_suitable_when",
            "use_limitations",
            "trust_constraints",
            "deliverable_boundary",
        )
    ):
        return True
    return False


def check_risky_language(errors: list[str]) -> None:
    for path in sorted(ROOT.rglob("*")):
        if path.suffix not in {".html", ".md", ".json"} or not path.is_file():
            continue
        if path.parts[0] == ".git":
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        previous = ""
        for line_no, line in enumerate(lines, 1):
            lowered = line.lower()
            for term in RISKY_TERMS:
                if term.lower() not in lowered:
                    continue
                if not is_prohibition_context(line, path, previous):
                    rel = path.relative_to(ROOT)
                    errors.append(
                        f"{rel}:{line_no}: risky term '{term}' outside prohibition context"
                    )
            previous = line


def resolve_internal_href(href: str, source_file: Path) -> Path | None:
    if not href or href.startswith(("mailto:", "tel:", "javascript:")):
        return None
    if href.startswith("http://") or href.startswith("https://"):
        return None
    if href in ALLOWED_SKIP_TARGETS:
        return source_file
    if href.startswith("#"):
        return source_file
    parsed = urlparse(href)
    path = parsed.path
    if path.startswith("/"):
        target = route_to_file(f"{DOMAIN}{path}")
    else:
        target = (source_file.parent / path).resolve()
    return target


def check_page_structure(path: Path, errors: list[str]) -> None:
    rel = path.relative_to(ROOT)
    content = path.read_text(encoding="utf-8")
    lowered = content.lower()

    if "<script" in lowered:
        errors.append(f"{rel}: contains script tag")
    if re.search(r"https?://[^\s\"']+\.js", content):
        errors.append(f"{rel}: references external JavaScript")
    if re.search(r"(fonts\.googleapis|fonts\.gstatic|cdn\.|unpkg|jsdelivr)", content, re.I):
        errors.append(f"{rel}: references external CDN or font dependency")

    h1_count = len(re.findall(r"<h1\b", content, re.IGNORECASE))
    if h1_count != 1:
        errors.append(f"{rel}: expected exactly one h1, found {h1_count}")

    for name, pattern in REQUIRED_META.items():
        match = pattern.search(content)
        if not match or not match.group("value").strip():
            errors.append(f"{rel}: missing or empty {name}")

    canonical = REQUIRED_META["canonical"].search(content)
    if canonical and not canonical.group("value").startswith(f"{DOMAIN}/"):
        errors.append(f"{rel}: canonical URL must use {DOMAIN}/")

    robots = REQUIRED_META["robots"].search(content)
    if robots and "noindex" in robots.group("value").lower():
        errors.append(f"{rel}: public page uses noindex")

    if not re.search(r'class="primary-nav"|aria-label="Primary navigation"', content):
        errors.append(f"{rel}: missing primary navigation")

    if re.search(r"<h3\b", content, re.IGNORECASE) and not re.search(r"<h2\b", content, re.IGNORECASE):
        errors.append(f"{rel}: h3 appears without h2")

    parser = LinkParser()
    parser.feed(content)
    for href, text in parser.links:
        if not href:
            errors.append(f"{rel}: empty href attribute")
            continue
        if href in {"#", "javascript:", "javascript:void(0)"} or "TODO" in href.upper():
            errors.append(f"{rel}: placeholder link href '{href}'")
            continue
        if href.startswith(("mailto:", "tel:", "http://", "https://")):
            continue
        target = resolve_internal_href(href, path)
        if target is None:
            continue
        if not target.exists():
            errors.append(f"{rel}: broken internal link '{href}' -> {target.relative_to(ROOT)}")
        if not text:
            errors.append(f"{rel}: link without visible text or aria-label: '{href}'")

    for src, alt in parser.images:
        if alt is None or not str(alt).strip():
            errors.append(f"{rel}: image missing alt text ({src})")


def main() -> None:
    errors: list[str] = []

    pages = public_html_pages()
    page_routes = {page_to_route(page) for page in pages}

    for page in pages:
        if not page.is_file():
            errors.append(f"missing public page: {page.relative_to(ROOT)}")
        else:
            check_page_structure(page, errors)

    try:
        sitemap_routes = set(parse_sitemap_routes())
    except (OSError, ET.ParseError) as exc:
        errors.append(f"sitemap.xml: could not parse ({exc})")
        sitemap_routes = set()

    for route in sorted(sitemap_routes):
        if not route.startswith(f"{DOMAIN}/"):
            errors.append(f"sitemap.xml: URL must use {DOMAIN}/ ({route})")
        target = route_to_file(route)
        if not target.is_file():
            errors.append(f"sitemap.xml: missing file for route {route}")

    missing_from_sitemap = sorted(page_routes - sitemap_routes)
    extra_in_sitemap = sorted(sitemap_routes - page_routes)
    for route in missing_from_sitemap:
        errors.append(f"sitemap.xml: missing route {route}")
    for route in extra_in_sitemap:
        errors.append(f"sitemap.xml: extra route without public page {route}")

    robots_path = ROOT / "robots.txt"
    if not robots_path.is_file():
        errors.append("robots.txt: missing")
    else:
        robots = robots_path.read_text(encoding="utf-8")
        if "Allow: /" not in robots:
            errors.append("robots.txt: must allow crawling with 'Allow: /'")
        if f"Sitemap: {DOMAIN}/sitemap.xml" not in robots:
            errors.append(f"robots.txt: must reference {DOMAIN}/sitemap.xml")

    cname_path = ROOT / "CNAME"
    if not cname_path.is_file():
        errors.append("CNAME: missing for custom domain readiness")
    elif cname_path.read_text(encoding="utf-8").strip() != "aielectronicchips.com":
        errors.append("CNAME: must contain aielectronicchips.com")

    check_risky_language(errors)

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        print(f"FAIL: public launch validation failed with {len(errors)} issue(s).", file=sys.stderr)
        raise SystemExit(1)

    print(f"PASS: Public launch readiness validated ({len(pages)} routes, sitemap aligned, robots and CNAME ready).")


if __name__ == "__main__":
    main()
