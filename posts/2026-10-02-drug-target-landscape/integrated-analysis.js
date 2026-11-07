/* Integrated exploratory figures. Counts are distinct partially deduplicated drug IDs. */
(() => {
  'use strict';
  const root = document.getElementById('integrated-landscape');
  if (!root) return;
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const number = value => Number(value).toLocaleString();
  const safeUrl = value => { try { const u = new URL(value); return u.protocol === 'https:' ? u.href : ''; } catch { return ''; } };
  const link = (url, text) => safeUrl(url) ? `<a href="${esc(safeUrl(url))}" target="_blank" rel="noopener noreferrer">${esc(text)}</a>` : '';
  const unique = values => new Set(values).size;
  const state = {limit:20, role:'all', type:'all', minimum:5, scatter:'approved', hotspot:'approved', hotspotRank:'none', disease:'drug', selected:null, detailAll:false, diseaseGroup:null, diseaseTerm:null};
  let data, drugs, targets;
  const proteinClasses = ['Enzymes','GPCRs','Ion channels','Catalytic receptors','Other proteins','Endogenous peptides','Transporters','Nuclear hormone receptors','Receptors'];

  function typeOf(t) {
    const value = String(t.type || '').toLowerCase(), name = String(t.name || '').toLowerCase();
    if (/\b(mrna|rna|dna)\b/.test(name) || value.includes('nonprotein') || value.includes('process')) return 'nonprotein';
    if (value.includes('family') || value.includes('complex') || /\b(family|complex|heterodimer)\b/.test(name)) return 'family';
    if (proteinClasses.includes(t.type) || value === 'source_reported_gene_target' || t.uniprot) return 'protein';
    return 'unclassified';
  }
  function sourceClass(t) {
    if (proteinClasses.includes(t.type)) return t.type;
    if (typeOf(t) === 'nonprotein') return 'Non-protein / process';
    if (typeOf(t) === 'family') return 'Family / complex';
    if (t.uniprot_class) return t.uniprot_class;
    const cs=(t.source_classes || []).map(v=>v.toLowerCase());
    if (cs.some(v=>v.startsWith('gpcr '))) return 'GPCRs';
    if (cs.some(v=>v==='nuclear hormone receptor')) return 'Nuclear hormone receptors';
    if (cs.some(v=>v.includes('ion channel'))) return 'Ion channels';
    if (cs.some(v=>v==='kinase') && /receptor/i.test(t.name)) return 'Catalytic receptors';
    if (cs.some(v=>v==='kinase'||v==='peptidase')) return 'Enzymes';
    if (cs.some(v=>v==='transporter')) return 'Transporters';
    return 'Unclassified / other';
  }
  function relevantLinks(role=state.role) {
    return data.links.filter(l => (role === 'all' || l.primary) && (state.type === 'all' || typeOf(targets.get(l.t)) === state.type));
  }
  function summaries(links) {
    const map=new Map();
    for(const l of links){
      if(!map.has(l.t)) map.set(l.t,{target:targets.get(l.t),all:new Set(),trial:new Set(),approved:new Set(),within:new Set(),fda:new Set(),unknown:new Set()});
      const r=map.get(l.t),d=drugs.get(l.d);r.all.add(l.d);if(l.trial)r.trial.add(l.d);
      if(d.approved){r.approved.add(l.d);if(l.trial)r.within.add(l.d);}if(d.fda)r.fda.add(l.d);
      if(!l.primary&&!l.secondary)r.unknown.add(l.d);
    }
    return [...map.values()];
  }
  const targetLabel = t => t.gene ? `${t.gene} · ${t.name}` : t.name;
  function shade(value,max) {
    const t=max?Math.max(0,Math.min(1,value/max)):0, lo=[180,218,228],hi=[16,72,112];
    return `rgb(${lo.map((x,i)=>Math.round(x+(hi[i]-x)*t)).join(',')})`;
  }
  function targetBars(rows,columns) {
    if(!rows.length)return '<p class="ia-muted">No target records match the selected filters.</p>';
    const max=Math.max(1,...rows.flatMap(r=>columns.map(c=>r[c.key].size)));
    return `<div class="ia-bar-list">${rows.map(r=>`<div class="ia-row"><button type="button" class="ia-target" data-target="${esc(r.target.id)}">${esc(targetLabel(r.target))}</button><div class="ia-bars">${columns.map(c=>{const n=r[c.key].size;const blue=c.key==='trial'||c.key==='all';return `<button type="button" class="ia-bar-line" data-target="${esc(r.target.id)}" aria-label="${esc(targetLabel(r.target))}: ${number(n)} ${esc(c.label)}"><span class="ia-bar-track"><span class="ia-bar-fill ${blue?'ia-blue':c.key==='fda'?'ia-green':'ia-orange'}" style="width:${100*n/max}%;${blue?`background:${shade(n,max)}`:''}"></span></span><span class="ia-bar-value">${number(n)}</span></button>`;}).join('')}</div></div>`).join('')}</div>`;
  }
  function legend(columns){return `<div class="ia-legend">${columns.map(c=>`<span><i class="${c.key==='trial'||c.key==='all'?'ia-blue':c.key==='fda'?'ia-green':'ia-orange'}"></i>${esc(c.label)}</span>`).join('')}</div>`;}
  function renderDeveloped(rows){const cols=[{key:'all',label:'All developed drug records'},{key:'approved',label:'Of these, reported approved'}];const top=[...rows].sort((a,b)=>b.all.size-a.all.size||targetLabel(a.target).localeCompare(targetLabel(b.target))).slice(0,state.limit);return `${legend(cols)}${targetBars(top,cols)}`;}
  function renderApproved(rows){const cols=[{key:'approved',label:'All linked drugs reported approved'},{key:'fda',label:'Of these, FDA evidence reviewed'}];const top=[...rows].sort((a,b)=>b.approved.size-a.approved.size||targetLabel(a.target).localeCompare(targetLabel(b.target))).slice(0,state.limit);return `${legend(cols)}${targetBars(top,cols)}`;}
  function renderComparison(rows) {
    const top=[...rows].sort((a,b)=>b.trial.size-a.trial.size||targetLabel(a.target).localeCompare(targetLabel(b.target))).slice(0,state.limit);
    const cols=[{key:'trial',label:'Drugs linked to selected study records'},{key:'within',label:'Of those drugs, approval reported'}];
    const all=[{key:'trial',label:'Drugs linked to selected study records'},{key:'approved',label:'All linked drugs with approval reported'}];
    return `<p class="ia-muted"><strong>How to read the colors:</strong> The blue count is distinct drugs linked to this target and selected using the study-record sources described above; some study matches are candidates, not individually verified. The orange count in the right chart is the number of those same drugs that also have an approval reported in the available sources. For example, if blue is 10 and orange is 4, four of those ten drugs have a reported approval. It does not mean four of ten trials succeeded. A drug's approval can be for another target or indication.</p><div class="ia-grid"><article><h3>All linked drugs with an approval reported</h3><p class="ia-muted">The orange count can include approved drugs outside the selected study-record set, so it can be larger than the blue count.</p>${legend(all)}${targetBars(top,all)}</article><article><h3>Reported approvals among drugs in the selected study set</h3><p class="ia-muted">The orange count is a subset of the blue count. The records are incomplete and this is not a clinical success rate.</p>${legend(cols)}${targetBars(top,cols)}</article></div>`;
  }
  function renderScatter(rows) {
    const list=rows.filter(r=>r.trial.size>=state.minimum).sort((a,b)=>b.trial.size-a.trial.size).slice(0,state.limit);
    if(!list.length)return '<p class="ia-muted">No targets meet the minimum.</p>';
    const xs=list.map(r=>r.trial.size), ys=list.map(r=>r[state.scatter].size), maxX=Math.max(1,...xs), maxY=Math.max(1,...ys), w=800,h=450,left=65,bottom=55,top=25,right=25;
    const xp=n=>left+n/maxX*(w-left-right),yp=n=>h-bottom-n/maxY*(h-top-bottom);
    let marks='';for(let i=0;i<=4;i++){let x=left+i*(w-left-right)/4,y=top+i*(h-top-bottom)/4;marks+=`<line x1="${x}" y1="${top}" x2="${x}" y2="${h-bottom}" stroke="#e5edf0"/><text x="${x}" y="${h-bottom+20}" text-anchor="middle">${Math.round(maxX*i/4)}</text><line x1="${left}" y1="${y}" x2="${w-right}" y2="${y}" stroke="#e5edf0"/><text x="${left-10}" y="${y+4}" text-anchor="end">${Math.round(maxY*(4-i)/4)}</text>`;}
    const dots=list.map((r,i)=>{const x=xp(r.trial.size),y=yp(r[state.scatter].size),label=targetLabel(r.target);return `<g tabindex="0" role="button" data-target="${esc(r.target.id)}" aria-label="${esc(label)}: ${r.trial.size} drugs linked to selected studies; ${r[state.scatter].size} reported approved"><title>${esc(label)}: ${r.trial.size} linked to selected studies; ${r[state.scatter].size} reported approved</title><circle cx="${x}" cy="${y}" r="7" fill="${shade(r.trial.size,maxX)}" stroke="#fff" stroke-width="2"/>${i<8?`<text x="${x+9}" y="${y-6}" class="ia-point-label">${esc(r.target.gene||r.target.name.slice(0,20))}</text>`:''}</g>`;}).join('');
    return `<svg class="ia-scatter" viewBox="0 0 ${w} ${h}" role="group" aria-label="Scatterplot of selected targets">${marks}${dots}<text x="${(left+w-right)/2}" y="${h-7}" text-anchor="middle">Drugs linked to selected study records</text><text transform="translate(14 ${(top+h-bottom)/2}) rotate(-90)" text-anchor="middle">Reported approved drug records</text></svg><p class="ia-muted">Select a point to see its drugs. With “all linked approvals,” the vertical count can be larger than the selected-study count.</p>`;
  }
  function renderHotspots(rows){
    const eligible=rows.filter(r=>r.trial.size>=state.minimum);
    const sorted=(state.hotspotRank==='none'?eligible.filter(r=>r[state.hotspot].size===0).sort((a,b)=>b.trial.size-a.trial.size):eligible.sort((a,b)=>{
      const av=a.within.size/a.trial.size,bv=b.within.size/b.trial.size;return av-bv||b.trial.size-a.trial.size;})).slice(0,state.limit);
    if(!sorted.length)return `<p class="ia-muted">${state.hotspotRank==='none'?'No targets above the minimum have zero approvals recorded in this view.':'No targets meet the minimum.'}</p>`;
    return `<div class="ia-table-wrap"><table class="ia-table"><thead><tr><th>Target</th><th>Drugs linked to selected study records</th><th>${state.hotspot==='within'?'Approval reported among those drugs':'Approval reported among all linked drugs'}</th>${state.hotspot==='within'?'<th>Share with reported approval</th>':''}</tr></thead><tbody>${sorted.map(r=>`<tr><td><button class="ia-text-button" data-target="${esc(r.target.id)}">${esc(targetLabel(r.target))}</button></td><td>${number(r.trial.size)}</td><td>${r[state.hotspot].size?number(r[state.hotspot].size):'None recorded'}</td>${state.hotspot==='within'?`<td>${(100*r.within.size/r.trial.size).toFixed(1)}%</td>`:''}</tr>`).join('')}</tbody></table></div>`;
  }
  function groupedBars(rows,groupFn,entityFn) {
    const groups=new Map();for(const r of rows){const group=groupFn(r);if(!groups.has(group))groups.set(group,new Set());groups.get(group).add(entityFn(r));}
    return [...groups].map(([name,ids])=>({name,count:ids.size})).sort((a,b)=>b.count-a.count||a.name.localeCompare(b.name));
  }
  function simpleBars(rows,kind){
    if(!rows.length)return '<p class="ia-muted">No records match the filters.</p>';
    const max=Math.max(1,...rows.map(r=>r.count));return `<div class="ia-simple-list">${rows.map(r=>`<button type="button" class="ia-simple-row" data-${kind}="${esc(r.name)}"><span>${esc(r.name)}</span><span class="ia-bar-track"><span class="ia-bar-fill" style="width:${100*r.count/max}%;background:${shade(r.count,max)}"></span></span><strong>${number(r.count)}</strong></button>`).join('')}</div>`;
  }
  function diseaseData(links) {
    const allowed=new Set(links.map(l=>state.disease==='drug'?l.d:l.t));
    return (state.disease==='drug'?data.drug_diseases:data.target_diseases).filter(r=>allowed.has(state.disease==='drug'?r.d:r.t));
  }
  function renderDisease(links){
    const rows=diseaseData(links),key=state.disease==='drug'?'d':'t';
    const groups=groupedBars(rows,r=>r.group,r=>r[key]);
    const terms=state.diseaseGroup?groupedBars(rows.filter(r=>r.group===state.diseaseGroup),r=>r.term,r=>r[key]).slice(0,50):[];
    const selected=state.diseaseTerm?rows.filter(r=>r.group===state.diseaseGroup&&r.term===state.diseaseTerm):[];
    const codes=[...new Set(selected.map(r=>r.code).filter(Boolean))].sort(),statuses=[...new Set(selected.map(r=>r.status).filter(Boolean))].sort();
    const ids=[...new Set(selected.map(r=>r[key]))].sort((a,b)=>{const na=state.disease==='drug'?drugs.get(a)?.name:targetLabel(targets.get(a));const nb=state.disease==='drug'?drugs.get(b)?.name:targetLabel(targets.get(b));return String(na).localeCompare(String(nb));});
    const examples=ids.slice(0,50).map(id=>state.disease==='drug'?esc(drugs.get(id)?.name||id):`<button class="ia-text-button" data-target="${esc(id)}">${esc(targetLabel(targets.get(id)))}</button>`).join(' · ');
    return `<p class="ia-muted">Counts are distinct ${state.disease==='drug'?'drug':'target'} records per group. Records can appear in several groups. Source-reported clinical or approved disease entries only; no target–drug–disease connection is inferred.</p>${simpleBars(groups,'disease-group')}${state.diseaseGroup?`<h4>${esc(state.diseaseGroup)}: source terms</h4><p class="ia-muted">Original disease terms; select a term for its source codes and statuses.</p>${simpleBars(terms,'disease-term')}${selected.length?`<p class="ia-muted"><strong>${esc(state.diseaseTerm)}</strong> · Source codes: ${esc(codes.join(' · ')||'not provided')} · Source statuses: ${esc(statuses.join(' · ')||'not provided')}</p><p class="ia-muted">${number(ids.length)} linked ${state.disease} records; showing up to 50: ${examples}</p>`:''}`:'<p class="ia-muted">Select a group to see its original disease terms.</p>'}`;
  }
  function mechanismGroup(s){const v=s.toLowerCase();if(v.includes('car-t'))return 'Cell therapy (source modality)';if(v.includes('antagonist'))return 'Antagonist';if(v.includes('agonist'))return 'Agonist';if(v.includes('inhibitor'))return 'Inhibitor';if(v.includes('degrader'))return 'Degrader';if(v.includes('activator'))return 'Activator';if(v.includes('blocker'))return 'Blocker';if(v.includes('modulat'))return 'Modulator';if(v.includes('replacement'))return 'Replacement';if(v.includes('binder'))return 'Binder';return 'Other source label';}
  function renderMechanisms(links){const rows=[];for(const l of links){if(!l.ttd)continue;for(const raw of l.mechanisms.length?l.mechanisms:['Unspecified'])rows.push({d:l.d,group:raw==='Unspecified'?raw:mechanismGroup(raw),raw});}const groups=groupedBars(rows,r=>r.group,r=>r.d);return `<p class="ia-muted">TTD trial-selected drug records; one drug may have several labels. “Cell therapy” is a source modality label, not a molecular mechanism.</p>${simpleBars(groups,'mechanism')}`;}
  function renderStatuses(links){const rows=[];for(const l of links){if(!l.ttd)continue;for(const status of l.statuses.length?l.statuses:['Not specified'])rows.push({d:l.d,status});}return `<p class="ia-muted">Equivalent source labels are combined; click a bar to inspect the original wording. All discontinued phases are grouped, and source-reported approvals are combined regardless of jurisdiction. Labels are not necessarily current status; one drug can appear in multiple rows.</p>${simpleBars(groupedBars(rows,r=>r.status,r=>r.d),'status')}`;}
  function renderClasses(rows){const classes=groupedBars(rows,r=>sourceClass(r.target),r=>r.target.id);return `<p class="ia-muted">Classes use the paper classification, TTD labels and reviewed <a href="https://www.uniprot.org/" target="_blank" rel="noopener">UniProt</a> annotations, including non-human entries explicitly identified by TTD. UniProt proteins without a supported narrower class are placed under Other proteins; remaining unmatched entities are unclassified. Select a class to see its targets and source evidence.</p>${simpleBars(classes,'class')}`;}
  function detail(id,links,scroll=true){
    const t=targets.get(id);if(!t)return;state.selected=id;const subset=links.filter(l=>l.t===id),r=summaries(subset)[0];
    const panel=document.getElementById('ia-detail');
    if(!r){panel.innerHTML='<p>No relationships match the current filters.</p>';return;}
    const entries=subset.sort((a,b)=>drugs.get(a.d).name.localeCompare(drugs.get(b.d).name));
    panel.innerHTML=`<h3>${esc(targetLabel(t))}</h3>${state.detailAll?'<p class="ia-muted">Showing all roles for this target, including links whose role is not specified.</p>':''}<p>${number(r.all.size)} developed drug records · ${number(r.trial.size)} trial-linked candidates · ${number(r.approved.size)} reported approved · ${number(r.fda.size)} with reviewed FDA evidence</p><p class="ia-muted">${esc(t.type||'Unclassified')} · ${esc((t.source_classes||[]).join(', '))}${t.uniprot_class?` · UniProt classification: ${esc(t.uniprot_class)} (${esc(t.uniprot_class_basis)}) ${link(t.uniprot_class_url,'UniProt record')}`:''}</p><div class="ia-drug-list">${entries.map(l=>{const d=drugs.get(l.d),role=l.primary?'Primary target (paper source)':l.secondary?'Secondary target (paper source)':'Primary or secondary target designation not specified';const labels=[l.trial?'Trial-linked candidate':'',d.approved?'Approval reported':'Approval not recorded',d.fda?'FDA evidence reviewed':d.fda_candidates?.length?'FDA application match needs review':''].filter(Boolean).join(' · ');const fda=(d.indications||[]).map(i=>`<li>${esc(i.name)}${i.population?` — ${esc(i.population)}`:''}${i.date?` (${esc(i.date)})`:''} ${link(i.url,'FDA label')}</li>`).join('');const candidates=!d.fda?(d.fda_candidates||[]).slice(0,4).map(i=>link(i.url,`${i.application} FDA candidate`)).filter(Boolean).join(' · '):'';return `<details><summary>${esc(d.name)} <span class="ia-muted">${esc(labels)}</span></summary>${d.aliases?.length?`<p class="ia-muted">FDA-reviewed aliases: ${esc(d.aliases.join(' · '))} ${(d.identity_urls||[]).map(u=>link(u,'FDA identity source')).join(' · ')}</p>`:''}<p>${esc(role)}${l.mechanisms.length?` · Source labels: ${esc(l.mechanisms.join(', '))}`:''}${l.statuses_original?.length?` · Original TTD status: ${esc(l.statuses_original.join(', '))}`:''}</p>${l.trial_evidence?.length?`<p class="ia-muted">Trial evidence: ${esc(l.trial_evidence.join(' · '))}</p>`:''}${l.notes.length?`<p class="ia-muted">${l.user_reviewed?'Association accepted after user review. ':''}Source scope note: ${esc(l.notes.join(' · '))}</p>`:''}${fda?`<ul>${fda}</ul>`:''}${candidates?`<p class="ia-muted">FDA application matches are candidates and require identity review: ${candidates}</p>`:''}<p>${[...l.sources.map(u=>link(u,'Target source')),...(l.trial_sources||[]).map(u=>link(u,'Study record')),...(d.fda_urls||[]).slice(0,3).map(u=>link(u,'FDA evidence'))].filter(Boolean).join(' · ')}</p></details>`;}).join('')}</div>`;
    panel.hidden=false;if(scroll)panel.scrollIntoView({behavior:'smooth',block:'start'});
  }
  function render() {
    const links=relevantLinks(),rows=summaries(links);
    document.getElementById('ia-summary').textContent=`${number(unique(links.map(l=>l.d)))} drug records · ${number(rows.length)} target records · ${number(links.length)} relationships in the current view`;
    document.getElementById('ia-comparison').innerHTML=renderComparison(rows);
    document.getElementById('ia-developed').innerHTML=renderDeveloped(rows);
    document.getElementById('ia-approved').innerHTML=renderApproved(rows);
    document.getElementById('ia-scatter').innerHTML=renderScatter(rows);
    document.getElementById('ia-hotspots').innerHTML=renderHotspots(rows);
    document.getElementById('ia-diseases').innerHTML=renderDisease(links);
    document.getElementById('ia-classes').innerHTML=renderClasses(rows);
    document.getElementById('ia-mechanisms').innerHTML=renderMechanisms(links);
    document.getElementById('ia-statuses').innerHTML=renderStatuses(links);
    document.getElementById('ia-class-detail').hidden=true;
    document.getElementById('ia-class-detail').replaceChildren();
    document.getElementById('ia-mechanism-detail').replaceChildren();
    document.getElementById('ia-status-detail').replaceChildren();
    const unknown=summaries(relevantLinks('all')).filter(r=>r.unknown.size).sort((a,b)=>b.unknown.size-a.unknown.size).slice(0,state.limit);
    document.getElementById('ia-unknown').innerHTML=targetBars(unknown,[{key:'unknown',label:'Role not specified'}]);
    const detailLinks=state.detailAll?relevantLinks('all'):links;
    if(state.selected && !detailLinks.some(l=>l.t===state.selected)){state.selected=null;document.getElementById('ia-detail').hidden=true;}
    else if(state.selected)detail(state.selected,detailLinks,false);
  }
  root.addEventListener('change',event=>{const el=event.target;if(!data||!el.dataset.state)return;let value=el.value;if(['limit','minimum'].includes(el.dataset.state))value=Number(value);state[el.dataset.state]=value;
    if(el.dataset.state==='disease'){state.diseaseGroup=null;state.diseaseTerm=null;}
    if(el.dataset.state==='hotspot'&&value==='approved'&&state.hotspotRank==='percentage'){state.hotspotRank='none';root.querySelector('[data-state="hotspotRank"]').value='none';}
    if(el.dataset.state==='hotspotRank'&&value==='percentage'&&state.hotspot==='approved'){state.hotspot='within';root.querySelector('[data-state="hotspot"]').value='within';}render();});
  root.addEventListener('click',event=>{if(!data)return;const el=event.target.closest('[data-target],[data-disease-group],[data-disease-term],[data-class],[data-mechanism],[data-status]');if(!el)return;
    if(el.dataset.target){state.detailAll=Boolean(el.closest('#ia-unknown'));detail(el.dataset.target,relevantLinks(state.detailAll?'all':state.role));return;}
    if(el.dataset.diseaseGroup){state.diseaseGroup=el.dataset.diseaseGroup;state.diseaseTerm=null;render();return;}
    if(el.dataset.diseaseTerm){state.diseaseTerm=el.dataset.diseaseTerm;render();return;}
    if(el.dataset.class){const rows=summaries(relevantLinks()).filter(r=>sourceClass(r.target)===el.dataset.class).sort((a,b)=>b.all.size-a.all.size);const box=document.getElementById('ia-class-detail');box.innerHTML=`<h4>${esc(el.dataset.class)} · ${number(rows.length)} targets</h4>${targetBars(rows.slice(0,50),[{key:'trial',label:'Drugs linked to selected study records'},{key:'approved',label:'All linked drugs with approval reported'}])}`;box.hidden=false;return;}
    if(el.dataset.mechanism){const names=new Set(),matched=relevantLinks().filter(l=>l.ttd&&(l.mechanisms.length?l.mechanisms:['Unspecified']).some(raw=>{if((raw==='Unspecified'?raw:mechanismGroup(raw))===el.dataset.mechanism){names.add(raw);return true;}return false;}));const ranked=summaries(matched).sort((a,b)=>b.trial.size-a.trial.size).slice(0,state.limit);document.getElementById('ia-mechanism-detail').innerHTML=`<p class="ia-muted">Original source labels: ${esc([...names].sort().join(' · '))}</p>${targetBars(ranked,[{key:'trial',label:'Drugs linked to selected study records'}])}`;}
    if(el.dataset.status){const matched=relevantLinks().filter(l=>l.ttd&&(l.statuses.length?l.statuses:['Not specified']).includes(el.dataset.status));const original=[...new Set(matched.flatMap(l=>l.status_variants?.[el.dataset.status]||[]))].sort();const ranked=summaries(matched).sort((a,b)=>b.trial.size-a.trial.size).slice(0,state.limit);document.getElementById('ia-status-detail').innerHTML=`<p class="ia-muted">Original source labels: ${esc(original.join(' · ')||'Not specified')}</p>${targetBars(ranked,[{key:'trial',label:'Drugs linked to selected study records'}])}`;}
  });
  root.addEventListener('keydown',event=>{if((event.key==='Enter'||event.key===' ')&&event.target.matches('g[data-target]')){event.preventDefault();detail(event.target.dataset.target,relevantLinks());}});
  fetch('/data/generated/blog-target-analysis.json',{cache:'no-store'}).then(response=>{if(!response.ok)throw new Error(`HTTP ${response.status}`);return response.json();}).then(payload=>{
    data=payload;drugs=new Map(data.drugs.map(d=>[d.id,d]));targets=new Map(data.targets.map(t=>[t.id,t]));render();
  }).catch(error=>{document.getElementById('ia-summary').textContent='The integrated analysis data could not be loaded. The paper baseline explorer remains available.';console.error(error);});
})();
