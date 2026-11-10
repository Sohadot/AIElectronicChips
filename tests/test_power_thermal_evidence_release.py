"""Regression tests for IDE-005 (power delivery and thermal infrastructure) and its calculations."""

from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import engineering_calcs as calc  # noqa: E402
from validate_evidence_releases import (  # noqa: E402
    check_inference_boundaries,
    check_public_references,
    check_release,
    check_review_representation,
    check_shared_candidate_nodes,
    inference_boundary_errors,
    reference_page,
)

RESEARCH = ROOT / "data" / "research"
RELEASE = RESEARCH / "power-thermal-evidence-release-005.json"
PAGE = ROOT / "power-and-thermal-limits" / "index.html"
TODAY = date(2026, 11, 10)


def load(path=RELEASE):
    release = json.loads(path.read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "data" / "source-registry.json").read_text(encoding="utf-8"))
    atlas = json.loads((ROOT / "data" / "dependency-atlas.json").read_text(encoding="utf-8"))
    return release, registry, atlas


def finding(release, fid):
    return next(f for f in release["findings"] if f["id"] == fid)


def errors_for(release):
    _, registry, atlas = load()
    return check_release(release, registry, atlas, TODAY, "fixture")


class EngineeringCalculationTests(unittest.TestCase):
    def test_energy_is_power_times_time(self):
        self.assertEqual(1051.2, round(calc.energy_kwh(120, calc.HOURS_PER_YEAR) / 1000, 1))

    def test_average_power_from_annual_energy(self):
        self.assertAlmostEqual(20.09, calc.average_power_gw(176), places=2)

    def test_conversion_input_and_loss(self):
        self.assertAlmostEqual(123.71, calc.input_power_kw(120, 0.97), places=2)
        self.assertAlmostEqual(3.71, calc.conversion_loss_kw(120, 0.97), places=2)
        with self.assertRaises(ValueError):
            calc.input_power_kw(120, 1.2)

    def test_redundancy_schemes(self):
        self.assertEqual(264, calc.redundant_capacity_kw(48, 5.5, "N"))
        self.assertEqual(132, calc.redundant_capacity_kw(48, 5.5, "N+N"))
        self.assertEqual(258.5, calc.redundant_capacity_kw(48, 5.5, "N+1"))
        with self.assertRaises(ValueError):
            calc.redundant_capacity_kw(47, 5.5, "N+N")

    def test_dc_power(self):
        self.assertEqual(70, calc.dc_power_kw(1400, 50))

    def test_coolant_flow_scales_inversely_with_temperature_rise(self):
        at10 = calc.coolant_volume_flow_lpm(120, 4.18, 10, 1.0)
        at15 = calc.coolant_volume_flow_lpm(120, 4.18, 15, 1.0)
        self.assertAlmostEqual(172.25, at10, places=2)
        self.assertAlmostEqual(at10 * 10 / 15, at15, places=6)
        with self.assertRaises(ValueError):
            calc.coolant_mass_flow_kg_s(120, 4.18, 0)

    def test_pue_and_wue_boundaries(self):
        self.assertEqual(1.2, calc.pue(1200, 1000))
        with self.assertRaises(ValueError):
            calc.pue(900, 1000)  # facility energy cannot be below IT energy
        self.assertEqual(0.5, calc.wue_l_per_kwh(500, 1000))
        with self.assertRaises(ValueError):
            calc.wue_l_per_kwh(500, 0)

    def test_page_results_match_the_formulas(self):
        html = PAGE.read_text(encoding="utf-8")
        shown = dict(re.findall(r'data-calc="([a-z0-9_]+)">([^<]+)<', html))
        expected = calc.worked_examples()
        self.assertEqual(set(expected), set(shown))
        for key, text in shown.items():
            number = re.search(r"[\d,]+(?:\.(\d+))?", text)
            value = float(number.group(0).replace(",", ""))
            decimals = len(number.group(1) or "")
            # The page rounds to the precision it displays; the formula must round to the same figure.
            self.assertAlmostEqual(expected[key], value, delta=0.5 * 10 ** -decimals + 1e-9, msg=key)

    def test_release_calculated_quantities_match_the_formulas(self):
        release, _, _ = load()
        values = {(q["quantity"], q["value"]) for f in release["findings"] for q in f.get("quantities", []) if q["basis"] == "calculated"}
        self.assertIn(("installed PSU rating per rack", "264"), values)
        self.assertIn(("power at 1,400 A and 50 V", "70"), values)
        self.assertIn(("volume flow at a 10 K rise", "172"), values)
        self.assertIn(("average power implied by 176 TWh", "20.1"), values)


