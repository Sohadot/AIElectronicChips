"""Tests for IDE-015: the Workflow C documentary preflight and the req-nw-north-south correction."""

from __future__ import annotations

import copy
import csv
import functools
import hashlib
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
import render_research_workbench as render  # noqa: E402
import validate_deployment_preflight as v  # noqa: E402
import validate_rack_deployment_dossier as rack  # noqa: E402

NODE = shutil.which("node")
PLAYWRIGHT = next((p for p in (os.environ.get("PLAYWRIGHT_MODULE", ""), "/opt/node22/lib/node_modules/playwright")
                   if p and Path(p).is_dir()), None)
REQUIRE_BROWSER = os.environ.get("AEC_REQUIRE_BROWSER") == "1"
# Files IDE-015 must leave byte-identical: historical releases and records, and the IDE-010 model.
UNCHANGED = {
    "data/research/deployment-evidence-release-006.json": "478648f444fd0f2da2dd80b59d80eeccdd10504f5b0aa2b7b3bd6ba4c43db368",
    "DEPLOYMENT_EVIDENCE_RELEASE_006.md": "4d9f38aa8975661cdefa289a89707b8f4890f5c45ee0f10bb0c8bc35eb68d4d9",
    "data/evidence-reconciliations-009.json": "a26600fcf6b3ac7ce9a6f767788025cfef4dbd18c5b81c74c6ebb6b10c82383b",
    "data/evidence-reconciliations-013.json": "0fb56a75578b444503866476aa8c7393f90627b812df62ae5b474b5126aeb39a",
    "data/industrial-evidence-requests.json": "fb1645d3acc6f9029977eb75e6fee2681747dfcd5164161bab74702b34d97492",
}
NS = "req-nw-north-south"
OLD_ROW = "North-south network switches physically installed before deployment A Infrastructure proposed"
STATE_WORDS = re.compile(r"(?i)\b(?:approved|certified|deployment[- ]ready|passed|validated|score|percent)\b")


