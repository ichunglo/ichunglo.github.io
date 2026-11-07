"""Check dataset-to-blog counting and the corrected disease association."""
import json
import unittest
from collections import defaultdict

from build_audited_landscape_analysis import DB
from build_unified_historical_dataset import ROOT, digest, readonly


class AuditedLandscapeAnalysisTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'data/generated/audited-landscape-analysis.json').read_text(encoding='utf8'))
        cls.drugs={d['id']:d for d in cls.data['drugs']}
        cls.targets={t['id']:t for t in cls.data['targets']}
        cls.links={(l['d'],l['t']):l for l in cls.data['links']}
        cls.db=readonly(DB)

    @classmethod
    def tearDownClass(cls):cls.db.close()

    def test_payload_matches_database_and_hash(self):
        self.assertEqual(self.data['meta']['database_sha256'],digest(DB))
        rows=self.db.execute('select drug_id,target_id from relationships').fetchall()
        self.assertEqual(len(self.data['links']),len(self.links))
        self.assertTrue(set(self.links)=={tuple(r) for r in rows})
        self.assertEqual(len(self.drugs),self.db.execute('select count(*) from drugs').fetchone()[0])
        self.assertEqual(len(self.targets),self.db.execute('select count(*) from targets').fetchone()[0])

    def test_approval_is_subset_of_the_displayed_denominator(self):
        for row in self.links.values():
            self.assertTrue(row['d'] in self.drugs and row['t'] in self.targets)
            if self.drugs[row['d']]['approved']:self.assertTrue(row['clinical'])

    def test_recent_studies_and_paper_year_are_separate(self):
        for row in self.links.values():
            for study in row['recent']:
                self.assertTrue('2015'<=study['date'][:4]<='2024')
                self.assertTrue(not study['url'] or study['url'].startswith('https://clinicaltrials.gov/study/NCT'))
        for did,drug in self.drugs.items():
            if 'paper_year' in drug:
                rows=self.db.execute("select approval_date from approval_events where drug_id=? and agency='paper-derived' and approval_date glob '[0-9][0-9][0-9][0-9]*'",(did,)).fetchall()
                self.assertEqual(drug['paper_year'],min(int(r[0][:4]) for r in rows))

    def test_hiv_association_is_excluded_and_h5n1_is_retained(self):
        records=[r for r in self.data['diseases'] if r['d']=='TTD:D09AWJ']
        self.assertTrue(any(r['term']=='Prevention of influenza A(H5N1)' for r in records))
        self.assertFalse(any(r['term']=='Human immunodeficiency virus infection' for r in records))

    def test_audit_identifiers_and_warnings_are_visible(self):
        self.assertEqual(self.targets['TGT-p51451-1']['gene'],'BLK')
        self.assertEqual(self.targets['TGT-q9nq94-clinical']['uniprot'],'Q14956')
        self.assertIn('accession_warning',self.targets['TTD:T49064'])
        self.assertIn('accession_warning',self.targets['TTD:T30727'])


if __name__=='__main__':unittest.main()
