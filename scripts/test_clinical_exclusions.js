/* Guard the dashboard boundary between held evidence and headline analysis. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.resolve(__dirname, "..");
const source = fs.readFileSync(path.join(root, "posts/2026-10-02-drug-target-landscape/index.qmd"), "utf8");
const payload = JSON.parse(fs.readFileSync(path.join(root, "data/generated/landscape.json"), "utf8"));
const auditRows = fs.readFileSync(path.join(root, "data/curated/publication-program-audit.csv"), "utf8")
  .trim().split(/\r?\n/).slice(1).map((line) => {
    const [programId, disposition] = line.split(",", 3);
    return { programId, disposition };
  });
const heldIds = new Set(payload.programs.filter((row) => row.inclusion_status === "needs_review").map((row) => row.program_id));
assert.equal(heldIds.size, 9);
assert.deepEqual(heldIds, new Set(auditRows.filter((row) => row.disposition === "held").map((row) => row.programId)));

const briskAps = payload.outcomes.find((row) => row.outcome_event_id === "OUT-NCT01108705");
const briskPs = payload.outcomes.find((row) => row.outcome_event_id === "OUT-NCT00825955");
assert.equal(briskAps.event_type, "unknown");
assert.equal(briskAps.stated_or_inferred, "unknown");
assert.equal(briskAps.primary_reason, "0");
assert.equal(briskPs.event_type, "endpoint_failure");
assert(heldIds.has(briskAps.program_id));

const badgeStart = source.indexOf("  const programOutcomeBadges = (events, program) => {");
const badgeEnd = source.indexOf("  const metricsEl =", badgeStart);
assert(badgeStart >= 0 && badgeEnd > badgeStart);
const context = {
  readableLabel: (value) => String(value || "unknown").replaceAll("_", " "),
  escapeHtml: (value) => String(value ?? "").replace(/[&<>\"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]),
};
vm.runInNewContext(`${source.slice(badgeStart, badgeEnd)}\nthis.badges = programOutcomeBadges;`, context);
const heldProgram = payload.programs.find((row) => row.program_id === "PRG-brivanib-hcc");
const badges = context.badges(payload.outcomes.filter((row) => row.program_id === heldProgram.program_id), heldProgram);
assert(badges.includes("endpoint failure · NCT00825955"));
assert(badges.includes("unknown · NCT01108705"));
assert(!badges.includes("endpoint failure · NCT01108705"));

assert(source.includes("const phaseCounts = includedPrograms.reduce("), "Stage chart must exclude held programs");
assert(source.includes("clinical: includedPrograms.filter("), "Development map must exclude held programs");
assert(source.includes('clinicalInclusionEl.value = "included";'), "Chart drill-down must retain included-only scope");
assert(source.includes("Needs review — held from headline analyses"), "Held table rows need an explicit exclusion label");
console.log("Clinical exclusion dashboard checks: pass (nine held, BRISK-APS unknown, included-only charts)");