class PowerThermalReleaseTests(unittest.TestCase):
    def assert_fails(self, release, fragment):
        errs = errors_for(release)
        self.assertTrue(any(fragment in e for e in errs), errs)

    def test_repository_release_is_valid(self):
        release, _, _ = load()
        self.assertEqual([], errors_for(release))

    def test_release_maps_to_power_page(self):
        release, _, _ = load()
        self.assertEqual(PAGE, reference_page(release))

    def test_page_passes_against_its_own_release(self):
        release, registry, _ = load()
        self.assertEqual([], check_inference_boundaries(release, PAGE))
        self.assertEqual([], check_public_references(PAGE, registry))
        self.assertEqual([], check_review_representation(PAGE, {release["as_of"]}))

    def test_candidates_unpublished_and_atlas_empty(self):
        release, _, atlas = load()
        self.assertEqual([], atlas["relationships"])
        for edge in release["candidate_relationships"]:
            self.assertEqual("awaiting_human_review", edge["review_status"])
            self.assertIsNone(edge["reviewed_at"])
            self.assertEqual("unassigned", edge["review_owner"])

    def test_all_releases_share_consistent_nodes(self):
        releases = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in sorted(RESEARCH.glob("*.json"))}
        self.assertGreaterEqual(len(releases), 4)  # releases 001-005 at least; later releases add to the set
        self.assertEqual([], check_shared_candidate_nodes(releases))

    def test_conflicts_recorded_as_unresolved(self):
        release, _, _ = load()
        ids = {u["id"] for u in release["unresolved"]}
        self.assertTrue({"u-pt-redundancy-conflict", "u-pt-bus-bar-paths", "u-pt-coolant-specification", "u-pt-site-evidence"} <= ids)

    def test_generations_are_not_merged(self):
        text = json.dumps(load()[0])
        self.assertNotIn("Vera Rubin", text)

    def test_energy_figure_cannot_be_a_rating(self):
        release, _, _ = load()
        q = next(q for q in finding(release, "pt-an-energy-versus-power")["quantities"] if q["unit"] == "MWh")
        q["peak_or_sustained"] = "rated"
        self.assert_fails(release, "is an amount of energy, not a power rating")

    def test_power_figure_has_no_direction(self):
        release, _, _ = load()
        finding(release, "pt-gb-power-shelves")["quantities"][2]["direction"] = "bidirectional"
        self.assert_fails(release, "kW has no direction")

    def test_kw_and_kwh_are_distinct(self):
        release, _, _ = load()
        q = next(q for q in finding(release, "pt-gb-power-shelves")["quantities"] if q["value"] == "120")
        q["unit"] = "kWh"
        self.assert_fails(release, "does not appear in the finding statement")

    def test_projection_must_be_modelled(self):
        release, _, _ = load()
        q = next(q for q in finding(release, "pt-doe-us-energy")["quantities"] if q["peak_or_sustained"] == "projected")
        q["basis"] = "vendor_stated"
        self.assert_fails(release, "a projected figure must have basis modelled")

    def test_modelled_estimate_cannot_be_presented_as_measured(self):
        release, _, _ = load()
        finding(release, "pt-doe-us-energy")["quantities"][1]["basis"] = "measured"
        self.assert_fails(release, "a measured figure needs a measurement source")

    def test_temperature_must_name_its_loop(self):
        release, _, _ = load()
        q = next(q for q in finding(release, "pt-ashrae-classes-via-ocp")["quantities"])
        q["scope"] = "per_rack"
        self.assert_fails(release, "a temperature must name its loop")

    def test_assumed_input_only_in_analysis(self):
        release, _, _ = load()
        finding(release, "pt-gb-power-shelves")["quantities"][2]["basis"] = "assumed"
        self.assert_fails(release, "an assumed input belongs in a bounded_analysis finding")

    def test_power_figures_require_quantities(self):
        release, _, _ = load()
        del finding(release, "pt-ocp-bus-bar")["quantities"]
        self.assert_fails(release, "without a quantities list")

    def test_class_labels_are_not_read_as_watts(self):
        release, _, _ = load()
        values = {(q["value"], q["unit"]) for q in finding(release, "pt-ashrae-classes-via-ocp")["quantities"]}
        self.assertNotIn(("17", "W"), values)
        self.assertEqual([], [e for e in errors_for(release) if "W has no quantities" in e])