def j(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def cfg():
    return j(v.CONFIG)


def model():
    return j(v.MODEL)


def page():
    return v.PAGE.read_text(encoding="utf-8")


def releases():
    return {j(p)["release_id"] for p in sorted((ROOT / "data" / "research").glob("*.json"))}


def workbench():
    return j(ROOT / "data" / "industrial-evidence-requests.json")


class ModelAndPageTests(unittest.TestCase):
    def test_validator_passes_and_is_wired(self):
        self.assertEqual(v.check_all(), [])
        self.assertIn('"validate_deployment_preflight.py"', (ROOT / "scripts" / "validate_all.py").read_text(encoding="utf-8"))
        self.assertTrue(render.in_sync())

    def test_all_fifteen_requirements_and_eighteen_record_types(self):
        p = page()
        rc = [r["id"] for r in workbench()["workflows"][2]["requirements"]]
        self.assertEqual(len(rc), 15)
        self.assertEqual(re.findall(r'<section class="pf-req" id="pf-([a-z0-9-]+)"', p), [m["requirement_id"] for m in model()["matrix"]])
        self.assertEqual(sorted(rc), sorted(m["requirement_id"] for m in model()["matrix"]))
        self.assertEqual(set(re.findall(r'data-record="(rt-[a-z0-9-]+)"', p)), {t["id"] for t in model()["record_types"]})
        self.assertEqual(len(model()["record_types"]), 18)

    def test_required_attributes_and_ceilings_follow_ide014(self):
        types = {t["id"]: t for t in model()["record_types"]}
        p = page()
        for row in model()["matrix"]:
            s = v.section(p, f"pf-{row['requirement_id']}")
            for rid, ceiling, body in re.findall(r'<div class="pf-record" data-record="([a-z0-9-]+)" data-ceiling="([a-z_]*)">(.*?)</ul></div>', s, re.S):
                self.assertEqual(re.findall(r'data-attr="([a-z_]+)"', body), types[rid]["required_attributes"])
                self.assertEqual(ceiling, types[rid]["state_ceiling"] or "")
        self.assertEqual(list(cfg()["attribute_guidance"]), list(model()["attributes"]))

    def test_acceptance_kept_apart_from_technical_testing(self):
        row = next(m for m in model()["matrix"] if m["requirement_id"] == "rc-12-acceptance")
        self.assertEqual(row["record_type_ids"], ["rt-integrated-test-record", "rt-acceptance-criteria", "rt-acceptance-record"])
        types = {t["id"]: t for t in model()["record_types"]}
        self.assertNotIn("signatory_authority", types["rt-integrated-test-record"]["required_attributes"])
        self.assertIn("signatory_authority", types["rt-acceptance-record"]["required_attributes"])
        s = v.section(page(), "pf-rc-12-acceptance")
        self.assertIn("ce-test-as-acceptance", s)
        self.assertIn("On its own this record type cannot support the claim", s)
        self.assertIn("formal contractual acceptance", page())

    def test_access_never_a_deployment_state(self):
        s = v.section(page(), "pf-rc-15-access-regulatory")
        self.assertIn('data-target-state="access"', s)
        self.assertEqual(re.findall(r'data-ceiling="([a-z_]*)"', s), ["", ""])
        self.assertIn("never advances a deployment state", s)
        self.assertIn("ce-access-as-stage", s)

    def test_dependencies_match_ide014(self):
        p = page()
        d = model()
        own = {m["requirement_id"]: set(m["ide006_requirement_ids"]) for m in d["matrix"]}
        for rid, ids in own.items():
            expected = sorted({("upstream", e["prerequisite"]) for e in d["dependencies"] if e["dependent"] in ids and e["prerequisite"] not in ids}
                              | {("downstream", e["dependent"]) for e in d["dependencies"] if e["prerequisite"] in ids and e["dependent"] not in ids})
            got = sorted(re.findall(r'data-direction="(\w+)" data-ide006="([a-z0-9-]+)"', v.section(p, f"pf-{rid}")))
            self.assertEqual(got, expected, rid)
        self.assertIn("req-sw-firmware-baseline", v.section(p, "pf-rc-10-network-integration"))

    def test_research_candidate_labelling(self):
        c = cfg()
        self.assertEqual((c["status"], c["scientific_review"]), ("research_tool", "pending"))
        self.assertEqual((model()["status"], model()["scientific_review"]), ("research_candidate", "pending"))
        p = page()
        panel = p[p.index('<section class="wb-preflight"'):]
        for phrase in (v.LABEL, "Scientific review pending", "Record model compiled: 2026-11-12", "AI-assisted"):
            self.assertIn(phrase, panel)
        self.assertIsNone(re.search(r"<(?:input|select|textarea|button)\b", panel[:panel.index("</article>")]))

    def test_no_new_route_and_no_atlas_change(self):
        self.assertEqual(j(ROOT / "data" / "dependency-atlas.json").get("relationships", []), [])
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"<loc>", sitemap)), 14)
        self.assertNotIn("preflight", sitemap)

    def test_history_and_workflows_a_b_unchanged(self):
        for rel, digest in UNCHANGED.items():
            self.assertEqual(hashlib.sha256((ROOT / rel).read_bytes()).hexdigest(), digest, rel)


