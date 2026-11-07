# Audited drug–target blog analysis

The article's new charts use `unified-historical-v6`, a local integrated
snapshot, not the older integrated dashboard dataset. Build with:

```powershell
python scripts/build_audited_landscape_analysis.py
python scripts/build_disease_similarity_layout.py
python scripts/test_audited_landscape_analysis.py -v
python scripts/test_disease_similarity_layout.py -v
quarto render posts/2026-10-02-drug-target-landscape/index.qmd
```

The generated JSON records the input SQLite SHA-256, and the build rejects a
database that differs from its audit checkpoint. Each chart groups by target
and counts distinct canonical drug IDs. A drug associated with two targets can
appear in both. Unresolved generic names remain separate records. Filters are
applied before counting.

The broad view includes every retained source relationship, including
investigative records without a phase, research compounds and radioligands; it
is not a clinical trial cohort. The phase/approval view uses the database's
`default_developed_count_eligible` flag or a source-reported drug-level
approval. The flag omits a combination when a qualifying mapped component is
counted against the same target. An approved drug can have an investigative
link that is not itself a documented target of an approved indication.

Approval means reported by the paper-derived dataset or TTD and is not limited
to FDA approvals. The descriptive approval share divides distinct approved
drug IDs by all distinct drug IDs in the selected view. It describes this
dataset and is not a clinical development success probability. Missing
approval is not proof of failure or lack of approval.

The 2015–2024 study series uses source-linked `candidate_study_date_proxy`
values in relationship evidence, which need not represent first trial entry
or a verified product match. The approval-year series uses the earliest valid
paper-derived approval year per drug; the year need not be a first worldwide
approval. They are separate source layers with different coverage. Their
counts should not be added or divided. TTD source snapshots are from 2024;
the version of the mapping workbook was not stated.

Disease charts count distinct drugs attached to disease records in the
selected evidence view and to at least one target in that view. They do not
assert a drug–target–disease mechanism. Explicit ICD-11 codes are grouped by
the conservative mapping in `scripts/build_blog_target_analysis.py`; other
codes remain unclassified. Original terms and drug names are available on
drill-down. The corrected H5N1 vaccine/HIV source row remains excluded.

Vector SVG downloads include the measure, color meaning, selected scope and
source summary; article captions provide the full methodological limitations.
The retained earlier dashboard and paper explorer remain separate views.
Check redistribution terms for all source-derived data before publishing.

The target-by-year matrix counts distinct linked drug records for each selected
study-date proxy year; one drug can occur in several years, and no cell counts
trials. The target-by-category matrix counts distinct drug records in each
modality. Both are filterable and drill down to their underlying records.

The disease network starts with the 120 most common source disease term/group
pairs in the broad view and displays only those that share at least three
distinct drug IDs and 3% of their combined drug IDs with another term. Its
NumPy force layout uses a fixed seed; the lines encode actual overlaps and
positions are for readability. Filters recalculate the visible edges and
counts, so some nodes can become isolated. This is not UMAP, a semantic
embedding, a count of clinical studies, or a validated drug–target–disease
association. A shared drug need not have been studied for both diseases in the
same trial. Point size is the number of matching distinct drugs.
