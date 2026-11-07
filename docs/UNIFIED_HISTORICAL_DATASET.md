# Unified drug–target dataset: build and analysis notes

The cleaned local build is at
`../The Envolving Landscape of Drug Targets/TTD/codex-analysis/unified-historical-v6/`.
The `unified-historical-v5` folder is the preserved input to the latest audit
corrections; v4 is its shared-name review input, v3 is the cleaned build,
and v2 is the preserved pre-cleaning input.
It is an integration of the existing paper-derived catalog, the local TTD
snapshot, clinical-trial candidates, UniProt classifications, and reviewed
FDA evidence. It is not an exhaustive inventory or a fully reviewed cohort.

## Files

- `drug_target_landscape.csv` is the flat table: one row per retained
  canonical drug–target pair, with classes, approval and scope flags.
- `unified-drug-targets.sqlite` contains the same view plus normalized evidence,
  identities, source rows, indications and combination components.
- `relationship_evidence.csv`, `drug_source_ids.csv`, `target_source_ids.csv`,
  and `source_register.csv` explain the provenance and identity crosswalks.
- `mapping_dispositions.csv` records the handling of every TTD mapping row;
  Investigative and Terminated rows are retained with their reported labels,
  while patented/preclinical-only mapping rows
  are excluded from the core relationship set.
- `unresolved_target_classification.csv` and `unresolved_drug_modality.csv`
  list records still missing the corresponding category.
- `checkpoint.json` records counts, limitations, source hashes and integrity
  results; the output folder's README describes the fields and caveats.
- `drug_group_members.csv` and `target_group_members.csv` map source IDs and
  names to cleaned entities. `unresolved-name-groups.csv` and
  `unresolved-target-accessions.csv` list identities left separate.
- `original_trial_evidence.csv` preserves trial links before aggregation.
- `shared_name_groups.csv` and `shared_name_members.csv` document the review
  of 43 groups and their 106 source records. They record the source-reported
  organizations, indications and reasons for retaining separate identities.
- `shared_name_trial_candidates.csv` records DrugMAP-referenced registry
  studies and organization comparisons; these remain candidates, not verified
  product identities. `shared_name_quality_flags.csv` records source conflicts.
- `curation_corrections.csv` records user-requested corrections with the
  source value, the curated interpretation, and its evidence scope.
- `ignored_drug_aliases.csv` preserves excluded source aliases outside the
  active `drug_aliases` matching index.
- `target_audit_corrections.csv` and `target_identifier_corrections.csv`
  record the audit's gene-level groupings and identifier corrections.

The v3 cleanup merges matching named medicines when the source evidence permits
and retains uncertain generic names, such as CAR-T descriptions, separately.
It groups human mutations and RNA under a supported gene identity. The
`source_target_forms_json` field retains the original target forms for each
drug–target pair; an RNA-directed treatment must not be presented as binding
the wild-type protein simply because both appear under the same gene.
For names shared by potentially distinct products, `drug_display_name` includes
the source ID and `drug_identity_note` says that identity is unresolved.

The v4 review retains all 43 shared-name groups as separate source records:
the available evidence did not establish the exact product identity needed for
a safe merge. Different source organizations help distinguish descriptions but
do not prove that the products are different; matching organizations do not prove
they are the same. Some DrugMAP pages list studies with different sponsors for
generic product names. Source-linked studies are therefore recorded separately
from verified product evidence. The lactoferrin group remains unmerged after
excluding the unrelated synonym because exact product identity remains unclear.
The HIV indication for `TTD:D09AWJ` remains in the source data with
`eligible_for_clinical_analysis=0`. A separate H5N1 prevention row is a
class-level interpretation; it does not establish a specific product or its
approval. See `shared_name_members.csv` and `curation_corrections.csv`.

The v6 audit groups CTGF and CCN2 RNA forms with CTGF protein, and groups the
BCR-ABL1 T315I form with BCR-ABL1. It also separates a paper BTK relationship
from TTD BLK relationships mistakenly attached to the same target record,
and corrects the GPNMB UniProt accession. The original target forms and evidence
are retained. A local stable ID can retain an old accession-like string after
its accession is corrected; use the `uniprot_id` field, not the ID string, to
retrieve the current cross-reference.

The audit results and review queues are in the separate
`unified-historical-audit-v6` directory. Its UniProt comparison uses primary
gene symbols; historical symbols or synonyms can create false positives.

## How to count

