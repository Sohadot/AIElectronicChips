#!/usr/bin/env python3
"""Guard the light visual system: AA contrast of the design tokens, no dark
surfaces, no automatic dark theme, and no suppressed keyboard focus."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = [ROOT / "assets" / "css" / "main.css", ROOT / "assets" / "css" / "evidence.css"]


REQUIRED_TOKENS = {"bg", "surface", "surface-2", "tint", "ink", "ink-strong", "muted",
                   "teal-ink", "copper-ink", "line-strong", "focus"}


def tokens() -> dict[str, str]:
    root = re.search(r":root\s*{(.*?)}", CSS[0].read_text(encoding="utf-8"), re.S).group(1)
    return {k: v.lower() for k, v in re.findall(r"--([a-z0-9-]+):\s*(#[0-9a-fA-F]{6})", root)}


def luminance(hex_color: str) -> float:
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


class VisualTokenTests(unittest.TestCase):
    def test_design_tokens_defined(self):
        self.assertEqual([], sorted(REQUIRED_TOKENS - set(tokens())))

    def tokens(self) -> dict[str, str]:
        t = tokens()
        missing = REQUIRED_TOKENS - set(t)
        if missing:
            self.fail(f"design tokens missing from main.css :root: {sorted(missing)}")
        return t

    def test_text_tokens_meet_aa_on_every_surface(self):
        t = self.tokens()
        for text in ("ink", "ink-strong", "muted", "teal-ink", "copper-ink"):
            for surface in ("bg", "surface", "surface-2", "tint"):
                with self.subTest(text=text, surface=surface):
                    self.assertGreaterEqual(contrast(t[text], t[surface]), 4.5)

    def test_controls_and_focus_meet_non_text_contrast(self):
        t = self.tokens()
        for part in ("line-strong", "focus"):
            for surface in ("bg", "surface"):
                with self.subTest(part=part, surface=surface):
                    self.assertGreaterEqual(contrast(t[part], t[surface]), 3.0)

    def test_default_surfaces_are_light(self):
        t = self.tokens()
        for surface in ("bg", "surface", "surface-2", "tint"):
            self.assertGreater(luminance(t[surface]), 0.8, surface)

    def test_no_dark_backgrounds_in_stylesheets(self):
        """Page, panel and card surfaces stay light. Small solid controls (buttons) may use the accent."""
        for path in CSS:
            css = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
            for selector, body in re.findall(r"([^{}]+){([^{}]*)}", css):
                if ".button" in selector:
                    continue
                for value in re.findall(r"background(?:-color)?\s*:\s*(#[0-9a-fA-F]{6})\b", body):
                    with self.subTest(file=path.name, selector=selector.strip(), value=value):
                        self.assertGreater(luminance(value.lower()), 0.5)

    def test_no_automatic_dark_theme(self):
        for path in CSS:
            self.assertNotIn("prefers-color-scheme: dark", path.read_text(encoding="utf-8").replace("prefers-color-scheme:dark", "prefers-color-scheme: dark"))
        self.assertIn("color-scheme: light", CSS[0].read_text(encoding="utf-8"))

    def test_focus_is_never_suppressed_without_replacement(self):
        for path in CSS:
            for rule in re.findall(r"([^{}]+){[^{}]*outline:\s*none[^{}]*}", path.read_text(encoding="utf-8")):
                with self.subTest(file=path.name, selector=rule.strip()):
                    self.assertIn(":not(:focus-visible)", rule)


if __name__ == "__main__":
    unittest.main()
