"""Regression tests for IDE-010: the Industrial Evidence Request & Research Workbench."""

from __future__ import annotations

import copy
import csv
import io
import functools
import http.server
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
import render_research_workbench as render  # noqa: E402
import validate_evidence_requests as v  # noqa: E402

NODE = shutil.which("node")
PLAYWRIGHT = next((p for p in (os.environ.get("PLAYWRIGHT_MODULE", ""), "/opt/node22/lib/node_modules/playwright")
                   if p and Path(p).is_dir()), None)
# CI sets AEC_REQUIRE_BROWSER=1 after installing Playwright and Chromium: the browser test then fails instead of skipping.
REQUIRE_BROWSER = os.environ.get("AEC_REQUIRE_BROWSER") == "1"


@functools.lru_cache(maxsize=1)
def context():
    return v.load_context()


def model():
    return json.loads(v.MODEL.read_text(encoding="utf-8"))


def req(m, rid):
    return next(r for w in m["workflows"] for r in w["requirements"] if r["id"] == rid)


def errors_for(m):
    return v.check_model(m, *context())


def page():
    return v.PAGE.read_text(encoding="utf-8")


def script():
    return v.SCRIPT.read_text(encoding="utf-8")


class ModelTests(unittest.TestCase):
    def test_everything_validates(self):
        self.assertEqual(v.check_all(), [])

    def test_exactly_three_workflows_of_ten_to_fifteen(self):
        m = model()
        self.assertEqual([w["id"] for w in m["workflows"]], v.EXPECTED)
        self.assertEqual([w["letter"] for w in m["workflows"]], ["A", "B", "C"])
        for w in m["workflows"]:
            self.assertTrue(10 <= len(w["requirements"]) <= 15, w["id"])

    def test_bandwidth_workflow_keeps_every_published_figure(self):
        text = json.dumps(model()["workflows"][1])
        for fig in ("896 GB/s", "22 TB/s", "19.2 TB/s", "3.6 TB/s", "3 TB/s"):
            self.assertIn(fig, text)
        self.assertIn("ec-mi300x-infinity-fabric-scope", text)
        self.assertIn("ec-rubin-memory-bandwidth", text)
        self.assertIn("ec-nvlink6-per-gpu", text)

    def test_rack_workflow_keeps_stages_distinct_and_ordered(self):
        m = model()
        stages = [r["deployment_stage"] for r in m["workflows"][2]["requirements"]]
        order = [s for s in m["deployment_stages"] if s in stages]
        self.assertEqual(order, m["deployment_stages"])
        self.assertEqual(stages, sorted(stages, key=m["deployment_stages"].index), "requirements follow the stage order")

    def test_statuses_never_mean_verified(self):
        m = model()
        self.assertEqual(list(m["session_statuses"]), ["not_requested", "requested", "received", "needs_expert_review"])
        self.assertIn("not reviewed", m["session_statuses"]["received"])
        self.assertNotRegex(json.dumps(m["session_statuses"]), r"(?i)verified|approved|valid")

    def test_unverified_cdna4_edition_not_used_as_evidence(self):
        text = json.dumps(model())
        for marker in ("MI350-007", "PID#2258402"):
            for m in re.finditer(re.escape(marker), text):
                self.fail(f"unverified edition marker {marker} appears in the model")

    def test_does_not_create_atlas_relationships(self):
        atlas = json.loads((ROOT / "data" / "dependency-atlas.json").read_text(encoding="utf-8"))
        self.assertEqual(len(atlas.get("relationships", [])), 0)


