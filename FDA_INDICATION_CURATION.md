# FDA primary-indication curation

## Release scope

The first FDA layer records **one primary indication per catalog drug**: the earliest FDA-approved use that can be established from an FDA approval record and its original label. This is a coverage layer, not a complete indication history. Later indication expansions and supplements are out of scope for the first pass. An application's original approval date alone does not establish the wording or patient group; the original FDA label and approval record must support the selected use.

The catalog includes drugs without a confirmed U.S. FDA approval and products whose FDA records are outside Drugs@FDA. A missing name match never means “not approved.” Use `unresolved_after_review` when identity, FDA jurisdiction, earliest application, label, or date cannot be settled. Keep candidates distinct from reviewed facts.

## FDA-only workflow

1. Build `data/generated/fda-application-review-queue.csv` from the [Drugs@FDA downloadable tables](https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files). The companion `fda-primary-indication-review-queue.csv` prioritizes exact-ingredient matches with original FDA labels first. The queues identify candidate first-approved applications, dates, and labels/letters when available. Record the data snapshot and ZIP checksum. Every queue field remains a candidate pending identity and source review.
2. Confirm that the catalog drug and the FDA product refer to the same active moiety. Check salt forms, biologic suffixes, combination products, brand/generic aliases, and relevant FDA centers. FDA says Drugs@FDA includes most products approved since 1939, while most labels and approval records are available for products approved since 1998; older products may require other FDA records or remain unresolved. [FDA coverage note](https://www.fda.gov/drugs/drug-approvals-and-databases/about-drugsfda)
3. Among the confirmed product's FDA applications, identify the earliest original approval. Read that FDA approval letter and original label. Capture the indication wording, the population or mutation, approval date, and direct FDA URLs. If more than one application shares the earliest date, reconcile them before choosing the primary record.
4. Add the selected row to `data/curated/fda-approved-indications.csv`. Add a source-backed `verified_primary_indication` decision to `data/curated/fda-review-decisions.csv` only when the identity, earliest application, date, indication, patient group, and links are supported. An existing indication row for a drug does not by itself verify that it is the earliest use.
5. For ambiguous or unsupported cases, record `unresolved_after_review` with the sources and reason. The generated ledger leaves untouched drugs as `pending`; it must not infer approval or nonapproval from a candidate match or a missing match.

## Publication condition

Describe coverage as “verified primary indications” and report the count separately from indication rows and pending/unresolved drugs. Do not describe the first-pass layer as all FDA-approved indications. Before reporting that the 1,766-drug audit is complete, every catalog drug must have an evidence-backed disposition: a verified primary indication or an explicit unresolved/out-of-scope status with its basis. Rebuild the ledger and site and review the reader-facing scope language before publishing.

## Bulk original-label review rule

Exact active-ingredient matches with one FDA application and an original label plus approval letter can be processed in batches. Each promoted record must still be supported by the original documents for product identity, approved use, date, and patient qualifiers. If one original action approves multiple uses simultaneously, this dataset records the first-listed use in the original label/approval letter as its one primary-use index. That is a consistent selection rule, not a claim that FDA ranked that use as the drug's main use. Later supplemental indication expansions are outside this layer.

### 2026-10-13 bulk review checkpoint

Downloaded and extracted original FDA labels and approval letters for 241 exact-ingredient, single-application candidates with both documents linked. Of these, 178 had extractable indication and approval-letter text; 25 need manual label-section review, 36 need manual approval-letter review, and 2 had fetch/extraction errors. Initial source-text review curated 48 candidates. Three subsequent bulk cross-check passes reviewed 57 more: the first added 16 indication rows and documented two existing rows (resmetirom and suzetrigine); the second added 17 rows and documented three existing rows (elafibranor, fezolinetant, and vadadustat); the third verified 19 further exact-ingredient candidates. The fourth and fifth review checkpoints each add 19 decisions based on matching original FDA labels and approval letters, including biologics. One candidate (lixisenatide) remains pending because the candidate export's BLA identifier conflicts with the NDA terminology in its FDA approval letter and requires application-type reconciliation. For five previously curated drugs, source links point to original approval labels and letters rather than later supplements or summaries. The ledger now has 164 verified primary indications, 1,602 pending drugs, and no unresolved-after-review cases. The curated indication table has 179 rows covering 176 distinct drugs. These counts do not complete the 1,766-drug audit.

## Candidate-stage checkpoint — 2026-10-13

### Audit update — 2026-10-13

After six additional FDA original-application reviews (elranatamab, fruquintinib, futibatinib, inavolisib, mavacamten, and olutasidenib), the curated table contains 44 indication rows covering 41 drugs. The review ledger now has 21 `verified_primary_indication` drugs, 1,745 pending drugs, and 0 unresolved-after-review drugs. The full 1,766-drug audit remains incomplete; no inference of nonapproval is made for pending records.

The FDA Drugs@FDA snapshot dated 2026-10-09 maps to 3,344 candidate applications across 1,766 catalog drugs; 355 have no exact or ingredient-prefix name match. The current queue identifies an earliest candidate approval date for 1,411 drugs and provides a candidate original approval label for 766; 428 of those are exact active-ingredient matches. These counts are triage, not verified coverage. The curated table has 38 indication rows for 35 drugs, while 15 drugs have documented primary-indication reviews and 1,751 remain pending. FDA's database notes that it covers most approvals since 1939, but most labels and approval records are available since 1998, which limits automated recovery for older products. The additional reviews this day confirmed the original FDA indications for abaloparatide, abrocitinib, adagrasib, bexagliflozin, capivasertib, and deucravacitinib.
