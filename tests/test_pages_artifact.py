#!/usr/bin/env python3
"""Run the workflow's own site-staging step and check the published artifact.

The artifact must contain everything the public site needs and nothing else:
no research candidates, workflow files, scripts, tests or internal documents.
The repository is public, so this controls what the website serves, not what
is visible on GitHub.

Staging copies only the files listed in .github/pages-allowlist.txt (scripts/stage_pages.py),
so the artifact must equal that list exactly, and an unlisted file can never be published.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "validate-and-deploy.yml"
ALLOWLIST = ROOT / ".github" / "pages-allowlist.txt"
STAGE = ROOT / "scripts" / "stage_pages.py"
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


def allowlisted() -> list[str]:
    return [line for line in ALLOWLIST.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]


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

    def test_artifact_is_exactly_the_allowlist(self):
        listed = allowlisted()
        self.assertEqual(len(listed), len(set(listed)))
        self.assertEqual(set(listed), self.files)
        self.assertTrue(set(listed) <= tracked())

    def test_required_site_files_preserved(self):
        # Every route page and root file the site needs is listed and staged; assets and data are published only when listed.
        expected = {f for f in tracked() if f in ROOT_SITE_FILES or re.fullmatch(r"[^/]+/index\.html", f)}
        self.assertEqual([], sorted(expected - self.files))
        self.assertEqual("aielectronicchips.com", (self.site / "CNAME").read_text(encoding="utf-8").strip())

    def test_staged_bytes_match_the_commit(self):
        for f in sorted(self.files):
            committed = subprocess.run(["git", "show", f"HEAD:{f}"], cwd=ROOT, capture_output=True, check=True).stdout
            self.assertEqual(committed, (self.site / f).read_bytes(), f)

    def test_no_symbolic_links_in_artifact(self):
        self.assertEqual([], [p for p in self.site.rglob("*") if p.is_symlink()])

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


@unittest.skipUnless(shutil.which("git"), "requires git")
class StagingGuardTests(unittest.TestCase):
    """The staging step itself decides what can be published, and stops the deploy on any doubt.

    Each case builds a throwaway repository containing the real scripts/stage_pages.py and runs the workflow's own
    staging block in it."""

    SITE = {"index.html": "x", "CNAME": "aielectronicchips.com", "robots.txt": "x", "sitemap.xml": "x",
            "assets/css/main.css": "x", "data/public.json": "{}"}

    def allowlist(self, entries) -> str:
        return "# fixture allowlist\n" + "".join(e + "\n" for e in entries)

    def run_staging_in_repo(self, files: dict[str, str], allowlist: str | None = None, after_commit=None):
        with tempfile.TemporaryDirectory() as tmp:
            repo, runner = Path(tmp) / "repo", Path(tmp) / "runner"
            repo.mkdir()
            runner.mkdir()
            files = dict(files)
            files.setdefault("scripts/stage_pages.py", STAGE.read_text(encoding="utf-8"))
            if allowlist is None:
                allowlist = self.allowlist(sorted(k for k in files if not k.startswith("scripts/")))
            files[".github/pages-allowlist.txt"] = allowlist
            for name, text in files.items():
                (repo / name).parent.mkdir(parents=True, exist_ok=True)
                (repo / name).write_text(text, encoding="utf-8")
            env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid",
                       GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
            for cmd in (["git", "init", "-q"], ["git", "add", "-A"], ["git", "commit", "-q", "-m", "fixture"]):
                subprocess.run(cmd, cwd=repo, env=env, check=True, capture_output=True)
            if after_commit:
                after_commit(repo, env)
            result = subprocess.run(["bash", "-euo", "pipefail", "-c", staging_script()], cwd=repo,
                                    env=dict(env, RUNNER_TEMP=str(runner)), capture_output=True, text=True, check=False)
            site = runner / "site"
            staged = {p.relative_to(site).as_posix(): p.read_text(encoding="utf-8") for p in site.rglob("*") if p.is_file()} \
                if site.exists() else {}
            return result, staged

    def assertRefused(self, files, allowlist, message):
        result, _ = self.run_staging_in_repo(files, allowlist)
        self.assertNotEqual(0, result.returncode, result.stdout)
        self.assertIn(message, result.stderr)

    def test_complete_fixture_stages(self):
        result, staged = self.run_staging_in_repo(self.SITE)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(set(self.SITE), set(staged))

    def test_missing_required_file_fails(self):
        for missing in ("index.html", "CNAME", "robots.txt", "sitemap.xml"):
            files = {"index.html": "x", "CNAME": "aielectronicchips.com", "robots.txt": "x", "sitemap.xml": "x"}
            del files[missing]
            with self.subTest(missing=missing):
                self.assertNotEqual(0, self.run_staging_in_repo(files)[0].returncode)

    def test_unlisted_data_and_asset_files_are_never_published(self):
        files = dict(self.SITE, **{"data/x.json": '{"secret": true}', "assets/x.png": "x", "assets/notes/plan.txt": "x",
                                   "data/nested/y.json": "{}", "extra/index.html": "x"})
        result, staged = self.run_staging_in_repo(files, self.allowlist(sorted(self.SITE)))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(set(self.SITE), set(staged))
        for unlisted in ("data/x.json", "assets/x.png", "extra/index.html"):
            self.assertIn(f"NOTE: {unlisted} is tracked but not in", result.stderr)

    def test_internal_files_do_not_block_development(self):
        files = dict(self.SITE, **{"scripts/new_tool.py": "x", "tests/test_new.py": "x", "data/research/new.json": "{}",
                                   "NOTES.md": "x", "docs/plan.txt": "x", ".github/workflows/other.yml": "x"})
        result, staged = self.run_staging_in_repo(files, self.allowlist(sorted(self.SITE)))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(set(self.SITE), set(staged))

    def test_malformed_entries_fail_closed(self):
        base = sorted(self.SITE)
        cases = {
            "duplicate entry": base + ["sitemap.xml"],
            "must be sorted": ["sitemap.xml"] + base,
            "listed but not tracked": sorted(base + ["data/absent.json"]),
            "not a plain relative path": sorted(base + ["/etc/passwd"]),
            "'.' and '..' segments": sorted(base + ["assets/../CNAME"]),
            "internal material": sorted(base + ["scripts/stage_pages.py"]),
        }
        for message, entries in cases.items():
            with self.subTest(message=message):
                self.assertRefused(self.SITE, self.allowlist(entries), message)
        for bad in ("data/*.json", "assets/", "assets//css/main.css", "assets\\css\\main.css", "data/research/x.json",
                    ".github/pages-allowlist.txt", "README.md", "index.html; rm -rf /", "./index.html"):
            with self.subTest(bad=bad):
                result, staged = self.run_staging_in_repo(self.SITE, self.allowlist(base) + bad + "\n")
                self.assertNotEqual(0, result.returncode, bad)
                self.assertEqual({}, staged)
        self.assertRefused(self.SITE, self.allowlist(base).replace("index.html", " index.html"), "whitespace")
        self.assertRefused(self.SITE, "# nothing listed\n", "no entries")

    def test_symbolic_links_and_submodules_are_refused(self):
        def add_link(repo, env):
            (repo / "assets" / "link.css").symlink_to("../CNAME")
            subprocess.run(["git", "add", "-A"], cwd=repo, env=env, check=True)
            oid = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()
            subprocess.run(["git", "update-index", "--add", "--cacheinfo", f"160000,{oid},vendored"], cwd=repo, env=env, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "link"], cwd=repo, env=env, check=True)
        for entry, message in (("assets/link.css", "symbolic links"), ("vendored", "submodules")):
            with self.subTest(entry=entry):
                result, staged = self.run_staging_in_repo(self.SITE, self.allowlist(sorted(list(self.SITE) + [entry])), after_commit=add_link)
                self.assertNotEqual(0, result.returncode)
                self.assertIn(message, result.stderr)
                self.assertEqual({}, staged)

    def test_only_committed_content_is_published(self):
        def local_edits(repo, env):
            (repo / "index.html").write_text("uncommitted", encoding="utf-8")
            (repo / "data" / "local.json").write_text("{}", encoding="utf-8")
            (repo / ".github" / "pages-allowlist.txt").write_text(self.allowlist(sorted(list(self.SITE) + ["data/local.json"])), encoding="utf-8")
        result, staged = self.run_staging_in_repo(self.SITE, after_commit=local_edits)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("x", staged["index.html"])
        self.assertNotIn("data/local.json", staged)

    def test_output_directory_must_be_new_or_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "site"
            out.mkdir()
            (out / "stale.txt").write_text("x", encoding="utf-8")
            result = subprocess.run([sys.executable, str(STAGE), "--out", str(out)], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("must be a new or empty directory", result.stderr)

    def test_repository_allowlist_check_passes(self):
        result = subprocess.run([sys.executable, str(STAGE), "--check"], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