class NegativeModelTests(unittest.TestCase):
    def assertFlags(self, m, pattern):
        errs = errors_for(m)
        self.assertTrue(any(re.search(pattern, e) for e in errs), f"expected /{pattern}/ in {errs}")

    def test_unknown_finding(self):
        m = model(); req(m, "ra-01-interface-revision")["finding_ids"].append("hbm-not-a-finding")
        self.assertFlags(m, r"finding hbm-not-a-finding does not exist")

    def test_unregistered_source(self):
        m = model(); req(m, "ra-01-interface-revision")["source_ids"].append("made-up-source-2026")
        self.assertFlags(m, r"made-up-source-2026 is not registered")

    def test_source_not_backed_by_findings(self):
        m = model(); r = req(m, "rc-04-busbar")
        r["source_ids"].append("tgg-pue-comprehensive-examination-2013")
        self.assertFlags(m, r"not cited by the requirement's findings")

    def test_pending_review_source(self):
        registry = context()[0]
        pending = next(s for s, rec in registry.items() if rec["status"] == "pending_review")
        m = model(); req(m, "ra-01-interface-revision")["source_ids"].append(pending)
        self.assertFlags(m, r"not active evidence")

    def test_unknown_conflict_and_broken_reference(self):
        m = model(); r = req(m, "rb-03-stack-bandwidth")
        r["conflict_ids"].append("ec-does-not-exist"); r["reference"] = "/hbm-memory/#no-such-anchor"
        self.assertFlags(m, r"register issue ec-does-not-exist does not exist")
        self.assertFlags(m, r"does not resolve")

    def test_readiness_and_approval_claims(self):
        for text in ("The HBM4 stack is qualified for Rubin", "The rack is ready for production",
                     "Interconnect is certified", "Integration is approved"):
            m = model(); req(m, "ra-12-production-integration")["why_it_matters"] = text
            self.assertFlags(m, r"readiness or verdict language")

    def test_comparative_claim(self):
        m = model(); req(m, "rb-04-device-memory-bandwidth")["why_it_matters"] = "Rubin outperforms MI355X on memory bandwidth"
        self.assertFlags(m, r"verdict language")

    def test_analytical_recommendation_cannot_cite_sources(self):
        m = model(); w = m["workflows"][2]
        r = req(m, "rb-11-software-configuration")
        r["finding_ids"] = ["pt-ocp-bus-bar"]
        self.assertFlags(m, r"analytical recommendation cannot cite")

    def test_published_without_sources(self):
        m = model(); r = req(m, "rc-04-busbar"); r["source_ids"] = []
        self.assertFlags(m, r"needs the reviewed sources")

    def test_unverified_edition_as_evidence(self):
        m = model(); req(m, "rb-05-link-bandwidth-direction")["why_it_matters"] += " AMD endnote MI350-007 settles it."
        self.assertFlags(m, r"unverified 2025 CDNA 4 edition")

    def test_dropped_published_figure(self):
        m = model()
        for r in m["workflows"][1]["requirements"]:
            for k, val in r.items():
                if isinstance(val, str):
                    r[k] = val.replace("19.2 TB/s", "a second figure")
                elif isinstance(val, list):
                    r[k] = [x.replace("19.2 TB/s", "a second figure") if isinstance(x, str) else x for x in val]
        self.assertFlags(m, r"published figure '19.2 TB/s'")

    def test_missing_requirements_and_workflow(self):
        m = model(); m["workflows"][0]["requirements"] = m["workflows"][0]["requirements"][:5]
        self.assertFlags(m, r"at least ten requirements")
        m = model(); m["workflows"].pop()
        self.assertFlags(m, r"workflows must be exactly")

    def test_missing_stage(self):
        m = model(); w = m["workflows"][2]
        w["requirements"] = [r for r in w["requirements"] if r["deployment_stage"] != "commissioned"]
        self.assertFlags(m, r"'commissioned'")

    def test_review_status_cannot_be_promoted(self):
        m = model(); m["scientific_review"] = "approved"
        self.assertFlags(m, r"scientific_review 'pending'")