class NegativeTests(unittest.TestCase):
    def config_errors(self, c):
        return v.check_config(c, model(), releases())

    def page_errors(self, p):
        return v.check_page(p, cfg(), model(), workbench())

    def assertAny(self, errs, pattern):
        self.assertTrue(any(re.search(pattern, e) for e in errs), f"expected /{pattern}/ in {errs}")

    def test_result_language_rejected(self):
        for field, text in (("completeness_boundary", "Every attribute is present, so the record is verified."),
                            ("no_state_statement", "A complete record has passed the preflight."),
                            ("dependency_rule", "Completion gives a readiness score.")):
            c = cfg(); c["packet"][field] = text
            self.assertAny(self.config_errors(c), "reads as a review result|must say")
        c = cfg(); c["attribute_statuses"]["present"] = "Approved"
        self.assertAny(self.config_errors(c), "reads as a review result")

    def test_statuses_and_review_cannot_change(self):
        c = cfg(); c["attribute_statuses"].pop("unknown")
        self.assertAny(self.config_errors(c), "must be exactly")
        c = cfg(); c["scientific_review"] = "complete"
        self.assertAny(self.config_errors(c), "scientific_review 'pending'")
        c = cfg(); c["packet"]["label"] = "Documentary Preflight"
        self.assertAny(self.config_errors(c), "label must be exactly")
        c = cfg(); c["boundaries"][0]["refs"] = ["ce-invented"]
        self.assertAny(self.config_errors(c), "resolving to IDE-014")
        c = cfg(); c["boundaries"].pop()
        self.assertAny(self.config_errors(c), "boundaries must be exactly")
        c = cfg(); c["record_model"]["compiled_at"] = "2026-01-01"
        self.assertAny(self.config_errors(c), "record_model must name")

    def test_page_tampering_detected(self):
        p = page()
        self.assertAny(self.page_errors(p.replace('<li class="pf-attr" data-attr="criteria">', '<li class="pf-attr" data-attr="results">', 1)),
                       "attributes must be exactly")
        self.assertAny(self.page_errors(p.replace('data-record="rt-commissioning-record" data-ceiling="subsystem_commissioned"',
                                                  'data-record="rt-commissioning-record" data-ceiling="integrated_configuration_verified"', 1)),
                       "ceiling must be")
        self.assertAny(self.page_errors(p.replace('data-record="rt-rule-text" data-ceiling=""', 'data-record="rt-rule-text" data-ceiling="equipment_installed"', 1)),
                       "ceiling must be|access record supports no deployment state")
        self.assertAny(self.page_errors(p.replace('<section class="pf-req" id="pf-rc-09-installation"', '<section class="pf-gone" id="x"', 1)),
                       "every Workflow C requirement exactly once")
        self.assertAny(self.page_errors(p.replace('<div class="pf-doc-controls"></div>', '<div class="pf-doc-controls"><input type="radio"></div>', 1)),
                       "must not contain form controls")
        self.assertAny(self.page_errors(p.replace("Scientific review pending", "Reviewed: 2026-11-12")), "completed review|Scientific review pending")

    def test_script_cannot_name_a_state(self):
        script = v.SCRIPT.read_text(encoding="utf-8")
        self.assertEqual(v.check_script(script), [])
        self.assertAny(v.check_script(script + '\nvar x = "subsystem_commissioned";'), "names the evidence state")
        self.assertAny(v.check_script(script.replace("evidence_state_established: null", "evidence_state_established: s")), "safeguard")


