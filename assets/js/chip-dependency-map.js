"use strict";
/*
 * Chip Dependency Map Engine v1.0.0 (AEC-CDM-ENGINE-001)
 * Implements CHIP_DEPENDENCY_MAP_ENGINE_SPEC.md exactly.
 * Runs entirely client-side. No network calls beyond fetching the
 * same-origin governed model file. No data is stored, transmitted, or logged.
 */
(function () {
  var LAYER_META = {
    design: { name: "Design", route: "/design-fabrication-packaging/" },
    fabrication: { name: "Fabrication", route: "/design-fabrication-packaging/" },
    packaging: { name: "Packaging", route: "/design-fabrication-packaging/" },
    memory: { name: "Memory", route: "/hbm-memory/" },
    interconnect: { name: "Interconnect", route: "/interconnects/" },
    power_thermal: { name: "Power / Thermal", route: "/power-and-thermal-limits/" },
    controls: { name: "Export-Control", route: "/export-control-layer/" },
    deployment: { name: "Deployment", route: "/ai-chip-infrastructure/" }
  };

  var EXPOSURE_META = {
    concentration_exposure: { name: "Concentration exposure", def: "Dependence on a narrow supplier or location." },
    access_exposure: { name: "Access exposure", def: "Dependence on permission, licensing, or allocation." },
    capacity_exposure: { name: "Capacity exposure", def: "Insufficient scale, lead time, power, or cooling." },
    technology_exposure: { name: "Technology exposure", def: "Dependence on proprietary technology or expertise." },
    operational_exposure: { name: "Operational exposure", def: "Inability to deploy, maintain, or recover systems." },
    evidence_exposure: { name: "Evidence exposure", def: "Insufficient reliable information to make a claim." }
  };

  var ANSWER_LABELS = [
    ["controlled", "Controlled"],
    ["accessible", "Accessible"],
    ["constrained", "Constrained"],
    ["unknown", "Unknown"],
    ["not_applicable", "Not applicable"]
  ];

  var ARTIFACT_NAMES = {
    compute_sovereignty_brief: "Compute Sovereignty Brief",
    chip_dependency_audit: "Chip Dependency Audit",
    infrastructure_readiness_brief: "Infrastructure Readiness Brief",
    premium_reference_dossier: "Premium Reference Dossier"
  };

  var CONFIDENCE_TEXT = {
    insufficient: "Too few controlled or accessible answers, or too many unknowns, to read any layer responsibly.",
    low: "Some unknowns or a majority of constrained answers limit how far this preview can be read.",
    medium: "Most answered questions indicate controlled or accessible conditions, with limited unknowns. Medium is the ceiling for a self-reported, unverified preview — this engine never returns High."
  };

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    attrs = attrs || {};
    Object.keys(attrs).forEach(function (key) {
      if (key === "text") {
        node.textContent = attrs[key];
      } else {
        node.setAttribute(key, attrs[key]);
      }
    });
    (children || []).forEach(function (child) {
      if (child) node.appendChild(child);
    });
    return node;
  }

  function buildForm(model, root) {
    var form = el("form", { id: "cdm-form", novalidate: "novalidate" });
    model.questions.forEach(function (q) {
      var legend = el("legend", { text: q.prompt });
      var fieldset = el("fieldset", { class: "cdm-question" }, [legend]);
      var group = el("div", { class: "cdm-answers", role: "radiogroup" });
      ANSWER_LABELS.forEach(function (pair, idx) {
        var id = "q_" + q.id + "_" + pair[0];
        var input = el("input", {
          type: "radio",
          name: "q_" + q.id,
          id: id,
          value: pair[0]
        });
        if (idx === ANSWER_LABELS.length - 1) input.checked = true;
        var label = el("label", { for: id, text: pair[1] });
        group.appendChild(el("span", { class: "cdm-answer" }, [input, label]));
      });
      fieldset.appendChild(group);
      form.appendChild(fieldset);
    });
    var submit = el("button", { type: "submit", class: "button primary" }, [
      document.createTextNode("Preview my reading")
    ]);
    form.appendChild(el("div", { class: "cdm-submit-row" }, [submit]));

    var results = el("section", {
      id: "cdm-results",
      class: "cdm-results",
      "aria-live": "polite",
      tabindex: "-1"
    });

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var outcome = computeOutcome(model, form);
      renderResults(outcome, results);
      results.focus();
      results.scrollIntoView({ behavior: "smooth", block: "start" });
    });

    root.appendChild(form);
    root.appendChild(results);
  }

  function computeOutcome(model, form) {
    var answered = [];
    model.questions.forEach(function (q) {
      var input = form.querySelector('input[name="q_' + q.id + '"]:checked');
      var answer = input ? input.value : "not_applicable";
      if (answer !== "not_applicable") {
        answered.push({ question: q, answer: answer });
      }
    });

    var touchedLayers = {};
    var raisedByLayer = {};
    var artifactTally = {};

    answered.forEach(function (item) {
      item.question.layers.forEach(function (layer) {
        touchedLayers[layer] = true;
      });
      if (item.answer === "constrained" || item.answer === "unknown") {
        item.question.layers.forEach(function (layer) {
          raisedByLayer[layer] = raisedByLayer[layer] || {};
          item.question.exposure_types.forEach(function (exp) {
            raisedByLayer[layer][exp] = true;
          });
        });
        item.question.suggested_artifacts.forEach(function (artifact) {
          artifactTally[artifact] = (artifactTally[artifact] || 0) + 1;
        });
      }
    });

    var n = answered.length;
    var u = answered.filter(function (i) { return i.answer === "unknown"; }).length;
    var c = answered.filter(function (i) { return i.answer === "constrained"; }).length;

    var confidence;
    if (n === 0 || u / n >= 0.5) {
      confidence = "insufficient";
    } else if (u > 0 || c / n >= 0.5) {
      confidence = "low";
    } else {
      confidence = "medium";
    }

    var artifacts = Object.keys(artifactTally)
      .sort(function (a, b) { return artifactTally[b] - artifactTally[a]; })
      .slice(0, 2);

    return {
      touchedLayers: Object.keys(touchedLayers),
      raisedByLayer: raisedByLayer,
      confidence: confidence,
      artifacts: artifacts,
      answeredCount: n
    };
  }

  function renderResults(outcome, root) {
    root.innerHTML = "";
    root.appendChild(el("h2", { text: "Your preview reading" }));

    var notice = el("p", { class: "framing-note cdm-notice" }, [
      el("strong", { text: "Boundary" }),
      el("span", {
        text:
          "This is a self-reported, unverified preview of your own answers. It creates no dependency record and is not saved, transmitted, or stored. It is not a score, ranking, sovereignty assignment, or governed finding, and it says nothing about any specific company, country, or product."
      })
    ]);
    root.appendChild(notice);

    var confBlock = el("div", { class: "cdm-confidence" }, [
      el("span", { class: "section-label blue", text: "Confidence · " + outcome.confidence }),
      el("p", { text: CONFIDENCE_TEXT[outcome.confidence] })
    ]);
    root.appendChild(confBlock);

    var layerList = el("div", { class: "cdm-layers" });
    Object.keys(LAYER_META).forEach(function (layerId) {
      var meta = LAYER_META[layerId];
      var touched = outcome.touchedLayers.indexOf(layerId) !== -1;
      var card = el("div", { class: "cdm-layer-card" + (touched ? " touched" : "") });
      card.appendChild(el("a", { href: meta.route, class: "cdm-layer-link" }, [
        document.createTextNode(meta.name)
      ]));
      if (!touched) {
        card.appendChild(el("p", { class: "cdm-muted", text: "Not assessed by this preview." }));
      } else {
        var raised = outcome.raisedByLayer[layerId];
        var raisedKeys = raised ? Object.keys(raised) : [];
        if (raisedKeys.length === 0) {
          card.appendChild(el("p", { class: "cdm-muted", text: "Touched — no exposure type raised from your answers." }));
        } else {
          var ul = el("ul", { class: "cdm-exposure-list" });
          raisedKeys.forEach(function (exp) {
            var expMeta = EXPOSURE_META[exp];
            ul.appendChild(el("li", {}, [
              el("strong", { text: expMeta.name }),
              document.createTextNode(" — " + expMeta.def)
            ]));
          });
          card.appendChild(ul);
        }
      }
      layerList.appendChild(card);
    });
    root.appendChild(layerList);

    var artifactBlock = el("div", { class: "cdm-artifacts" });
    if (outcome.artifacts.length === 0) {
      artifactBlock.appendChild(el("h3", { text: "No governed artifact suggested" }));
      artifactBlock.appendChild(el("p", {
        text: "Your answers did not raise constrained or unknown conditions, so this preview has no reason to suggest a paid pathway. Continue with the reference layer."
      }));
      artifactBlock.appendChild(el("a", { class: "text-link", href: "/sovereignty-stack/" }, [
        document.createTextNode("Open the Silicon Sovereignty Stack →")
      ]));
    } else {
      artifactBlock.appendChild(el("h3", { text: "Candidate next governed format" }));
      artifactBlock.appendChild(el("p", { class: "cdm-muted", text: "A classification hint, not a recommendation to buy, invest, deploy, or act." }));
      var artList = el("ul", { class: "cdm-artifact-list" });
      outcome.artifacts.forEach(function (id) {
        artList.appendChild(el("li", {}, [
          el("strong", { text: ARTIFACT_NAMES[id] })
        ]));
      });
      artifactBlock.appendChild(artList);
      artifactBlock.appendChild(el("a", { class: "button", href: "/strategic-availability/" }, [
        document.createTextNode("Open Strategic Availability →")
      ]));
    }
    root.appendChild(artifactBlock);
  }

  function init() {
    var root = document.getElementById("cdm-engine-root");
    if (!root) return;
    fetch("/data/chip-dependency-model.json")
      .then(function (res) { return res.json(); })
      .then(function (model) { buildForm(model, root); })
      .catch(function () {
        root.appendChild(el("p", {
          class: "cdm-muted",
          text: "The governed model could not be loaded. Read the model directly in CHIP_DEPENDENCY_MAP_MODEL.md, or try again."
        }));
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
