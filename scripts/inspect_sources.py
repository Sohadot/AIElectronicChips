#!/usr/bin/env python3
"""Inspect registered sources against their original documents (IDE-008). Run explicitly; never in CI.

For each requested source ID this command:

1. fetches the registry's canonical URL (and any extra pages of a multi-page document listed in
   EXTRA_PAGES), recording HTTP status, final URL, content type, size and a SHA-256 of the bytes;
2. extracts text (HTML tags stripped; PDFs through `pdftotext`);
3. compares the text with every passage that a release finding quotes from that source, and
   records which passages were found and which were not.

It writes the observations into data/source-inspections.json. It never edits the source registry,
never changes `accessed_at`, `status` or any claim, and never treats a successful retrieval as proof
that a claim is correct. A passage that is not found is recorded as `review_required`, not as a
change: the text may have moved, been reformatted or been revised, and only a reviewer can say which.

    python3 scripts/inspect_sources.py --date 2026-11-10 SOURCE_ID [SOURCE_ID ...]
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import ssl
import subprocess
import sys
import tempfile
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "source-registry.json"
INSPECTIONS = ROOT / "data" / "source-inspections.json"
RESEARCH_DIR = ROOT / "data" / "research"
CA_BUNDLE = Path("/root/.ccr/ca-bundle.crt")
USER_AGENT = "Mozilla/5.0 (compatible; source-provenance-check)"
QUOTED = re.compile(r'"([^"]+)"')
# Multi-page documents: the canonical URL is the document's entry page; quoted passages may sit on these pages.
EXTRA_PAGES = {
    "nvidia-mission-control-rack-setup-guide-2026": [
        "https://docs.nvidia.com/mission-control/docs/rack-bring-up-install/2.5.0/introduction.html",
        "https://docs.nvidia.com/mission-control/docs/rack-bring-up-install/2.5.0/pre-deployment-checklist.html",
        "https://docs.nvidia.com/mission-control/docs/rack-bring-up-install/2.5.0/rack-bring-up.html",
        "https://docs.nvidia.com/mission-control/docs/rack-bring-up-install/2.5.0/rack-firmware-update.html",
        "https://docs.nvidia.com/mission-control/docs/rack-bring-up-install/2.5.0/deployment-summary-validation-checklist.html",
    ],
    # eCFR pages are read through the eCFR renderer API, which returns the same current section text.
    "ecfr-15-cfr-742-6-2026": ["https://www.ecfr.gov/api/renderer/v1/content/enhanced/current/title-15?part=742&section=742.6"],
    "ecfr-15-cfr-740-25-2024": ["https://www.ecfr.gov/api/renderer/v1/content/enhanced/current/title-15?part=740&section=740.25"],
    # The registry's canonical URL is the consortium's press-release listing; the release itself is this PDF.
    "ucie-2-specification-release-2024": [
        "https://www.uciexpress.org/_files/ugd/0c1418_c9fb71cbbd4644e3b73b123216fa2e52.pdf",
    ],
}

Fetcher = Callable[[str], tuple[int, str, str, bytes]]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text).replace("\xad", "")).strip()


def fetch(url: str) -> tuple[int, str, str, bytes]:
    """Return (status, final_url, content_type, body). Raises on network failure."""
    ctx = ssl.create_default_context(cafile=str(CA_BUNDLE)) if CA_BUNDLE.is_file() else ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            return resp.status, resp.geturl(), resp.headers.get("Content-Type", ""), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, url, exc.headers.get("Content-Type", "") if exc.headers else "", b""


def dehyphenate(text: str) -> str:
    """Fallback for PDF line-break hyphenation and table layout: drop hyphens between letters."""
    return re.sub(r"(?<=[A-Za-z])-\s*(?=[A-Za-z])", "", text)


def alnum(text: str) -> str:
    """Second fallback: letters and digits only, so typographic marks (®, ™, curly quotes, footnote markers) do not hide a passage."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def extract_text(content_type: str, body: bytes) -> str:
    if "pdf" in content_type or body[:4] == b"%PDF":
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "doc.pdf"
            pdf.write_bytes(body)
            # Both reading-order and layout extraction: tables survive one or the other.
            parts = [subprocess.run(["pdftotext", *mode, str(pdf), "-"], capture_output=True, check=False).stdout.decode("utf-8", "replace")
                     for mode in ([], ["-layout"])]
            return "\n".join(parts)
    text = body.decode("utf-8", "replace")
    text = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", text)
    return html.unescape(re.sub(r"<[^>]+>", " ", text))


