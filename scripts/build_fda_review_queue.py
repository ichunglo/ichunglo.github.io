"""Build an FDA-only application *candidate* queue, not approved indications.

The Drugs@FDA ZIP is a point-in-time FDA download. Exact ingredient/name
matches are useful for triage but are not evidence that a particular indication
or patient population was approved, and a nonmatch does not prove no U.S.
approval. Only separately verified rows belong in fda-approved-indications.csv.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
DRUGS = ROOT / "data/curated/drugs.csv"
CURATED = ROOT / "data/curated/fda-approved-indications.csv"
DECISIONS = ROOT / "data/curated/fda-review-decisions.csv"
QUEUE = ROOT / "data/generated/fda-application-review-queue.csv"
SUMMARY = ROOT / "data/generated/fda-application-review-summary.json"
EFFICACY = ROOT / "data/generated/fda-efficacy-supplement-candidates.csv"
SOURCE_URL = "https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files"
DOWNLOAD_URL = "https://www.fda.gov/media/89850/download?attachment="


def normalized(value: str) -> str:
    value = re.sub(r"\([^)]*\)", "", value).casefold()
    value = value.replace("β", "beta").replace("α", "alpha")
    return " ".join(re.findall(r"[a-z0-9]+", value))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_zip_table(archive: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    with archive.open(name) as raw:
        # FDA's tab-delimited download contains Windows-1252 punctuation.
        with io.TextIOWrapper(raw, encoding="cp1252", newline="") as text:
            return list(csv.DictReader(text, delimiter="\t"))


def fda_url(value: str) -> str:
    parts = urlsplit(value.strip())
    if parts.hostname not in {"www.accessdata.fda.gov", "accessdata.fda.gov", "www.fda.gov"}:
        return ""
    return urlunsplit(("https", parts.netloc, parts.path, parts.query, parts.fragment))


def build_queue(
    archive_path: Path,
    snapshot_date: str,
    drugs_path: Path = DRUGS,
    curated_path: Path = CURATED,
) -> tuple[list[dict[str, str]], dict]:
    drugs = read_csv(drugs_path)
    curated_by_drug: dict[str, int] = defaultdict(int)
    for item in read_csv(curated_path):
        curated_by_drug[item["drug_id"]] += 1
    review_decisions = {
        row["drug_id"]: row["review_status"]
        for row in read_csv(DECISIONS)
    } if DECISIONS.exists() else {}

    with zipfile.ZipFile(archive_path) as archive:
        applications = {r["ApplNo"]: r["ApplType"] for r in read_zip_table(archive, "Applications.txt")}
        products = read_zip_table(archive, "Products.txt")
        submissions = read_zip_table(archive, "Submissions.txt")
        application_docs = read_zip_table(archive, "ApplicationDocs.txt")

    approved_originals: dict[str, list[str]] = defaultdict(list)
    for row in submissions:
        if row["SubmissionType"] == "ORIG" and row["SubmissionStatus"] == "AP":
            day = row["SubmissionStatusDate"][:10]
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
                approved_originals[row["ApplNo"]].append(day)

    latest_label: dict[str, tuple[str, str]] = {}
    for row in application_docs:
        if row["ApplicationDocsTypeID"] != "2":
            continue
        url = fda_url(row["ApplicationDocsURL"])
        if not url:
            continue
        date = row["ApplicationDocsDate"][:10]
        appl = row["ApplNo"]
        if date and (appl not in latest_label or date > latest_label[appl][0]):
            latest_label[appl] = (date, url)

    by_ingredient: dict[str, set[str]] = defaultdict(set)
    by_product_name: dict[str, set[str]] = defaultdict(set)
    single_ingredients: list[tuple[str, str]] = []
    for row in products:
        appl = row["ApplNo"]
        if applications.get(appl) not in {"NDA", "BLA"} or appl not in approved_originals:
            continue
        ingredient = normalized(row["ActiveIngredient"])
        product_name = normalized(row["DrugName"])
        if ingredient:
            by_ingredient[ingredient].add(appl)
            if ";" not in row["ActiveIngredient"] and "," not in row["ActiveIngredient"]:
                single_ingredients.append((ingredient, appl))
        if product_name:
            by_product_name[product_name].add(appl)

    queue = []
    for drug in sorted(drugs, key=lambda r: (r["generic_name"].casefold(), r["drug_id"])):
        name = normalized(drug["generic_name"])
        ingredient_apps = by_ingredient.get(name, set())
        product_apps = by_product_name.get(name, set())
        prefix_apps = {
            appl for ingredient, appl in single_ingredients if ingredient.startswith(name + " ")
        } if name else set()
        candidates = sorted(ingredient_apps | product_apps | prefix_apps)
        if ingredient_apps:
            basis = "exact_active_ingredient"
        elif product_apps:
            basis = "exact_product_name"
        elif prefix_apps:
            basis = "ingredient_prefix_candidate"
        else:
            basis = "no_exact_match"
        queue.append(
            {
                "drug_id": drug["drug_id"],
                "generic_name": drug["generic_name"],
                "indication_rows_present": "yes" if curated_by_drug[drug["drug_id"]] else "no",
                "completeness_review_status": review_decisions.get(
                    drug["drug_id"], "needs_full_indication_audit"
                ),
                "curated_indication_count": str(curated_by_drug[drug["drug_id"]]),
                "candidate_match_basis": basis,
                "candidate_application_count": str(len(candidates)),
                "candidate_applications": "|".join(f"{applications[a]}{a}" for a in candidates),
                "candidate_fda_pages": "|".join(
                    "https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm"
                    f"?event=overview.process&ApplNo={a}" for a in candidates
                ),
                "candidate_original_approval_dates": "|".join(
                    min(approved_originals[a]) for a in candidates
                ),
                "candidate_latest_label_dates": "|".join(
                    latest_label.get(a, ("", ""))[0] for a in candidates
                ),
                "candidate_latest_label_urls": "|".join(
                    latest_label.get(a, ("", ""))[1] for a in candidates
                ),
                "source_snapshot_date": snapshot_date,
                "source_dataset_url": SOURCE_URL,
            }
        )

    summary = {
        "source_dataset_url": SOURCE_URL,
        "source_download_url": DOWNLOAD_URL,
        "source_zip_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        "source_snapshot_date": snapshot_date,
        "warning": (
            "These are name-matched application candidates, not verified indication records. "
            "A no-exact-match result does not establish a lack of FDA approval. "
            "An original application approval date is not an indication-specific approval date."
        ),
        "total_catalog_drugs": len(queue),
        "drugs_with_curated_rows": sum(r["indication_rows_present"] == "yes" for r in queue),
        "drugs_without_curated_rows": sum(r["indication_rows_present"] == "no" for r in queue),
        "drugs_with_completed_indication_audit": sum(
            r["completeness_review_status"] == "verified_complete" for r in queue
        ),
        "exact_ingredient_candidate_drugs": sum(
            r["candidate_match_basis"] == "exact_active_ingredient" for r in queue
        ),
        "exact_product_name_only_candidate_drugs": sum(
            r["candidate_match_basis"] == "exact_product_name" for r in queue
        ),
        "ingredient_prefix_candidate_drugs": sum(
            r["candidate_match_basis"] == "ingredient_prefix_candidate" for r in queue
        ),
        "no_exact_match_drugs": sum(r["candidate_match_basis"] == "no_exact_match" for r in queue),
        "candidate_drugs_with_fda_label_url": sum(
            bool(r["candidate_latest_label_urls"].strip("|")) for r in queue
        ),
    }
    return queue, summary


def efficacy_candidates(archive_path: Path, queue: list[dict[str, str]]) -> list[dict[str, str]]:
    """FDA EFFICACY supplements are review leads, not confirmed new indications."""
    drugs_by_app: dict[str, list[dict[str, str]]] = defaultdict(list)
    for drug in queue:
        for candidate in drug["candidate_applications"].split("|"):
            match = re.fullmatch(r"(?:NDA|BLA)(\d{6})", candidate)
            if match:
                drugs_by_app[match.group(1)].append(drug)
    with zipfile.ZipFile(archive_path) as archive:
        submissions = read_zip_table(archive, "Submissions.txt")
        docs = read_zip_table(archive, "ApplicationDocs.txt")
    docs_by_submission: dict[tuple[str, str, str], dict[str, set[str]]] = defaultdict(
        lambda: {"label": set(), "letter": set()}
    )
    for doc in docs:
        kind = {"1": "letter", "2": "label"}.get(doc["ApplicationDocsTypeID"])
        url = fda_url(doc["ApplicationDocsURL"])
        if kind and url:
            key = (doc["ApplNo"], doc["SubmissionType"].strip(), doc["SubmissionNo"].strip())
            docs_by_submission[key][kind].add(url)
    rows = []
    for sub in submissions:
        appl = sub["ApplNo"]
        if (
            appl not in drugs_by_app
            or sub["SubmissionType"].strip() != "SUPPL"
            or sub["SubmissionStatus"] != "AP"
            or sub["SubmissionClassCodeID"] != "2"
        ):
            continue
        number = sub["SubmissionNo"].strip()
        links = docs_by_submission.get((appl, "SUPPL", number), {"label": set(), "letter": set()})
        for drug in drugs_by_app[appl]:
            rows.append({
                "drug_id": drug["drug_id"],
                "generic_name": drug["generic_name"],
                "application_number": next(
                    x for x in drug["candidate_applications"].split("|") if x.endswith(appl)
                ),
                "supplement_number": number,
                "fda_approved_submission_date": sub["SubmissionStatusDate"][:10],
                "fda_approval_letter_urls": "|".join(sorted(links["letter"])),
                "fda_label_urls": "|".join(sorted(links["label"])),
                "review_status": "candidate_not_indication_verified",
            })
    return sorted(rows, key=lambda r: (r["generic_name"].casefold(), r["application_number"], r["fda_approved_submission_date"], r["supplement_number"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fda-zip", required=True, type=Path)
    parser.add_argument("--snapshot-date", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.snapshot_date):
        parser.error("--snapshot-date must be YYYY-MM-DD")
    queue, summary = build_queue(args.fda_zip, args.snapshot_date)
    supplements = efficacy_candidates(args.fda_zip, queue)
    summary["approved_efficacy_supplement_candidates"] = len(supplements)
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    with QUEUE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(queue[0]))
        writer.writeheader()
        writer.writerows(queue)
    with EFFICACY.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "drug_id", "generic_name", "application_number", "supplement_number",
            "fda_approved_submission_date", "fda_approval_letter_urls", "fda_label_urls", "review_status",
        ])
        writer.writeheader()
        writer.writerows(supplements)
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
