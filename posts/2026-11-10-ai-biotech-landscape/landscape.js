(() => {
  const data = window.landscapeCompanies;
  const $ = id => document.getElementById(id);
  const fields = ['search','application','modality','model','region'];
  const stages = ['Target discovery','Molecular design','Preclinical prediction','Clinical development'];
  let selectedStage = '';
  const esc = x => String(x).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  for (const [id, key] of [['modality','modalities'],['model','model'],['region','region']]) {
    const values = [...new Set(data.flatMap(c => Array.isArray(c[key]) ? c[key] : [c[key]]))].sort();
    values.forEach(value => $(id).add(new Option(value, value)));
  }
  window.applicationGroups.forEach(group => {
    const optgroup = document.createElement('optgroup'); optgroup.label = group.name;
    group.items.forEach(item => optgroup.appendChild(new Option(item[0], item[0])));
    $('application').appendChild(optgroup);
  });
  function filtered() {
    const term = $('search').value.trim().toLowerCase();
    return data.filter(c => (!selectedStage || c.stages.includes(selectedStage)) && (!$('modality').value || c.modalities.includes($('modality').value)) && (!$('model').value || c.model === $('model').value) && (!$('region').value || c.region === $('region').value) && (!$('application').value || c.applicationEvidence.some(e => e[0] === $('application').value)) && (!term || JSON.stringify([c, window.assetAudit.filter(a=>a.company===c.name), window.clinicalTrialAudit.filter(t=>t.company_or_affiliate===c.name)]).toLowerCase().includes(term)));
  }
  function renderOverview(rows) {
    const colors = ['#1c6454','#cf753f','#a5c965','#6a8e98'];
    const models = [...new Set(data.map(c=>c.model))].sort();
    const counts = models.map(model=>({label:model,count:rows.filter(c=>c.model===model).length}));
    let cursor = 0;
    const stops = counts.map((item,i)=>{const start=cursor; cursor += rows.length ? item.count/rows.length*100 : 0; return `${colors[i]} ${start}% ${cursor}%`;});
    $('model-donut').style.background = rows.length ? `conic-gradient(${stops.join(',')})` : '#d9e3d6';
    $('model-donut').setAttribute('aria-label', rows.length ? `Business models: ${counts.map(x=>`${x.label}, ${x.count}`).join('; ')}` : 'No matching companies');
    $('donut-total').textContent = rows.length;
    $('model-legend').innerHTML = counts.map((x,i)=>`<button type="button" class="legend-item" data-model-chart="${esc(x.label)}"><span class="legend-key" style="background:${colors[i]}"></span><span>${esc(x.label)}</span><strong>${x.count}</strong></button>`).join('');
    $('model-legend').querySelectorAll('[data-model-chart]').forEach(b=>b.addEventListener('click',()=>{$('model').value=b.dataset.modelChart;render();$('explore').scrollIntoView({behavior:'smooth'});}));
    const modalities = [...new Set(data.flatMap(c=>c.modalities))].filter(x=>x !== 'Not specified').sort();
    const entries = modalities.map(label=>({label,count:rows.filter(c=>c.modalities.includes(label)).length}));
    const max = Math.max(1,...entries.map(x=>x.count));
    $('modality-bubbles').innerHTML = entries.map(x=>{const size=18+42*Math.sqrt(x.count/max);return `<button class="bubble-item" type="button" data-modality-chart="${esc(x.label)}"><span class="bubble" style="--size:${size}px" aria-hidden="true">${x.count}</span><span>${esc(x.label)}</span><span class="sr-only">: ${x.count} companies</span></button>`;}).join('');
    $('modality-bubbles').querySelectorAll('[data-modality-chart]').forEach(b=>b.addEventListener('click',()=>{$('modality').value=b.dataset.modalityChart;render();$('explore').scrollIntoView({behavior:'smooth'});}));
  }
  function render() {
    $('stage-map').innerHTML = stages.map((s,i) => `<button type="button" class="stage ${s === selectedStage ? 'active' : ''}" data-stage="${esc(s)}" aria-pressed="${s === selectedStage}"><span>0${i+1}</span><strong>${esc(s)}</strong><small>${data.filter(c => c.stages.includes(s)).length} companies in this set ↗</small></button>`).join('');
    document.querySelectorAll('[data-stage]').forEach(b => b.addEventListener('click', () => {selectedStage = selectedStage === b.dataset.stage ? '' : b.dataset.stage; render();}));
    const rows = filtered();
    renderOverview(rows);
    $('matrix-body').innerHTML = rows.map(c => `<tr><th scope="row"><button type="button" class="matrix-link" data-matrix-company="${esc(c.name)}">${esc(c.name)} ↗</button></th>${stages.map(s=>`<td><span aria-label="${c.stages.includes(s) ? 'Capability mapped' : 'Not mapped'}">${c.stages.includes(s) ? '●' : '—'}</span></td>`).join('')}</tr>`).join('');
    document.querySelectorAll('[data-matrix-company]').forEach(b => b.addEventListener('click', () => openDetail(b.dataset.matrixCompany)));
    $('result-count').textContent = `${rows.length} of ${data.length} companies`;
    $('company-list').innerHTML = rows.length ? rows.map(c => `<button type="button" class="company" data-company="${esc(c.name)}"><span class="company-top"><span class="company-name">${esc(c.name)}</span><span class="arrow">↗</span></span><span class="company-desc">${esc(c.summary)}</span><span class="tags">${[c.region,c.model,...c.modalities].map(t=>`<span>${esc(t)}</span>`).join('')}</span></button>`).join('') : '<p class="empty">No matching companies. Try a broader search or clear the filters.</p>';
    document.querySelectorAll('[data-company]').forEach(b => b.addEventListener('click', () => openDetail(b.dataset.company)));
  }
  function openDetail(name) {
    const c = data.find(x => x.name === name);
    const assets = window.assetAudit.filter(asset => asset.company === c.name);
    const assetHtml = assets.length ? `<details><summary>View ${assets.length} selected asset ${assets.length === 1 ? "record" : "records"}</summary><ul class="trial-list">${assets.map(a=>`<li><a href="${esc(a.source)}" target="_blank" rel="noopener noreferrer">${esc(a.asset)} ↗</a> · ${esc(a.indication)}<br>${esc(a.stage)}<br>Rights: ${esc(a.rights)} <a href="${esc(a.rights_source || a.source)}" target="_blank" rel="noopener noreferrer">Rights source ↗</a><br>Evidence dated or checked: ${esc(a.source_date)}</li>`).join("")}</ul></details>` : "";
    const studies = window.clinicalTrialAudit.filter(study => study.company_or_affiliate === c.name);
    const companyStatus = c.corporate[1] ? `<a href="${esc(c.corporate[1])}" target="_blank" rel="noopener noreferrer">${esc(c.corporate[0])} ↗</a>` : esc(c.corporate[0]);
    const trialHtml = studies.length ? `<p class="eyebrow">STUDIES · REGISTRY SNAPSHOT</p><p class="study-note">Includes historical and selected partner-sponsored studies; registry status and sponsor do not establish current asset ownership or a complete pipeline. Last-posted dates refer to each registry record.</p><details><summary>View ${studies.length} registry ${studies.length === 1 ? 'record' : 'records'}</summary><ul class="trial-list">${studies.map(s=>`<li><a href="${esc(s.source)}" target="_blank" rel="noopener noreferrer">${esc(s.study_id)} · ${esc(s.asset)} ↗</a><br>${esc(s.brief_title)}<br>${esc(s.registry_phase || 'Phase not specified')} · ${esc(s.registry_status.replaceAll('_',' '))}<br>Sponsor: ${esc(s.lead_sponsor || 'Not disclosed')} · Updated: ${esc(s.registry_last_posted || 'Not available')}</li>`).join('')}</ul></details>` : '<p class="study-note">No individual study is included for this company in the selected registry audit. This is not proof that no study exists.</p>';
    $('detail-body').innerHTML = `<p class="eyebrow">COMPANY PROFILE / ${esc(c.region)}</p><h2 id="detail-title">${esc(c.name)}</h2><p class="detail-location">${esc(c.location)} · ${esc(c.model)}</p><p class="detail-summary">${esc(c.summary)}</p><dl><dt>Company listing and control</dt><dd>${companyStatus}</dd><dt>Investor and control evidence</dt><dd>${esc(c.ownershipDisclosure.note)} <a href="${esc(c.ownershipDisclosure.url)}" target="_blank" rel="noopener noreferrer">Source ↗</a> <span class="study-note">${esc(c.ownershipDisclosure.date ? `Disclosure date: ${c.ownershipDisclosure.date}. ` : "") }Historical disclosures may change; check the source for date and scope.</span></dd><dt>Development functions</dt><dd>${esc(c.stages.join(' · '))}</dd><dt>Modalities</dt><dd>${esc(c.modalities.join(' · '))}</dd><dt>Applications supported by cited sources</dt><dd>${c.applicationEvidence.length ? c.applicationEvidence.map(e=>`<a href="${esc(e[1])}" target="_blank" rel="noopener noreferrer">${esc(e[0])} ↗</a>`).join(' · ') : 'Not yet classified in this framework.'}</dd><dt>Lead asset or status</dt><dd>${esc(c.asset)}</dd><dt>Selected disclosed portfolio</dt><dd>${esc(c.dossier.portfolio)} <a href="${esc(c.dossier.url)}" target="_blank" rel="noopener noreferrer">Portfolio source ↗</a></dd><dt>Program rights and collaborations</dt><dd>${esc(c.dossier.rights)} <a href="${esc(c.dossier.rightsUrl)}" target="_blank" rel="noopener noreferrer">Disclosure ↗</a></dd><dt>Evidence context</dt><dd>${esc(c.caveat)}</dd></dl>${assetHtml}${trialHtml}<p class="eyebrow">ADDITIONAL SOURCE LINKS · ACCESSED NOVEMBER 2026</p><ul>${c.sources.map(s=>`<li><a href="${esc(s[1])}" target="_blank" rel="noopener noreferrer">${esc(s[0])} ↗</a></li>`).join('')}</ul>`;
    $('detail').showModal();
  }
  fields.forEach(id => $(id).addEventListener(id === 'search' ? 'input' : 'change', render));
  $('reset-stage').addEventListener('click', () => {selectedStage = ''; render();});
  $('clear').addEventListener('click', () => {selectedStage = ''; fields.forEach(id => $(id).value = ''); render();});
  $('close-detail').addEventListener('click', () => $('detail').close());
  $('detail').addEventListener('click', e => {if(e.target === $('detail')) $('detail').close();});
  $('download').addEventListener('click', () => {
    const columns = ['name','region','location','model','corporate','stages','modalities','methods','summary','asset','caveat','dossier','applicationEvidence','sources'];
    const cell = value => '"' + String(value).replace(/"/g, '""') + '"';
    const csv = [columns.join(','), ...filtered().map(c => columns.map(k => cell(k === 'dossier' ? JSON.stringify(c[k]) : k === 'sources' || k === 'applicationEvidence' ? c[k].map(s=>s.join(': ')).join(' | ') : Array.isArray(c[k]) ? c[k].filter(Boolean).join(' | ') : c[k])).join(','))].join('\r\n');
    const url = URL.createObjectURL(new Blob(['\ufeff',csv],{type:'text/csv;charset=utf-8'}));
    const a = document.createElement('a'); a.href = url; a.download = 'ai-biotech-landscape.csv'; a.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  $('application-catalog').innerHTML = window.applicationGroups.map(group => `<div class="application-group"><h3>${esc(group.name)}</h3><div class="application-grid">${group.items.map(item => {const count = data.filter(c => c.applicationEvidence.some(e => e[0] === item[0])).length; return `<article class="application-card"><h4>${esc(item[0])}</h4><p>${esc(item[1])}</p><p class="application-limit"><strong>Challenge:</strong> ${esc(item[2])}</p><button type="button" class="application-select" data-application="${esc(item[0])}">${count} mapped ${count === 1 ? 'company' : 'companies'} ↗</button></article>`;}).join('')}</div></div>`).join('');
  document.querySelectorAll('[data-application]').forEach(button => button.addEventListener('click', () => {fields.forEach(id => $(id).value = ''); selectedStage = ''; $('application').value = button.dataset.application; render(); $('explore').scrollIntoView({behavior:'smooth'});}));
  render();
})();
