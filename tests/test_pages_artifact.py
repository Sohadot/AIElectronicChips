#!/usr/bin/env python3
"""Run the workflow's own site-staging step and check the published artifact.

The artifact must contain everything the public site needs and nothing else:
no research candidates, workflow files, scripts, tests or internal documents.
The repository is public, so this controls what the website serves, not what
is visible on GitHub.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "validate-and-deploy.yml"
ROOT_SITE_FILES = {"index.html", "CNAME", "robots.txt", "sitemap.xml", ".nojekyll"}


def staging_script() -> str:
    """Extract the `run: |` block of the 'Stage public site' step verbatim."""
    lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if "name: Stage public site" in line)
    run = next(i for i in range(start, len(lines)) if lines[i].strip() == "run: |")
    body, indent = [], None
    for line in lines[run + 1:]:
        if not line.strip():
            continue
        width = len(line) - len(line.lstrip())
        indent = width if indent is None else indent
        if width < indent:
            break
        body.append(line[indent:])
    return "\n".join(body)


def tracked() -> set[str]:
    out = subprocess.run(["git", "ls-tree", "-r", "--name-only", "HEAD"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    return set(out.split())


@unittest.skipUnless(shutil.which("git") and shutil.which("tar") and (ROOT / ".git").exists(),
                     "requires git, tar and a checkout")
class PagesArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        env = dict(os.environ, RUNNER_TEMP=cls.tmp.name)
        result = subprocess.run(["bash", "-euo", "pipefail", "-c", staging_script()], cwd=ROOT,
                                env=env, capture_output=True, text=True, check=False)
        cls.returncode, cls.stderr = result.returncode, result.stderr
        cls.site = Path(cls.tmp.name) / "site"
        cls.files = {p.relative_to(cls.site).as_posix() for p in cls.site.rglob("*") if p.is_file()} if cls.site.exists() else set()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_staging_step_succeeds(self):
        self.assertEqual(0, self.returncode, self.stderr)

    def test_only_publication_files_are_staged(self):
        def allowed(path: str) -> bool:
            parts = path.split("/")
            return (
                path in ROOT_SITE_FILES
                or parts[0] == "assets"
                or (len(parts) == 2 and parts[0] == "data" and parts[1].endswith(".json"))
                or (len(parts) == 2 and parts[1] == "index.html")
            )
        self.assertEqual([], sorted(f for f in self.files if not allowed(f)))

    def test_internal_material_excluded(self):
        for prefix in (".github/", "data/research/", "scripts/", "tests/"):
            self.assertFalse(any(f.startswith(prefix) for f in self.files), prefix)
        self.assertFalse(any(f.endswith(".md") for f in self.files))

    def test_required_site_files_preserved(self):
        expected = {f for f in tracked() if f.startswith("assets/")}
        expected |= {f for f in tracked() if re.fullmatch(r"data/[^/]+\.json", f)}
        expected |= {f for f in tracked() if f in ROOT_SITE_FILES or re.fullmatch(r"[^/]+/index\.html", f)}
        self.assertEqual([], sorted(expected - self.files))
        self.assertEqual("aielectronicchips.com", (self.site / "CNAME").read_text(encoding="utf-8").strip())

    def test_every_sitemap_route_is_staged(self):
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        for loc in ET.parse(self.site / "sitemap.xml").findall(".//sm:loc", ns):
            path = loc.text.strip().replace("https://aielectronicchips.com/", "")
            self.assertIn(f"{path}index.html" if path else "index.html", self.files, loc.text)

    def test_local_references_resolve_inside_artifact(self):
        pattern = re.compile(r'(?:href|src)="(/[^"#?]*)"|fetch\("(/[^"]+)"|content="https://aielectronicchips\.com(/[^"]+\.(?:png|json))"')
        missing = []
        for page in [f for f in self.files if f.endswith(".html")] + [f for f in self.files if f.endswith(".js")]:
            for groups in pattern.findall((self.site / page).read_text(encoding="utf-8")):
                ref = next(g for g in groups if g)
                target = ref.lstrip("/")
                if target == "" or target.endswith("/"):
                    target += "index.html"
                if target not in self.files:
                    missing.append(f"{page} -> {ref}")
        self.assertEqual([], missing)


if __name__ == "__main__":
    unittest.main()
