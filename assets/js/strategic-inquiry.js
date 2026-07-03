"use strict";
/*
 * Qualified Inquiry Builder v1.0.0 (AEC-SA-INQUIRY-001)
 * Governed by STRATEGIC_AVAILABILITY_PROTOCOL.md, PREMIUM_BRIEF_BOUNDARY.md,
 * MONETIZATION_BOUNDARY.md, and DECISION_LOG.md ADR-018.
 *
 * Composes a structured inquiry email from the governed offerings model and
 * opens it in the visitor's own mail client. Runs entirely client-side: no
 * checkout, no prices, no server, and nothing entered here is transmitted,
 * stored, or logged by this site. The only same-origin request is fetching
 * the public governed offerings file.
 */
(function () {
  var INQUIRY_ADDRESS = "agent@sohadot.com";

  var LAYERS = [
    "Design",
    "Fabrication",
    "Packaging",
    "Memory",
    "Interconnect",
    "Power / Thermal",
    "Export-Control",
    "Deployment"
  ];

  var COMMON_FIELDS = [
    { id: "organization", label: "Organization and role", placeholder: "Institution, team, and your role" },
    { id: "subject", label: "Entity, sector, or topic", placeholder: "The bounded subject of the inquiry" },
    { id: "decision_context", label: "Decision context and intended use", placeholder: "What decision or use the work informs" },
    { id: "time_horizon", label: "Time horizon", placeholder: "e.g. next 12 months; FY2027 planning" },
    { id: "geographic_scope", label: "Geographic scope", placeholder: "Jurisdictions or regions in scope" },
    { id: "constraints", label: "Known constraints, exclusions, confidentiality", placeholder: "Anything already fixed or out of bounds" }
  ];

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    attrs = attrs || {};
    Object.keys(attrs).forEach(function (key) {
      if (key === "text") node.textContent = attrs[key];
      else node.setAttribute(key, attrs[key]);
    });
    (children || []).forEach(function (child) { if (child) node.appendChild(child); });
    return node;
  }

  function buildForm(model, root) {
    var offerings = model.strategic_offerings;
    var form = el("form", { id: "sa-inquiry-form", novalidate: "novalidate" });

    var pathwayField = el("div", { class: "sa-field" });
    pathwayField.appendChild(el("label", { for: "sa-pathway", text: "Pathway" }));
    var select = el("select", { id: "sa-pathway" });
    select.appendChild(el("option", { value: "", text: "Select a governed pathway…" }));
    offerings.forEach(function (o) {
      select.appendChild(el("option", { value: o.id, text: o.label }));
    });
    pathwayField.appendChild(select);
    form.appendChild(pathwayField);

    var pathwayNote = el("p", { class: "sa-pathway-note cdm-muted" });
    form.appendChild(pathwayNote);

    COMMON_FIELDS.forEach(function (f) {
      var field = el("div", { class: "sa-field" });
      field.appendChild(el("label", { for: "sa-" + f.id, text: f.label }));
      field.appendChild(el("textarea", { id: "sa-" + f.id, rows: "2", placeholder: f.placeholder }));
      form.appendChild(field);
    });

    var layerField = el("fieldset", { class: "sa-field sa-layers" }, [
      el("legend", { text: "Relevant sovereignty layers" })
    ]);
    var layerGroup = el("div", { class: "cdm-answers" });
    LAYERS.forEach(function (name, i) {
      var id = "sa-layer-" + i;
      var input = el("input", { type: "checkbox", id: id, value: name });
      var label = el("label", { for: id, text: name });
      layerGroup.appendChild(el("span", { class: "cdm-answer" }, [input, label]));
    });
    layerField.appendChild(layerGroup);
    form.appendChild(layerField);

    var actions = el("div", { class: "hero-actions" });
    var composeBtn = el("button", { type: "submit", class: "button primary" }, [
      document.createTextNode("Compose inquiry email")
    ]);
    actions.appendChild(composeBtn);
    form.appendChild(actions);

    var preview = el("section", {
      id: "sa-preview",
      class: "sa-preview",
      "aria-live": "polite",
      tabindex: "-1"
    });

    select.addEventListener("change", function () {
      var offering = offerings.filter(function (o) { return o.id === select.value; })[0];
      if (!offering) { pathwayNote.textContent = ""; return; }
      pathwayNote.textContent = offering.purpose + " Boundary: " + offering.deliverable_boundary;
    });

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var offering = offerings.filter(function (o) { return o.id === select.value; })[0];
      var lines = [];
      lines.push("Pathway: " + (offering ? offering.label : "Not selected"));
      COMMON_FIELDS.forEach(function (f) {
        var value = document.getElementById("sa-" + f.id).value.trim();
        lines.push(f.label + ": " + (value || "—"));
      });
      var layers = [];
      layerField.querySelectorAll("input:checked").forEach(function (input) {
        layers.push(input.value);
      });
      lines.push("Relevant sovereignty layers: " + (layers.length ? layers.join(", ") : "—"));
      lines.push("");
      lines.push("I understand no predetermined conclusion, score, ranking, certification, or guarantee can be purchased, and that insufficient evidence produces no operational finding.");

      var subjectLine = "AIElectronicChips.com — Strategic Inquiry" + (offering ? " — " + offering.label : "");
      var body = lines.join("\n");
      var href = "mailto:" + INQUIRY_ADDRESS +
        "?subject=" + encodeURIComponent(subjectLine) +
        "&body=" + encodeURIComponent(body);

      preview.innerHTML = "";
      preview.appendChild(el("h3", { text: "Composed inquiry" }));
      preview.appendChild(el("p", {
        class: "cdm-muted",
        text: "Nothing has been sent or stored. Review the text below, then open it in your own mail client or copy it."
      }));
      var pre = el("pre", { class: "sa-preview-text" });
      pre.textContent = "To: " + INQUIRY_ADDRESS + "\nSubject: " + subjectLine + "\n\n" + body;
      preview.appendChild(pre);
      var previewActions = el("div", { class: "hero-actions" });
      previewActions.appendChild(el("a", { class: "button primary", href: href }, [
        document.createTextNode("Open in mail client")
      ]));
      var copyBtn = el("button", { type: "button", class: "button" }, [
        document.createTextNode("Copy to clipboard")
      ]);
      copyBtn.addEventListener("click", function () {
        navigator.clipboard.writeText(pre.textContent).then(function () {
          copyBtn.textContent = "Copied";
        }, function () {
          copyBtn.textContent = "Copy failed — select the text manually";
        });
      });
      previewActions.appendChild(copyBtn);
      preview.appendChild(previewActions);
      preview.focus();
      preview.scrollIntoView({ behavior: "smooth", block: "start" });
    });

    root.appendChild(form);
    root.appendChild(preview);
  }

  function init() {
    var root = document.getElementById("sa-inquiry-root");
    if (!root) return;
    fetch("/data/strategic-offerings.json")
      .then(function (res) { return res.json(); })
      .then(function (model) { buildForm(model, root); })
      .catch(function () {
        /* The plain mailto pathway below the builder remains available. */
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
