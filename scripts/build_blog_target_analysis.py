"""Build the article's local, source-traceable integrated analysis payload."""
import argparse
import csv
import hashlib
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parent / 'The Envolving Landscape of Drug Targets' / 'TTD' / 'codex-analysis'


def source_stage_allowed(status):
    s = (status or '').strip().casefold()
    if 'preclinical' in s:
        return False
    return bool(re.search(r'\bphase\s*[1-4]', s) or s.startswith('approved') or s == 'clinical trial')


def normalize_development_status(status):
    """Consolidate source spelling without discarding original labels."""
    raw=(status or '').strip();s=raw.casefold()
    if not s:return 'Not specified'
    if 'discontinued' in s:return 'Discontinued'
    if s.startswith('approved'):return 'Approved'
    if re.match(r'^phase\s*1\s*/\s*2',s):return 'Phase 1/2'
    if re.match(r'^phase\s*2\s*/\s*3',s):return 'Phase 2/3'
    if re.match(r'^phase\s*1[abc]?\b',s):return 'Phase 1'
    if re.match(r'^phase\s*2[abc]?\b',s):return 'Phase 2'
    if re.match(r'^phase\s*3[abc]?\b',s):return 'Phase 3'
    if re.match(r'^phase\s*4\b',s):return 'Phase 4'
    return raw


def disease_group(name, code):
    """Conservative, documented ICD-11 chapter grouping; unknowns stay visible."""
    match = re.search(r'(?:ICD-11:\s*)?([0-9A-Z][0-9A-Z][0-9A-Z])', code or '', re.I)
    c = match.group(1).upper() if match else ''
    if c.startswith('2'): return 'Neoplasms'
    if c.startswith('1'): return 'Infectious and parasitic diseases'
    if c.startswith('6'): return 'Mental and behavioural disorders'
    if c.startswith('8'): return 'Nervous system diseases'
    if c.startswith('9'): return 'Eye and visual system diseases'
    if c.startswith('BA') or c.startswith('BB') or c.startswith('BC') or c.startswith('BD') or c.startswith('BE'): return 'Circulatory system diseases'
    if c.startswith(('CA','CB')): return 'Respiratory system diseases'
    if c.startswith(('DA','DB','DC','DD','DE','DF','DG','DH','DJ','DK','DL','DM','DN')): return 'Digestive system diseases'
    if c.startswith(('EA','EB','EC','ED','EE','EF','EG','EH','EJ','EK')): return 'Skin diseases'
    if c.startswith(('FA','FB','FC','FD','FE')): return 'Musculoskeletal diseases'
    if c.startswith(('GA','GB','GC','GD')): return 'Genitourinary diseases'
    if c.startswith(('5A','5B','5C','5D')): return 'Endocrine, nutritional and metabolic diseases'
    if c.startswith(('4A','4B')): return 'Immune system diseases'
    if c.startswith(('3A','3B')): return 'Blood and blood-forming diseases'
    return 'Unclassified'


