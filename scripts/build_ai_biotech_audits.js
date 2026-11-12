const fs = require('fs');
const path = require('path');
const base = path.resolve(__dirname, '../posts/2026-11-10-ai-biotech-landscape');
global.window = {};
for (const file of ['landscape-data.js','landscape-expansion.js','landscape-expansion-2.js','landscape-expansion-3.js','landscape-dossiers.js','landscape-expansion-4.js','ownership-disclosures.js','landscape-expansion-5.js','asset-audit.js','trial-audit.js','asset-registry-links.js','asset-rights-review.js']) require(path.join(base,file));
const companies = window.landscapeCompanies;
const asOf = process.argv[2] || '2026-11-12';
function writeCsv(file, fields, rows) {
  const quote = x => '"' + String(x ?? '').replace(/"/g,'""') + '"';
  fs.writeFileSync(path.join(base,file), '\ufeff' + fields.join(',') + '\r\n' + rows.map(row => row.map(quote).join(',')).join('\r\n') + '\r\n');
}
writeCsv('ownership-audit.csv',['company','listing_and_control','investor_evidence','disclosure_date','source','evidence_status','review_date'],companies.map(c=>[c.name,c.corporate[0],c.ownershipDisclosure.note,c.ownershipDisclosure.date,c.ownershipDisclosure.url,c.ownershipDisclosure.status,asOf]));
writeCsv('company-audit.csv',['company','region','location','business_model','corporate_status','corporate_status_source','lead_asset','evidence_context','disclosed_portfolio','portfolio_source','rights_and_collaborations','rights_source','application_evidence','other_sources','audit_as_of'],companies.map(c=>[c.name,c.region,c.location,c.model,c.corporate[0],c.corporate[1],c.asset,c.caveat,c.dossier.portfolio,c.dossier.url,c.dossier.rights,c.dossier.rightsUrl,c.applicationEvidence.map(x=>x.join(': ')).join(' | '),c.sources.map(x=>x.join(': ')).join(' | '),asOf]));
const assetFields = ['company','asset','indication','stage','rights','rights_source','source_date','source'];
writeCsv('asset-audit.csv',assetFields,window.assetAudit.map(a=>assetFields.map(k=>a[k])));
writeCsv('pipeline-coverage.csv',['company','business_model','portfolio_summary','portfolio_source','named_asset_records','asset_record_names','rights_summary','rights_source','review_date'],companies.map(c=>{const assets=window.assetAudit.filter(a=>a.company===c.name);return [c.name,c.model,c.dossier.portfolio,c.dossier.url,assets.length,assets.map(a=>a.asset).join(' | '),c.dossier.rights,c.dossier.rightsUrl,asOf];}));
const names = new Set(companies.map(c=>c.name));
const errors = [...window.assetAudit.filter(a=>!names.has(a.company)).map(a=>`orphan asset ${a.asset}`), ...window.clinicalTrialAudit.filter(t=>!names.has(t.company_or_affiliate)).map(t=>`orphan trial ${t.study_id}`), ...companies.filter(c=>!c.ownershipDisclosure.url || !c.dossier.rightsUrl).map(c=>`missing source ${c.name}`)];
if (names.size !== companies.length) errors.push('duplicate company names');
if (errors.length) throw new Error(errors.join('\n'));
console.log(JSON.stringify({companies:companies.length,assets:window.assetAudit.length,trials:window.clinicalTrialAudit.length,investorDisclosures:companies.filter(c=>c.ownershipDisclosure.status!=='Not established in reviewed sources').length}));
