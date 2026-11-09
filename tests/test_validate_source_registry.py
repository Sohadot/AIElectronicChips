#!/usr/bin/env python3
"""Regression checks: the public /sources/ index must mirror the registry."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_source_registry import check_public_index  # noqa: E402

RECORDS = [{"id": "a-source", "status": "active"}, {"id": "b-source", "status": "pending_review"}]


def page(items: str) -> str:
    return f'<ul class="source-id-list" aria-label="Seed source registry IDs">{items}</ul>'


class PublicIndexTests(unittest.TestCase):
    def run_check(self, html):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "index.html"
            path.write_text(html, encoding="utf-8")
            return check_public_index(path, RECORDS)

    def test_consistent_index(self):
        html = page('<li>a-source</li><li class="pending">b-source · pending_review</li>')
        self.assertEqual([], self.run_check(html))

    def test_missing_id(self):
        errors = self.run_check(page("<li>a-source</li>"))
        self.assertTrue(any("does not list registry ID: b-source" in e for e in errors), errors)

    def test_unregistered_id(self):
        html = page('<li>a-source</li><li class="pending">b-source</li><li>ghost-source</li>')
        self.assertTrue(any("unregistered ID: ghost-source" in e for e in self.run_check(html)))

    def test_pending_marker_mismatch(self):
        html = page('<li class="pending">a-source</li><li>b-source</li>')
        errors = self.run_check(html)
        self.assertEqual(2, sum("pending marker" in e for e in errors), errors)

    def test_repository_index_matches_registry(self):
        import json
        records = json.loads((ROOT / "data" / "source-registry.json").read_text(encoding="utf-8"))["source_records"]
        self.assertEqual([], check_public_index(ROOT / "sources" / "index.html", records))


if __name__ == "__main__":
    unittest.main()
