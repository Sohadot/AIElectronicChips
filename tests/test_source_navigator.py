"""Tests for IDE-017: the Institutional Evidence Navigator on /sources/."""

from __future__ import annotations

import csv
import functools
import http.server
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import render_source_navigator as render  # noqa: E402
import validate_public_launch as launch  # noqa: E402
import validate_source_navigator as v  # noqa: E402

NODE = shutil.which("node")
PLAYWRIGHT = next((p for p in (os.environ.get("PLAYWRIGHT_MODULE", ""), "/opt/node22/lib/node_modules/playwright")
                   if p and Path(p).is_dir()), None)
REQUIRE_BROWSER = os.environ.get("AEC_REQUIRE_BROWSER") == "1"
REGISTRATION = ("The registry records source identity and metadata, including entries still pending review. "
                "Registration does not verify any claim.")


def registry():
    return json.loads(render.REGISTRY.read_text(encoding="utf-8"))


def records():
    return registry()["source_records"]


def page():
    return render.PAGE.read_text(encoding="utf-8")


def script():
    return v.SCRIPT.read_text(encoding="utf-8")


def year(r):
    return (r.get("publication_date") or r.get("effective_date") or "")[:4]


def issue_sources():
    issues = json.loads(render.CONFLICTS.read_text(encoding="utf-8"))["issues"]
    return {s for i in issues for s in i["source_ids"]}


