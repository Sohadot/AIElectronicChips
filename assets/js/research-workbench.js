"use strict";
/*
 * AIElectronicChips.com Research Workbench (IDE-010).
 * Progressive enhancement over a static catalog: adds per-requirement collection status and notes,
 * JSON and CSV export, and a print view. Everything stays in this browser tab: nothing is sent,
 * stored, written to the URL or interpolated as HTML. Reloading the page clears the session.
 */
(function () {
  var DISCLAIMER = "User-recorded checklist. The evidence listed has not been independently validated: a received document has " +
    "not been reviewed, authenticated or found sufficient, and this export is not a certification, audit conclusion or assessment.";
  var STATUSES = [
    ["not_requested", "Not requested"],
    ["requested", "Requested"],
    ["received", "Document received (not reviewed)"],
    ["needs_expert_review", "Needs expert review"]
  ];
  var NOTE_LIMIT = 500;

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

  function text(el, selector) {
    var node = selector ? el.querySelector(selector) : el;
    return node ? node.textContent.replace(/\s+/g, " ").trim() : "";
  }

  function listText(el, selector) {
    return Array.prototype.map.call(el.querySelectorAll(selector), function (n) { return n.textContent.replace(/\s+/g, " ").trim(); });
  }

  function collect(workflow) {
    var items = Array.prototype.map.call(workflow.querySelectorAll("li.wb-req"), function (li) {
      var checked = li.querySelector("input[type=radio]:checked");
      var note = li.querySelector("textarea");
      return {
        id: li.id,
        title: text(li, ".wb-req-title"),
        document_requested: text(li, ".wb-doc"),
        why_it_matters: text(li, ".wb-why"),
        evidence_category: li.getAttribute("data-category"),
        basis: li.getAttribute("data-basis"),
        public_availability: li.getAttribute("data-availability"),
        reference: li.getAttribute("data-reference"),
        source_ids: listText(li, ".wb-sources code"),
        unresolved_ids: listText(li, ".wb-unresolved code"),
        conflict_ids: listText(li, ".wb-conflicts code"),
        limitations: listText(li, ".wb-limitations li"),
        not_established_without_review: text(li, ".wb-not-established"),
        user_status: checked ? checked.value : "not_requested",
        user_note: note ? note.value.slice(0, NOTE_LIMIT) : ""
      };
    });
    return {
      format: "aec-evidence-request-checklist",
      format_version: "1.0.0",
      exported_at: new Date().toISOString(),
      disclaimer: DISCLAIMER,
      workflow: { id: workflow.id, title: text(workflow, "h2"), research_question: text(workflow, ".wb-question") },
      requirements: items
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

  function toCsv(data) {
    var rows = [["workflow", "requirement_id", "title", "document_requested", "public_availability", "reference", "source_ids",
      "unresolved_ids", "conflict_ids", "limitations", "user_status", "user_note"]];
    data.requirements.forEach(function (r) {
      rows.push([data.workflow.id, r.id, r.title, r.document_requested, r.public_availability, r.reference, r.source_ids.join(" "),
        r.unresolved_ids.join(" "), r.conflict_ids.join(" "), r.limitations.join(" | "), r.user_status, r.user_note]);
    });
    rows.push(["disclaimer", DISCLAIMER]);
    rows.push(["exported_at", data.exported_at]);
    return buildCsv(rows);
  }

  function button(label, handler) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "button";
    b.textContent = label;
    b.addEventListener("click", handler);
    return b;
  }

  function addControls(li) {
    var host = li.querySelector(".wb-controls");
    if (!host) { return; }
    var fieldset = document.createElement("fieldset");
    var legend = document.createElement("legend");
    legend.textContent = "Your collection status (kept only in this tab)";
    fieldset.appendChild(legend);
    STATUSES.forEach(function (s, i) {
      var id = li.id + "-status-" + s[0];
      var input = document.createElement("input");
      input.type = "radio";
      input.name = li.id + "-status";
      input.id = id;
      input.value = s[0];
      if (i === 0) { input.checked = true; }
      var label = document.createElement("label");
      label.htmlFor = id;
      label.textContent = s[1];
      var wrap = document.createElement("span");
      wrap.className = "wb-option";
      wrap.appendChild(input);
      wrap.appendChild(label);
      fieldset.appendChild(wrap);
    });
    var noteId = li.id + "-note";
    var noteLabel = document.createElement("label");
    noteLabel.htmlFor = noteId;
    noteLabel.className = "wb-note-label";
    noteLabel.textContent = "Note (optional, up to " + NOTE_LIMIT + " characters, not sent anywhere)";
    var note = document.createElement("textarea");
    note.id = noteId;
    note.maxLength = NOTE_LIMIT;
    note.rows = 2;
    note.setAttribute("autocomplete", "off");
    note.setAttribute("spellcheck", "true");
    fieldset.appendChild(noteLabel);
    fieldset.appendChild(note);
    host.appendChild(fieldset);
  }

  function addToolbar(workflow) {
    var bar = workflow.querySelector(".wb-toolbar");
    if (!bar) { return; }
    var status = document.createElement("p");
    status.className = "wb-toolbar-status";
    status.setAttribute("role", "status");
    bar.appendChild(button("Export JSON", function () {
      download(workflow.id + "-checklist.json", "application/json", JSON.stringify(collect(workflow), null, 2) + "\n");
      status.textContent = "JSON checklist prepared for download.";
    }));
    bar.appendChild(button("Export CSV", function () {
      download(workflow.id + "-checklist.csv", "text/csv", toCsv(collect(workflow)));
      status.textContent = "CSV checklist prepared for download.";
    }));
    bar.appendChild(button("Print checklist", function () {
      document.body.setAttribute("data-print-workflow", workflow.id);
      window.print();
    }));
    bar.appendChild(button("Clear this session", function () {
      Array.prototype.forEach.call(workflow.querySelectorAll("li.wb-req"), function (li) {
        var first = li.querySelector("input[type=radio]");
        if (first) { first.checked = true; }
        var note = li.querySelector("textarea");
        if (note) { note.value = ""; }
      });
      status.textContent = "Statuses and notes cleared.";
    }));
    bar.appendChild(status);
    bar.hidden = false;
  }

  function init() {
    Array.prototype.forEach.call(document.querySelectorAll("li.wb-req"), addControls);
    Array.prototype.forEach.call(document.querySelectorAll("article.wb-workflow"), addToolbar);
    var opened = [];
    window.addEventListener("beforeprint", function () {
      // Open closed traces so they print; remember them (across repeated beforeprint events) to close afterwards.
      Array.prototype.forEach.call(document.querySelectorAll("details.evidence-trace"), function (d) {
        if (!d.open) { d.open = true; opened.push(d); }
      });
    });
    window.addEventListener("afterprint", function () {
      opened.forEach(function (d) { d.open = false; });
      opened = [];
      document.body.removeAttribute("data-print-workflow");
    });
  }

  if (typeof window !== "undefined") {
    window.AECWorkbench = { csvCell: csvCell, buildCsv: buildCsv, DISCLAIMER: DISCLAIMER };
  }
  if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", init);
    } else {
      init();
    }
  }
})();