class NorthSouthCorrectionTests(unittest.TestCase):
    def test_correction_applied_and_history_kept(self):
        ide006 = j(rack.IDE006_DOSSIER)
        q = next(r for r in ide006["requirements"] if r["id"] == NS)
        self.assertEqual((q["evidence_classification"], q["current_state"]), ("documented_procedure", "product_specification_documented"))
        entry = next(x for x in model()["ide006_consistency"] if x["requirement_id"] == NS)
        self.assertEqual(entry["current_state"], "infrastructure_proposed")  # the flag is kept as recorded
        res = entry["resolution"]
        self.assertEqual((res["previous_state"], res["corrected_state"], res["resolved_by"]),
                         ("infrastructure_proposed", "product_specification_documented", "IDE-015"))
        self.assertIn("planning and design", res["uncertainty_remaining"])
        infra = (ROOT / "ai-chip-infrastructure" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="correction-req-nw-north-south"', infra)
        self.assertIn("Correction, 2026-11-12", infra)
        self.assertIn("Infrastructure proposed", re.search(r'<tr><th scope="row"><code>req-nw-tested-scale</code>.*?</tr>', infra).group(0))
        self.assertEqual(rack.check(model(), rack.load_context()), [])
        # Only this one IDE-006 entry changed state.
        main = {"req-ch-rack-configuration", "req-el-rack-power", "req-th-liquid-cooling", "req-nw-nvlink-bring-up", "req-sw-management-stack",
                "req-sw-firmware-baseline", "req-fo-leak-response", "req-fo-offline-artifacts", NS}
        self.assertEqual({r["id"] for r in ide006["requirements"] if r["current_state"] == "product_specification_documented"}, main)

    def test_correction_must_stay_exact(self):
        def errs(d=None, c=None):
            return [e for e in rack.check(d or model(), c or rack.load_context()) if "resolution" in e or "ide006_consistency" in e]
        c = rack.load_context()
        next(q for q in c["ide006"]["requirements"] if q["id"] == NS)["current_state"] = "infrastructure_proposed"
        self.assertTrue(any("must carry the corrected state" in e for e in errs(c=c)))
        d = model(); d["ide006_consistency"][0]["resolution"]["previous_state"] = "equipment_installed"
        self.assertTrue(any("previous_state must be the flagged state" in e for e in errs(d)))
        d = model(); d["ide006_consistency"][0]["resolution"]["corrected_state"] = "infrastructure_proposed"
        self.assertTrue(any("corrected state" in e for e in errs(d)))
        d = model(); d["ide006_consistency"][0]["resolution"]["evidence_checked"]["locator"] = "Invented passage"
        self.assertTrue(any("own cited source and locator" in e for e in errs(d)))
        d = model(); d["ide006_consistency"][0]["resolution"]["publication_change"]["new_text"] = OLD_ROW
        self.assertTrue(any("must carry the new text and not the old" in e for e in errs(d)))
        d = model(); d["ide006_consistency"][0]["resolution"]["approved_by"] = "someone"
        self.assertTrue(any("must contain exactly" in e for e in errs(d)))


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
            out = subprocess.run([NODE, str(js), f"http://127.0.0.1:{server.server_address[1]}/research-workbench/", tmp],
                                 capture_output=True, text=True, timeout=180, env={**os.environ, "NODE_PATH": str(Path(PLAYWRIGHT).parent)})
            if out.returncode != 0:
                raise AssertionError(out.stderr + out.stdout)
            r = json.loads(out.stdout.strip().splitlines()[-1])
            r["port"] = server.server_address[1]
            return r
    finally:
        server.shutdown()
        server.server_close()


class BrowserTests(unittest.TestCase):
    """Hypothetical scenarios in headless Chromium. Required in CI (AEC_REQUIRE_BROWSER=1)."""

    @classmethod
    def setUpClass(cls):
        if not (NODE and PLAYWRIGHT):
            if REQUIRE_BROWSER:
                raise AssertionError("AEC_REQUIRE_BROWSER=1 but node or Playwright is not available")
            raise unittest.SkipTest("node and Playwright are not available")
        cls.r = browser_run()

    def test_progressive_disclosure_and_no_js(self):
        r = self.r
        self.assertEqual(r["browser"], "chromium")
        self.assertEqual(r["options"], 15)
        self.assertEqual(r["visible_sections"], 1)
        self.assertEqual(r["no_js"], {"sections": 15, "visible": 15, "controls": 0})
        self.assertEqual(r["errors"], [])

    def test_hypothetical_commissioning_summary_missing_criteria(self):
        # Hypothetical: an analyst holds a commissioning summary for rc-03 with method and results, no criteria, date unknown.
        p = self.r["h1"]
        self.assertEqual(p["format"], "aec-deployment-evidence-preflight")
        self.assertEqual(p["title"], v.LABEL)
        self.assertIsNone(p["evidence_state_established"])
        rec = p["records"][0]
        self.assertEqual(rec["state_ceiling"], {"id": "subsystem_commissioned", "label": "Subsystem commissioned"})
        status = {a["id"]: a["status"] for a in rec["attributes"]}
        self.assertEqual((status["criteria"], status["dated"], status["method"], status["named_site"]), ("missing", "unknown", "present", "not_marked"))
        joined = " ".join(p["outstanding_requests"])
        self.assertIn("provide a version of", joined)
        self.assertIn("thresholds, set before the results were known", joined)
        self.assertIn("confirm whether", joined)
        self.assertIn("carries the date of the act it records", joined)
        self.assertTrue(any("Named site" in x for x in p["not_yet_marked"]))
        self.assertTrue(any(c["id"] == "ce-checklist-as-commissioning" for c in p["category_errors"]))
        self.assertTrue(any(s["record_type_id"] == "rt-checklist-template" for s in p["substitutes_not_accepted"]))
        self.assertEqual(len(p["boundaries"]), 10)
        for key in ("record_model", "record_model_file", "evidence_states_release", "preflight_definitions"):
            self.assertTrue(p["methodology"][key])
        self.assertIn("not been independently validated", p["checklist_disclaimer"])
        self.assertIn("has not seen", p["disclaimer"])
        self.assertIn("Scientific review pending", p["research_status"])

    def test_complete_record_is_never_a_result(self):
        # Hypothetical: every attribute of the rc-03 record marked present.
        p = self.r["h_complete"]
        rec = p["records"][0]
        self.assertTrue(all(a["status"] == "present" for a in rec["attributes"]))
        self.assertEqual(rec["state_ceiling"]["id"], "subsystem_commissioned")
        self.assertIsNone(p["evidence_state_established"])
        self.assertEqual(p["outstanding_requests"], [])
        self.assertIn("ready only for substantive examination by a qualified human reviewer", self.r["complete_text"])
        self.assertIn("That subsystems work together", self.r["complete_text"])
        self.assertIsNone(STATE_WORDS.search(json.dumps({k: p[k] for k in ("records", "outstanding_requests", "not_yet_marked")})))

    def test_acceptance_needs_its_own_records(self):
        # Hypothetical: a complete integrated test record for rc-12, criteria not held, signed acceptance unknown.
        p = self.r["h2"]
        recs = {x["record_type_id"]: x for x in p["records"]}
        self.assertTrue(all(a["status"] == "present" for a in recs["rt-integrated-test-record"]["attributes"]))
        self.assertEqual(recs["rt-acceptance-criteria"]["document_status"], "missing")
        self.assertEqual(recs["rt-acceptance-record"]["document_status"], "unknown")
        joined = " ".join(p["outstanding_requests"])
        self.assertIn("provide “Agreed acceptance criteria for a named configuration”", joined)
        self.assertIn("confirm whether “Signed acceptance of a named configuration against agreed criteria” exists", joined)
        self.assertTrue(any(c["id"] == "ce-test-as-acceptance" for c in p["category_errors"]))
        self.assertIsNone(p["evidence_state_established"])

    def test_access_record_complete_still_no_state(self):
        p = self.r["h3"]
        self.assertEqual(p["requirement"]["target_state"]["id"], "access")
        self.assertTrue(all(r["state_ceiling"]["id"] is None for r in p["records"]))
        self.assertTrue(all(r["state_ceiling"]["label"].startswith("None") for r in p["records"]))
        self.assertTrue(any(c["id"] == "ce-rule-as-determination" for c in p["category_errors"]))

    def test_upstream_record_does_not_advance_dependent(self):
        before, after = self.r["dep_before"], self.r["dep_after"]
        self.assertEqual(before["records"], after["records"])
        self.assertEqual(before["dependencies"], after["dependencies"])
        self.assertTrue(any(d["requirement"] == "req-sw-firmware-baseline" and d["direction"] == "upstream" for d in after["dependencies"]))
        self.assertIn("does not advance", after["dependency_rule"])

    def test_csv_packet_well_formed(self):
        rows = list(csv.reader(io.StringIO(self.r["csv"], newline="")))
        self.assertEqual(rows[0], ["section", "requirement_id", "record_type_id", "item_id", "item", "user_status", "detail"])
        self.assertTrue(all(len(row) == 7 for row in rows))
        self.assertTrue(all(c.startswith('"') for line in self.r["csv"].strip().split("\r\n") for c in [line]))
        self.assertIn(["attribute", "rc-03-redundancy", "rt-commissioning-record", "criteria", "Criteria", "missing",
                       next(row[6] for row in rows if row[3] == "criteria")], rows)
        sections = {row[0] for row in rows}
        for s in ("ceiling", "request", "prohibited_inference", "category_error", "boundary", "title", "disclaimer", "exported_at", "format"):
            self.assertIn(s, sections)
        self.assertIn(v.LABEL, self.r["csv"])

    def test_privacy_and_reset(self):
        r = self.r
        self.assertEqual(r["flagged_requests"], [])
        self.assertEqual(r["storage"], {"local": 0, "session": 0, "cookie": ""})
        self.assertEqual(r["url_after"], f"http://127.0.0.1:{r['port']}/research-workbench/")
        self.assertEqual(r["downloads"], 7)  # one per click: six JSON packets and one CSV
        self.assertEqual(r["after_clear"], "not_marked")
        self.assertEqual(r["after_reload"], {"status": "not_marked", "selected": "pf-rc-01-hardware-configuration"})

    def test_print_shows_one_preflight(self):
        pr = self.r["print"]
        self.assertEqual(pr["visible_workflows"], ["workflow-rack-deployment"])
        self.assertEqual(pr["visible_sections"], ["pf-rc-12-acceptance"])
        self.assertFalse(pr["requirements_list_visible"])
        self.assertFalse(pr["toolbar_visible"])
        self.assertEqual(self.r["after_print"], {"preflight": False, "workflow": False})

    def test_catalog_button_opens_preflight(self):
        self.assertEqual(self.r["catalog_open"], "pf-rc-09-installation")


BROWSER_SCRIPT = r"""
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [url, dir] = process.argv.slice(2);
  const browser = await chromium.launch();
  const context = await browser.newContext({ acceptDownloads: true });
  const page = await context.newPage();
  const flagged = [], errors = [];
  let downloads = 0;
  context.on('request', (req) => { const u = new URL(req.url()); if (u.origin !== new URL(url).origin || req.method() !== 'GET') flagged.push(req.method() + ' ' + req.url()); });
  page.on('download', () => { downloads += 1; });
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.goto(url, { waitUntil: 'load' });
  const options = await page.locator('#pf-select option').count();
  const visibleSections = await page.locator('section.pf-req:visible').count();
  const mark = async (sec, rec, attr, value) => {
    const r = page.locator('#' + sec + ' .pf-record[data-record="' + rec + '"]');
    if (attr === null) await r.locator('.pf-doc-controls input[value=' + value + ']').check();
    else await r.locator('li.pf-attr[data-attr="' + attr + '"] input[value=' + value + ']').check();
  };
  const exportJson = async (name) => {
    const [d] = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: 'Export preflight JSON' }).click()]);
    await d.saveAs(dir + '/' + name + '.json');
    return JSON.parse(fs.readFileSync(dir + '/' + name + '.json', 'utf8'));
  };
  // H1: commissioning summary for rc-03, method and results present, criteria missing, date unknown.
  await page.selectOption('#pf-select', 'pf-rc-03-redundancy');
  await mark('pf-rc-03-redundancy', 'rt-commissioning-record', null, 'present');
  await mark('pf-rc-03-redundancy', 'rt-commissioning-record', 'method', 'present');
  await mark('pf-rc-03-redundancy', 'rt-commissioning-record', 'results', 'present');
  await mark('pf-rc-03-redundancy', 'rt-commissioning-record', 'criteria', 'missing');
  await mark('pf-rc-03-redundancy', 'rt-commissioning-record', 'dated', 'unknown');
  const h1 = await exportJson('h1');
  const [dc] = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: 'Export preflight CSV' }).click()]);
  await dc.saveAs(dir + '/h1.csv');
  // Complete: every attribute present.
  for (const a of ['named_site', 'configuration_identity', 'dated', 'method', 'criteria', 'results', 'issuing_party'])
    await mark('pf-rc-03-redundancy', 'rt-commissioning-record', a, 'present');
  const completeText = await page.locator('#pf-rc-03-redundancy .pf-result').innerText();
  const hComplete = await exportJson('complete');
  // H2: rc-12, complete integrated test, criteria not held, signed acceptance unknown.
  await page.selectOption('#pf-select', 'pf-rc-12-acceptance');
  await mark('pf-rc-12-acceptance', 'rt-integrated-test-record', null, 'present');
  for (const a of ['named_site', 'configuration_identity', 'dated', 'method', 'criteria', 'results', 'conditions', 'issuing_party'])
    await mark('pf-rc-12-acceptance', 'rt-integrated-test-record', a, 'present');
  await mark('pf-rc-12-acceptance', 'rt-acceptance-criteria', null, 'missing');
  await mark('pf-rc-12-acceptance', 'rt-acceptance-record', null, 'unknown');
  const h2 = await exportJson('h2');
  // Print: one preflight only.
  await page.evaluate(() => { document.body.setAttribute('data-print-workflow', 'workflow-rack-deployment');
    document.body.setAttribute('data-print-preflight', 'pf-rc-12-acceptance'); window.dispatchEvent(new Event('beforeprint')); });
  await page.emulateMedia({ media: 'print' });
  const print = await page.evaluate(() => ({
    visible_workflows: [...document.querySelectorAll('.wb-workflow')].filter((e) => getComputedStyle(e).display !== 'none').map((e) => e.id),
    visible_sections: [...document.querySelectorAll('section.pf-req')].filter((e) => getComputedStyle(e).display !== 'none').map((e) => e.id),
    requirements_list_visible: getComputedStyle(document.querySelector('#workflow-rack-deployment .wb-requirements')).display !== 'none',
    toolbar_visible: getComputedStyle(document.querySelector('.pf-toolbar')).display !== 'none' }));
  await page.evaluate(() => window.dispatchEvent(new Event('afterprint')));
  await page.emulateMedia({ media: 'screen' });
  const afterPrint = await page.evaluate(() => ({ preflight: document.body.hasAttribute('data-print-preflight'), workflow: document.body.hasAttribute('data-print-workflow') }));
  // H3: rc-15, rule text with every attribute present.
  await page.selectOption('#pf-select', 'pf-rc-15-access-regulatory');
  await mark('pf-rc-15-access-regulatory', 'rt-rule-text', null, 'present');
  await mark('pf-rc-15-access-regulatory', 'rt-rule-text', 'issuing_party', 'present');
  await mark('pf-rc-15-access-regulatory', 'rt-rule-text', 'dated', 'present');
  const h3 = await exportJson('h3');
  // Dependency: rc-10 before and after the upstream rc-06 record is marked complete.
  await page.selectOption('#pf-select', 'pf-rc-10-network-integration');
  const depBefore = await exportJson('dep-before');
  await page.selectOption('#pf-select', 'pf-rc-06-firmware-software');
  await mark('pf-rc-06-firmware-software', 'rt-installation-record', null, 'present');
  for (const a of ['named_site', 'configuration_identity', 'dated', 'issuing_party', 'completeness'])
    await mark('pf-rc-06-firmware-software', 'rt-installation-record', a, 'present');
  await page.selectOption('#pf-select', 'pf-rc-10-network-integration');
  const depAfter = await exportJson('dep-after');
  // Catalog entry point.
  await page.locator('#rc-09-installation').getByRole('button', { name: 'Open documentary preflight' }).click();
  const catalogOpen = await page.locator('#pf-select').inputValue();
  const storage = await page.evaluate(() => ({ local: localStorage.length, session: sessionStorage.length, cookie: document.cookie }));
  await page.getByRole('button', { name: 'Clear preflight' }).click();
  const afterClear = await page.locator('#pf-rc-03-redundancy li.pf-attr[data-attr=criteria] input:checked').getAttribute('value');
  await page.selectOption('#pf-select', 'pf-rc-03-redundancy');
  await mark('pf-rc-03-redundancy', 'rt-commissioning-record', 'criteria', 'missing');
  const urlAfter = page.url();
  await page.reload({ waitUntil: 'load' });
  const afterReload = { status: await page.locator('#pf-rc-03-redundancy li.pf-attr[data-attr=criteria] input:checked').getAttribute('value'),
    selected: await page.locator('#pf-select').inputValue() };
  const nj = await browser.newContext({ javaScriptEnabled: false });
  const pj = await nj.newPage();
  await pj.goto(url, { waitUntil: 'load' });
  const noJs = await pj.evaluate(() => { const s = [...document.querySelectorAll('section.pf-req')];
    return { sections: s.length, visible: s.filter((e) => e.offsetParent !== null).length,
      controls: document.querySelectorAll('.wb-preflight input, .wb-preflight select, .wb-preflight button').length }; });
  await nj.close();
  console.log(JSON.stringify({ browser: browser.browserType().name(), options, visible_sections: visibleSections, errors, h1,
    h_complete: hComplete, complete_text: completeText, h2, h3, dep_before: depBefore, dep_after: depAfter, csv: fs.readFileSync(dir + '/h1.csv', 'utf8'),
    print, after_print: afterPrint, catalog_open: catalogOpen, storage, flagged_requests: flagged, url_after: urlAfter, downloads,
    after_clear: afterClear, after_reload: afterReload, no_js: noJs }));
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
"""


if __name__ == "__main__":
    unittest.main()
