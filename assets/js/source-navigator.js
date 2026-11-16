"use strict";
/*
 * AIElectronicChips.com Institutional Evidence Navigator (IDE-017).
 * Progressive enhancement over the static source inventory on /sources/: filters what is already on the page and
 * exports the sources shown. Every exported record is rebuilt from the page's own markup, which is generated from
 * data/source-registry.json, so nothing is added to it and no source is evaluated. The site itself never
 * submits, stores, writes to the URL or interpolates as HTML anything selected or typed here; reloading clears it.
 */
(function () {
  var FORMAT = "aec-source-inventory";
  var FORMAT_VERSION = "1.0.0";

  // CSV cell: quote, double inner quotes, and neutralise spreadsheet formulas (leading = + - @ tab or CR).
  function csvCell(value) {
    var s = value === null || value === undefined ? "" : String(value);
    if (/^[=+\-@\t\r]/.test(s)) {
      s = "'" + s;
    }
    return '"' + s.replace(/"/g, '""') + '"';
  }

  function buildCsv(rows) {
    return rows.map(function (row) { return row.map(csvCell).join(","); }).join("\r\n") + "\r\n";
  }

  function all(root, selector) {
    return Array.prototype.slice.call(root.querySelectorAll(selector));
  }

  function text(root, selector) {
    var n = selector ? root.querySelector(selector) : root;
    return n ? n.textContent.replace(/\s+/g, " ").trim() : "";
  }

  function values(root, selector) {
    return all(root, selector).map(function (n) { return n.getAttribute("data-value"); });
  }

  function record(li) {
    var date = li.querySelector(".nav-date");
    var r = {
      id: li.getAttribute("data-id"),
      title: text(li, ".nav-url"),
      publisher: text(li, ".nav-publisher"),
      source_type: li.querySelector(".nav-type").getAttribute("data-value"),
      status: li.querySelector(".nav-status").getAttribute("data-value")
    };
    if (date && date.getAttribute("data-kind") === "published") { r.publication_date = text(date); }
    if (date && date.getAttribute("data-kind") === "effective") { r.effective_date = text(date); }
    r.accessed_at = text(li, ".nav-accessed");
    r.canonical_url = li.querySelector(".nav-url").getAttribute("href");
    r.ontology_layers = values(li, ".nav-layers li");
    r.supported_claim_types = values(li, ".nav-claims li");
    r.geographic_scope = text(li, ".nav-geo");
    r.temporal_scope = text(li, ".nav-temporal");
    r.confidence_use = text(li, ".nav-use");
    r.use_limitations = all(li, ".nav-limits li").map(function (n) { return text(n); });
    return r;
  }

  function context(li) {
    var insp = li.querySelector(".nav-inspection");
    return {
      latest_inspection: insp && insp.getAttribute("data-date") ? text(insp) : null,
      register_issues: values(li, ".nav-issues li"),
      used_in: text(li, ".nav-used"),
      page_record: "/sources/#source-" + li.getAttribute("data-id")
    };
  }

  function download(name, type, content) {
    var blob = new Blob([content], { type: type });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 0);
  }

  function button(label, handler) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "button";
    b.textContent = label;
    b.addEventListener("click", handler);
    return b;
  }

  function init() {
    var section = document.getElementById("source-navigator");
    if (!section) { return; }
    var controls = section.querySelector(".nav-controls");
    var items = all(section, "li.nav-source");
    var count = section.querySelector(".nav-count");
    var empty = section.querySelector(".nav-empty");
    var search = controls.querySelector("#nav-search");
    var year = controls.querySelector("#nav-year");
    var boundary = text(section, ".nav-boundary");

    function checked(name) {
      return all(controls, 'input[name="' + name + '"]:checked').map(function (i) { return i.value; });
    }

    function filters() {
      return {
        layers: checked("nav-layer"),
        layer_mode: checked("nav-layer-mode")[0] || "any",
        source_types: checked("nav-type"),
        statuses: checked("nav-status"),
        year: year.value || null,
        named_in_register_issue: checked("nav-issues").length > 0,
        search: search.value.trim()
      };
    }

    function matches(li, f) {
      var layers = (li.getAttribute("data-layers") || "").split(" ");
      if (f.layers.length) {
        var hit = f.layers.filter(function (l) { return layers.indexOf(l) !== -1; }).length;
        if (f.layer_mode === "all" ? hit !== f.layers.length : hit === 0) { return false; }
      }
      if (f.source_types.length && f.source_types.indexOf(li.getAttribute("data-type")) === -1) { return false; }
      if (f.statuses.length && f.statuses.indexOf(li.getAttribute("data-status")) === -1) { return false; }
      if (f.year) {
        var y = li.getAttribute("data-year");
        if (f.year === "undated" ? y !== "" : y !== f.year) { return false; }
      }
      if (f.named_in_register_issue && !li.getAttribute("data-issues")) { return false; }
      if (f.search) {
        var hay = li.getAttribute("data-search") || "";
        var terms = f.search.toLowerCase().split(/\s+/);
        for (var i = 0; i < terms.length; i++) {
          if (hay.indexOf(terms[i]) === -1) { return false; }
        }
      }
      return true;
    }

    function describe(f) {
      var parts = [];
      if (f.layers.length) { parts.push((f.layer_mode === "all" ? "every one of " : "any of ") + "layers " + f.layers.join(", ")); }
      if (f.source_types.length) { parts.push("type " + f.source_types.join(" or ")); }
      if (f.statuses.length) { parts.push("status " + f.statuses.join(" or ")); }
      if (f.year) { parts.push("year " + f.year); }
      if (f.named_in_register_issue) { parts.push("named in a register issue"); }
      if (f.search) { parts.push("text containing every word of “" + f.search + "”"); }
      return parts.length ? parts.join("; ") : "no filters";
    }

    function visible() {
      return items.filter(function (li) { return !li.hidden; });
    }

    function apply() {
      var f = filters();
      var shown = 0;
      items.forEach(function (li) {
        li.hidden = !matches(li, f);
        if (!li.hidden) { shown += 1; }
      });
      empty.hidden = shown !== 0;
      count.textContent = "Showing " + shown + " of " + items.length + " registered sources (" + describe(f) + ").";
    }

    function inventory() {
      var f = filters();
      return {
        format: FORMAT,
        format_version: FORMAT_VERSION,
        exported_at: new Date().toISOString(),
        source: "https://aielectronicchips.com/sources/#source-navigator",
        registry_version: controls.getAttribute("data-registry-version"),
        registry_updated_at: controls.getAttribute("data-registry-updated"),
        boundary: boundary,
        filters: f,
        filter_description: describe(f),
        count: visible().length,
        total_registered: items.length,
        sources: visible().map(function (li) { return { record: record(li), context: context(li) }; })
      };
    }

    function toCsv(inv) {
      var head = ["id", "title", "publisher", "source_type", "status", "publication_date", "effective_date", "accessed_at", "canonical_url",
        "ontology_layers", "supported_claim_types", "geographic_scope", "temporal_scope", "confidence_use", "use_limitations",
        "latest_inspection", "register_issues", "page_record"];
      var rows = [head];
      inv.sources.forEach(function (s) {
        var r = s.record;
        rows.push([r.id, r.title, r.publisher, r.source_type, r.status, r.publication_date || "", r.effective_date || "", r.accessed_at,
          r.canonical_url, r.ontology_layers.join(" "), r.supported_claim_types.join(" "), r.geographic_scope, r.temporal_scope,
          r.confidence_use, r.use_limitations.join(" | "), s.context.latest_inspection || "", s.context.register_issues.join(" "),
          s.context.page_record]);
      });
      var width = head.length;
      [["boundary", inv.boundary], ["filters", inv.filter_description], ["count", inv.count + " of " + inv.total_registered],
        ["registry_version", inv.registry_version + " (updated " + inv.registry_updated_at + ")"], ["format", inv.format + " " + inv.format_version],
        ["exported_at", inv.exported_at]].forEach(function (m) {
        var row = [m[0], m[1]];
        while (row.length < width) { row.push(""); }
        rows.push(row);
      });
      return buildCsv(rows);
    }

    var bar = controls.querySelector(".nav-toolbar");
    var status = document.createElement("p");
    status.className = "wb-toolbar-status";
    status.setAttribute("role", "status");
    bar.appendChild(button("Reset filters", function () {
      all(controls, 'input[type="checkbox"]').forEach(function (i) { i.checked = false; });
      controls.querySelector('input[name="nav-layer-mode"][value="any"]').checked = true;
      year.value = "";
      search.value = "";
      apply();
      status.textContent = "Filters cleared.";
    }));
    bar.appendChild(button("Export shown sources (JSON)", function () {
      download("aec-source-inventory.json", "application/json", JSON.stringify(inventory(), null, 2) + "\n");
      status.textContent = "Source inventory (JSON) prepared for download.";
    }));
    bar.appendChild(button("Export shown sources (CSV)", function () {
      download("aec-source-inventory.csv", "text/csv", toCsv(inventory()));
      status.textContent = "Source inventory (CSV) prepared for download.";
    }));
    bar.appendChild(status);
    controls.addEventListener("change", apply);
    search.addEventListener("input", apply);
    controls.hidden = false;
    apply();
  }

  if (typeof window !== "undefined") {
    window.AECSourceNavigator = { csvCell: csvCell, buildCsv: buildCsv };
  }
  if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", init);
    } else {
      init();
    }
  }
})();
