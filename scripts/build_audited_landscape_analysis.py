"""Build the blog analysis from the audited v6 database, without modifying it."""
import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from build_blog_target_analysis import disease_group, source_stage_allowed
from build_unified_historical_dataset import BASE, ROOT, digest, readonly

DB = BASE / 'unified-historical-v6' / 'unified-drug-targets.sqlite'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,default=ROOT/'data/generated/audited-landscape-analysis.json')
    args=parser.parse_args()
    expected=json.loads((DB.parent/'checkpoint.json').read_text(encoding='utf8'))['output_sha256']
    if digest(DB)!=expected:raise ValueError('Database differs from audited checkpoint')
    with readonly(DB) as db:
        if db.execute('pragma integrity_check').fetchone()[0]!='ok' or db.execute('pragma foreign_key_check').fetchall():raise ValueError('Database integrity failure')
        drugs={r['drug_id']:{'id':r['drug_id'],'name':r['drug_display_name'] or r['drug_name'],
          'category':r['drug_category'],'approved':bool(r['approval_reported']),
          'status':r['source_reported_development_status'],'fda':bool(r['fda_approval_reviewed'])}
          for r in db.execute('select * from drugs')}
        targets={r['target_id']:{'id':r['target_id'],'name':r['target_name'],'gene':r['gene_symbol'] or '',
          'category':r['target_category'],'uniprot':r['uniprot_id'] or '', 'organism':r['organism'] or ''}
          for r in db.execute('select * from targets')}
        audit_file=BASE/'unified-historical-audit-v6'/'uniprot-gene-name-candidates.csv'
        with audit_file.open(encoding='utf8',newline='') as file:
            for row in csv.DictReader(file):
                if row['target_id'] in targets:targets[row['target_id']]['accession_warning']='Gene/accession disagreement or historical synonym; verify identity before use.'
        if 'TTD:T30727' in targets:
            targets['TTD:T30727']['accession_warning']='Source target name CASP11 conflicts with its human CASP4 accession; identity requires review.'
        links={}
        for r in db.execute('select * from drug_target_landscape'):
            key=(r['drug_id'],r['target_id'])
            forms=json.loads(r['source_target_forms_json'])
            special=[f['name'] for f in forms if re.search(r'\b(?:rna|mrna|mutant|variant|t315i|exon)\b',f.get('name',''),re.I)]
            links[key]={'d':key[0],'t':key[1],
              # Per the agreed scope, an approved drug contributes to the
              # developed view even if this particular link has no phase.
              'clinical':bool(r['default_developed_count_eligible'] or r['approval_reported']),
              'association_clinical':r['association_scope']=='clinical_or_approval',
              'status':r['relationship_reported_development_status'],
              'phase':r['reported_phase'],'primary':bool(r['primary_documented']),
              'forms':special,'urls':[],'recent':[]}
        for r in db.execute('select drug_id,target_id,source_url,source_detail from relationship_evidence'):
            link=links[(r['drug_id'],r['target_id'])]
            url=r['source_url'] or ''
            if url.startswith('https://') and url not in link['urls'] and len(link['urls'])<4:link['urls'].append(url)
            raw=r['source_detail'] or ''
            if raw.startswith('{'):
                try: detail=json.loads(raw)
                except (ValueError,TypeError): continue
                if not isinstance(detail,dict):continue
                date=detail.get('candidate_study_date_proxy') or '';study=detail.get('candidate_study_url') or ''
                if re.fullmatch(r'20\d\d(?:-\d\d(?:-\d\d)?)?',date) and '2015'<=date[:4]<='2024':
                    item={'date':date,'url':study if study.startswith('https://clinicaltrials.gov/study/NCT') else ''}
                    if item not in link['recent']:link['recent'].append(item)
        years=defaultdict(list)
        for r in db.execute("select drug_id,approval_date from approval_events where agency='paper-derived'"):
            match=re.match(r'^(\d{4})(?:-|$)',r['approval_date'] or '')
            if match:years[r['drug_id']].append(int(match.group(1)))
        for did,values in years.items():drugs[did]['paper_year']=min(values)
        diseases=[];seen=set()
        for r in db.execute('select * from drug_diseases'):
            # Keep corrected source row for provenance, not analysis.
            if r['drug_id']=='TTD:D09AWJ' and r['disease']=='Human immunodeficiency virus infection':continue
            status=(r['source_status'] or '').strip()
            if not (r['eligible_for_clinical_analysis'] or status.casefold() in ('investigative','terminated')):continue
            term=(r['disease'] or '').strip()
            if not term:continue
            # Only treat explicit ICD-11 codes as chapter evidence.
            code=r['source_code'] or ''
            group=disease_group(term,code) if code.startswith('ICD-11:') else 'Unclassified'
            k=(r['drug_id'],term,group,bool(r['eligible_for_clinical_analysis']))
            if k in seen:continue
            seen.add(k);diseases.append({'d':k[0],'term':term,'group':group,'clinical':k[3]})
        payload={'meta':{'built_utc':datetime.now(timezone.utc).isoformat(),'database_sha256':expected,
          'ttd_snapshot':'2024 source snapshots; mapping workbook version not stated',
          'recent_start':2015,'recent_end':2024,
          'note':'Source-reported approval is drug-level and may be outside the US; it does not establish that every associated target mediates approval.'},
          'drugs':list(drugs.values()),'targets':list(targets.values()),'links':list(links.values()),'diseases':diseases}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf8')
    print(json.dumps({'drugs':len(drugs),'targets':len(targets),'relationships':len(links),'disease_rows':len(diseases),
      'clinical_or_approved_links':sum(x['clinical'] for x in links.values()),
      'recent_candidate_pairs':sum(bool(x['recent']) for x in links.values()),
      'paper_earliest_approval_2015_2024_drugs':sum(2015<=d.get('paper_year',0)<=2024 for d in drugs.values()),
      'bytes':args.out.stat().st_size,'out':str(args.out)},indent=2))


if __name__=='__main__':main()