def open_db(path):
    db=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    return db


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    integrated=BASE/'portfolio-integrated-008/target-drug-integrated.sqlite';intake=BASE/'ttd-intake.sqlite'
    source_checkpoint=BASE/'portfolio-integrated-008/checkpoint.json'
    expected=json.loads(source_checkpoint.read_text(encoding='utf8'))['output_sha256']
    if hashlib.sha256(integrated.read_bytes()).hexdigest()!=expected:raise ValueError('Integrated database changed since checkpoint')
    with open_db(integrated) as db:
        if db.execute('pragma integrity_check').fetchone()[0]!='ok' or db.execute('pragma foreign_key_check').fetchall():raise ValueError('Database integrity failure')
        drugs={r['drug_id']:{'id':r['drug_id'],'name':r['drug_name'],'approved':bool(r['any_source_approval_reported']),
                'fda':bool(r['fda_approval_reviewed'])} for r in db.execute('select * from drugs')}
        targets={r['target_id']:{'id':r['target_id'],'name':r['target_name'],'gene':r['gene_symbol'],
                  'type':r['target_type'],'uniprot':r['uniprot_accession']} for r in db.execute('select * from targets')}
        ttd_drug_map={r['source_id']:r['drug_id'] for r in db.execute("select * from drug_sources where source='TTD'")}
        ttd_target_map={r['source_id']:r['target_id'] for r in db.execute("select * from target_sources where source='TTD'")}
        for r in db.execute('select * from fda_indications'):
            if r['drug_id'] in drugs:
                drugs[r['drug_id']].setdefault('indications',[]).append({'name':r['indication'],'date':r['approval_date'],
                   'population':r['qualifying_population'],'url':r['label_url']})
        for r in db.execute("select drug_id,source_url from fda_evidence where match_status in ('reviewed_fda_product_event','reviewed_primary_indication','curated_fda_approved_indication')"):
            if r['drug_id'] in drugs and r['source_url']:
                drugs[r['drug_id']].setdefault('fda_urls',[]).append(r['source_url'])
        for r in db.execute("select drug_id,match_status,application,source_url from fda_evidence where match_status in ('exact_ingredient_candidate_unreviewed','catalog_identity_and_fda_application_candidate','product_name_candidate_unreviewed')"):
            if r['drug_id'] not in drugs:continue
            for application in (r['application'] or '').split('|'):
                application=application.strip()
                if not application:continue
                url=r['source_url'] or ('https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=overview.process&ApplNo='+application[3:] if re.fullmatch(r'(?:NDA|BLA)\d{6}',application) else '')
                drugs[r['drug_id']].setdefault('fda_candidates',[]).append({'application':application,'url':url,'match':r['match_status']})
        overlay=ROOT/'data/curated/blog-fda-target-approval-evidence.csv'
        with overlay.open(encoding='utf8',newline='') as handle:
            fda_additions=list(csv.DictReader(handle))
        for r in fda_additions:
            drug=drugs.get(r['drug_id'])
            if not drug:raise ValueError('FDA overlay references unknown drug: '+r['drug_id'])
            if not r['label_url'].startswith('https://www.accessdata.fda.gov/') or not r['approval_source_url'].startswith(('https://www.fda.gov/','https://www.accessdata.fda.gov/')):
                raise ValueError('FDA overlay requires direct FDA evidence')
            drug['approved']=True;drug['fda']=True
            drug.setdefault('fda_urls',[]).append(r['approval_source_url'])
            if not any(i['name']==r['indication'] and i['date']==r['approval_date'] for i in drug.get('indications',[])):
                drug.setdefault('indications',[]).append({'name':r['indication'],'date':r['approval_date'],
                   'population':r['population'],'url':r['label_url']})
        # Preserve two explicitly FDA-verified brand/research-code identities.
        # This is an article-layer reconciliation; the source database is unchanged.
        with (ROOT/'data/curated/blog-reviewed-drug-aliases.csv').open(encoding='utf8',newline='') as handle:
            alias_rows=list(csv.DictReader(handle))
        aliases={r['source_drug_id']:r['canonical_drug_id'] for r in alias_rows}
        if len(aliases)!=len(alias_rows) or set(aliases)&set(aliases.values()):raise ValueError('Invalid drug alias mapping')
        for r in alias_rows:
            source=drugs.get(r['source_drug_id']);canonical=drugs.get(r['canonical_drug_id'])
            if not source or not canonical or source['name']!=r['source_name'] or canonical['name']!=r['canonical_name']:
                raise ValueError('Reviewed FDA alias identity differs from the source database')
            if not r['fda_identity_url'].startswith('https://www.accessdata.fda.gov/'):
                raise ValueError('Alias merge requires the reviewed FDA identity source')
            canonical['approved']|=source['approved'];canonical['fda']|=source['fda']
            canonical.setdefault('aliases',[]).append(source['name'])
            canonical.setdefault('identity_urls',[]).append(r['fda_identity_url'])
            for key in ('indications','fda_urls','fda_candidates'):
                if source.get(key):canonical.setdefault(key,[]).extend(source[key])
            del drugs[r['source_drug_id']]
        ttd_drug_map={source:aliases.get(did,did) for source,did in ttd_drug_map.items()}
        pairs={}
        for r in db.execute('select * from relationship_evidence'):
            d,t=aliases.get(r['drug_id'],r['drug_id']),r['target_id']
            if r['source']=='paper_catalog' and not drugs[d]['approved']:continue
            k=(d,t);row=pairs.setdefault(k,{'d':d,'t':t,'trial':False,'primary':False,'secondary':False,
                                           'ttd':False,'mechanisms':[],'statuses':[],'statuses_original':[],'status_variants':{},'sources':[],'notes':[],'user_reviewed':False,
                                           'trial_sources':[],'trial_evidence':[]})
            if r['source']=='paper_catalog':
                role=r['relationship_role_or_mechanism'].casefold()
                row['primary']|=role=='primary';row['secondary']|=role=='secondary'
                row['sources'].append('https://doi.org/10.1038/s41573-026-01530-3')
            elif r['source']=='TTD':
                row['trial']=True;row['ttd']=True
                note=json.loads(r['source_note']);status=note.get('ttd_source_status','')
                row['trial_evidence'].append('TTD-linked study candidate')
                if note.get('candidate_study_url'):row['trial_sources'].append(note['candidate_study_url'])
                if note.get('target_scope_note'):row['notes'].append(note['target_scope_note'])
                row['user_reviewed']|=note.get('user_association_review')=='user_accepts_drug_target_association'
                if status:
                    raw=[s.strip() for s in status.split(' | ') if s.strip()]
                    row['statuses_original'].extend(raw)
                    for s in raw:
                        normalized=normalize_development_status(s)
                        row['statuses'].append(normalized)
                        row['status_variants'].setdefault(normalized,[]).append(s)
                moa=r['relationship_role_or_mechanism']
                if moa and moa.strip() not in ('.','-'):row['mechanisms'].append(moa)
                if r['source_url']:row['sources'].append(r['source_url'])
        # Reuse the earlier period-registry discovery only for an unambiguous
        # exact drug name and an existing target–drug link. These links remain
        # explicitly labeled name-matched study candidates, not trial proof.
        snapshot=json.loads((ROOT/'data/generated/landscape.json').read_text(encoding='utf8'))
        names=defaultdict(set)
        for did,drug in drugs.items():
            for name in [*drug['name'].split('|'),*drug.get('aliases',[])]:
                if name.strip():names[' '.join(name.casefold().split())].add(did)
        registry_added=0
        for target in snapshot['recent_investigational_analysis']['clinical_targets']:
            for candidate in target['activity_drug_records']:
                matches=names.get(' '.join(candidate['name'].casefold().split()),set())
                if len(matches)!=1:continue
                key=(next(iter(matches)),target['target_id']);row=pairs.get(key)
                if row is None or row['trial'] or not candidate.get('period_studies'):continue
                studies=[n for n in candidate.get('period_study_ids',[]) if re.fullmatch(r'NCT\d{8}',n)]
                if not studies:continue
                row['trial']=True;row['trial_evidence'].append('Exact-name registry study candidate')
                row['trial_sources'].extend('https://clinicaltrials.gov/study/'+n for n in studies[:3]);registry_added+=1
        with (ROOT/'data/curated/blog-reviewed-trial-links.csv').open(encoding='utf8',newline='') as handle:
            for r in csv.DictReader(handle):
                key=(r['drug_id'],r['target_id']);row=pairs.get(key)
                if row is None or not re.fullmatch(r'NCT\d{8}',r['nct_id']) or r['trial_url']!='https://clinicaltrials.gov/study/'+r['nct_id']:
                    raise ValueError('Invalid reviewed trial link: '+str(key))
                row['trial']=True;row['trial_evidence'].append('Directly reviewed registry study')
                row['trial_sources'].append(r['trial_url'])
        for row in pairs.values():
            for key in ('mechanisms','statuses','statuses_original','sources','notes','trial_sources','trial_evidence'):row[key]=sorted(set(row[key]))
            for key,values in row['status_variants'].items():row['status_variants'][key]=sorted(set(values))
        for drug in drugs.values():
            if drug.get('fda_urls'):drug['fda_urls']=sorted(set(drug['fda_urls']))
            if drug.get('fda_candidates'):
                seen=set();drug['fda_candidates']=[r for r in drug['fda_candidates'] if not ((r['application'],r['match']) in seen or seen.add((r['application'],r['match'])))]
    disease=[];target_diseases=[]; bioclass=defaultdict(set)
    with open_db(intake) as db:
        for r in db.execute("select ttd_target_id,value_json from target_field where field='BIOCLASS'"):
            if r['ttd_target_id'] not in ttd_target_map:continue
            try:values=json.loads(r['value_json'])
            except (ValueError,TypeError):continue
            for value in values if isinstance(values,list) else []:
                if isinstance(value,str) and value.strip():bioclass[ttd_target_map[r['ttd_target_id']]].add(value.strip())
        for r in db.execute('select * from drug_disease'):
            did=ttd_drug_map.get(r['ttd_drug_id'])
            if not did or not source_stage_allowed(r['source_status']):continue
            disease.append({'d':did,'term':r['disease'],'code':r['icd_source'],'status':r['source_status'],
                            'group':disease_group(r['disease'],r['icd_source'])})
        for r in db.execute('select * from target_disease'):
            tid=ttd_target_map.get(r['ttd_target_id'])
            if not tid or not source_stage_allowed(r['source_status']):continue
            target_diseases.append({'t':tid,'term':r['disease'],'code':r['icd_source'],'status':r['source_status'],
                                    'group':disease_group(r['disease'],r['icd_source'])})
    for tid,values in bioclass.items():targets[tid]['source_classes']=sorted(values)
    classification=ROOT/'data/intake/blog-uniprot-classification.json'
    if not classification.exists():raise ValueError('UniProt classification snapshot missing; run scripts/fetch_blog_uniprot_classes.py')
    annotations=json.loads(classification.read_text(encoding='utf8'))
    for r in annotations['records']:
        if r['target_id'] not in targets:raise ValueError('UniProt annotation references unknown target')
        t=targets[r['target_id']];t['uniprot']=r['uniprot_accession'];t['uniprot_class']=r['class']
        t['uniprot_class_basis']=r['basis'];t['uniprot_class_url']=r['source_url']
    used_drugs={r['d'] for r in pairs.values()};used_targets={r['t'] for r in pairs.values()}
    disease=[r for r in disease if r['d'] in used_drugs];target_diseases=[r for r in target_diseases if r['t'] in used_targets]
    for rows,keys in [(disease,('d','term','code','status')),(target_diseases,('t','term','code','status'))]:
        seen=set();rows[:]=[r for r in rows if not (tuple(r[k] for k in keys) in seen or seen.add(tuple(r[k] for k in keys)))]
    payload={'meta':{'built_utc':datetime.now(timezone.utc).isoformat(),'ttd_selection_window':'2015–2024',
            'paper_approved_date_scope':'all years in paper baseline','input_sha256':expected,
            'additional_registry_candidate_relationships':registry_added,
            'uniprot_classification_date':annotations['retrieved_utc'],
            'note':'TTD/paper reported approval can be outside the US. FDA verified is a subset; missing approval does not mean failure.'},
      'drugs':[drugs[x] for x in sorted(used_drugs)],'targets':[targets[x] for x in sorted(used_targets)],
      'links':sorted(pairs.values(),key=lambda x:(x['t'],x['d'])),
      'drug_diseases':disease,'target_diseases':target_diseases}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf8')
    print(json.dumps({'drugs':len(payload['drugs']),'targets':len(payload['targets']),'links':len(payload['links']),
      'trial_drugs':len({r['d'] for r in payload['links'] if r['trial']}),'drug_disease_rows':len(disease),
      'target_disease_rows':len(target_diseases),'disease_groups':dict(Counter(r['group'] for r in disease)),
      'output':str(args.out),'bytes':args.out.stat().st_size},indent=2))


if __name__=='__main__':main()
