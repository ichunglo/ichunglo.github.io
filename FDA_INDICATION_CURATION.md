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

## Candidate-stage checkpoint — 2026-10-13

The FDA Drugs@FDA snapshot dated 2026-10-09 maps to 3,344 candidate applications across 1,766 catalog drugs; 355 have no exact or ingredient-prefix name match. The current queue identifies an earliest candidate approval date for 1,411 drugs and provides a candidate original approval label for 766; 428 of those are exact active-ingredient matches. These counts are triage, not verified coverage. The curated table has 38 indication rows for 35 drugs, while 15 drugs have documented primary-indication reviews and 1,751 remain pending. FDA's database notes that it covers most approvals since 1939, but most labels and approval records are available since 1998, which limits automated recovery for older products. The additional reviews this day confirmed the original FDA indications for abaloparatide, abrocitinib, adagrasib, bexagliflozin, capivasertib, and deucravacitinib.
