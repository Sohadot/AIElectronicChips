#!/usr/bin/env python3
"""Homepage positioning: approved copy, ontology preserved, compute sovereignty
framed as one framework, and no unearned claims of leadership, verification,
qualification or proprietary intelligence."""

from __future__ import annotations

import html
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "index.html").read_text(encoding="utf-8")
TITLE = "AI Chips, from Silicon to Systems"
LEAD = ("An evidence-led reference to AI chip technologies, manufacturing, supply chains, "
        "and the industrial dependencies shaping compute systems.")


def text_of(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def graph() -> dict:
    block = re.search(r'<script type="application/ld\+json">(.*?)</script>', PAGE, re.S).group(1)
    return {node["@id"]: node for node in json.loads(block)["@graph"]}


class HomepagePositioningTests(unittest.TestCase):
    def test_hero_copy(self):
        hero = re.search(r'<section class="home-hero">(.*?)</section>', PAGE, re.S).group(1)
        self.assertIn('<p class="eyebrow">AI Chip Systems Intelligence</p>', hero)
        self.assertIn(f"<h1>{TITLE}.</h1>", hero)
        self.assertIn(f'<p class="lead">{LEAD}</p>', hero)
        self.assertIn('href="/sovereignty-stack/">Explore the Eight-Layer Stack</a>', hero)
        self.assertIn('href="/hbm-memory/">Read the HBM4 Evidence Reference</a>', hero)

    def test_metadata_matches_positioning(self):
        self.assertIn(f"<title>{TITLE} | AIElectronicChips.com</title>", PAGE)
        self.assertIn(f'<meta property="og:title" content="{TITLE}">', PAGE)
        self.assertIn(f'<meta property="og:description" content="{LEAD}">', PAGE)
        self.assertIn('<link rel="canonical" href="https://aielectronicchips.com/">', PAGE)
        g = graph()
        self.assertEqual(f"{TITLE}.", g["https://aielectronicchips.com/#organization"]["slogan"])
        self.assertEqual(TITLE, g["https://aielectronicchips.com/#webpage"]["name"])

    def test_ontology_and_standard_preserved(self):
        ontology = graph()["https://aielectronicchips.com/sovereignty-stack/#ontology"]
        self.assertEqual("Compute Sovereignty Ontology", ontology["name"])
        self.assertEqual("Silicon Sovereignty Stack", ontology["alternateName"])
        self.assertEqual(8, len(ontology["hasDefinedTerm"]))
        # The standard's thesis stays on the homepage, attributed to AEC-CS-001 as one framework.
        body = text_of(PAGE.split("<main", 1)[1])
        self.assertIn("Compute sovereignty is one framework this reference applies", body)
        self.assertRegex(body, r"AEC-CS-001\s*, reads AI chips as the physical substrate of compute sovereignty")
        self.assertIn("compute sovereignty", graph()["https://aielectronicchips.com/#organization"]["knowsAbout"])

    def test_sovereignty_is_not_the_headline_category(self):
        for pattern in (r"<title>[^<]*</title>", r"<h1>[^<]*</h1>", r'<p class="eyebrow">[^<]*</p>'):
            self.assertNotIn("sovereignty", re.search(pattern, PAGE).group(0).lower())

    def test_no_unearned_claims(self):
        body = text_of(PAGE.split("<main", 1)[1]) + " " + json.dumps(graph())
        for phrase in (r"\bmarket[- ]lead\w*", r"\bindustry[- ]lead\w*", r"\bleading\b", r"#1\b", r"world'?s first",
                       r"\bverified\b", r"\bpeer[- ]reviewed\b", r"\bproprietary\b", r"\bqualified\b", r"\bexclusive\b"):
            self.assertIsNone(re.search(phrase, body, re.I), phrase)


if __name__ == "__main__":
    unittest.main()