For an initial historical analysis, group the flat table by target, filter
`default_developed_count_eligible=1`, and count distinct `drug_id`. The flag
includes source-reported clinical-phase or approval associations; it excludes
associations without a reported qualifying phase or approval, and combinations when a mapped component is
counted against the same target. Check unresolved combination identities.

For the approved subset additionally filter `approval_reported=1`; this includes
source-reported approvals outside the United States. `fda_approval_reviewed=1`
is the separate reviewed FDA-evidence subset. Approval is a drug-level claim;
it does not establish that each associated target mediates an approved use.
Candidate trial links and exact-name/UniProt identity matches are not equivalent
to independently reviewed clinical evidence. Drug–disease and target–disease
records do not imply a validated drug–target–disease triple.

The drug and relationship fields report `Investigative` and `Terminated` when
the source uses those labels. The flat table's `reported_phase` is separate:
`Not reported` means the source did not specify a phase, not that the status is
unknown. `Terminated` does not by itself explain why development stopped or
prove a clinical trial failed. Multiple reported statuses are preserved together.

The local classifications include reviewed UniProt annotations and IUPHAR/BPS
target families. ChEMBL modality matches use a full InChIKey where possible;
unique exact-name matches are explicitly marked as identity candidates in
`category_basis`. ChEMBL's broad `Protein` label is not automatically mapped
to a biologic, since the molecule may be a synthetic peptide. Missing or
conflicting identity and insufficient modality evidence remain unresolved.
NCATS GSRS matches use an exact substance name and retain the UNII and source
record in the local evidence overlay. An explicit antibody/fusion-protein type
or linked ChEMBL modality supports the assigned class; a GSRS registration
status is not FDA drug approval. Exact-name matches remain identity candidates.
IUPHAR groups some noncatalytic receptors with catalytic receptors; these are
shown as other proteins rather than assigned catalytic activity.

The remaining-classification overlay uses exact-name candidate matches to the
FDA Purple Book or IUPHAR ligand types, and broad target categories stated in
TTD target names. A name such as “calcium channel unspecific” supports an ion
channel class without identifying a particular channel protein. The flat table
includes `drug_category_basis` and `target_category_basis` for the source and
matching method. `Unknown` drug modality means the same as unclear; it is not
counted as a confirmed small molecule, biologic, or other modality.
TTD synonym fields can contain related compounds within a development series;
an uncorroborated TTD synonym alone is not used to assign a modality.

## Rebuild and validation

From the blog workspace, run:

```powershell
python scripts/build_unified_classification_overlays.py
python scripts/build_unified_gsrs_overlay.py
python scripts/build_unified_remaining_classifications.py
python scripts/build_unified_historical_dataset.py
python scripts/test_unified_historical_dataset.py -v
python scripts/build_unified_cleaned_dataset.py
python scripts/test_unified_cleaned_dataset.py -v
python scripts/curate_shared_drug_names.py
python scripts/test_shared_drug_name_curation.py -v
python scripts/apply_shared_name_corrections.py
python scripts/test_shared_name_corrections.py -v
python scripts/fix_audit_target_duplicates.py
python scripts/test_audited_target_corrections.py -v
python scripts/audit_current_drug_target_database.py
python -m unittest scripts.test_blog_target_analysis -v
```

The external classification overlay uses the local IUPHAR 2026.3.1 download
and ChEMBL clinical molecule snapshot; their source hashes are recorded in the
overlay and database. UniProt annotations can be refreshed separately with
`python scripts/fetch_unified_uniprot_classes.py` before building. The fetch
requires `requests` and the installed UniProt research skill client.
Additional ChEMBL queries and NCATS match indexing are performed with
`scripts/fetch_unified_chembl_expansion.py`, `scripts/index_unified_gsrs_matches.py`,
and `scripts/fetch_unified_gsrs_chembl_ids.py`; the source files and request
batch cache are retained locally. The public GSRS download is approximately
329 MB compressed. Check the source terms before distributing derived data.

The previous `unified-historical-v1` folder was superseded after an open CSV
prevented its rebuild from completing. Its SQLite file and CSV exports may
therefore represent different builds; use the v2 folder for a consistent set.

The build uses local snapshots and preserves source IDs and source hashes. It
does not alter the current blog's generated data or publish a webpage. Confirm
the source redistribution terms before committing or publishing the outputs.

The next analysis should inspect high-ranked drug–target identities, resolve
ambiguous entities and classifications, and build figures that distinguish
source-reported clinical activity, global approvals, and FDA-reviewed records.
Historical source coverage and source snapshot dates must accompany any chart.
