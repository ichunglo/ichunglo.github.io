/* Ensure target profiles treat curated text as text, not executable markup. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname, "../posts/2026-10-02-drug-target-landscape/index.qmd"), "utf8");
const start = source.indexOf("  const renderTargetDetail = (target) => {");
const end = source.indexOf("  const updateExplorerHash = () => {", start);
const badgeStart = source.indexOf("  const programOutcomeBadges = (events, program) => {");
const badgeEnd = source.indexOf("  const metricsEl =", badgeStart);
assert(start >= 0 && end > start, "Target-detail renderer not found");
assert(badgeStart >= 0 && badgeEnd > badgeStart, "Program-outcome badge renderer not found");

const attack = '<img src=x onerror="alert(1)">';
const target = { target_id: "TGT-test", preferred_name: attack, gene_symbol: attack, uniprot_accession: attack, protein_group: attack, landscape_scope: attack };
const drug = { drug_id: "DRG-test", preferred_name: attack };
const payload = {
  targets: [target, { target_id: "TGT-unknown-test", preferred_name: attack, gene_symbol: attack }],
  drugs: [drug],
  drug_targets: [
    { drug_id: drug.drug_id, target_id: target.target_id, target_role: "primary", source_id: "SRC-evil" },
    { drug_id: drug.drug_id, target_id: "TGT-unknown-test", target_role: "secondary", source_id: "SRC-evil" },
  ],
  approvals: [{ drug_id: drug.drug_id, approval_date: "2020", source_id: "SRC-evil" }],
  programs: [
    { program_id: "PRG-direct", drug_id: drug.drug_id, primary_target_id: target.target_id, indication_name: "Alzheimer disease", lifecycle_status: attack, inclusion_status: "included" },
    { program_id: "PRG-review", drug_id: drug.drug_id, primary_target_id: target.target_id, indication_name: "Review indication", lifecycle_status: "phase_2", inclusion_status: "needs_review" },
    { program_id: "PRG-unclear", drug_id: drug.drug_id, primary_target_id: "TGT-unknown-test", indication_name: attack, lifecycle_status: attack, inclusion_status: attack },
  ],
  trials: [{ trial_id: "TRIAL-test", program_id: "PRG-direct", registry_identifier: attack, recruitment_status: attack, start_date: "2020-01" }],
  evidence_review: [],
  outcomes: [
    { program_id: "PRG-direct", event_type: attack, description: attack, event_date: "2021-01", source_id: "SRC-evil" },
    { program_id: "PRG-direct", event_type: "endpoint_failure", description: "Published outcome", confidence: "high", stated_or_inferred: "stated", source_id: "SRC-good" },
    { program_id: "PRG-review", event_type: "safety_failure", description: "Provisional event", event_date: "2021-02", source_id: "SRC-good" },
  ],
  sources: [{ source_id: "SRC-evil", title: attack, url: "javascript:alert(1)" }, { source_id: "SRC-good", title: "Primary publication", url: "https://example.org/source" }],
};
let drugClick;
let drugResultsRendered = 0;
let drugHashUpdated = 0;
const detailEl = {
  innerHTML: "",
  insertAdjacentHTML(_position, html) { this.innerHTML += html; },
  querySelectorAll: () => [{ dataset: { detailDrug: drug.drug_id }, addEventListener: (_event, callback) => { drugClick = callback; } }],
};
const drugSearchEl = { value: "" };
const drugYearEl = { value: "2020" };
const context = {
  payload,
  detailEl,
  drugSearchEl,
  drugYearEl,
  focusedDrugId: null,
  drugResultsVisible: 50,
  updateDrugHash: () => { drugHashUpdated++; },
  renderDrugResults: () => { drugResultsRendered++; },
  document: { querySelector: () => ({ scrollIntoView: () => {} }) },
  targetDrugs: () => [drug],
  escapeHtml: (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]),
  readableLabel: (value) => String(value || "unknown").replaceAll("_", " "),
  formatNumber: (value) => Number(value).toLocaleString("en-US"),
};
vm.runInNewContext(`${source.slice(badgeStart, badgeEnd)}\n${source.slice(start, end)}\nrenderTargetDetail(payload.targets[0]);`, context);
assert(detailEl.innerHTML.includes("&lt;img"), "Markup-like text should remain visible as escaped text");
assert(!detailEl.innerHTML.includes("<img"), "No injected image markup should be created");
assert(!detailEl.innerHTML.includes('href="javascript:'), "Unsafe source URLs should not become links");
assert(detailEl.innerHTML.includes("Clinical programs through co-target links"));
assert(detailEl.innerHTML.includes("Outcome evidence (2)"));
assert(detailEl.innerHTML.includes("Indication: Alzheimer disease"));
assert(detailEl.innerHTML.includes("high confidence · stated"));
assert(detailEl.innerHTML.includes("Outcome events in included programs:"));
assert(detailEl.innerHTML.includes("1 program remains held from headline analyses"));
assert(detailEl.innerHTML.includes("Held from headline analyses; event labels do not establish whole-program failure."));
assert(!detailEl.innerHTML.includes("safety failure: 1"), "Provisional events should not appear in included-program summary counts");
assert(detailEl.innerHTML.includes("safety failure event (needs review)"), "Dated provisional outcomes should be qualified in the timeline");
assert(detailEl.innerHTML.includes('href="https://example.org/source"'), "Each outcome should link directly to its cited source");
assert(detailEl.innerHTML.includes('data-detail-drug="DRG-test"'), "Drug names should link back to the drug explorer");
assert.equal(typeof drugClick, "function");
drugClick();
assert.equal(context.focusedDrugId, drug.drug_id);
assert.equal(drugSearchEl.value, drug.preferred_name);
assert.equal(drugYearEl.value, "all");
assert.equal(drugResultsRendered, 1);
assert.equal(drugHashUpdated, 1);
console.log("Dashboard target detail: pass (escaping and drug-to-target navigation)");
