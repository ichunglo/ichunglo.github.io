"""Build a local unified historical drug–target dataset from frozen sources.

Clinical/approval claims, candidate links, identity decisions and excluded
source rows are kept separate. This does not assert exhaustive coverage.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent/'The Envolving Landscape of Drug Targets'/'TTD'/'codex-analysis'
OUT=BASE/'unified-historical-v2'


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):h.update(part)
    return h.hexdigest()


def readonly(path):
    db=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    return db


def norm(value):return ' '.join(str(value or '').casefold().split())


def source_scope(value):
    s=norm(value)
    if s.startswith('approved') or s=='withdrawn from market':return 'clinical_or_approval'
    if re.search(r'\bphase\s*[1-4]',s) or s=='clinical trial':return 'clinical_or_approval'
    if 'preclinical' in s or s=='patented' or s=='ind submitted':return 'excluded_preclinical_or_patent'
    return 'phase_or_approval_not_reported'


def reported_statuses(values):
    """Keep reported lifecycle labels, independently of clinical-phase evidence."""
    labels=set()
    for value in values:
        value=str(value or '').strip()
        if not value:continue
        if norm(value)=='terminated':labels.add('Terminated')
        elif norm(value)=='investigative':labels.add('Investigative')
        else:labels.add(value)
    return '; '.join(sorted(labels,key=str.casefold)) if labels else 'Not reported'


def reported_phases(values):
    phases={m.group(0).strip() for v in values for m in [re.search(r'\bphase\s*[0-4](?:\s*/\s*[0-4])?(?:[ab])?',str(v or ''),re.I)] if m}
    return '; '.join(sorted(phases,key=str.casefold)) if phases else 'Not reported'


def modality(values):
    values=sorted({v.strip() for v in values if v and v.strip()});classes=set()
    combination=any('combination' in s.casefold() for s in values)
    for value in values:
        s=value.casefold()
        if 'combination' in s:continue
        if 'small molecular' in s or 'small molecule' in s or s=='protac':classes.add('Small molecule')
        elif any(x in s for x in ('antibody','nanobody','probody','vaccine','cell therapy','gene therapy','recombinant','fusion protein','oncolytic virus','live biotherapeutic','enzyme replacement','t-cell engager','stem cell')) or s=='protein':classes.add('Biologic')
        elif any(x in s for x in ('rna','nucleotide','oligonucleotide','antisense','peptide','carbohydrate','radiopharmaceutical','radioligand','aptamer','contrast','conjugate')):classes.add('Other')
    if len(classes)>1:return 'Unknown',values,combination,'conflicting_source_types'
    if classes:return next(iter(classes)),values,combination,'source_type'
    return ('Other' if combination else 'Unknown'),values,combination,('combination_type_only' if combination else 'no_mapped_source_type')


def target_class(name,paper_class,source_classes,uniprot_class,uniprot_id):
    n=norm(name);cs=[norm(x) for x in source_classes];joined=' '.join(cs)
    if re.search(r'\b(?:mrna|messenger rna|non-coding rna)\b',n) or n.startswith(('dna replication','rna replication')) or any('rna target' in x for x in cs):return 'Non-protein targets','source name or TTD RNA class'
    if re.search(r'\b(?:family|complex|heterodimer|heterotrimer)\b',n):return 'Protein families or complexes','source target name'
    if uniprot_class=='Kinases' or any(x=='kinase' for x in cs) or (re.search(r'\bkinase\b',n) and not re.search(r'\bkinase inhibitor\b|\binhibitor of\b.*\bkinase\b',n)):return 'Kinases','UniProt, TTD class or explicit target name'
    if paper_class=='GPCRs' or any(x.startswith('gpcr ') for x in cs) or uniprot_class=='GPCRs':return 'GPCRs','paper, TTD or UniProt classification'
    if paper_class=='Ion channels' or any('ion channel' in x for x in cs) or uniprot_class=='Ion channels':return 'Ion channels','paper, TTD or UniProt classification'
    if paper_class=='Nuclear hormone receptors' or 'nuclear hormone receptor' in cs or uniprot_class=='Nuclear hormone receptors':return 'Nuclear hormone receptors','paper, TTD or UniProt classification'
    if paper_class=='Transporters' or 'transporter' in cs or uniprot_class=='Transporters':return 'Transporters','paper, TTD or UniProt classification'
    if paper_class=='Catalytic receptors' or uniprot_class=='Catalytic receptors':return 'Catalytic receptors','paper or UniProt classification'
    enzyme_terms=('peptidase','protease','hydrolase','oxidoreductase','transferase','ligase','isomerase','lyase','synthase','synthesis enzyme','reductase','dehydrogenase','phosphatase','esterase')
    if paper_class=='Enzymes' or uniprot_class=='Enzymes' or any(any(term in c for term in enzyme_terms) for c in cs):return 'Other enzymes','paper, TTD enzyme class or UniProt EC number'
    if paper_class=='Endogenous peptides' or uniprot_class=='Endogenous peptides':return 'Endogenous peptides','paper or UniProt classification'
    if paper_class in ('Other proteins','Receptors') or uniprot_class=='Other proteins' or uniprot_id:return 'Other proteins','paper or mapped UniProt protein'
    return 'Unclear','no supported classification'


def export(db,table,dest):
    cur=db.execute('SELECT * FROM '+table)
    with dest.open('w',encoding='utf8',newline='') as f:
        w=csv.writer(f);w.writerow([x[0] for x in cur.description]);w.writerows(cur)


def main():
    ttd_path=BASE/'ttd-intake.sqlite';old_path=BASE/'portfolio-integrated-008/target-drug-integrated.sqlite'
    blog_path=ROOT/'data/generated/blog-target-analysis.json';catalog_path=ROOT/'data/generated/landscape.json'
    uniprot_path=ROOT/'data/intake/blog-uniprot-classification.json';alias_path=ROOT/'data/curated/blog-reviewed-drug-aliases.csv'
    fda_path=ROOT/'data/curated/blog-fda-target-approval-evidence.csv'
    reviewed_trials_path=ROOT/'data/curated/blog-reviewed-trial-links.csv'
    organism_path=ROOT/'data/curated/organisms.csv'
    uniprot_entries_path=BASE.parent/'codex-source-downloads/uniprot-reviewed-human.tsv'
    fda_snapshot=BASE/'ttd-fda-product-evidence-v31-bulk006-reviewed.sqlite'
    historical_uniprot_path=ROOT/'data/intake/unified-uniprot-classification.json'
    external_classification_path=ROOT/'data/intake/unified-external-classification.json'
    gsrs_classification_path=ROOT/'data/intake/unified-gsrs-classification.json'
    remaining_classification_path=ROOT/'data/intake/unified-remaining-classifications.json'
    input_paths=[ttd_path,old_path,blog_path,catalog_path,uniprot_path,alias_path,fda_path,
                 reviewed_trials_path,organism_path,uniprot_entries_path,fda_snapshot]
    if historical_uniprot_path.exists():input_paths.append(historical_uniprot_path)
    if external_classification_path.exists():input_paths.append(external_classification_path)
    if gsrs_classification_path.exists():input_paths.append(gsrs_classification_path)
    if remaining_classification_path.exists():input_paths.append(remaining_classification_path)
    if any(not p.exists() for p in input_paths):raise FileNotFoundError('A required local source snapshot is missing')
    blog=json.loads(blog_path.read_text(encoding='utf8'));catalog=json.loads(catalog_path.read_text(encoding='utf8'))
    uni=json.loads(uniprot_path.read_text(encoding='utf8'));uni_classes={r['target_id']:r for r in uni['records']}
    historical_uni={}
    if historical_uniprot_path.exists():
        historical_uni={r['target_id']:r for r in json.loads(historical_uniprot_path.read_text(encoding='utf8'))['records']}
        uni_classes.update(historical_uni)
    external={'targets':[],'drugs':[]}
    if external_classification_path.exists():external=json.loads(external_classification_path.read_text(encoding='utf8'))
    external_targets={r['target_id']:r for r in external['targets']}
    external_drugs={r['drug_id']:r for r in external['drugs']}
    gsrs_drugs={}
    if gsrs_classification_path.exists():
        gsrs_drugs={r['drug_id']:r for r in json.loads(gsrs_classification_path.read_text(encoding='utf8'))['drugs']}
    remaining={'targets':[],'drugs':[]}
    if remaining_classification_path.exists():remaining=json.loads(remaining_classification_path.read_text(encoding='utf8'))
    remaining_drugs={r['drug_id']:r for r in remaining['drugs']}
    remaining_targets={r['target_id']:r for r in remaining['targets']}
    with alias_path.open(encoding='utf8',newline='') as f:alias_rows=list(csv.DictReader(f))
    aliases={r['source_drug_id']:r['canonical_drug_id'] for r in alias_rows}
    if len(aliases)!=len(alias_rows) or set(aliases)&set(aliases.values()):raise ValueError('Invalid reviewed alias map')
    with readonly(old_path) as old:
        old_drugs={r['drug_id']:dict(r) for r in old.execute('SELECT * FROM drugs')}
        old_targets={r['target_id']:dict(r) for r in old.execute('SELECT * FROM targets')}
        old_dsource=[dict(r) for r in old.execute('SELECT * FROM drug_sources')]
        old_tsource=[dict(r) for r in old.execute('SELECT * FROM target_sources')]
        old_rel=[dict(r) for r in old.execute('SELECT * FROM relationship_evidence')]
        old_fda=[dict(r) for r in old.execute('SELECT * FROM fda_evidence')]
        old_ind=[dict(r) for r in old.execute('SELECT * FROM fda_indications')]
        old_approval=[dict(r) for r in old.execute('SELECT * FROM approval_events')]
    for source,canonical in aliases.items():
        if source not in old_drugs or canonical not in old_drugs:raise ValueError('Reviewed alias ID missing from source database')
    dm={r['source_id']:aliases.get(r['drug_id'],r['drug_id']) for r in old_dsource if r['source']=='TTD'}
    tm={r['source_id']:r['target_id'] for r in old_tsource if r['source']=='TTD'}
    dfield=defaultdict(lambda:defaultdict(set));tfield=defaultdict(lambda:defaultdict(set));target_drug_names=defaultdict(set)
    with readonly(ttd_path) as src:
        source_files=[dict(r) for r in src.execute('SELECT * FROM source_file')]
        mappings=[dict(r) for r in src.execute('SELECT * FROM drug_target')]
        for r in src.execute("SELECT * FROM drug_field WHERE field IN ('DRUGNAME','DRUGTYPE','HIGHSTAT','SYNONYMS')"):
            for v in json.loads(r['value_json']):
                if isinstance(v,str) and v.strip():dfield[r['ttd_drug_id']][r['field']].add(v.strip())
        for r in src.execute("SELECT * FROM target_field WHERE field IN ('TARGNAME','GENENAME','UNIPROID','BIOCLASS','DRUGINFO')"):
            vals=json.loads(r['value_json'])
            if r['field']=='DRUGINFO':
                if len(vals)>=2 and isinstance(vals[0],str) and isinstance(vals[1],str) and vals[1].strip():target_drug_names[vals[0]].add(vals[1].strip())
            else:
                for v in vals:
                    if isinstance(v,str) and v.strip():tfield[r['ttd_target_id']][r['field']].add(v.strip())
        drug_diseases=[dict(r) for r in src.execute('SELECT * FROM drug_disease')]
        target_diseases=[dict(r) for r in src.execute('SELECT * FROM target_disease')]
    eligible=[r for r in mappings if source_scope(r['source_highest_status'])!='excluded_preclinical_or_patent']
    wanted_drugs={r['ttd_drug_id'] for r in eligible};wanted_targets={r['ttd_target_id'] for r in eligible}
    source_names={did:(dfield[did]['DRUGNAME'] | target_drug_names[did]) for did in wanted_drugs}
    # Extend existing mapping using unique exact source names, with collisions
    # retained as separate records rather than guessing an identity.
    paper_names=defaultdict(set);ttd_names=defaultdict(set)
    for did,r in old_drugs.items():
        if did.startswith('DRG-') and norm(r['drug_name']):paper_names[norm(r['drug_name'])].add(did)
    for did,values in source_names.items():
        for name in values:
            if norm(name):ttd_names[norm(name)].add(did)
    possible=defaultdict(set)
    for name,ids in ttd_names.items():
        if len(ids)==1 and len(paper_names[name])==1:possible[next(iter(ids))].add(next(iter(paper_names[name])))
    singles={did:next(iter(values)) for did,values in possible.items() if len(values)==1}
    reverse=Counter(singles.values());occupied=set(dm.values());new_name_matches={}
    for did,cid in singles.items():
        if did not in dm and reverse[cid]==1 and cid not in occupied:
            dm[did]=cid;new_name_matches[did]=cid;occupied.add(cid)
    for did in wanted_drugs:dm.setdefault(did,'TTD:'+did)
    # Exact human UniProt IDs can reconcile protein names across sources; RNA,
    # complexes and ambiguous entries remain distinct.
    entry_to_accession={}
    with uniprot_entries_path.open(encoding='utf8',newline='') as f:
        for r in csv.DictReader(f,delimiter='\t'):entry_to_accession[r['Entry Name']]=r['Entry']
    catalog_accessions=defaultdict(set)
    for tid,t in old_targets.items():
        if tid.startswith('TGT-') and re.fullmatch(r'[A-Z0-9]{6,10}',t['uniprot_accession'] or ''):
            catalog_accessions[t['uniprot_accession']].add(tid)
    new_target_matches={}
    for tid in wanted_targets:
        if tid in tm:continue
        names=tfield[tid]['TARGNAME'];entries=tfield[tid]['UNIPROID']
        if len(entries)!=1 or any(re.search(r'\b(?:rna|dna|family|complex|heterodimer|mutant|isoform)\b',v,re.I) for v in names):continue
        accession=entry_to_accession.get(next(iter(entries)))
        candidates=catalog_accessions.get(accession,set())
        if accession and len(candidates)==1:tm[tid]=next(iter(candidates));new_target_matches[tid]=tm[tid]
    for tid in wanted_targets:tm.setdefault(tid,'TTD:'+tid)

    out=sqlite3.connect(':memory:');out.execute('PRAGMA foreign_keys=ON')
    out.executescript('''
    CREATE TABLE drugs(drug_id TEXT PRIMARY KEY,drug_name TEXT NOT NULL,drug_category TEXT NOT NULL,source_types_json TEXT NOT NULL,
      category_basis TEXT NOT NULL,is_combination INTEGER NOT NULL,approval_status TEXT NOT NULL,approval_reported INTEGER NOT NULL,
      fda_approval_reviewed INTEGER NOT NULL,withdrawal_reported INTEGER NOT NULL,clinical_stage_reported INTEGER NOT NULL,
      trial_linked_candidate INTEGER NOT NULL,source_statuses_json TEXT NOT NULL,source_reported_development_status TEXT NOT NULL);
    CREATE TABLE targets(target_id TEXT PRIMARY KEY,target_name TEXT NOT NULL,gene_symbol TEXT,uniprot_id TEXT,organism TEXT,
      target_category TEXT NOT NULL,category_basis TEXT NOT NULL,source_classes_json TEXT NOT NULL);
    CREATE TABLE drug_source_ids(source TEXT NOT NULL,source_id TEXT NOT NULL,drug_id TEXT NOT NULL REFERENCES drugs,identity_basis TEXT NOT NULL,PRIMARY KEY(source,source_id));
    CREATE TABLE target_source_ids(source TEXT NOT NULL,source_id TEXT NOT NULL,target_id TEXT NOT NULL REFERENCES targets,identity_basis TEXT NOT NULL,PRIMARY KEY(source,source_id));
    CREATE TABLE drug_aliases(drug_id TEXT NOT NULL REFERENCES drugs,alias TEXT NOT NULL,source TEXT NOT NULL,PRIMARY KEY(drug_id,alias,source));
    CREATE TABLE relationships(drug_id TEXT NOT NULL REFERENCES drugs,target_id TEXT NOT NULL REFERENCES targets,
      association_scope TEXT NOT NULL,primary_documented INTEGER NOT NULL,secondary_documented INTEGER NOT NULL,
      trial_linked_candidate INTEGER NOT NULL,source_reported_development_status TEXT NOT NULL,reported_phase TEXT NOT NULL,
      PRIMARY KEY(drug_id,target_id));
    CREATE TABLE relationship_evidence(evidence_id TEXT PRIMARY KEY,drug_id TEXT NOT NULL,target_id TEXT NOT NULL,
      source TEXT NOT NULL,source_drug_id TEXT,source_target_id TEXT,source_status TEXT,mechanism_or_role TEXT,source_url TEXT,source_detail TEXT,
      FOREIGN KEY(drug_id,target_id) REFERENCES relationships(drug_id,target_id));
    CREATE TABLE mapping_dispositions(excel_row INTEGER PRIMARY KEY,source_drug_id TEXT,source_target_id TEXT,source_status TEXT,disposition TEXT,reason TEXT);
    CREATE TABLE drug_diseases(drug_id TEXT NOT NULL REFERENCES drugs,disease TEXT,source_code TEXT,source_status TEXT,source_row INTEGER,eligible_for_clinical_analysis INTEGER,PRIMARY KEY(drug_id,source_row));
    CREATE TABLE target_diseases(target_id TEXT NOT NULL REFERENCES targets,disease TEXT,source_code TEXT,source_status TEXT,source_row INTEGER,eligible_for_clinical_analysis INTEGER,PRIMARY KEY(target_id,source_row));
    CREATE TABLE trial_evidence(drug_id TEXT NOT NULL REFERENCES drugs,target_id TEXT NOT NULL REFERENCES targets,study_url TEXT,evidence_kind TEXT,
      PRIMARY KEY(drug_id,target_id,study_url,evidence_kind));
    CREATE TABLE fda_evidence(evidence_id INTEGER PRIMARY KEY,drug_id TEXT NOT NULL REFERENCES drugs,source TEXT,match_status TEXT,application TEXT,evidence_date TEXT,source_url TEXT,details TEXT);
    CREATE TABLE approval_events(event_id TEXT PRIMARY KEY,drug_id TEXT NOT NULL REFERENCES drugs,agency TEXT,jurisdiction TEXT,approval_date TEXT,date_precision TEXT,source_id TEXT);
    CREATE TABLE fda_indications(indication_id TEXT PRIMARY KEY,drug_id TEXT NOT NULL REFERENCES drugs,application TEXT,indication TEXT,approval_date TEXT,population TEXT,label_url TEXT,approval_source_url TEXT);
    CREATE TABLE combination_components(combination_drug_id TEXT NOT NULL REFERENCES drugs,component_drug_id TEXT NOT NULL REFERENCES drugs,source_name TEXT NOT NULL,evidence TEXT NOT NULL,PRIMARY KEY(combination_drug_id,component_drug_id));
    CREATE TABLE source_register(source_key TEXT PRIMARY KEY,source_path TEXT,sha256 TEXT,version TEXT,source_url TEXT);
    ''')

    # Prepare canonical drug attributes; preserve all contributing source claims.
    dmeta=defaultdict(lambda:{'names':set(),'types':set(),'statuses':set(),'paper':False,'approved':False,'fda':False,'trial':False,'name_from_target':False})
    for did,r in old_drugs.items():
        canon=aliases.get(did,did);a=dmeta[canon];a['names'].add(r['drug_name']);a['paper']|=did.startswith('DRG-')
        a['approved']|=bool(r['any_source_approval_reported']);a['fda']|=bool(r['fda_approval_reviewed'])
    for source,did in dm.items():
        if source not in wanted_drugs and did not in dmeta:continue
        a=dmeta[did];a['names'].update(source_names.get(source,set()));a['name_from_target']|=not bool(dfield[source]['DRUGNAME']) and bool(target_drug_names[source])
        a['types'].update(dfield[source]['DRUGTYPE']);a['statuses'].update(dfield[source]['HIGHSTAT'])
    for r in eligible:dmeta[dm[r['ttd_drug_id']]]['statuses'].add(r['source_highest_status'])
    for d in blog['drugs']:
        canon=aliases.get(d['id'],d['id'])
        if canon in dmeta:dmeta[canon]['approved']|=d['approved'];dmeta[canon]['fda']|=d['fda']
    for r in blog['links']:
        canon=aliases.get(r['d'],r['d'])
        if r['trial'] and canon in dmeta:dmeta[canon]['trial']=True
    fda_verified=[]; fda_supplemental=[]
    with readonly(fda_snapshot) as source:
        for r in source.execute('SELECT * FROM fda_product_observation'):
            if r['ttd_drug_id'] in dm and r['review_status'].startswith('verified_'):
                did=dm[r['ttd_drug_id']];dmeta[did]['fda']=True;dmeta[did]['approved']=True;fda_verified.append(dict(r))
        for table in ('fda_cross_center_application_observation','fda_historical_source_observation'):
            for row in source.execute('SELECT * FROM '+table):
                r=dict(row)
                if r['ttd_drug_id'] in dm and r['review_status'].startswith('verified_'):
                    did=dm[r['ttd_drug_id']];dmeta[did]['fda']=True;dmeta[did]['approved']=True
                    fda_supplemental.append((did,table,r))
    catalog_types={r['drug_id']:r['modality'] for r in catalog['drugs']}
    for did,a in sorted(dmeta.items()):
        base=old_drugs.get(did);name=base['drug_name'] if base else (sorted(a['names'],key=lambda v:(len(v),v.casefold()))[0] if a['names'] else did)
        source_types=set(a['types']);known=catalog_types.get(did,'unknown')
        if known=='small_molecule':source_types.add('Small molecule')
        elif known=='biologic':source_types.add('Protein')
        category,types,combo,basis=modality(source_types)
        if category=='Unknown' and (did in external_drugs or did in gsrs_drugs or did in remaining_drugs):
            annotation=external_drugs.get(did) or gsrs_drugs.get(did) or remaining_drugs[did]
            if norm(name)!=norm(annotation['drug_name']):raise ValueError('Drug name changed since classification overlay: '+did)
            origin=annotation.get('source','ChEMBL')
            category=annotation['category'];types=sorted(set(types)|{origin+': '+annotation['source_type']})
            basis=origin+' '+annotation['basis']+'; '+annotation['source_url']
        statuses=sorted(a['statuses']);lower=[norm(s) for s in statuses]
        approved=a['approved'] or any(s.startswith('approved') for s in lower)
        withdrawn=any('withdrawn from market' in s for s in lower)
        clinical=any(source_scope(s)=='clinical_or_approval' and not norm(s).startswith('approved') and 'withdrawn' not in norm(s) for s in statuses)
        source_status=reported_statuses(statuses)
        status=('Previously approved; withdrawal reported' if withdrawn else 'Approved' if approved else
                'Clinical-stage; no approval recorded' if clinical else source_status if source_status!='Not reported' else 'Status unclear')
        out.execute('INSERT INTO drugs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
          (did,name,category,json.dumps(types,ensure_ascii=False),basis,int(combo),status,int(approved or withdrawn),int(a['fda']),int(withdrawn),int(clinical),int(a['trial']),json.dumps(statuses,ensure_ascii=False),source_status))
    for r in old_dsource:
        did=aliases.get(r['drug_id'],r['drug_id'])
        if did in dmeta:out.execute('INSERT OR IGNORE INTO drug_source_ids VALUES (?,?,?,?)',(r['source'],r['source_id'],did,'FDA-reviewed alias' if r['drug_id'] in aliases else r['identity_basis']))
    existing_drug_sources={r['source_id'] for r in old_dsource if r['source']=='TTD'}
    for source in sorted(wanted_drugs):
        did=dm[source];basis='existing crosswalk' if source in existing_drug_sources else 'unique exact-name candidate' if source in new_name_matches else 'source ID'
        out.execute('INSERT OR IGNORE INTO drug_source_ids VALUES (?,?,?,?)',('TTD',source,did,basis))
        for name in dfield[source]['SYNONYMS'] | source_names[source]:out.execute('INSERT OR IGNORE INTO drug_aliases VALUES (?,?,?)',(did,name,'TTD'))
    for r in alias_rows:out.execute('INSERT OR IGNORE INTO drug_aliases VALUES (?,?,?)',(r['canonical_drug_id'],r['source_name'],'FDA reviewed identity'))

    # Use paper classes and TTD biological classes; keep target entity granularity.
    target_meta=defaultdict(lambda:{'names':set(),'genes':set(),'entries':set(),'classes':set()})
    for source in wanted_targets:
        a=target_meta[tm[source]];a['names'].update(tfield[source]['TARGNAME']);a['genes'].update(tfield[source]['GENENAME']);a['entries'].update(tfield[source]['UNIPROID']);a['classes'].update(tfield[source]['BIOCLASS'])
    for tid,r in old_targets.items():
        a=target_meta[tid];a['names'].add(r['target_name'])
        if r['gene_symbol']:a['genes'].add(r['gene_symbol'])
    catalog_target_organisms={r['target_id']:r['organism_id'] for r in catalog['targets']}
    with organism_path.open(encoding='utf8',newline='') as f:
        organism_names={r['organism_id']:r['name'] for r in csv.DictReader(f)}
    for tid,a in sorted(target_meta.items()):
        original=old_targets.get(tid);name=original['target_name'] if original else (sorted(a['names'])[0] if a['names'] else tid)
        gene=original['gene_symbol'] if original and original['gene_symbol'] else (next(iter(a['genes'])) if len(a['genes'])==1 else '')
        u=uni_classes.get(tid,{});accession=(original['uniprot_accession'] if original else '') or u.get('uniprot_accession','')
        if not accession and len(a['entries'])==1:accession=entry_to_accession.get(next(iter(a['entries'])),'')
        organism=organism_names.get(catalog_target_organisms.get(tid,''),'') or ('Homo sapiens' if a['entries'] and all(x.endswith('_HUMAN') for x in a['entries']) else 'Source entry: '+next(iter(a['entries'])) if len(a['entries'])==1 else 'Unspecified')
        pc=original['target_type'] if original else '';category,basis=target_class(name,pc,a['classes'],u.get('class',''),accession)
        if tid in historical_uni:
            expected={'Enzymes':'Other enzymes'}.get(u['class'],u['class'])
            if category==expected:basis=u['basis']+'; '+u['source_url']
        if category=='Unclear' and tid in external_targets:
            annotation=external_targets[tid];category=annotation['category']
            basis='IUPHAR/BPS '+annotation['basis']+'; '+annotation['source_url']
        if category=='Unclear' and tid in remaining_targets:
            annotation=remaining_targets[tid]
            if name!=annotation['target_name']:raise ValueError('Target name changed since classification overlay: '+tid)
            category=annotation['category'];basis=annotation['source']+' '+annotation['basis']+'; '+annotation['source_url']
        out.execute('INSERT INTO targets VALUES (?,?,?,?,?,?,?,?)',(tid,name,gene,accession,organism,category,basis,json.dumps(sorted(a['classes']),ensure_ascii=False)))
    for r in old_tsource:
        if r['target_id'] in target_meta:out.execute('INSERT OR IGNORE INTO target_source_ids VALUES (?,?,?,?)',(r['source'],r['source_id'],r['target_id'],r['identity_basis']))
    existing_targets={r['source_id'] for r in old_tsource if r['source']=='TTD'}
    for source in sorted(wanted_targets):
        out.execute('INSERT OR IGNORE INTO target_source_ids VALUES (?,?,?,?)',('TTD',source,tm[source], 'existing crosswalk' if source in existing_targets else 'exact UniProt candidate' if source in new_target_matches else 'source ID'))

    # Aggregate source claims once per canonical pair, retaining each input row.
    rel=defaultdict(lambda:{'scopes':set(),'primary':False,'secondary':False,'trial':False,'evidence':[]})
    for r in old_rel:
        did,tid=aliases.get(r['drug_id'],r['drug_id']),r['target_id'];a=rel[(did,tid)]
        # A legacy source relationship alone does not prove clinical development.
        # The TTD status in the old evidence remains source-reported; candidate
        # registry name matches do not promote an unclear record to clinical.
        try: note=json.loads(r['source_note'] or '{}')
        except (ValueError,TypeError): note={}
        source_status=note.get('ttd_source_status','') if isinstance(note,dict) else ''
        approved=out.execute('SELECT approval_reported FROM drugs WHERE drug_id=?',(did,)).fetchone()[0]
        scope='clinical_or_approval' if approved else source_scope(source_status)
        a['scopes'].add(scope if scope!='excluded_preclinical_or_patent' else 'phase_or_approval_not_reported')
        a['primary']|=r['source']=='paper_catalog' and r['relationship_role_or_mechanism']=='primary';a['secondary']|=r['source']=='paper_catalog' and r['relationship_role_or_mechanism']=='secondary'
        a['evidence'].append(('previous:'+r['evidence_id'],r['source'],r['source_drug_id'],r['source_target_id'],source_status,r['relationship_role_or_mechanism'],r['source_url'],r['source_note']))
    for r in eligible:
        did,tid=dm[r['ttd_drug_id']],tm[r['ttd_target_id']];a=rel[(did,tid)];scope=source_scope(r['source_highest_status']);a['scopes'].add(scope)
        a['evidence'].append(('ttd-row:'+str(r['excel_row']),'TTD',r['ttd_drug_id'],r['ttd_target_id'],r['source_highest_status'],r['source_moa'],'https://ttd.idrblab.cn/full-data-download','TTD mapping workbook row '+str(r['excel_row'])))
    for r in blog['links']:
        key=(aliases.get(r['d'],r['d']),r['t'])
        if key in rel and r['trial']:rel[key]['trial']=True
    for (did,tid),a in rel.items():
        evidence_status=[e[4] for e in a['evidence']]
        out.execute('INSERT INTO relationships VALUES (?,?,?,?,?,?,?,?)',(did,tid,'clinical_or_approval' if 'clinical_or_approval' in a['scopes'] else 'phase_or_approval_not_reported',int(a['primary']),int(a['secondary']),int(a['trial']),reported_statuses(evidence_status),reported_phases(evidence_status)))
        for eid,source,sd,st,status,moa,url,detail in a['evidence']:
            out.execute('INSERT INTO relationship_evidence VALUES (?,?,?,?,?,?,?,?,?,?)',(eid,did,tid,source,sd,st,status,moa,url,detail))
    for r in mappings:
        scope=source_scope(r['source_highest_status'])
        out.execute('INSERT INTO mapping_dispositions VALUES (?,?,?,?,?,?)',(r['excel_row'],r['ttd_drug_id'],r['ttd_target_id'],r['source_highest_status'],scope,'TTD status as reported; Investigative and Terminated do not themselves identify a trial phase.'))
    for r in drug_diseases:
        if r['ttd_drug_id'] in dm and dm[r['ttd_drug_id']] in dmeta:
            out.execute('INSERT OR IGNORE INTO drug_diseases VALUES (?,?,?,?,?,?)',(dm[r['ttd_drug_id']],r['disease'],r['icd_source'],r['source_status'],r['line_number'],int(source_scope(r['source_status'])=='clinical_or_approval')))
    for r in target_diseases:
        if r['ttd_target_id'] in tm and tm[r['ttd_target_id']] in target_meta:
            out.execute('INSERT OR IGNORE INTO target_diseases VALUES (?,?,?,?,?,?)',(tm[r['ttd_target_id']],r['disease'],r['icd_source'],r['source_status'],r['line_number'],int(source_scope(r['source_status'])=='clinical_or_approval')))
    with reviewed_trials_path.open(encoding='utf8',newline='') as f:
        reviewed_trials={(r['drug_id'],r['target_id'],r['trial_url']) for r in csv.DictReader(f)}
    for r in blog['links']:
        did=aliases.get(r['d'],r['d']);tid=r['t']
        if (did,tid) not in rel:continue
        for url in r.get('trial_sources',[]):
            kind='Directly reviewed registry study' if (did,tid,url) in reviewed_trials else 'Source-linked study candidate'
            out.execute('INSERT OR IGNORE INTO trial_evidence VALUES (?,?,?,?)',(did,tid,url,kind))
    for r in old_fda:
        did=aliases.get(r['drug_id'],r['drug_id'])
        if did in dmeta:out.execute('INSERT INTO fda_evidence(drug_id,source,match_status,application,evidence_date,source_url,details) VALUES (?,?,?,?,?,?,?)',(did,r['source'],r['match_status'],r['application'],r['evidence_date'],r['source_url'],r['details']))
    for r in fda_verified:
        out.execute('INSERT INTO fda_evidence(drug_id,source,match_status,application,evidence_date,source_url,details) VALUES (?,?,?,?,?,?,?)',(dm[r['ttd_drug_id']],'FDA reviewed TTD product',r['review_status'],r['fda_application'],r['fda_product_approval_date'],r['source_url'],r['caveat']))
    for did,table,r in fda_supplemental:
        out.execute('INSERT INTO fda_evidence(drug_id,source,match_status,application,evidence_date,source_url,details) VALUES (?,?,?,?,?,?,?)',
          (did,table,r['review_status'],r['fda_application'],r.get('fda_application_approval_date') or r.get('evidence_date'),
           r.get('approval_source_url') or r.get('source_url'),r['notes']))
    for r in old_approval:
        out.execute('INSERT OR IGNORE INTO approval_events VALUES (?,?,?,?,?,?,?)',(r['approval_event_id'],aliases.get(r['drug_id'],r['drug_id']),r['agency'],r['jurisdiction'],r['approval_date'],r['date_precision'],r['source_id']))
    for r in old_ind:
        out.execute('INSERT OR IGNORE INTO fda_indications VALUES (?,?,?,?,?,?,?,?)',(r['fda_indication_id'],aliases.get(r['drug_id'],r['drug_id']),r['application_number'],r['indication'],r['approval_date'],r['qualifying_population'],r['label_url'],r['approval_source_url']))
    with fda_path.open(encoding='utf8',newline='') as f:
        for r in csv.DictReader(f):
            did=aliases.get(r['drug_id'],r['drug_id']);out.execute('INSERT OR IGNORE INTO fda_indications VALUES (?,?,?,?,?,?,?,?)',('article:'+did,did,r['application'],r['indication'],r['approval_date'],r['population'],r['label_url'],r['approval_source_url']))
            out.execute('INSERT INTO fda_evidence(drug_id,source,match_status,application,evidence_date,source_url,details) VALUES (?,?,?,?,?,?,?)',(did,'FDA article review','reviewed FDA approval',r['application'],r['approval_date'],r['approval_source_url'],r['review_note']))

    # Parse only source-labeled combinations and exact unambiguous component names.
    names=defaultdict(set)
    for did,name in out.execute('SELECT drug_id,drug_name FROM drugs'):names[norm(name)].add(did)
    for did,name in out.execute('SELECT drug_id,alias FROM drug_aliases'):names[norm(name)].add(did)
    combos=out.execute('SELECT drug_id,drug_name FROM drugs WHERE is_combination=1').fetchall()
    for did,name in combos:
        parts=[p.strip() for p in re.split(r'\s*;\s*|\s+\+\s+|\s*/\s*',name)]
        if len(parts)<2:continue
        matches=[names[norm(p)] for p in parts]
        if all(len(x)==1 and did not in x for x in matches):
            for part,values in zip(parts,matches):out.execute('INSERT OR IGNORE INTO combination_components VALUES (?,?,?,?)',(did,next(iter(values)),part,'Exact unambiguous ingredient name in source-labeled combination'))
    for r in source_files:out.execute('INSERT INTO source_register VALUES (?,?,?,?,?)',(r['source_key'],r['relative_path'],r['sha256'],r['declared_version'],r['attribution_url']))
    for key,path,version,url in [
        ('paper_catalog',catalog_path,'local paper-derived snapshot','https://doi.org/10.1038/s41573-026-01530-3'),
        ('integrated_seed',old_path,'local integrated snapshot',''),
        ('blog_analysis',blog_path,'local integrated snapshot','https://clinicaltrials.gov/'),
        ('uniprot_classification',uniprot_path,'local annotation snapshot','https://www.uniprot.org/'),
        ('uniprot_human_entries',uniprot_entries_path,'local reviewed human snapshot','https://www.uniprot.org/'),
        ('fda_reviewed_snapshot',fda_snapshot,'local reviewed snapshot','https://www.fda.gov/drugs/drug-approvals-and-databases'),
        ('reviewed_fda_overlay',fda_path,'local curated overlay','https://www.fda.gov/'),
        ('reviewed_trial_overlay',reviewed_trials_path,'local curated overlay','https://clinicaltrials.gov/'),
        ('reviewed_drug_aliases',alias_path,'local curated overlay',''),
        ('organism_names',organism_path,'local catalog','')]:
        out.execute('INSERT INTO source_register VALUES (?,?,?,?,?)',(key,str(path),digest(path),version,url))
    if historical_uniprot_path.exists():
        out.execute('INSERT INTO source_register VALUES (?,?,?,?,?)',('unified_uniprot_classification',str(historical_uniprot_path),digest(historical_uniprot_path),'reviewed UniProt annotation snapshot','https://www.uniprot.org/'))
    if gsrs_classification_path.exists():
        for key,path,version,url in [
            ('gsrs_classification',gsrs_classification_path,'GSRS modality overlay','https://gsrs.ncats.nih.gov/'),
            ('gsrs_name_matches',BASE/'unified-gsrs-matches.json','local exact name match index','https://gsrs.ncats.nih.gov/'),
            ('gsrs_substances',BASE.parent/'codex-source-downloads/ncats-gsrs-public-2026-08-06.gsrs','NCATS public dataset 2026-08-06','https://gsrs.ncats.nih.gov/assets/downloads/dump-public-2026-08-06.gsrs')]:
            out.execute('INSERT INTO source_register VALUES (?,?,?,?,?)',(key,str(path),digest(path),version,url))
        gsrs_chembl_path=BASE/'unified-gsrs-chembl-molecules.json'
        if gsrs_chembl_path.exists():
            out.execute('INSERT INTO source_register VALUES (?,?,?,?,?)',('gsrs_chembl_molecules',str(gsrs_chembl_path),digest(gsrs_chembl_path),'ChEMBL molecules referenced by GSRS','https://www.ebi.ac.uk/chembl/api/data/molecule'))
    if remaining_classification_path.exists():
        for key,path,version,url in [
            ('remaining_classification',remaining_classification_path,'descriptive target and modality overlay',''),
            ('iuphar_ligands',BASE.parent/'codex-source-downloads/iuphar-ligands.csv',remaining['iuphar_version'],'https://www.guidetopharmacology.org/DATA/ligands.csv'),
            ('purplebook',BASE/'portfolio-source-reconciliation-002/fda-purplebook-2026-10.csv','FDA October 2026','https://www.accessdata.fda.gov/drugsatfda_docs/PurpleBook/2026/purplebook-search-October-data-download.csv')]:
            out.execute('INSERT INTO source_register VALUES (?,?,?,?,?)',(key,str(path),digest(path),version,url))
    if external_classification_path.exists():
        out.execute('INSERT INTO source_register VALUES (?,?,?,?,?)',('external_classification',str(external_classification_path),digest(external_classification_path),'IUPHAR and ChEMBL classification overlay','https://www.guidetopharmacology.org/'))
        for key,path,version,url in [
            ('iuphar_targets',BASE.parent/'codex-source-downloads/iuphar-targets_and_families.csv',external['iuphar_version'],'https://www.guidetopharmacology.org/DATA/targets_and_families.csv'),
            ('chembl_clinical_molecules',BASE/'chembl-clinical-molecules.json','clinical molecule snapshot 2026-11-03','https://www.ebi.ac.uk/chembl/api/data/molecule'),
            ('chembl_synonyms',BASE/'ttd-chembl-synonym-snapshot.json','local synonym snapshot','https://www.ebi.ac.uk/chembl/api/data/molecule')]:
            out.execute('INSERT INTO source_register VALUES (?,?,?,?,?)',(key,str(path),digest(path),version,url))
        expanded_path=BASE/'unified-chembl-expanded.json'
        if expanded_path.exists() and 'chembl_expanded' in external.get('input_sha256',{}):
            out.execute('INSERT INTO source_register VALUES (?,?,?,?,?)',('chembl_expanded',str(expanded_path),digest(expanded_path),'expanded ChEMBL exact search snapshot','https://www.ebi.ac.uk/chembl/api/data/molecule'))
    out.executescript('''
      CREATE VIEW drug_target_landscape AS
      SELECT t.target_id,t.target_name,t.gene_symbol,t.uniprot_id,t.organism,
             t.target_category,t.category_basis AS target_category_basis,
             d.drug_id,d.drug_name,d.drug_category,d.category_basis AS drug_category_basis,d.source_types_json,d.is_combination,
             d.approval_status,d.source_reported_development_status AS drug_reported_development_status,d.approval_reported,d.fda_approval_reviewed,
             d.withdrawal_reported,d.clinical_stage_reported,
             r.association_scope,r.source_reported_development_status AS relationship_reported_development_status,r.reported_phase,
             r.primary_documented,r.secondary_documented,r.trial_linked_candidate,
             CASE WHEN r.association_scope='clinical_or_approval' AND NOT EXISTS (
                 SELECT 1 FROM combination_components cc JOIN relationships component
                   ON component.drug_id=cc.component_drug_id AND component.target_id=r.target_id
                 WHERE cc.combination_drug_id=d.drug_id
                   AND component.association_scope='clinical_or_approval'
             ) THEN 1 ELSE 0 END AS default_developed_count_eligible
      FROM relationships r JOIN drugs d USING(drug_id) JOIN targets t USING(target_id);
      CREATE VIEW unresolved_target_classification AS
        SELECT * FROM targets WHERE target_category='Unclear';
      CREATE VIEW unresolved_drug_modality AS
        SELECT * FROM drugs WHERE drug_category='Unknown';
    ''')
    out.commit()
    if out.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or out.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('integrity failure')
    counts={table:out.execute('SELECT count(*) FROM '+table).fetchone()[0] for table in ['drugs','targets','relationships','relationship_evidence','mapping_dispositions','drug_source_ids','target_source_ids','drug_aliases','drug_diseases','target_diseases','trial_evidence','fda_evidence','fda_indications','approval_events','combination_components']}
    counts['drug_categories']=dict(out.execute('SELECT drug_category,count(*) FROM drugs GROUP BY drug_category'))
    counts['target_categories']=dict(out.execute('SELECT target_category,count(*) FROM targets GROUP BY target_category'))
    counts['drug_statuses']=dict(out.execute('SELECT approval_status,count(*) FROM drugs GROUP BY approval_status'))
    counts['mapping_scope']=dict(out.execute('SELECT disposition,count(*) FROM mapping_dispositions GROUP BY disposition'))
    counts['relationship_scope']=dict(out.execute('SELECT association_scope,count(*) FROM relationships GROUP BY association_scope'))
    counts['new_exact_name_identity_candidates']=len(new_name_matches);counts['new_uniprot_target_identity_candidates']=len(new_target_matches)
    counts['combination_drugs']=len(combos);counts['combinations_with_mapped_components']=out.execute('SELECT count(distinct combination_drug_id) FROM combination_components').fetchone()[0]
    counts['ttd_missing_drug_names']=sum(not source_names.get(did) for did in wanted_drugs)
    counts['ttd_names_recovered_from_target_records']=sum(not dfield[did]['DRUGNAME'] and bool(target_drug_names[did]) for did in wanted_drugs)
    OUT.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix='unified-',suffix='.sqlite',dir=OUT,delete=False) as f:temp=Path(f.name)
    try:
        dest=sqlite3.connect(temp);out.backup(dest);dest.close();temp.replace(OUT/'unified-drug-targets.sqlite')
    finally:
        if temp.exists():temp.unlink()
    for table in ['drug_target_landscape','unresolved_target_classification','unresolved_drug_modality','drugs','targets','relationships','relationship_evidence','mapping_dispositions','drug_source_ids','target_source_ids','drug_aliases','drug_diseases','target_diseases','trial_evidence','fda_evidence','fda_indications','approval_events','combination_components','source_register']:
        export(out,table,OUT/(table+'.csv'))
    report={'built_utc':datetime.now(timezone.utc).isoformat(),'counts':counts,'sqlite_integrity':'ok','foreign_key_violations':0,
      'input_sha256':{str(p):digest(p) for p in input_paths},'output_sha256':digest(OUT/'unified-drug-targets.sqlite'),
      'limitations':['TTD source statuses and relationships are source-reported; neither the full historical clinical cohort nor every approval is verified.',
       'Investigative and Terminated are preserved as source-reported statuses; without a reported phase or approval they are not counted as confirmed clinical-phase or approval evidence.',
       'Exact name and UniProt crosswalks may be candidates; source identities and unresolved collisions remain traceable.',
       'FDA candidate matches are not treated as reviewed approvals; no match does not prove absence of approval.',
       'Combination components are mapped only when source-labeled combinations have unique exact constituent names.',
       'Drug and target disease records are separate; no three-way target-drug-disease indication is inferred.',
       'Source redistribution terms have not been established; outputs are local research artifacts.']}
    (OUT/'checkpoint.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
    (OUT/'README.md').write_text('''# Unified historical drug–target dataset

The SQLite file and CSV exports combine the paper-derived catalog, the full
local TTD mapping, existing registry candidates and reviewed FDA evidence.
Each relationship is distinct at the retained canonical drug–target level;
`relationship_evidence` preserves source rows, source status and mechanism.
`drug_target_landscape.csv` is the flat, analysis-ready view. Its
`default_developed_count_eligible` flag excludes relationships without reported qualifying phase or approval evidence
and combinations when a mapped component is also counted for the same target;
unresolved combinations remain identifiable. Source-reported clinical stages are not
independently verified merely by inclusion. For a target, count distinct drug
IDs, and treat an approved drug as developed. To count approvals, additionally
filter `approval_reported=1`; FDA-reviewed approvals are a separate subset.
Approval is a drug-level property and does not establish that a specific target
is the mechanism of an approved indication.
`mapping_dispositions` documents every TTD mapping row, including preclinical
and patented-only rows excluded from the core dataset. Source-reported
Investigative and Terminated labels are retained as development statuses; a
separate field says Not reported when no phase is stated. These labels alone
are not counted as confirmed clinical-phase evidence. A source-reported approval counts as approval, with reviewed
FDA approval in a separate field. Withdrawn products remain historically
approved with a distinct withdrawal label.

Drug and target source IDs, synonyms, FDA evidence and separate drug–disease
and target–disease records are included. Combination records are marked and
their components are linked only where exact unambiguous names are supported;
an unmapped component is not evidence that the combination has no components.
Drug and target identity, modality and target class may remain unknown.
Do not treat a missing FDA record as an unapproved drug or a documented failure.
Counts represent partially reconciled source identities, not proven unique
ingredients. The 2024 TTD snapshot is not a complete current global pipeline.
These source-derived outputs stay local until reuse terms are resolved.

Rebuild from the Scientific_Blog workspace using
`python scripts/build_unified_historical_dataset.py`. The checkpoint records
source hashes, scope, counts and data-integrity results.
''',encoding='utf8')
    print(json.dumps(report,indent=2,ensure_ascii=False))


if __name__=='__main__':main()
