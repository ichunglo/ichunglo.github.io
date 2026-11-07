"""Verify map provenance and distinct-drug counting against its input."""
import hashlib
import json
import math
import unittest
from collections import defaultdict

from build_disease_similarity_layout import INPUT, OUTPUT, MAX_POINTS, MIN_SHARED, MIN_JACCARD


class DiseaseLayoutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=INPUT.read_bytes();cls.data=json.loads(cls.raw);cls.layout=json.loads(OUTPUT.read_text(encoding='utf8'))

    def test_layout_matches_source_and_is_not_mislabeled(self):
        self.assertEqual(self.layout['input_sha256'],hashlib.sha256(self.raw).hexdigest())
        self.assertIn('network',self.layout['method'])
        self.assertLessEqual(len(self.layout['points']),MAX_POINTS)
        self.assertEqual(len({(p['group'],p['term']) for p in self.layout['points']}),len(self.layout['points']))
        self.assertTrue(all(math.isfinite(p['x']) and math.isfinite(p['y']) for p in self.layout['points']))

    def test_disease_counts_are_distinct_drugs_not_trials(self):
        linked={r['d'] for r in self.data['links']};terms=defaultdict(set)
        for r in self.data['diseases']:
            if r['d'] in linked:terms[(r['group'],r['term'])].add(r['d'])
        selected=sorted(terms,key=lambda k:(-len(terms[k]),k[0],k[1]))[:MAX_POINTS]
        self.assertTrue(set((r['group'],r['term']) for r in self.layout['points']).issubset(set(selected)))
        for point in self.layout['points']:
            self.assertEqual(point['broad_drug_count'],len(terms[(point['group'],point['term'])]))
        for edge in self.layout['edges']:
            a=self.layout['points'][edge['a']];b=self.layout['points'][edge['b']]
            x=terms[(a['group'],a['term'])];y=terms[(b['group'],b['term'])]
            self.assertEqual(edge['shared_drugs'],len(x&y))
            self.assertGreaterEqual(len(x&y),MIN_SHARED)
            self.assertGreaterEqual(len(x&y)/len(x|y),MIN_JACCARD)


if __name__=='__main__':unittest.main()
