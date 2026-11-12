// Link preliminary asset entries to registry records without treating trial status as program status or sponsor as owner.
(() => {
const normalized=s=>String(s).toUpperCase().replace(/[^A-Z0-9]/g,'');
for(const a of window.assetAudit) {
 if(!a.stage.includes('review pending')) continue;
 const code=normalized(a.asset);
 const matches=window.clinicalTrialAudit.filter(t=>t.company_or_affiliate===a.company && normalized(t.asset).includes(code));
 if(!matches.length) continue;
 const t=matches[0];
 a.stage=`Registry study ${t.study_id}: ${t.registry_phase || 'phase not specified'}, ${t.registry_status.replaceAll('_',' ')}; last posted ${t.registry_last_posted}. This is one study, not a complete current program status.`;
 a.source=t.source;
 a.source_date=t.registry_last_posted;
}
})();
