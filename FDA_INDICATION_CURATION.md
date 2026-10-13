# FDA indication curation — release gate

The live indication table is a manually verified pilot, **not a complete review of the 1,766-drug catalog**. Do not present the Drugs@FDA application queue as approved indications, or publish a claim of complete FDA coverage from it.

## FDA-only source path

1. Build `data/generated/fda-application-review-queue.csv` from the [Drugs@FDA downloadable tables](https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files) with `scripts/build_fda_review_queue.py`. Record the FDA snapshot date and ZIP checksum from its summary file.
2. For each catalog drug, confirm the active moiety and all relevant NDA/BLA applications. A salt, four-letter biologic suffix, brand name, combination product, or cell/gene therapy may require manual alias review. An unmatched name is **not** proof of no FDA approval.
3. Read the FDA approval letters for the original application and all indication-changing supplements. Determine the first U.S. approval date for **each indication**, not merely the original application date. A conversion from accelerated to traditional approval is not a new indication.
4. Check the most relevant FDA label for the indication wording, qualifying mutation or patient group, prior-therapy requirements, and required combination therapy. Capture a dated, direct FDA label URL and the FDA approval-record URL. The label may have changed since the initial approval.
5. Record verified indication rows in `data/curated/fda-approved-indications.csv`. Perform an explicit completeness check for that drug; the presence of one row does not prove all its U.S. indications are covered.
6. For drugs with no confirmed U.S. approval, retain a separate evidence-backed review state. Never translate a missing Drugs@FDA name match into “not approved”; the source may omit aliases or products handled elsewhere at FDA.

## Publication condition

Before announcing full FDA coverage, every catalog drug must have a completed FDA status review, all verified U.S. indications must have indication-specific dates and source links, and all unresolved or out-of-scope cases must be clearly labeled. Run the curated-data validator, dashboard tests, a clean production render, and live-page checks before deployment. Until then, keep the reader-facing count labeled as partial curated coverage.