class ScriptAndPageTests(unittest.TestCase):
    def test_script_has_no_transmission_storage_or_html_injection(self):
        self.assertEqual(v.check_script(script()), [])
        for bad in ("fetch('/x')", "navigator.sendBeacon(u)", "localStorage.setItem('a', b)", "sessionStorage.x = 1",
                    "el.innerHTML = note", "document.cookie = 'a'", "history.pushState({}, '', '?s=1')",
                    "location.hash = 'x'", "new XMLHttpRequest()", "indexedDB.open('x')"):
            errs = v.check_script(script() + "\n" + bad + ";\n")
            self.assertTrue(any("forbidden API" in e for e in errs), bad)

    def test_note_field_keeps_browser_spelling_services_off(self):
        text = script()
        self.assertIn('setAttribute("spellcheck", "false")', text)
        self.assertIn('setAttribute("autocorrect", "off")', text)
        self.assertNotRegex(text, r'spellcheck"?\s*,\s*"true')
        bad = text.replace('note.setAttribute("spellcheck", "false");', 'note.setAttribute("spellcheck", "true");')
        self.assertTrue(any("spell-check" in e for e in v.check_script(bad)))
        bad = text.replace('note.setAttribute("autocorrect", "off");', "")
        self.assertTrue(any("autocorrect" in e for e in v.check_script(bad)))

    def test_privacy_copy_is_accurate(self):
        self.assertIn("this website does not submit, save or add to the address", page())
        self.assertTrue(any("browser-wide privacy" in e for e in v.check_script(script() + '\n"not sent anywhere";\n')))
        self.assertTrue(any("browser-wide privacy" in e for e in v.check_page(page().replace("Privacy:", "Privacy: completely private."), model())))
        self.assertTrue(v.check_page(page().replace("follow your own settings", "are disabled"), model()))

    def test_script_safeguards_required(self):
        self.assertTrue(v.check_script(script().replace("not been independently validated", "x")))
        self.assertTrue(v.check_script(script().replace("csvCell", "cell")))
        self.assertTrue(any("status vocabulary" in e for e in v.check_script(script() + '\n["verified", "Verified"];\n')))

    def test_page_static_catalog(self):
        text = page()
        self.assertEqual(v.check_page(text, model()), [])
        for w in model()["workflows"]:
            for r in w["requirements"]:
                self.assertIn(f'id="{r["id"]}"', text)
                for c in r["conflict_ids"]:
                    self.assertIn(f'href="/sources/#{c}"', text)
        # No inputs, forms or visible toolbar without JavaScript.
        self.assertNotRegex(text, r"<(?:input|textarea|form|select)\b")
        self.assertEqual(text.count('class="wb-toolbar"'), 3)
        self.assertEqual(len(re.findall(r'class="wb-toolbar"[^>]*\bhidden\b', text)), 3)
        self.assertIn("<noscript>", text)

    def test_page_negative(self):
        m = model(); text = page()
        self.assertTrue(v.check_page(text.replace('id="rb-03-stack-bandwidth"', 'id="x"'), m))
        self.assertTrue(v.check_page(text.replace("</head>", '<script src="https://cdn.example.com/a.js"></script></head>'), m))
        self.assertTrue(v.check_page(text.replace("<noscript>", "<div>").replace("</noscript>", "</div>"), m))
        self.assertTrue(v.check_page(text.replace('href="/data/industrial-evidence-requests.json"', 'href="/data/"'), m))

    def test_render_in_sync(self):
        self.assertTrue(render.in_sync())

    def test_fails_closed_when_files_missing(self):
        for attr in ("MODEL", "PAGE", "SCRIPT"):
            original = getattr(v, attr)
            try:
                setattr(v, attr, ROOT / "does-not-exist" / original.name)
                errs = v.check_all()
                self.assertTrue(errs and "required workbench file missing" in errs[0], attr)
            finally:
                setattr(v, attr, original)

    def test_wired_into_gates(self):
        self.assertIn("validate_evidence_requests.py", (ROOT / "scripts" / "validate_all.py").read_text(encoding="utf-8"))
        launch = (ROOT / "scripts" / "validate_public_launch.py").read_text(encoding="utf-8")
        self.assertIn('"research-workbench/index.html"', launch)
        self.assertIn("/research-workbench/</loc>", (ROOT / "sitemap.xml").read_text(encoding="utf-8"))
        ci = (ROOT / ".github" / "workflows" / "validate-and-deploy.yml").read_text(encoding="utf-8")
        self.assertIn("playwright@1.63.0", ci)
        self.assertGreaterEqual(ci.count("AEC_REQUIRE_BROWSER: '1'"), 2, "CI must require the browser test, not skip it")
        self.assertIn("tests.test_research_workbench.BrowserTests", ci)

    def test_contextual_links(self):
        for route, anchor in (("sovereignty-stack", ""), ("hbm-memory", "#workflow-hbm4-integration"),
                              ("interconnects", "#workflow-bandwidth-comparison"),
                              ("ai-chip-infrastructure", "#workflow-rack-deployment")):
            self.assertIn(f'href="/research-workbench/{anchor}"', (ROOT / route / "index.html").read_text(encoding="utf-8"))