class PageTests(unittest.TestCase):
    def test_validator_passes_and_is_wired(self):
        self.assertEqual(v.check_all(), [])
        self.assertTrue(render.in_sync())
        self.assertIn('"validate_source_navigator.py"', (ROOT / "scripts" / "validate_all.py").read_text(encoding="utf-8"))

    def test_every_record_rendered_once_with_its_metadata(self):
        p = page()
        ids = re.findall(r'<li class="nav-source" id="nav-([a-z0-9-]+)"', p)
        self.assertEqual(sorted(ids), sorted(r["id"] for r in records()))
        self.assertEqual(len(ids), 76)
        for r in records():
            item = re.search(rf'<li class="nav-source" id="nav-{r["id"]}".*?\n</li>', p, re.S).group(0)
            self.assertIn(f'data-status="{r["status"]}"', item)
            self.assertIn(f'data-year="{year(r)}"', item)
            self.assertEqual(set(re.search(r'data-layers="([^"]*)"', item).group(1).split()), set(r["ontology_layers"]))
            self.assertIn(f'href="#source-{r["id"]}"', item)
            self.assertIn(f'id="source-{r["id"]}"', p)  # the linked inspection row exists

    def test_pending_sources_visible_and_nothing_promoted(self):
        pending = [r["id"] for r in records() if r["status"] == "pending_review"]
        self.assertEqual(len(pending), 2)
        for sid in pending:
            item = re.search(rf'<li class="nav-source" id="nav-{sid}".*?\n</li>', page(), re.S).group(0)
            self.assertIn("nav-pending", item)
            self.assertIn("Pending review", item)
        section = v.block(page())
        self.assertIsNone(v.INVENTED.search(v.own_text(section)))
        self.assertIn(REGISTRATION, section)
        self.assertNotIn("has passed identity and metadata review", section)

    def test_status_is_never_promoted_by_registration(self):
        # Every record keeps its registry status on the page; pending records are labelled, and nothing says "verified".
        p = page()
        for r in records():
            item = re.search(rf'<li class="nav-source" id="nav-{r["id"]}".*?\n</li>', p, re.S).group(0)
            self.assertIn(f'class="nav-status{" nav-pending" if r["status"] != "active" else ""}" data-value="{r["status"]}"', item)
            meta = re.search(r'<p class="nav-meta">.*?</p>', item).group(0)
            self.assertNotRegex(meta.lower(), r"\bverified\b|\bvalidated\b|\bapproved\b")
        self.assertEqual(sorted(r["id"] for r in records() if r["status"] == "pending_review"),
                         ["asml-2024-annual-reports", "ucie-2-specification-release-2024"])

    def test_commercial_pointer_restrained(self):
        section = v.block(page())
        self.assertEqual(section.count('href="/strategic-availability/"'), 1)
        for name in v.OFFERINGS:
            self.assertIn(name, section)
        self.assertIsNone(re.search(r"(?i)[$€£]\s?\d|subscri|checkout", v.own_text(section)))

    def test_script_page_and_publication(self):
        self.assertIn("sources/index.html", launch.SCRIPT_ALLOWED_PAGES)
        self.assertIn('<script src="/assets/js/source-navigator.js" defer></script>', page())
        allow = [l for l in (ROOT / ".github" / "pages-allowlist.txt").read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")]
        self.assertIn("assets/js/source-navigator.js", allow)
        self.assertEqual(allow, sorted(allow))
        self.assertEqual(len(allow), 50)
        for internal in ("scripts/render_source_navigator.py", "scripts/validate_source_navigator.py", "tests/test_source_navigator.py"):
            self.assertNotIn(internal, allow)


class NegativeTests(unittest.TestCase):
    def assertFlags(self, p, pattern):
        errs = v.check_page(p, registry())
        self.assertTrue(any(re.search(pattern, e) for e in errs), f"expected /{pattern}/ in {errs}")

    def test_tampered_page(self):
        p = page()
        first = records()[0]["id"]
        self.assertFlags(p.replace(f'id="nav-{first}"', 'id="nav-invented-source"', 1), "every registry record exactly once")
        pend = next(r for r in records() if r["status"] == "pending_review")
        item = re.search(rf'<li class="nav-source" id="nav-{pend["id"]}".*?\n</li>', p, re.S).group(0)
        self.assertFlags(p.replace(item, item.replace('data-status="pending_review"', 'data-status="active"')), "status or source type")
        self.assertFlags(p.replace(item, item.replace(" nav-pending", "")), "marked visibly")
        r0 = records()[0]
        self.assertFlags(p.replace(f'href="{r0["canonical_url"]}"', 'href="https://example.invalid/"', 1), "canonical URL")
        self.assertFlags(p.replace(r0["use_limitations"][0], "No limitation", 1), "recorded text missing")
        self.assertFlags(p.replace("<h2 id=\"navigator-title\">Evidence navigator</h2>", "<h2 id=\"navigator-title\">Evidence navigator</h2><p>Trust score: 9</p>"),
                         "evaluative wording")
        self.assertFlags(p.replace("Registration does not verify any claim.", "Registration confirms each claim."), "boundary wording")
        self.assertFlags(p.replace("The registry records source identity and metadata, including entries still pending review.",
                                   "A registered source has passed identity and metadata review."), "completed review")
        self.assertFlags(p.replace("Scoped work beyond the public inventory</h3>", "Scoped work beyond the public inventory</h3><p>From $499 per month</p>"),
                         "no prices")
        self.assertFlags(p.replace('<script src="/assets/js/source-navigator.js" defer></script>',
                                   '<script src="/assets/js/source-navigator.js" defer></script><script src="https://cdn.example/x.js"></script>'),
                         "exactly the local deferred navigator script")

    def test_tampered_script(self):
        js = script()
        for bad in ('fetch("/collect", {method: "POST"});', "localStorage.setItem('x', 1);", "el.innerHTML = q;", "history.pushState({}, '', '?q=1');",
                    "navigator.sendBeacon('/x');"):
            with self.subTest(bad=bad):
                self.assertTrue(v.check_script(js + "\n" + bad))
        self.assertTrue(v.check_script(js.replace("csvCell", "cell")))
        self.assertTrue(v.check_script(js + "\n// trust score"))


@unittest.skipUnless(NODE, "node is not installed")
class CsvTests(unittest.TestCase):
    def test_formula_injection_neutralised(self):
        code = ("global.window = {}; require(%s);" % json.dumps(str(v.SCRIPT)) +
                "console.log(JSON.stringify(['=1+1','+x','-x','@x','\\tx','\\rx','a\"b','plain',null].map(window.AECSourceNavigator.csvCell)))")
        out = json.loads(subprocess.run([NODE, "-e", code], capture_output=True, text=True, check=True).stdout)
        self.assertEqual(out, ["\"'=1+1\"", "\"'+x\"", "\"'-x\"", "\"'@x\"", "\"'\tx\"", "\"'\rx\"", '"a""b"', '"plain"', '""'])


@functools.lru_cache(maxsize=1)
def browser_run():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            js = Path(tmp) / "drive.js"
            js.write_text(BROWSER_SCRIPT, encoding="utf-8")
            out = subprocess.run([NODE, str(js), f"http://127.0.0.1:{server.server_address[1]}/sources/", tmp], capture_output=True, text=True,
                                 timeout=180, env={**os.environ, "NODE_PATH": str(Path(PLAYWRIGHT).parent)})
            if out.returncode != 0:
                raise AssertionError(out.stderr + out.stdout)
            r = json.loads(out.stdout.strip().splitlines()[-1])
            r["port"] = server.server_address[1]
            return r
    finally:
        server.shutdown()
        server.server_close()


class BrowserTests(unittest.TestCase):
    """Drive /sources/ in headless Chromium. Required in CI (AEC_REQUIRE_BROWSER=1)."""

    @classmethod
    def setUpClass(cls):
        if not (NODE and PLAYWRIGHT):
            if REQUIRE_BROWSER:
                raise AssertionError("AEC_REQUIRE_BROWSER=1 but node or Playwright is not available")
            raise unittest.SkipTest("node and Playwright are not available")
        cls.r = browser_run()
        print(f"\nBrowser under test: {cls.r['browser']}", file=sys.stderr)

    def ids(self, pred):
        return sorted(x["id"] for x in records() if pred(x))

    def test_loads_and_no_js_fallback(self):
        r = self.r
        self.assertTrue(r["browser"].startswith("chromium"))
        self.assertEqual(r["errors"], [])
        self.assertEqual(r["initial"]["visible"], 76)
        self.assertTrue(r["initial"]["controls_visible"])
        self.assertEqual(r["initial"]["count"], "Showing 76 of 76 registered sources (no filters).")
        self.assertEqual(r["no_js"], {"items": 76, "visible": 76, "controls_visible": False, "noscript": True})

    def test_single_and_combined_filters(self):
        f = self.r["filters"]
        for layer in render.LAYER_ORDER:
            self.assertEqual(f["layer_" + layer], self.ids(lambda x: layer in x["ontology_layers"]), layer)
        three = {"memory", "packaging", "interconnect"}
        self.assertEqual(f["research_any"], self.ids(lambda x: three & set(x["ontology_layers"])))
        self.assertEqual(f["research_all"], self.ids(lambda x: three <= set(x["ontology_layers"])))
        self.assertEqual(f["strategy"], self.ids(lambda x: {"memory", "packaging"} <= set(x["ontology_layers"]) and x["id"] in issue_sources()))
        self.assertEqual(f["maintenance"], self.ids(lambda x: x["source_type"] == "company_announcement" and x["status"] == "active"))
        self.assertEqual(f["year_2025"], self.ids(lambda x: year(x) == "2025"))
        self.assertEqual(f["pending"], self.ids(lambda x: x["status"] == "pending_review"))
        blobs = dict(re.findall(r'data-id="([a-z0-9-]+)"[^>]*data-search="([^"]*)"', page()))
        self.assertEqual(f["search_hbm4_base"], sorted(i for i, s in blobs.items() if "hbm4" in s and "base" in s))
        self.assertTrue(f["search_hbm4_base"])

    def test_empty_result_and_reset(self):
        e = self.r["empty"]
        self.assertEqual(e["visible"], 0)
        self.assertTrue(e["message"])
        self.assertIn("Showing 0 of 76", e["count"])
        self.assertEqual(self.r["reset"], {"visible": 76, "checked": 1, "search": "", "year": "", "message": False,
                                           "count": "Showing 76 of 76 registered sources (no filters)."})

    def test_json_export_is_the_registry_record(self):
        j = self.r["json"]
        self.assertEqual((j["format"], j["format_version"], j["registry_version"]), ("aec-source-inventory", "1.0.0", registry()["registry_version"]))
        self.assertIn(REGISTRATION, j["boundary"])
        self.assertEqual(j["filters"]["layers"], ["packaging", "memory", "interconnect"])
        by_id = {x["id"]: x for x in records()}
        self.assertEqual(j["count"], len(j["sources"]))
        self.assertEqual(sorted(s["record"]["id"] for s in j["sources"]), self.r["filters"]["research_any"])
        for s in j["sources"]:
            self.assertEqual(s["record"], by_id[s["record"]["id"]])  # exact: nothing added, nothing dropped
            self.assertEqual(s["context"]["page_record"], "/sources/#source-" + s["record"]["id"])
        self.assertNotRegex(json.dumps(j).lower(), r"\btrust score\b|\bconfidence score\b|\branked\b")

    def test_csv_export_matches_and_is_safe(self):
        rows = list(csv.reader(io.StringIO(self.r["csv"], newline="")))
        head = rows[0]
        self.assertEqual(head[:3], ["id", "title", "publisher"])
        self.assertTrue(all(len(row) == len(head) for row in rows))
        body = [row for row in rows[1:] if row[0] in {x["id"] for x in records()}]
        self.assertEqual(sorted(row[0] for row in body), self.r["filters"]["maintenance"])
        by_id = {x["id"]: x for x in records()}
        for row in body:
            rec = dict(zip(head, row))
            src = by_id[rec["id"]]
            self.assertEqual(rec["canonical_url"], src["canonical_url"])
            self.assertEqual(rec["use_limitations"], " | ".join(src["use_limitations"]))
        meta = {row[0]: row[1] for row in rows if row[0] in ("boundary", "filters", "count", "format")}
        self.assertIn(REGISTRATION, meta["boundary"])
        self.assertIn("status active", meta["filters"])
        self.assertTrue(all(line.startswith('"') for line in self.r["csv"].strip().split("\r\n")))

    def test_keyboard_operation(self):
        k = self.r["keyboard"]
        self.assertEqual(k["first_checkbox_after_tab"], "nav-layer")
        self.assertTrue(k["toggled_by_space"])
        self.assertIn("any of layers design", k["count_after_space"])
        self.assertEqual(k["download_by_enter"], "aec-source-inventory.json")

    def test_privacy_mobile_and_reload(self):
        r = self.r
        self.assertEqual(r["flagged_requests"], [])
        self.assertEqual(r["storage"], {"local": 0, "session": 0, "cookie": ""})
        self.assertEqual(r["url_after"], f"http://127.0.0.1:{r['port']}/sources/")
        self.assertEqual(r["after_reload"], {"visible": 76, "checked": 1, "search": ""})
        self.assertEqual(r["mobile_overflow"], 0)
        self.assertEqual(r["injection"], {"flag": 0, "search_echo_is_text": True})


BROWSER_SCRIPT = r"""
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [url, dir] = process.argv.slice(2);
  const browser = await chromium.launch();
  const context = await browser.newContext({ acceptDownloads: true, viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  const flagged = [], errors = [];
  context.on('request', (q) => { const u = new URL(q.url()); if (u.origin !== new URL(url).origin || q.method() !== 'GET') flagged.push(q.method() + ' ' + q.url()); });
  page.on('pageerror', (e) => errors.push(String(e)));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(url, { waitUntil: 'load' });
  const state = () => page.evaluate(() => ({
    visible: [...document.querySelectorAll('li.nav-source')].filter((li) => !li.hidden).length,
    ids: [...document.querySelectorAll('li.nav-source')].filter((li) => !li.hidden).map((li) => li.getAttribute('data-id')).sort(),
    count: document.querySelector('.nav-count').textContent,
    message: !document.querySelector('.nav-empty').hidden,
    checked: document.querySelectorAll('.nav-controls input:checked').length,
    search: document.querySelector('#nav-search').value, year: document.querySelector('#nav-year').value,
    controls_visible: !document.querySelector('.nav-controls').hidden }));
  const reset = () => page.getByRole('button', { name: 'Reset filters' }).click();
  const layer = (l) => page.check(`input[name=nav-layer][value=${l}]`);
  const initial = await state();
  const filters = {};
  for (const l of ['design', 'fabrication', 'packaging', 'memory', 'interconnect', 'power_thermal', 'controls', 'deployment']) {
    await reset(); await layer(l); filters['layer_' + l] = (await state()).ids;
  }
  await reset(); for (const l of ['packaging', 'memory', 'interconnect']) await layer(l);
  filters.research_any = (await state()).ids;
  const [dj] = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: 'Export shown sources (JSON)' }).click()]);
  await dj.saveAs(dir + '/inv.json');
  await page.check('input[name=nav-layer-mode][value=all]');
  filters.research_all = (await state()).ids;
  await reset(); await layer('memory'); await layer('packaging'); await page.check('input[name=nav-layer-mode][value=all]'); await page.check('input[name=nav-issues]');
  filters.strategy = (await state()).ids;
  await reset(); await page.check('input[name=nav-type][value=company_announcement]'); await page.check('input[name=nav-status][value=active]');
  filters.maintenance = (await state()).ids;
  const [dc] = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: 'Export shown sources (CSV)' }).click()]);
  await dc.saveAs(dir + '/inv.csv');
  await reset(); await page.selectOption('#nav-year', '2025'); filters.year_2025 = (await state()).ids;
  await reset(); await page.check('input[name=nav-status][value=pending_review]'); filters.pending = (await state()).ids;
  await reset(); await page.fill('#nav-search', 'HBM4  Base'); filters.search_hbm4_base = (await state()).ids;
  await reset(); await page.selectOption('#nav-year', 'undated'); await layer('controls');
  const empty = await state();
  await reset();
  const afterReset = await state();
  // Injection probe through the search box: it is matched as text and echoed only through textContent.
  await page.fill('#nav-search', '<img src=x onerror="window.__x=1">');
  const injection = await page.evaluate(() => ({ flag: window.__x || 0,
    search_echo_is_text: !document.querySelector('.nav-count img') && document.querySelector('.nav-count').textContent.includes('<img') }));
  await reset();
  const storage = await page.evaluate(() => ({ local: localStorage.length, session: sessionStorage.length, cookie: document.cookie }));
  // Keyboard: focus the search box, Shift+Tab back into the filters is not needed; tab from the panel start.
  await page.locator('.nav-group[data-group=layers] input').first().focus();
  await page.keyboard.press('Shift+Tab'); await page.keyboard.press('Tab');
  const firstName = await page.evaluate(() => document.activeElement.name);
  await page.keyboard.press('Space');
  const toggled = await page.evaluate(() => document.activeElement.checked);
  const countAfter = await page.locator('.nav-count').textContent();
  await page.getByRole('button', { name: 'Export shown sources (JSON)' }).focus();
  const [dk] = await Promise.all([page.waitForEvent('download'), page.keyboard.press('Enter')]);
  await layer('memory');
  const urlAfter = page.url();
  await page.reload({ waitUntil: 'load' });
  const reloaded = await state();
  const m = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  const mp = await m.newPage(); await mp.goto(url, { waitUntil: 'load' });
  await mp.check('input[name=nav-layer][value=memory]');
  const mobileOverflow = await mp.evaluate(() => document.documentElement.scrollWidth - innerWidth);
  await m.close();
  const nj = await browser.newContext({ javaScriptEnabled: false });
  const np = await nj.newPage(); await np.goto(url, { waitUntil: 'load' });
  const noJs = await np.evaluate(() => { const items = [...document.querySelectorAll('li.nav-source')];
    return { items: items.length, visible: items.filter((li) => li.offsetParent !== null).length,
      controls_visible: document.querySelector('.nav-controls').offsetParent !== null,
      noscript: [...document.querySelectorAll('#source-navigator p')].some((p) => p.textContent.includes('Without JavaScript') && p.offsetParent !== null) }; });
  await nj.close();
  console.log(JSON.stringify({ browser: browser.browserType().name() + ' ' + browser.version(), errors, initial: { visible: initial.visible,
    count: initial.count, controls_visible: initial.controls_visible }, filters, empty: { visible: empty.visible, message: empty.message, count: empty.count },
    reset: { visible: afterReset.visible, checked: afterReset.checked, search: afterReset.search, year: afterReset.year, message: afterReset.message, count: afterReset.count },
    json: JSON.parse(fs.readFileSync(dir + '/inv.json', 'utf8')), csv: fs.readFileSync(dir + '/inv.csv', 'utf8'), injection, storage,
    keyboard: { first_checkbox_after_tab: firstName, toggled_by_space: toggled, count_after_space: countAfter, download_by_enter: dk.suggestedFilename() },
    flagged_requests: flagged, url_after: urlAfter, after_reload: { visible: reloaded.visible, checked: reloaded.checked, search: reloaded.search },
    mobile_overflow: mobileOverflow, no_js: noJs }));
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
"""


if __name__ == "__main__":
    unittest.main()