def quoted_passages(source_id: str) -> list[dict]:
    """Every passage quoted from this source by a release finding, the conflict register or a reconciliation record."""
    out = []
    for path in sorted(RESEARCH_DIR.glob("*.json")):
        release = json.loads(path.read_text(encoding="utf-8"))
        for finding in release.get("findings", []):
            for ev in finding.get("evidence", []):
                if ev.get("source_id") == source_id:
                    for quote in QUOTED.findall(ev.get("locator", "")):
                        out.append({"cited_in": finding["id"], "passage": quote})
    for path in [ROOT / "data" / "evidence-conflicts.json", *sorted((ROOT / "data").glob("evidence-reconciliations-*.json"))]:
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data.get("issues", []) + data.get("reconciliations", []):
            for ev in item.get("evidence", []) + item.get("new_evidence", []):
                if ev.get("source_id") == source_id:
                    for quote in QUOTED.findall(ev.get("locator", "")):
                        out.append({"cited_in": item["id"], "passage": quote})
    return out


def inspect(source: dict, date: str, fetcher: Fetcher = fetch) -> dict:
    urls = [source["canonical_url"], *EXTRA_PAGES.get(source["id"], [])]
    retrievals, texts = [], []
    for url in urls:
        try:
            status, final, ctype, body = fetcher(url)
        except Exception as exc:  # network failure is an observation, not an error
            retrievals.append({"url": url, "outcome": "failed", "detail": type(exc).__name__})
            continue
        ok = 200 <= status < 300 and len(body) > 0
        retrievals.append({"url": url, "http_status": status, "final_url": final, "content_type": ctype.split(";")[0].strip(),
                           "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest() if body else None,
                           "outcome": "retrieved" if ok else "failed"})
        if ok:
            texts.append(normalize(extract_text(ctype, body)))
    retrieved = any(r["outcome"] == "retrieved" for r in retrievals)
    passages = quoted_passages(source["id"])
    corpus = " ".join(texts)
    exact = [p for p in passages if normalize(p["passage"]) in corpus] if retrieved else []
    loose_corpus = dehyphenate(corpus)
    loose = [p for p in passages if p not in exact and dehyphenate(normalize(p["passage"])) in loose_corpus] if retrieved else []
    alnum_corpus = alnum(corpus)
    chars = [p for p in passages if p not in exact and p not in loose and alnum(p["passage"]) in alnum_corpus] if retrieved else []
    found = exact + loose + chars
    missing = [p for p in passages if p not in found] if retrieved else []
    states = ["metadata_validated"]
    if retrieved:
        states.append("source_retrieved")
        if passages:
            states.append("source_content_compared")
        if missing:
            states.append("review_required")
    else:
        states.append("source_inaccessible")
    return {
        "source_id": source["id"],
        "inspected_at": date,
        "states": states,
        "retrievals": retrievals,
        "passage_check": {"quoted_passages": len(passages), "found": len(found), "found_after_hyphenation_fallback": len(loose),
                          "found_after_character_fallback": len(chars),
                          "not_found": [{"cited_in": p["cited_in"], "passage": p["passage"]} for p in missing]}
        if retrieved and passages else None,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source_ids", nargs="+")
    parser.add_argument("--date", required=True, help="inspection date (ISO), recorded as inspected_at")
    parser.add_argument("--out", type=Path, default=ROOT / "build" / "source-inspection-observations.json",
                        help="where to write raw observations for editorial review (not the committed log)")
    args = parser.parse_args(argv)
    registry = {s["id"]: s for s in json.loads(REGISTRY.read_text(encoding="utf-8"))["source_records"]}
    unknown = [s for s in args.source_ids if s not in registry]
    if unknown:
        raise SystemExit(f"unregistered source IDs: {unknown}")
    results = [inspect(registry[s], args.date) for s in args.source_ids]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for r in results:
        pc = r["passage_check"]
        print(r["source_id"], r["states"], f"{pc['found']}/{pc['quoted_passages']} passages" if pc else "")


if __name__ == "__main__":
    main()