class PowerThermalBoundaryTests(unittest.TestCase):
    def test_facility_metric_on_product_rejected(self):
        self.assertTrue(inference_boundary_errors("The GB200 NVL72 rack achieves a PUE of 1.1.", "p"))
        self.assertTrue(inference_boundary_errors("Each GPU has a WUE of 0.2 L/kWh.", "p"))

    def test_negated_facility_metric_allowed(self):
        self.assertEqual([], inference_boundary_errors("PUE cannot be stated for a server or GPU on its own.", "p"))

    def test_tdp_is_not_consumption(self):
        self.assertTrue(inference_boundary_errors("The scalable unit's TDP of 1.2 MW is its consumption.", "p"))
        self.assertEqual([], inference_boundary_errors("The 1.2 MW TDP is a design value, not measured consumption.", "p"))

    def test_reference_design_is_not_operating(self):
        self.assertTrue(inference_boundary_errors("The 7 MW reference architecture is deployed in Texas.", "p"))
        self.assertEqual([], inference_boundary_errors("A reference design is not evidence that any facility is built.", "p"))

    def test_facility_readiness_needs_site_evidence(self):
        self.assertTrue(inference_boundary_errors("The facility is ready for GB200 NVL72 racks.", "p"))
        self.assertTrue(inference_boundary_errors("Data centers are capable of supporting 132 kW racks.", "p"))

    def test_unattributed_cooling_compatibility_rejected(self):
        self.assertTrue(inference_boundary_errors("This CDU is compatible with GB200 NVL72.", "p"))
        self.assertEqual([], inference_boundary_errors("The vendor states its CDU is compatible with GB200 NVL72.", "p"))
        self.assertEqual([], inference_boundary_errors("No source shows that any CDU is compatible with this rack.", "p"))

    def test_heat_load_is_not_rated_capacity(self):
        self.assertTrue(inference_boundary_errors("The heat load equals the rated power of the PSUs.", "p"))

    def test_page_rejects_injected_readiness_claim(self):
        release, _, _ = load()
        html = PAGE.read_text(encoding="utf-8").replace(
            "A connection request is not energised capacity.",
            "The facility is ready for these racks.")
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "index.html"
            page.write_text(html, encoding="utf-8")
            errs = check_inference_boundaries(release, page)
        self.assertTrue(any("facility readiness" in e for e in errs), errs)


class EarlierReleaseRegressionTests(unittest.TestCase):
    def test_earlier_releases_still_valid(self):
        _, registry, atlas = load()
        for name in ("hbm4-evidence-release-001.json", "packaging-evidence-release-003.json", "interconnect-evidence-release-004.json"):
            release = json.loads((RESEARCH / name).read_text(encoding="utf-8"))
            self.assertEqual([], check_release(release, registry, atlas, TODAY, name), name)

    def test_interconnect_unit_rules_unchanged(self):
        release = json.loads((RESEARCH / "interconnect-evidence-release-004.json").read_text(encoding="utf-8"))
        f = next(f for f in release["findings"] if f["id"] == "i-cxl-3-rate")
        q = next(q for q in f["quantities"] if q["unit"] == "GT/s")
        q["scope"] = "per_link"
        _, registry, atlas = load()
        errs = check_release(release, registry, atlas, TODAY, "ide4")
        self.assertTrue(any("GT/s is a per-lane transfer rate" in e for e in errs), errs)


if __name__ == "__main__":
    unittest.main()
