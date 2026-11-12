"use strict";
/*
 * AIElectronicChips.com Research Workbench (IDE-010).
 * Progressive enhancement over a static catalog: adds per-requirement collection status and notes,
 * JSON and CSV export, and a print view; for Workflow C, a documentary preflight (IDE-015). The site itself never submits, stores, writes to the URL or
 * interpolates as HTML anything entered here; reloading the page clears the session. Browser spelling
 * and autocorrect services are switched off on the note field, because some send typed text elsewhere.
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
    legend.textContent = "Your collection status (held only in this tab)";
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
    noteLabel.textContent = "Note (optional, up to " + NOTE_LIMIT + " characters; this site does not submit or save it)";
    var note = document.createElement("textarea");
    note.id = noteId;
    note.maxLength = NOTE_LIMIT;
    note.rows = 2;
    note.setAttribute("autocomplete", "off");
    // Browser spell-check services (for example Chrome's Enhanced Spell Check) can send typed text to a third party.
    note.spellcheck = false;
    note.setAttribute("spellcheck", "false");
    note.setAttribute("autocorrect", "off");
    note.setAttribute("autocapitalize", "off");
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

  /*
   * Documentary preflight (IDE-015), Workflow C only. Every label, definition, ceiling and boundary is read from the
   * static page, which is generated from the IDE-014 record model. This script records only whether the user reports a
   * document and each of its attributes as present, missing or unknown, explains the gaps, and exports or prints that
   * summary. It never computes, raises or reports an evidence state: a ceiling is copied from the page unchanged.
   */
  function all(root, selector) {
    return Array.prototype.slice.call(root.querySelectorAll(selector));
  }

  function radioGroup(host, name, legendText, options, labelKey) {
    var fieldset = document.createElement("fieldset");
    fieldset.className = "pf-options";
    var legend = document.createElement("legend");
    legend.textContent = legendText;
    fieldset.appendChild(legend);
    options.forEach(function (o, i) {
      var input = document.createElement("input");
      input.type = "radio";
      input.name = name;
      input.id = name + "-" + o.value;
      input.value = o.value;
      if (i === 0) { input.checked = true; }
      var label = document.createElement("label");
      label.htmlFor = input.id;
      label.textContent = o[labelKey];
      var wrap = document.createElement("span");
      wrap.className = "wb-option";
      wrap.appendChild(input);
      wrap.appendChild(label);
      fieldset.appendChild(wrap);
    });
    host.appendChild(fieldset);
  }

  function checkedValue(root, selector) {
    var c = root.querySelector(selector + " input[type=radio]:checked");
    return c ? c.value : "not_marked";
  }

  function el(tag, cls, content) {
    var n = document.createElement(tag);
    if (cls) { n.className = cls; }
    if (content !== undefined) { n.textContent = content; }
    return n;
  }

  function listInto(parent, items, empty) {
    if (!items.length) {
      parent.appendChild(el("p", "muted", empty));
      return;
    }
    var ul = el("ul");
    items.forEach(function (s) { ul.appendChild(el("li", "", s)); });
    parent.appendChild(ul);
  }

  function initPreflight() {
    var panel = document.querySelector("section.wb-preflight");
    if (!panel) { return; }
    var options = all(panel, ".pf-status-defs dt[data-status]").map(function (dt) {
      return { value: dt.getAttribute("data-status"), attribute: text(dt), document: dt.getAttribute("data-document-label") };
    });
    var labelOf = {};
    options.forEach(function (o) { labelOf[o.value] = o.attribute; });
    var statement = function (key) { return text(panel, '.pf-statements [data-key="' + key + '"]'); };
    var guide = {};
    all(panel, ".pf-guide dd[data-attr]").forEach(function (dd) {
      guide[dd.getAttribute("data-attr")] = { significance: text(dd, ".pf-sig"), request: text(dd, ".pf-ask") };
    });
    var sections = all(panel, "section.pf-req");

    function snapshot(section) {
      var holderDefault = text(section, ".pf-holder");
      var records = all(section, ".pf-record").map(function (rec) {
        var attrs = all(rec, "li.pf-attr").map(function (li) {
          var id = li.getAttribute("data-attr");
          return { id: id, label: text(li, ".pf-attr-label"), description: text(li, ".pf-attr-desc"),
            status: checkedValue(li, ".pf-attr-controls"), significance: guide[id] ? guide[id].significance : "",
            request: guide[id] ? guide[id].request : "" };
        });
        return { record_type_id: rec.getAttribute("data-record"), label: text(rec, ".pf-record-label"),
          holder: text(rec, ".pf-record-holder") || holderDefault, ceiling_id: rec.getAttribute("data-ceiling") || null,
          ceiling: text(rec, ".pf-record-meta"), ceiling_label: text(rec, ".pf-ceiling"),
          does_not_establish: text(rec, ".pf-dne span"), document_status: checkedValue(rec, ".pf-doc-controls"), attributes: attrs };
      });
      var requests = [];
      var notMarked = [];
      records.forEach(function (r) {
        if (r.document_status === "missing") {
          requests.push(r.holder + ": provide “" + r.label + "”. It must carry: " +
            r.attributes.map(function (a) { return a.label; }).join(", ") + ".");
          return;
        }
        if (r.document_status === "unknown") {
          requests.push(r.holder + ": confirm whether “" + r.label + "” exists for the named site and configuration.");
        }
        if (r.document_status === "not_marked") { notMarked.push(r.label + " (the record itself)"); }
        r.attributes.forEach(function (a) {
          if (a.status === "missing") {
            requests.push(r.holder + ": provide a version of “" + r.label + "” that " + a.request + ".");
          } else if (a.status === "unknown") {
            requests.push(r.holder + ": confirm whether “" + r.label + "” " + a.request + ".");
          } else if (a.status === "not_marked") {
            notMarked.push(r.label + ": " + a.label);
          }
        });
      });
      return {
        requirement: {
          id: section.getAttribute("data-requirement"), title: text(section, ".pf-title"), domain: text(section, ".pf-domain"),
          claim: text(section, ".pf-claim"), target_state: { id: section.getAttribute("data-target-state"), label: text(section, ".pf-target") },
          stage_note: text(section, ".pf-stage-note") || null, holder: holderDefault, verification_conditions: listText(section, ".pf-conditions li"),
          potential_supported_claim: text(section, ".pf-supported"), prohibited_inference: text(section, ".pf-prohibited"),
          public_record: text(section, ".pf-gap")
        },
        records: records,
        outstanding_requests: requests,
        not_yet_marked: notMarked,
        substitutes_not_accepted: all(section, ".pf-substitutes li").map(function (li) {
          return { record_type_id: li.getAttribute("data-record"), label: text(li, ".pf-sub-label"), detail: text(li) };
        }),
        category_errors: all(section, ".pf-errors li").map(function (li) {
          return { id: li.getAttribute("data-error"), inference: text(li, ".pf-error-inference"), why_not: text(li, ".pf-error-why") };
        }),
        dependencies: all(section, ".pf-deps li").map(function (li) {
          return { direction: li.getAttribute("data-direction"), requirement: li.getAttribute("data-ide006"), text: text(li) };
        }),
        dependency_rule: statement("dependency_rule")
      };
    }

    function explain(section) {
      var out = section.querySelector(".pf-result");
      while (out.firstChild) { out.removeChild(out.firstChild); }
      var s = snapshot(section);
      out.appendChild(el("h5", "", "Gap explanation for your selections"));
      out.appendChild(el("p", "pf-no-state", statement("no_state_statement")));
      s.records.forEach(function (r) {
        var box = el("div", "pf-result-record");
        box.appendChild(el("h6", "", "Required record: " + r.label));
        box.appendChild(el("p", "", "Document: " + options.filter(function (o) { return o.value === r.document_status; })[0].document +
          ". Holder: " + r.holder + ". Ceiling, unchanged by your selections: " + r.ceiling_label + "."));
        var by = function (st) { return r.attributes.filter(function (a) { return a.status === st; }); };
        box.appendChild(el("p", "pf-result-head", "Present, as you report it"));
        listInto(box, by("present").map(function (a) { return a.label; }), "None marked present.");
        box.appendChild(el("p", "pf-result-head", "Missing material and why it matters"));
        listInto(box, by("missing").concat(by("unknown")).map(function (a) {
          return a.label + " (" + labelOf[a.status].toLowerCase() + "): " + a.significance;
        }), r.document_status === "missing" ? "The record itself is not held; every attribute above is outstanding." : "None marked missing or unknown.");
        if (r.document_status === "present" && by("present").length === r.attributes.length) {
          box.appendChild(el("p", "pf-complete", statement("completeness_boundary")));
        }
        box.appendChild(el("p", "pf-result-head", "Still not established, even by a complete record"));
        listInto(box, [r.does_not_establish], "");
        out.appendChild(box);
      });
      out.appendChild(el("p", "pf-result-head", "Next documentary requests"));
      listInto(out, s.outstanding_requests, "None from your selections. Items not yet marked are listed below.");
      out.appendChild(el("p", "pf-result-head", "Not yet marked"));
      listInto(out, s.not_yet_marked, "Every item is marked.");
      out.appendChild(el("p", "pf-result-head", "Prohibited inference"));
      listInto(out, [s.requirement.prohibited_inference], "");
      out.hidden = false;
    }

    function packet(section) {
      var s = snapshot(section);
      return {
        format: panel.getAttribute("data-format"),
        format_version: panel.getAttribute("data-format-version"),
        title: text(panel, ".pf-packet-label"),
        exported_at: new Date().toISOString(),
        disclaimer: text(panel, ".pf-disclaimer"),
        checklist_disclaimer: DISCLAIMER,
        research_status: text(panel, ".pf-research-status"),
        evidence_state_established: null,
        no_state_statement: statement("no_state_statement"),
        completeness_boundary: statement("completeness_boundary"),
        methodology: {
          record_model: panel.getAttribute("data-record-model"),
          record_model_file: panel.getAttribute("data-record-model-file"),
          record_model_compiled: panel.getAttribute("data-record-model-compiled"),
          evidence_states_release: panel.getAttribute("data-states-release"),
          preflight_definitions: "/data/deployment-evidence-preflight.json",
          workbench_model: "/data/industrial-evidence-requests.json",
          workbench_requirement: "/research-workbench/#" + s.requirement.id
        },
        requirement: s.requirement,
        records: s.records.map(function (r) {
          return { record_type_id: r.record_type_id, label: r.label, holder: r.holder,
            state_ceiling: { id: r.ceiling_id, label: r.ceiling_label }, ceiling_note: r.ceiling,
            does_not_establish: r.does_not_establish, document_status: r.document_status,
            attributes: r.attributes.map(function (a) {
              return { id: a.id, label: a.label, description: a.description, status: a.status, significance: a.significance };
            }) };
        }),
        outstanding_requests: s.outstanding_requests,
        not_yet_marked: s.not_yet_marked,
        prohibited_inferences: [s.requirement.prohibited_inference].concat(s.records.map(function (r) { return r.does_not_establish; })),
        category_errors: s.category_errors,
        substitutes_not_accepted: s.substitutes_not_accepted,
        dependencies: s.dependencies,
        dependency_rule: s.dependency_rule,
        boundaries: all(panel, ".pf-boundaries li").map(function (li) { return { id: li.getAttribute("data-boundary"), text: text(li) }; })
      };
    }

    function packetCsv(p) {
      var rid = p.requirement.id;
      var rows = [["section", "requirement_id", "record_type_id", "item_id", "item", "user_status", "detail"]];
      rows.push(["requirement", rid, "", "", p.requirement.title, "", p.requirement.claim]);
      rows.push(["target", rid, "", p.requirement.target_state.id, p.requirement.target_state.label, "", ""]);
      p.records.forEach(function (r) {
        rows.push(["record", rid, r.record_type_id, "", r.label, r.document_status, "Holder: " + r.holder]);
        rows.push(["ceiling", rid, r.record_type_id, r.state_ceiling.id || "", r.state_ceiling.label, "", r.ceiling_note]);
        r.attributes.forEach(function (a) {
          rows.push(["attribute", rid, r.record_type_id, a.id, a.label, a.status, a.significance]);
        });
        rows.push(["does_not_establish", rid, r.record_type_id, "", r.does_not_establish, "", ""]);
      });
      p.outstanding_requests.forEach(function (q) { rows.push(["request", rid, "", "", q, "", ""]); });
      p.not_yet_marked.forEach(function (q) { rows.push(["not_yet_marked", rid, "", "", q, "", ""]); });
      rows.push(["prohibited_inference", rid, "", "", p.requirement.prohibited_inference, "", ""]);
      p.category_errors.forEach(function (c) { rows.push(["category_error", rid, "", c.id, c.inference, "", c.why_not]); });
      p.dependencies.forEach(function (d) { rows.push(["dependency", rid, "", d.requirement, d.direction, "", d.text]); });
      p.boundaries.forEach(function (b) { rows.push(["boundary", rid, "", b.id, b.text, "", ""]); });
      [["title", p.title], ["disclaimer", p.disclaimer], ["checklist_disclaimer", p.checklist_disclaimer],
        ["research_status", p.research_status], ["no_state_statement", p.no_state_statement],
        ["record_model", p.methodology.record_model + " (" + p.methodology.record_model_file + ")"],
        ["format", p.format + " " + p.format_version], ["exported_at", p.exported_at]].forEach(function (m) {
        rows.push([m[0], rid, "", "", m[1], "", ""]);
      });
      return buildCsv(rows);
    }

    var current = sections[0];
    function show(section) {
      sections.forEach(function (s) { s.hidden = s !== section; });
      current = section;
      explain(section);
    }

    sections.forEach(function (section) {
      all(section, ".pf-record").forEach(function (rec) {
        radioGroup(rec.querySelector(".pf-doc-controls"), section.id + "--" + rec.getAttribute("data-record") + "--document",
          "Do you hold this record? (your report only)", options, "document");
        all(rec, "li.pf-attr").forEach(function (li) {
          radioGroup(li.querySelector(".pf-attr-controls"), section.id + "--" + rec.getAttribute("data-record") + "--" + li.getAttribute("data-attr"),
            text(li, ".pf-attr-label") + " in this record", options, "attribute");
        });
      });
      section.addEventListener("change", function () { explain(section); });
    });

    var picker = panel.querySelector(".pf-picker");
    var selectId = "pf-select";
    var selectLabel = el("label", "", "Workflow C requirement");
    selectLabel.htmlFor = selectId;
    var select = document.createElement("select");
    select.id = selectId;
    sections.forEach(function (s) {
      var o = document.createElement("option");
      o.value = s.id;
      o.textContent = text(s, "h4");
      select.appendChild(o);
    });
    select.addEventListener("change", function () { show(document.getElementById(select.value)); });
    picker.appendChild(selectLabel);
    picker.appendChild(select);
    picker.hidden = false;

    var bar = panel.querySelector(".pf-toolbar");
    var status = el("p", "wb-toolbar-status");
    status.setAttribute("role", "status");
    bar.appendChild(button("Export preflight JSON", function () {
      download("workflow-rack-deployment-preflight-" + current.getAttribute("data-requirement") + ".json", "application/json",
        JSON.stringify(packet(current), null, 2) + "\n");
      status.textContent = "Preflight packet (JSON) prepared for download.";
    }));
    bar.appendChild(button("Export preflight CSV", function () {
      download("workflow-rack-deployment-preflight-" + current.getAttribute("data-requirement") + ".csv", "text/csv", packetCsv(packet(current)));
      status.textContent = "Preflight packet (CSV) prepared for download.";
    }));
    bar.appendChild(button("Print preflight", function () {
      document.body.setAttribute("data-print-workflow", "workflow-rack-deployment");
      document.body.setAttribute("data-print-preflight", current.id);
      window.print();
    }));
    bar.appendChild(button("Clear preflight", function () {
      sections.forEach(function (s) {
        all(s, "fieldset.pf-options").forEach(function (f) { f.querySelector("input[type=radio]").checked = true; });
      });
      explain(current);
      status.textContent = "Preflight selections cleared.";
    }));
    bar.appendChild(status);
    bar.hidden = false;

    // From the catalog: each Workflow C requirement offers a way into its preflight.
    all(document, "#workflow-rack-deployment li.wb-req").forEach(function (li) {
      var target = document.getElementById("pf-" + li.id);
      var host = li.querySelector(".wb-controls");
      if (!target || !host) { return; }
      host.appendChild(button("Open documentary preflight", function () {
        select.value = target.id;
        show(target);
        select.focus();
        panel.scrollIntoView();
      }));
    });
    show(current);
  }

  function init() {
    Array.prototype.forEach.call(document.querySelectorAll("li.wb-req"), addControls);
    Array.prototype.forEach.call(document.querySelectorAll("article.wb-workflow"), addToolbar);
    initPreflight();
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
      document.body.removeAttribute("data-print-preflight");
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
