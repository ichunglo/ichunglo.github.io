/* Regression test for the browser's drug–target CSV export without a browser dependency. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.resolve(__dirname, "..");
const source = fs.readFileSync(path.join(root, "posts/2026-10-02-drug-target-landscape/index.qmd"), "utf8");
const payload = JSON.parse(fs.readFileSync(path.join(root, "data/generated/landscape.json"), "utf8"));

function section(start, end) {
  const first = source.indexOf(start);
  const last = source.indexOf(end, first + start.length);
  assert(first >= 0 && last > first, `Dashboard code section not found: ${start}`);
  return source.slice(first, last);
}

const serializer = section("  const downloadCsv = (", "  const renderMetrics = (");
const drugHandler = section('  drugExportEl.addEventListener("click", () => {', "  [clinicalInclusionEl,");

function parseCsvLine(line) {
  const cells = [];
  let cell = "";
  let quoted = false;
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"' && quoted && line[i + 1] === '"') {
      cell += '"';
      i++;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (char === "," && !quoted) {
      cells.push(cell);
      cell = "";
    } else {
      cell += char;
    }
  }
  cells.push(cell);
  return cells;
}

async function exportDrug(drugId, nameOverride) {
  let handler;
  let downloaded;
  let filename;
  let clicked = false;
  const drug = payload.drugs.find((row) => row.drug_id === drugId);
  assert(drug, `Missing test drug ${drugId}`);
  const context = {
    Blob,
    Map,
    Set,
    payload,
    currentDrugMatches: [{ ...drug, preferred_name: nameOverride || drug.preferred_name }],
    firstApprovalYearByDrug: new Map(),
    drugExportEl: { addEventListener: (event, callback) => { assert.equal(event, "click"); handler = callback; } },
    URL: { createObjectURL: (blob) => { downloaded = blob; return "blob:test"; }, revokeObjectURL: () => {} },
    document: {
      body: { appendChild: () => {} },
      createElement: () => ({ click() { clicked = true; filename = this.download; }, remove() {} }),
    },
    setTimeout: () => {},
  };
  vm.runInNewContext(`${serializer}\n${drugHandler}`, context);
  assert.equal(typeof handler, "function");
  handler();
  assert(clicked && downloaded, "Export did not trigger a CSV download");
  assert.equal(filename, `drug-target-links-${payload.release.version}-filtered.csv`);
  const bytes = new Uint8Array(await downloaded.arrayBuffer());
  assert.deepEqual(Array.from(bytes.slice(0, 3)), [0xef, 0xbb, 0xbf], "CSV should have a UTF-8 BOM for spreadsheet compatibility");
  const csv = await downloaded.text();
  const lines = csv.trimEnd().split("\r\n").map(parseCsvLine);
  const headers = lines.shift();
  return lines.map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index]])));
}

async function main() {
  const imatinib = await exportDrug("DRG-imatinib");
  assert.equal(imatinib.length, 3, "Multi-target drugs must have one row per relationship");
  assert.deepEqual(new Set(imatinib.map((row) => row.target_gene)), new Set(["KIT", "PDGFRB", "ABL1"]));
  assert(imatinib.every((row) => row.target_role === "primary" && row.link_source_url.startsWith("https://")));

  const alectinib = await exportDrug("DRG-alectinib");
  assert.equal(alectinib.length, 2);
  assert.deepEqual(new Set(alectinib.map((row) => row.target_role)), new Set(["primary", "secondary"]));
  assert(alectinib.every((row) => row.drug_has_approval_record === "yes"));

  const formula = await exportDrug("DRG-alectinib", '=HYPERLINK("https://example.invalid","click")');
  assert(formula.every((row) => row.drug_name.startsWith("'=HYPERLINK(")));
  console.log("Dashboard drug–target CSV export: pass (multi-target rows, roles, sources, spreadsheet safety)");
}

main().catch((error) => { console.error(error); process.exitCode = 1; });