@unittest.skipUnless(NODE, "node is not installed")
class CsvEscapeTests(unittest.TestCase):
    def run_node(self, code):
        prog = "var window = {};\n" + script() + "\n" + code
        out = subprocess.run([NODE, "-e", prog], capture_output=True, text=True, timeout=30)
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout)

    def test_formula_injection_neutralised(self):
        cases = ["=HYPERLINK(\"http://x\")", "+1", "-2+3", "@SUM(A1)", "\tcmd", "\rcmd", 'say "hi"', "plain", "", "a,b\nc"]
        got = self.run_node("console.log(JSON.stringify(%s.map(window.AECWorkbench.csvCell)))" % json.dumps(cases))
        self.assertEqual(got[0], '"\'=HYPERLINK(""http://x"")"')
        self.assertEqual(got[1:6], ['"\'+1"', '"\'-2+3"', '"\'@SUM(A1)"', '"\'\tcmd"', '"\'\rcmd"'])
        self.assertEqual(got[6:], ['"say ""hi"""', '"plain"', '""', '"a,b\nc"'])

    def test_build_csv_rows(self):
        got = self.run_node('console.log(JSON.stringify(window.AECWorkbench.buildCsv([["a", "=b"], ["c", null]])))')
        self.assertEqual(got, '"a","\'=b"\r\n"c",""\r\n')


