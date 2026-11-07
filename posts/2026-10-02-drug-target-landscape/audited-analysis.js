/* Source-reported landscape: distinct drug records, not a development cohort. */
(() => {
  'use strict';
  const root=document.getElementById('audited-landscape');
  if(!root)return;
  const $=id=>document.getElementById(id);
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const num=n=>Number(n).toLocaleString();
  const safe=url=>{try{const x=new URL(url);return x.protocol==='https:'?x.href:'';}catch{return '';}};
  const href=(url,label)=>safe(url)?`<a href="${esc(safe(url))}" target="_blank" rel="noopener noreferrer">${esc(label)}</a>`:'';
  const state={scope:'clinical',category:'all',modality:'all',limit:50};
  let data,drugs,targets,diseaseLayout;
  const empty=()=>new Set();
  function color(value,max){const t=max?Math.pow(value/max,.65):0;const a=[190,222,231],b=[14,64,100];return `rgb(${a.map((x,i)=>Math.round(x+(b[i]-x)*t)).join(',')})`;}
  function filtered(){return data.links.filter(l=>(state.scope==='broad'||l.clinical)&&
    (state.category==='all'||targets.get(l.t).category===state.category)&&
    (state.modality==='all'||drugs.get(l.d).category===state.modality));}
  function aggregate(links){const result=new Map();for(const l of links){let t=result.get(l.t);if(!t){t={target:targets.get(l.t),all:empty(),approved:empty(),recent:empty(),recentApproved:empty()};result.set(l.t,t);}
    const d=drugs.get(l.d);t.all.add(l.d);if(d.approved)t.approved.add(l.d);if(l.recent.length)t.recent.add(l.d);if(d.paper_year>=2015&&d.paper_year<=2024)t.recentApproved.add(l.d);}
    return [...result.values()];}
  const targetLabel=t=>t.gene||t.name;
  function svgNode(tag,attrs={}){const el=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v] of Object.entries(attrs))el.setAttribute(k,String(v));return el;}
  function addDownload(container,svg,id){const download=document.createElement('button');download.type='button';download.className='audited-download';download.textContent='Download chart (SVG)';
    download.addEventListener('click',()=>{const copy=svg.cloneNode(true);copy.setAttribute('xmlns','http://www.w3.org/2000/svg');const css=document.createElementNS('http://www.w3.org/2000/svg','style');css.textContent='.audited-svg-title{font:700 16px system-ui;fill:#17384c}.audited-label{font:15px system-ui;fill:#243f50}.audited-axis{font:13px system-ui;fill:#526b79}.audited-value{font:650 14px system-ui;fill:#19384a}.audited-footnote{font:11px system-ui;fill:#526b79}.audited-heat-value{font:650 12px system-ui}';copy.prepend(css);const url=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(copy)],{type:'image/svg+xml'}));const a=document.createElement('a');a.href=url;a.download=id+'.svg';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});container.append(download);}
  function bars(id,rows,fields,click){const container=$(id);container.replaceChildren();if(!rows.length){container.textContent='No records match these filters.';return;}
    const width=800, left=200,right=70,rowHeight=fields.length===2?48:34,top=52,bottom=58, plot=width-left-right;
    const max=Math.max(1,...rows.flatMap(r=>fields.map(f=>f.value(r))));const h=top+rows.length*rowHeight+bottom;
    const svg=svgNode('svg',{viewBox:`0 0 ${width} ${h}`,role:'group','aria-label':container.dataset.label||'Interactive bar chart'});
    svg.classList.add('audited-svg');
    const title=svgNode('title');title.textContent=container.dataset.label||'Interactive bar chart';svg.append(title);
    const heading=svgNode('text',{x:12,y:19,class:'audited-svg-title'});heading.textContent=container.dataset.label||'Distinct records';svg.append(heading);
    const legend=svgNode('text',{x:12,y:37,class:'audited-footnote'});legend.textContent=fields.length===2?`Filled: ${fields[0].name} · Outline: ${fields[1].name}`:`Bars: ${fields[0].name} · Darker shade indicates more records`;svg.append(legend);
    for(let i=0;i<=4;i++){const x=left+plot*i/4;svg.append(svgNode('line',{x1:x,y1:top,x2:x,y2:h-bottom,stroke:'#d9e3e8','stroke-width':'1'}));
      const tx=svgNode('text',{x,y:h-38,'text-anchor':'middle',class:'audited-axis'});tx.textContent=num(Math.round(max*i/4));svg.append(tx);}
    const axis=svgNode('text',{x:left+plot/2,y:h-23,'text-anchor':'middle',class:'audited-axis'});axis.textContent='Distinct records';svg.append(axis);
    const foot=svgNode('text',{x:12,y:h-6,class:'audited-footnote'});foot.textContent=`TTD 2024 snapshots, paper baseline and linked sources · ${state.scope==='broad'?'broad source view':'phase or approved view'} · ${state.category} · ${state.modality}`;svg.append(foot);
    rows.forEach((row,index)=>{const y=top+index*rowHeight,g=svgNode('g',{tabindex:'0',role:'button','aria-label':`${row.label}: ${fields.map(f=>`${f.name} ${f.value(row)}`).join(', ')}. Select for details.`});
      g.classList.add('audited-chart-row');const name=svgNode('text',{x:left-9,y:y+rowHeight/2+4,'text-anchor':'end',class:'audited-label'});name.textContent=row.label.length>24?row.label.slice(0,22)+'…':row.label;g.append(name);
      const tooltip=svgNode('title');tooltip.textContent=row.label;g.append(tooltip);
      fields.forEach((field,j)=>{const value=field.value(row), barY=y+4+j*(fields.length===2?19:0),barH=fields.length===2?14:22,w=plot*value/max;
        g.append(svgNode('rect',{x:left,y:barY,width:Math.max(0,w),height:barH,rx:2,fill:field.outline?'#fff':color(value,max),stroke:field.outline?'#26566d':'none','stroke-width':field.outline?1.5:0}));
        const text=svgNode('text',{x:left+w+6,y:barY+barH-1,class:'audited-value'});text.textContent=num(value);g.append(text);});
      const action=()=>click(row);g.addEventListener('click',action);g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();action();}});svg.append(g);});
    container.append(svg);addDownload(container,svg,id);}
  function targetRows(items,key){return items.slice().sort((a,b)=>b[key].size-a[key].size||targetLabel(a.target).localeCompare(targetLabel(b.target))).slice(0,state.limit)
    .map(r=>({...r,label:targetLabel(r.target)}));}
  function targetDetail(tid,match=()=>true,context=''){const t=targets.get(tid),links=filtered().filter(l=>l.t===tid&&match(l)).sort((a,b)=>drugs.get(a.d).name.localeCompare(drugs.get(b.d).name));
    const card=$('audit-target-detail');card.hidden=false;const rows=links.map(l=>{const d=drugs.get(l.d);const evidence=[...l.urls.map(u=>href(u,'Source')), ...l.recent.map(x=>href(x.url,`Study ${x.date}`))].filter(Boolean);
      return `<tr><td>${esc(d.name)}</td><td>${esc(d.category)}</td><td>${d.approved?'Source-reported approval':'No approval recorded'}</td><td>${esc(l.status||'Not reported')}</td><td>${esc(l.forms.join('; ')||'—')}</td><td>${evidence.join(' · ')||'See source register'}</td></tr>`;}).join('');
    card.innerHTML=`<div class="audited-detail-title"><h3>${esc(targetLabel(t))} <small>${esc(t.name)}</small></h3><button type="button" data-close-target>Close</button></div>
      <p>${num(links.length)} linked drug records ${esc(context||'in this view')} · ${esc(t.category)} · ${t.uniprot?href('https://www.uniprot.org/uniprotkb/'+encodeURIComponent(t.uniprot)+'/entry','UniProt '+t.uniprot):'No UniProt accession'}.</p>
      <p class="audited-note">Approval is reported for the drug. A link does not prove this target mediates an approved use. RNA and variants are grouped for counting but their source forms are listed.${t.accession_warning?' '+esc(t.accession_warning):''}</p>
      <div class="audited-table-wrap"><table><thead><tr><th>Drug</th><th>Category</th><th>Drug approval</th><th>Link status</th><th>RNA / variant form</th><th>Evidence</th></tr></thead><tbody>${rows}</tbody></table></div>`;
    card.scrollIntoView({behavior:'smooth',block:'start'});}
  function categoryChart(id,links,kind){const groups=new Map();for(const l of links){const label=kind==='target'?targets.get(l.t).category:drugs.get(l.d).category;let s=groups.get(label);if(!s){s=new Set();groups.set(label,s);}s.add(kind==='target'?l.t:l.d);}
    const rows=[...groups].map(([label,ids])=>({label,ids})).sort((a,b)=>b.ids.size-a.ids.size||a.label.localeCompare(b.label));
    bars(id,rows,[{name:kind==='target'?'Targets':'Drugs',value:r=>r.ids.size}],r=>{if(kind==='target'){$('audit-category').value=r.label;state.category=r.label;}else{$('audit-modality').value=r.label;state.modality=r.label;}render();root.scrollIntoView({behavior:'smooth'});});}
  function diseaseCharts(links){const available=new Set(links.map(l=>l.d)),groups=new Map();
    for(const row of data.diseases){if(!available.has(row.d)||(state.scope==='clinical'&&!row.clinical))continue;let group=groups.get(row.group);if(!group){group={label:row.group,ids:empty(),terms:new Map()};groups.set(row.group,group);}group.ids.add(row.d);
      if(!group.terms.has(row.term))group.terms.set(row.term,new Set());group.terms.get(row.term).add(row.d);}
    const rows=[...groups.values()].sort((a,b)=>b.ids.size-a.ids.size||a.label.localeCompare(b.label));
    bars('audit-disease',rows,[{name:'Distinct drugs',value:r=>r.ids.size}],r=>{const box=$('audit-disease-detail');box.hidden=false;
      const terms=[...r.terms].sort((a,b)=>b[1].size-a[1].size||a[0].localeCompare(b[0]));box.innerHTML=`<div class="audited-detail-title"><h3>${esc(r.label)}</h3><button type="button" data-close-disease>Close</button></div><p>Distinct drug counts within each original source term. A drug can appear in several terms or groups.</p>`+
        terms.map(([name,ids])=>`<details><summary>${esc(name)} · ${num(ids.size)} drugs</summary><p>${[...ids].map(id=>esc(drugs.get(id).name)).sort().join(' · ')}</p></details>`).join('');box.scrollIntoView({behavior:'smooth',block:'start'});});
    diseaseMap(available);}
  function heatmap(id,rows,columns,getCount,onSelect){const container=$(id);container.replaceChildren();if(!rows.length){container.textContent='No records match these filters.';return;}
    const left=185,top=57,width=790,right=12,bottom=30,rowHeight=27,cell=(width-left-right)/columns.length,h=top+rows.length*rowHeight+bottom;
    const max=Math.max(1,...rows.flatMap(r=>columns.map(c=>getCount(r,c))));const svg=svgNode('svg',{viewBox:`0 0 ${width} ${h}`,role:'group','aria-label':container.dataset.label});svg.classList.add('audited-svg');
    const title=svgNode('text',{x:12,y:19,class:'audited-svg-title'});title.textContent=container.dataset.label;svg.append(title);
    const caption=svgNode('text',{x:12,y:37,class:'audited-footnote'});caption.textContent='Distinct drug records · darker means more · click a cell for details';svg.append(caption);
    columns.forEach((col,j)=>{const text=svgNode('text',{x:left+cell*(j+.5),y:top-5,'text-anchor':'middle',class:'audited-axis'});text.textContent=col;svg.append(text);});
    rows.forEach((row,i)=>{const y=top+i*rowHeight;const label=svgNode('text',{x:left-8,y:y+18,'text-anchor':'end',class:'audited-label'});label.textContent=row.label.length>22?row.label.slice(0,20)+'…':row.label;const title=svgNode('title');title.textContent=row.label;label.append(title);svg.append(label);
      columns.forEach((col,j)=>{const n=getCount(row,col),x=left+j*cell,g=svgNode('g',{role:'button',tabindex:'0','aria-label':`${row.label}, ${col}: ${n} distinct drug records`});g.classList.add('audited-chart-row');
        g.append(svgNode('rect',{x:x+1,y:y+1,width:cell-2,height:rowHeight-2,fill:n?color(n,max):'#f1f5f6',rx:2}));const txt=svgNode('text',{x:x+cell/2,y:y+18,'text-anchor':'middle',fill:n/max>.55?'#fff':'#244656',class:'audited-heat-value'});txt.textContent=n||'–';g.append(txt);
        const action=()=>onSelect(row,col);g.addEventListener('click',action);g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();action();}});svg.append(g);});});
    const foot=svgNode('text',{x:12,y:h-7,class:'audited-footnote'});foot.textContent=`TTD 2024 snapshots, paper baseline and linked sources · ${state.scope==='broad'?'broad source view':'phase or approved view'}`;svg.append(foot);container.append(svg);addDownload(container,svg,id);}
  function renderMatrices(links,agg){const all=targetRows(agg,'all'),types=['Small molecule','Biologic','Other','Unknown'];const byTarget=new Map();for(const l of links){if(!byTarget.has(l.t))byTarget.set(l.t,new Map());const m=byTarget.get(l.t),type=drugs.get(l.d).category;if(!m.has(type))m.set(type,new Set());m.get(type).add(l.d);}
    heatmap('audit-modality-heatmap',all,types,(r,c)=>byTarget.get(r.target.id)?.get(c)?.size||0,(r,c)=>targetDetail(r.target.id,l=>drugs.get(l.d).category===c,`classified as ${c}`));
    const years=Array.from({length:10},(_,i)=>String(2015+i)),yearMap=new Map();
    for(const l of links)for(const year of new Set(l.recent.map(x=>x.date.slice(0,4)))){if(!yearMap.has(l.t))yearMap.set(l.t,new Map());const m=yearMap.get(l.t);if(!m.has(year))m.set(year,new Set());m.get(year).add(l.d);}
    const recentRows=targetRows(agg.filter(r=>r.recent.size),'recent');
    heatmap('audit-year-heatmap',recentRows,years,(r,y)=>yearMap.get(r.target.id)?.get(y)?.size||0,(r,y)=>targetDetail(r.target.id,l=>l.recent.some(x=>x.date.startsWith(y)),`with a selected ${y} study-date candidate`));}
  function diseaseMap(available){const box=$('audit-disease-map');box.replaceChildren();if(!diseaseLayout){box.textContent='The disease similarity layout could not be loaded.';return;}
    const counts=new Map();for(const row of data.diseases){if(!available.has(row.d)||(state.scope==='clinical'&&!row.clinical))continue;const key=row.group+'\u0000'+row.term;if(!counts.has(key))counts.set(key,new Set());counts.get(key).add(row.d);}
    const points=diseaseLayout.points.map((p,index)=>({...p,index,ids:counts.get(p.group+'\u0000'+p.term)||new Set()})).filter(p=>p.ids.size);
    if(!points.length){box.textContent='No mapped terms match these filters.';return;}
    const categories=[...new Set(diseaseLayout.points.map(p=>p.group))].sort(),palette=['#246ca0','#cb6428','#2b8675','#865ab2','#c94d6a','#b68416','#6376a8','#5c8d37','#a24f35','#74838a','#b45c9b','#2f8d9d','#87643f','#607657','#605997','#b47c6b','#348d76'];
    const groupColor=g=>palette[categories.indexOf(g)%palette.length],w=820,h=540,pad=45,xs=diseaseLayout.points.map(p=>p.x),ys=diseaseLayout.points.map(p=>p.y),minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys),maxN=Math.max(...points.map(p=>p.ids.size));
    const xp=x=>pad+(x-minX)/(maxX-minX||1)*(w-2*pad),yp=y=>h-pad-(y-minY)/(maxY-minY||1)*(h-2*pad);
    const svg=svgNode('svg',{viewBox:`0 0 ${w} ${h}`,role:'group','aria-label':'Network of disease terms sharing linked drug records'});svg.classList.add('audited-disease-svg');
    let edgeCount=0;
    for(let i=0;i<points.length;i++)for(let j=0;j<i;j++){const a=points[i],b=points[j];
      const [small,large]=a.ids.size<=b.ids.size?[a.ids,b.ids]:[b.ids,a.ids];const shared=[...small].filter(id=>large.has(id));const union=a.ids.size+b.ids.size-shared.length;
      if(shared.length<diseaseLayout.min_shared_drugs||shared.length/union<diseaseLayout.min_jaccard)continue;edgeCount++;
      const g=svgNode('g',{role:'button',tabindex:'0','aria-label':`${a.term} and ${b.term}: ${num(shared.length)} shared drug records`});g.classList.add('audited-network-edge');
      g.append(svgNode('line',{x1:xp(a.x),y1:yp(a.y),x2:xp(b.x),y2:yp(b.y),stroke:'#9caeb7','stroke-width':Math.min(4,1+Math.sqrt(shared.length)/3),'stroke-opacity':'.65'}));
      const title=svgNode('title');title.textContent=`${a.term} + ${b.term}: ${num(shared.length)} shared drug records`;g.append(title);
      const action=()=>{const detail=$('audit-disease-detail');detail.hidden=false;detail.innerHTML=`<div class="audited-detail-title"><h3>${esc(a.term)} &amp; ${esc(b.term)}</h3><button type="button" data-close-disease>Close</button></div><p>${num(shared.length)} drug records appear under both source disease terms. This does not establish that they were studied in the same trial or that either indication is approved.</p><p>${shared.map(id=>esc(drugs.get(id).name)).sort().join(' · ')}</p>`;detail.scrollIntoView({behavior:'smooth',block:'start'});};
      g.addEventListener('click',action);g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();action();}});svg.append(g);}
    points.sort((a,b)=>b.ids.size-a.ids.size).forEach(p=>{const r=4+9*Math.sqrt(p.ids.size/maxN),g=svgNode('g',{role:'button',tabindex:'0','aria-label':`${p.term}, ${p.group}: ${num(p.ids.size)} linked drugs`});g.classList.add('audited-chart-row');
      g.append(svgNode('circle',{cx:xp(p.x),cy:yp(p.y),r,fill:groupColor(p.group),'fill-opacity':'.8',stroke:'#fff','stroke-width':1.2}));const title=svgNode('title');title.textContent=`${p.term} · ${p.group} · ${num(p.ids.size)} drugs`;g.append(title);
      const action=()=>{const detail=$('audit-disease-detail');detail.hidden=false;detail.innerHTML=`<div class="audited-detail-title"><h3>${esc(p.term)}</h3><button type="button" data-close-disease>Close</button></div><p>${esc(p.group)} · ${num(p.ids.size)} distinct linked drug records in this view.</p><p>${[...p.ids].map(id=>esc(drugs.get(id).name)).sort().join(' · ')}</p>`;detail.scrollIntoView({behavior:'smooth',block:'start'});};
      g.addEventListener('click',action);g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();action();}});svg.append(g);});
    const occupied=[];for(const p of points){if(occupied.length>=10)break;const label=p.term.length>27?p.term.slice(0,25)+'…':p.term;
      const tw=label.length*7.1,x=Math.max(6,Math.min(w-tw-6,xp(p.x)+7)),y=Math.max(14,Math.min(h-5,yp(p.y)-7));
      if(occupied.some(b=>x<b.x+b.w+5&&x+tw+5>b.x&&y-13<b.y+17&&y+4>b.y))continue;
      occupied.push({x,y:y-13,w:tw});const text=svgNode('text',{x,y,class:'audited-map-label','pointer-events':'none'});text.textContent=label;svg.append(text);}
    box.append(svg);const status=document.createElement('p');status.className='audited-note';status.textContent=`${num(points.length)} disease terms and ${num(edgeCount)} qualifying shared-drug connections in the selected view.`;box.append(status);const legend=document.createElement('div');legend.className='audited-map-legend';legend.innerHTML=categories.filter(c=>points.some(p=>p.group===c)).map(c=>`<span><i style="background:${groupColor(c)}"></i>${esc(c)}</span>`).join('');box.append(legend);}
  function render(){const links=filtered(),a=aggregate(links),allDrugs=new Set(links.map(l=>l.d));
    $('audit-summary').textContent=`${num(allDrugs.size)} distinct linked drug records · ${num(a.length)} targets · ${num(links.length)} relationships in this view`;
    const leader=a.slice().sort((x,y)=>y.all.size-x.all.size||targetLabel(x.target).localeCompare(targetLabel(y.target)))[0];
    const without=a.filter(x=>x.approved.size===0&&x.all.size>0).sort((x,y)=>y.all.size-x.all.size||targetLabel(x.target).localeCompare(targetLabel(y.target)))[0];
    $('audit-insight').textContent=leader?`${targetLabel(leader.target)} has the most linked drug records in this filtered view (${num(leader.all.size)}; ${num(leader.approved.size)} have a source-reported approval). ${without?`${targetLabel(without.target)} leads the targets with no approval recorded (${num(without.all.size)} linked drugs).`:''} These rankings describe source coverage, not target efficacy or clinical success.`:'No target records match these filters.';
    $('audit-target-detail').hidden=true;$('audit-disease-detail').hidden=true;
    const targetClick=r=>targetDetail(r.target.id);
    bars('audit-top',targetRows(a,'all'),[{name:'Distinct linked drugs',value:r=>r.all.size}],targetClick);
    bars('audit-approved-only',targetRows(a.filter(r=>r.approved.size),'approved'),[{name:'Drugs with reported approval',value:r=>r.approved.size}],targetClick);
    bars('audit-approval',targetRows(a,'all'),[{name:'Linked drugs',value:r=>r.all.size},{name:'Drugs with reported approval',value:r=>r.approved.size,outline:true}],targetClick);
    const hot=a.filter(r=>r.approved.size===0&&r.all.size>0);
    bars('audit-no-approval',targetRows(hot,'all'),[{name:'Linked drugs',value:r=>r.all.size}],targetClick);
    const share=targetRows(a,'all').map(r=>`<tr><td><button type="button" class="audited-text-button" data-target="${esc(r.target.id)}">${esc(targetLabel(r.target))}</button></td><td>${num(r.all.size)}</td><td>${num(r.approved.size)}</td><td>${(100*r.approved.size/r.all.size).toFixed(1)}%</td></tr>`).join('');
    $('audit-share').innerHTML=`<div class="audited-table-wrap"><table><thead><tr><th>Target</th><th>Linked drugs</th><th>With recorded approval</th><th>Descriptive share</th></tr></thead><tbody>${share}</tbody></table></div>`;
    categoryChart('audit-classes',links,'target');categoryChart('audit-modalities',links,'drug');diseaseCharts(links);
    renderMatrices(links,a);
    const recent=targetRows(a.filter(r=>r.recent.size),'recent'),approved=targetRows(a.filter(r=>r.recentApproved.size),'recentApproved');
    bars('audit-recent-trial',recent,[{name:'Study-date candidates',value:r=>r.recent.size}],targetClick);
    bars('audit-recent-approval',approved,[{name:'Paper-year approvals',value:r=>r.recentApproved.size}],targetClick);
    const combined=a.filter(r=>r.recent.size||r.recentApproved.size).sort((x,y)=>Math.max(y.recent.size,y.recentApproved.size)-Math.max(x.recent.size,x.recentApproved.size)||targetLabel(x.target).localeCompare(targetLabel(y.target))).slice(0,20).map(r=>({...r,label:targetLabel(r.target)}));
    bars('audit-recent-combined',combined,[{name:'Study-date candidates',value:r=>r.recent.size},{name:'Paper-year approvals',value:r=>r.recentApproved.size,outline:true}],targetClick);
  }
  root.addEventListener('change',e=>{const el=e.target;if(el.id==='audit-scope')state.scope=el.value;if(el.id==='audit-category')state.category=el.value;if(el.id==='audit-modality')state.modality=el.value;if(el.id==='audit-limit')state.limit=Number(el.value);render();});
  root.addEventListener('click',e=>{const target=e.target.closest('[data-target]');if(target)targetDetail(target.dataset.target);if(e.target.closest('[data-close-target]'))$('audit-target-detail').hidden=true;if(e.target.closest('[data-close-disease]'))$('audit-disease-detail').hidden=true;
    if(e.target.closest('[data-reset-audited]')){state.scope='clinical';state.category='all';state.modality='all';state.limit=50;$('audit-scope').value='clinical';$('audit-category').value='all';$('audit-modality').value='all';$('audit-limit').value='50';render();}});
  Promise.all([fetch('/data/generated/audited-landscape-analysis.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.json();}),fetch('/data/generated/disease-similarity-layout.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.json();}).catch(()=>null)]).then(([payload,layout])=>{data=payload;diseaseLayout=layout;drugs=new Map(data.drugs.map(d=>[d.id,d]));targets=new Map(data.targets.map(t=>[t.id,t]));
    for(const [id,values] of [['audit-category',[...new Set(data.targets.map(t=>t.category))]],['audit-modality',[...new Set(data.drugs.map(d=>d.category))]]])for(const value of values.sort()){const option=document.createElement('option');option.value=value;option.textContent=value;$(id).append(option);}
    render();}).catch(error=>{$('audit-summary').textContent='The audited analysis could not be loaded. Please reload the page.';console.error(error);});
})();
