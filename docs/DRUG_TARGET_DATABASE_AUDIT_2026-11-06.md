# Drug–target database audit, 6 November 2026

This audit covers the local `unified-historical-v6` snapshot, whose SHA-256 is
recorded in `unified-historical-audit-v6/audit-summary.json`. It is a
structural and targeted consistency review, not manual verification of every
drug–target relationship. The source snapshot has 27,932 drugs, 3,156 targets
and 40,915 retained drug–target pairs.

## Corrections applied

- Grouped the CTGF and CCN2 RNA entries under the same CCN2 target as the
  CTGF protein, while retaining each original molecular form.
- Grouped BCR-ABL1 T315I with BCR-ABL1, while retaining the mutation.
- Separated an evobrutinib–BTK paper association from three TTD BLK
  associations that had been attached to the same incorrectly labeled record.
  BTK is Q06187; BLK is P51451. Original evidence IDs are retained.
- Corrected the GPNMB accession from Q9NQ94 (A1CF) to Q14956 (GPNMB); the
  old accession-like local ID is retained for stable referencing.

Sources: [UniProt CCN2](https://www.uniprot.org/uniprot/P29279/entry),
[NCI BCR-ABL1 and T315I](https://www.cancer.gov/publications/dictionaries/cancer-drug/def/bcr-abl-kinase-inhibitor-k0706),
[UniProt BTK](https://www.uniprot.org/uniprotkb/Q06187/genomic-coordinates),
[UniProt BLK](https://www.uniprot.org/uniprotkb/P51451/entry), and
[UniProt GPNMB](https://www.uniprot.org/uniref/UniRef100_Q14956).

## Checks and open issues

- SQLite integrity and foreign keys pass. The flat CSV contains exactly one
  row for each of the 40,915 database pairs. Every pair has at least one
  source-evidence row; this does not independently verify its scientific claim.
- 43 shared drug-name groups, containing 106 records, remain separate because
  product identity is uncertain. These are potential duplicates, not proven
  duplicates. See `same-name-drug-groups.csv`.
- 17 target gene/accession comparisons disagree with the primary gene name in
  the local UniProt snapshot. The comparison does not include all UniProt gene
  synonyms, so these are candidates, not 17 confirmed errors. For example,
  the LIPF record's accession corresponds to LIPG and needs source review.
  Four accessions are shared by target records; shared viral polyproteins and
  the SMN1/SMN2 protein entry show why this cannot automatically mean a duplicate.
- 26,412 relationships have no qualifying source-reported trial phase or
  approval for that association. Of these, 24,853 report Investigative and
  1,446 report Terminated. They are relationships, not drug counts. Neither
  label alone confirms clinical trial entry or gives a stopping reason.
- 27 links involving a drug with a source-reported approval are excluded from
  the default developed-target count because the association itself lacks a
  qualifying phase or approval. They include possible repurposing or secondary
  links, and require source review before attributing approval to the target.
- 4,041 drugs have unknown modality, and 430 targets have unclear category.
  Those are missing classifications, not proven data errors.
- 2,846 drugs have a source-reported approval, of which 317 have an FDA-reviewed
  flag. The audit checked that flagged drugs have non-candidate evidence labels;
  it did not independently re-review every label or establish full FDA coverage.
- 4,811 study-reference rows are source-linked candidates, while 3 rows are
  labeled directly reviewed registry studies. Candidate links are not proof of
  first trial entry, exact product identity, or trial outcome.
- 2,963 relationship-evidence rows labeled `paper_catalog` do not have a direct
  URL in that field, although many carry source IDs. Source IDs may refer to
  material other than the target-landscape paper and need individual resolution.

Do not calculate a trial-to-approval success rate from the independently
assembled layers. Time-specific rankings require an explicit date definition
and coverage disclosure. The automated audit can be regenerated with
`python scripts/audit_current_drug_target_database.py`; its CSVs are review
queues, not a list of established mistakes.