class BrowserTests(unittest.TestCase):
    """Drive the page in headless Chromium: controls, note privacy attributes, JSON/CSV export, print view,
    per-tab state, network silence and no storage. Required in CI (AEC_REQUIRE_BROWSER=1); skipped elsewhere
    only when Node or Playwright is absent."""

    @classmethod
    def setUpClass(cls):
        if not (NODE and PLAYWRIGHT):
            if REQUIRE_BROWSER:
                raise AssertionError("AEC_REQUIRE_BROWSER=1 but node or Playwright is not available")
            raise unittest.SkipTest("node and Playwright are not available")
        class Quiet(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass
        handler = functools.partial(Quiet, directory=str(ROOT))
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_interaction_and_export(self):
        port = self.server.server_address[1]
        with tempfile.TemporaryDirectory() as tmp:
            js = Path(tmp) / "drive.js"
            js.write_text(BROWSER_SCRIPT, encoding="utf-8")
            out = subprocess.run([NODE, str(js), f"http://127.0.0.1:{port}/research-workbench/", tmp],
                                 capture_output=True, text=True, timeout=120, env={**os.environ, "NODE_PATH": str(Path(PLAYWRIGHT).parent)})
            self.assertEqual(out.returncode, 0, out.stderr + out.stdout)
            r = json.loads(out.stdout.strip().splitlines()[-1])
        # Proof of a real browser run, printed into the CI log.
        print(f"\nBrowser under test: {r['browser']['name']} {r['browser']['version']}", file=sys.stderr)
        self.assertEqual(r["browser"]["name"], "chromium")
        self.assertRegex(r["browser"]["version"], r"^\d+\.")
        m = model()
        # Three workflows and 41 requirements, each with a visible reference link.
        self.assertEqual([w["id"] for w in r["reqs"]], v.EXPECTED)
        for got, w in zip(r["reqs"], m["workflows"]):
            self.assertEqual(got["ids"], [x["id"] for x in w["requirements"]])
            self.assertEqual(got["refs"], len(w["requirements"]))
        self.assertEqual(sum(len(w["ids"]) for w in r["reqs"]), 41)
        # Export is user-initiated: nothing downloads until a button is clicked; each click yields one file.
        self.assertEqual(r["downloads_before_click"], 0)
        self.assertEqual(r["downloads_total"], 4)
        for w in m["workflows"][1:]:
            got = r["other_exports"][w["id"]]
            self.assertEqual(got["workflow"]["id"], w["id"])
            self.assertEqual([x["id"] for x in got["requirements"]], [x["id"] for x in w["requirements"]])
            self.assertTrue(all(x["user_status"] == "not_requested" and x["user_note"] == "" for x in got["requirements"]))
            self.assertIn("not been independently validated", got["disclaimer"])
        # No-JavaScript fallback, in the same real browser.
        self.assertEqual(r["no_js"], {"reqs": 41, "controls": 0, "toolbars_visible": 0, "noscript_visible": True, "data_link": True})
        self.assertEqual(r["radios"], 41 * 4)
        self.assertEqual(r["textareas"], 41)
        self.assertEqual(r["toolbars_visible"], 3)
        self.assertEqual(r["external_or_post_requests"], [])
        self.assertEqual(r["storage"], {"local": 0, "session": 0, "cookie": ""})
        self.assertEqual(r["url_after"], f"http://127.0.0.1:{port}/research-workbench/")
        data = r["json"]
        self.assertEqual(data["format"], "aec-evidence-request-checklist")
        self.assertIn("not been independently validated", data["disclaimer"])
        self.assertEqual(data["workflow"]["id"], "workflow-hbm4-integration")
        self.assertEqual(len(data["requirements"]), 13)
        first = data["requirements"][0]
        self.assertEqual(first["user_status"], "received")
        self.assertEqual(first["user_note"], "=cmd|' /C calc'!A0")
        self.assertTrue(first["reference"].startswith("/hbm-memory/#"))
        self.assertNotIn("score", json.dumps(data).lower())
        self.assertIn("\"'=cmd|' /C calc'!A0\"", r["csv"])
        # CSV is a well-formed table: header, one row per requirement, then disclaimer and timestamp rows.
        rows = list(csv.reader(io.StringIO(r["csv"], newline="")))
        self.assertEqual(rows[0][:2], ["workflow", "requirement_id"])
        self.assertEqual(len(rows), 1 + 13 + 2)
        self.assertTrue(all(len(row) == len(rows[0]) for row in rows[1:14]))
        self.assertEqual([row[1] for row in rows[1:14]], [x["id"] for x in m["workflows"][0]["requirements"]])
        self.assertEqual(rows[1][-2:], ["received", "'=cmd|' /C calc'!A0"])
        self.assertEqual(rows[14][0], "disclaimer")
        self.assertIn("not been independently validated", r["csv"])
        self.assertEqual(r["after_clear"], {"status": "not_requested", "note": ""})
        # Note field: browser spelling and autocorrect services off on every note.
        self.assertEqual(r["note_attrs"], {"count": 41, "spellcheck_false": 41, "prop_false": 41, "autocorrect_off": 41,
                                           "autocapitalize_off": 41, "maxlength": 41})
        # Print: only the chosen workflow, traces opened, everything restored afterwards.
        self.assertEqual(r["print"]["visible"], ["workflow-bandwidth-comparison"])
        self.assertTrue(r["print"]["traces_open"])
        self.assertTrue(r["print"]["chrome_hidden"])
        self.assertEqual(r["after_print"], {"attr": False, "open": 0})
        # Per tab: another tab and a reload start from defaults.
        self.assertEqual(r["other_tab"], {"status": "not_requested", "note": ""})
        self.assertEqual(r["after_reload"], {"status": "not_requested", "note": ""})


BROWSER_SCRIPT = r"""
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [url, dir] = process.argv.slice(2);
  const browser = await chromium.launch();
  const context = await browser.newContext({ acceptDownloads: true });
  const page = await context.newPage();
  const flagged = [];
  let downloads = 0;
  context.on('request', (req) => {
    const u = new URL(req.url());
    if (u.origin !== new URL(url).origin || req.method() !== 'GET') flagged.push(req.method() + ' ' + req.url());
  });
  page.on('download', () => { downloads += 1; });
  await page.goto(url, { waitUntil: 'load' });
  const reqs = await page.evaluate(() => [...document.querySelectorAll('article.wb-workflow')].map((w) => ({
    id: w.id, ids: [...w.querySelectorAll('li.wb-req')].map((li) => li.id),
    refs: [...w.querySelectorAll('li.wb-req .step-link a')].filter((a) => a.offsetParent !== null).length })));
  const radios = await page.locator('li.wb-req .wb-controls input[type=radio]').count();
  const textareas = await page.locator('textarea').count();
  const toolbars = await page.locator('.wb-toolbar:visible').count();
  const wf = page.locator('#workflow-hbm4-integration');
  await wf.locator('li.wb-req').first().locator('input[value=received]').check();
  await wf.locator('li.wb-req').first().locator('textarea').fill("=cmd|' /C calc'!A0");
  const downloadsBeforeClick = downloads;
  const [dj] = await Promise.all([page.waitForEvent('download'), wf.getByRole('button', { name: 'Export JSON' }).click()]);
  await dj.saveAs(dir + '/out.json');
  const [dc] = await Promise.all([page.waitForEvent('download'), wf.getByRole('button', { name: 'Export CSV' }).click()]);
  await dc.saveAs(dir + '/out.csv');
  const otherExports = {};
  for (const id of ['workflow-bandwidth-comparison', 'workflow-rack-deployment']) {
    const w = page.locator('#' + id);
    const [d] = await Promise.all([page.waitForEvent('download'), w.getByRole('button', { name: 'Export JSON' }).click()]);
    await d.saveAs(dir + '/' + id + '.json');
    otherExports[id] = JSON.parse(fs.readFileSync(dir + '/' + id + '.json', 'utf8'));
  }
  const storage = await page.evaluate(() => ({ local: localStorage.length, session: sessionStorage.length, cookie: document.cookie }));
  const first = (p) => p.locator('#ra-01-interface-revision').evaluate((li) => ({
    status: li.querySelector('input[type=radio]:checked').value, note: li.querySelector('textarea').value }));
  const other = await context.newPage();
  await other.goto(url, { waitUntil: 'load' });
  const otherTab = await first(other);
  await other.close();
  const noteAttrs = await page.evaluate(() => {
    const t = [...document.querySelectorAll('textarea')];
    return { count: t.length, spellcheck_false: t.filter((x) => x.getAttribute('spellcheck') === 'false').length,
      prop_false: t.filter((x) => x.spellcheck === false).length,
      autocorrect_off: t.filter((x) => x.getAttribute('autocorrect') === 'off').length,
      autocapitalize_off: t.filter((x) => x.getAttribute('autocapitalize') === 'off').length,
      maxlength: t.filter((x) => x.maxLength === 500).length };
  });
  await page.evaluate(() => { document.body.setAttribute('data-print-workflow', 'workflow-bandwidth-comparison');
    window.dispatchEvent(new Event('beforeprint')); });
  await page.emulateMedia({ media: 'print' });
  const print = await page.evaluate(() => ({
    visible: [...document.querySelectorAll('.wb-workflow')].filter((e) => getComputedStyle(e).display !== 'none').map((e) => e.id),
    traces_open: [...document.querySelectorAll('#workflow-bandwidth-comparison details')].every((d) => d.open),
    chrome_hidden: getComputedStyle(document.querySelector('.site-header')).display === 'none' &&
      getComputedStyle(document.querySelector('.wb-toolbar')).display === 'none' }));
  await page.evaluate(() => window.dispatchEvent(new Event('afterprint')));
  await page.emulateMedia({ media: 'screen' });
  const afterPrint = await page.evaluate(() => ({ attr: document.body.hasAttribute('data-print-workflow'),
    open: [...document.querySelectorAll('details')].filter((d) => d.open).length }));
  await wf.getByRole('button', { name: 'Clear this session' }).click();
  const afterClear = await first(page);
  await wf.locator('li.wb-req').first().locator('input[value=requested]').check();
  await page.reload({ waitUntil: 'load' });
  const afterReload = await first(page);
  const nj = await browser.newContext({ javaScriptEnabled: false });
  const pj = await nj.newPage();
  await pj.goto(url, { waitUntil: 'load' });
  const noJs = await pj.evaluate(() => ({ reqs: document.querySelectorAll('li.wb-req').length,
    controls: document.querySelectorAll('input, textarea, button').length,
    toolbars_visible: [...document.querySelectorAll('.wb-toolbar')].filter((e) => getComputedStyle(e).display !== 'none').length,
    noscript_visible: !!document.querySelector('.wb-noscript') && document.querySelector('.wb-noscript').offsetParent !== null,
    data_link: !!document.querySelector('a[href="/data/industrial-evidence-requests.json"]') }));
  await nj.close();
  console.log(JSON.stringify({ browser: { name: browser.browserType().name(), version: browser.version() },
    reqs, downloads_before_click: downloadsBeforeClick, downloads_total: downloads, other_exports: otherExports, no_js: noJs, radios, textareas, toolbars_visible: toolbars, external_or_post_requests: flagged, storage,
    url_after: page.url(), json: JSON.parse(fs.readFileSync(dir + '/out.json', 'utf8')),
    csv: fs.readFileSync(dir + '/out.csv', 'utf8'), after_clear: afterClear, note_attrs: noteAttrs, print,
    after_print: afterPrint, other_tab: otherTab, after_reload: afterReload }));
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
"""


if __name__ == "__main__":
    unittest.main()
