#!/usr/bin/env python3
"""Stage the GitHub Pages artifact from an explicit allowlist (fail closed).

The canonical list of public files is `.github/pages-allowlist.txt`: one repository path per line, sorted, with
blank lines and `#` comments ignored. Only listed files are copied into the artifact, so a new file under `assets/`
or `data/` (or anywhere else) is never published until a reviewer adds it to the list. The list is never generated
or extended here.

Every file is read from the committed tree (`git ls-tree` / `git cat-file` at HEAD), not from the working directory,
so untracked or modified local files cannot leak into the artifact and the output is reproducible for a commit.

The run fails, and nothing is published, if any entry:
- is not a plain relative POSIX path of safe characters (no absolute paths, `..`, `.`, empty segments, backslashes,
  glob characters, whitespace or control characters);
- is duplicated or out of sorted order;
- names internal material (`.github/`, `data/research/`, `scripts/`, `tests/`, Markdown);
- is not tracked at HEAD as a regular file (missing paths, directories, symbolic links and submodules are rejected);
or if a required root file is not listed, or the staged directory does not match the list exactly, byte for byte.

    python3 scripts/stage_pages.py --out "$RUNNER_TEMP/site"   # stage (the deploy workflow)
    python3 scripts/stage_pages.py --check                     # validate the list and stage into a temporary directory
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ALLOWLIST = Path(".github") / "pages-allowlist.txt"
REQUIRED = ("CNAME", "index.html", "robots.txt", "sitemap.xml")
FORBIDDEN_PREFIXES = (".github/", "data/research/", "scripts/", "tests/", ".git/")
SAFE_PATH = re.compile(r"[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*")
REGULAR_MODES = {"100644", "100755"}


class StagingError(Exception):
    pass


def git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, check=False)
    if result.returncode != 0:
        raise StagingError(f"git {' '.join(args)} failed: {result.stderr.decode(errors='replace').strip()}")
    return result.stdout


def parse_allowlist(text: str) -> tuple[list[str], list[str]]:
    """Return (entries, errors). Every rule here is a reason to refuse publication."""
    entries, errors, seen = [], [], set()
    for n, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        where = f"{ALLOWLIST}:{n}: {raw!r}"
        if raw != line:
            errors.append(f"{where}: leading or trailing whitespace")
        elif not SAFE_PATH.fullmatch(line):
            errors.append(f"{where}: not a plain relative path of safe characters")
        elif any(seg in (".", "..") for seg in line.split("/")):
            errors.append(f"{where}: '.' and '..' segments are not allowed")
        elif line.startswith(FORBIDDEN_PREFIXES) or line.lower().endswith(".md"):
            errors.append(f"{where}: internal material cannot be published")
        elif line in seen:
            errors.append(f"{where}: duplicate entry")
        else:
            if entries and line < entries[-1]:
                errors.append(f"{where}: entries must be sorted (after {entries[-1]!r})")
            seen.add(line)
            entries.append(line)
    if not entries:
        errors.append(f"{ALLOWLIST}: no entries")
    for name in REQUIRED:
        if name not in seen:
            errors.append(f"{ALLOWLIST}: required public file {name} is not listed")
    return entries, errors


def tracked_blobs(repo: Path) -> dict[str, tuple[str, str]]:
    """path -> (mode, object id) for every entry committed at HEAD."""
    out = {}
    for record in git(repo, "ls-tree", "-r", "-z", "HEAD").split(b"\0"):
        if not record:
            continue
        meta, path = record.split(b"\t", 1)
        mode, kind, oid = meta.decode().split()
        out[path.decode("utf-8", errors="surrogateescape")] = (mode, oid if kind == "blob" else "")
    return out


def stage(repo: Path, out: Path) -> list[str]:
    """Stage exactly the allowlisted files into `out`. Returns the published paths; raises StagingError otherwise."""
    blobs = tracked_blobs(repo)
    # The list itself is read from the commit too, so an uncommitted local edit can neither widen nor narrow publication.
    mode, oid = blobs.get(ALLOWLIST.as_posix(), ("", ""))
    if mode not in REGULAR_MODES or not oid:
        raise StagingError(f"{ALLOWLIST} is not committed as a regular file at HEAD")
    entries, errors = parse_allowlist(git(repo, "cat-file", "blob", oid).decode("utf-8"))
    for path in entries:
        mode, oid = blobs.get(path, ("", ""))
        if not mode:
            errors.append(f"{path}: listed but not tracked at HEAD")
        elif mode not in REGULAR_MODES or not oid:
            errors.append(f"{path}: not a regular file at HEAD (mode {mode}); symbolic links and submodules are never published")
    if errors:
        raise StagingError("\n".join(errors))
    if out.exists() and (out.is_symlink() or not out.is_dir() or any(out.iterdir())):
        raise StagingError(f"output {out} must be a new or empty directory")
    out.mkdir(parents=True, exist_ok=True)
    root = out.resolve()
    digests = {}
    for path in entries:
        data = git(repo, "cat-file", "blob", blobs[path][1])
        target = out / path
        if not target.resolve().is_relative_to(root):
            raise StagingError(f"{path}: resolves outside the artifact")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        digests[path] = hashlib.sha256(data).hexdigest()
    # Verify the artifact independently of how it was written: exactly the listed files, regular, byte-identical.
    found = {}
    for dirpath, dirnames, filenames in os.walk(out):
        for name in dirnames + filenames:
            p = Path(dirpath) / name
            if p.is_symlink():
                raise StagingError(f"{p.relative_to(out)}: symbolic link in the artifact")
        for name in filenames:
            p = Path(dirpath) / name
            found[p.relative_to(out).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    if found != digests:
        extra, missing = sorted(set(found) - set(digests)), sorted(set(digests) - set(found))
        raise StagingError(f"artifact does not match {ALLOWLIST}: extra={extra} missing={missing}")
    return entries


def unlisted_candidates(repo: Path, entries: list[str]) -> list[str]:
    """Tracked files that look publishable but are not listed: reported for review, never published."""
    listed = set(entries)
    return sorted(p for p in tracked_blobs(repo) if p not in listed and not p.startswith(FORBIDDEN_PREFIXES)
                  and not p.lower().endswith(".md") and (p.startswith(("assets/", "data/")) or p.endswith(".html")))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--out", type=Path, help="directory to stage the artifact into (must be new or empty)")
    group.add_argument("--check", action="store_true", help="validate the allowlist by staging into a temporary directory")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="repository root (default: current directory)")
    args = parser.parse_args(argv)
    try:
        if args.check:
            with tempfile.TemporaryDirectory() as tmp:
                entries = stage(args.repo, Path(tmp) / "site")
        else:
            entries = stage(args.repo, args.out)
    except StagingError as exc:
        print(f"FAIL: Pages artifact not staged:\n{exc}", file=sys.stderr)
        return 1
    for path in unlisted_candidates(args.repo, entries):
        print(f"NOTE: {path} is tracked but not in {ALLOWLIST}; it is not published", file=sys.stderr)
    print(f"PASS: Pages artifact staged from {ALLOWLIST} ({len(entries)} files, byte-identical to HEAD).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
