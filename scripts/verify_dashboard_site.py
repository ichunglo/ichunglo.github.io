"""Render and verify the dashboard in a small, disposable website copy.

The working site's source and output directory are never changed. This also
avoids local scratch files that are irrelevant to the publishable site.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POST = Path("posts/2026-10-02-drug-target-landscape/index.qmd")
ROOT_FILES = (
    "_quarto.yml",
    "references.bib",
    "vancouver.csl",
    "styles.css",
    "styles.scss",
    "index.qmd",
    "writing.qmd",
    "topics.qmd",
    "about.qmd",
    "editorial-notes.qmd",
)
GENERATED_FILES = ("landscape.json", "target-landscape-publication.svg")
REQUIRED_MARKERS = (
    "The evolving landscape of drug targets",
    "Clinical programs through co-target links",
    "unclear-target entry",
    "Drugs by first documented approval year",
    "Open the full-size vector figure",
    "more-target-results",
    "more-evidence-results",
    "Browse clinical programs by phase and outcome",
    "Scrollable clinical program table",
    "clinical_phase",
    "Clear clinical filters",
    "Development timeline",
    "Program stage × outcome label",
    "Target protein class",
    "clinical_group",
    "Explore by drug",
    "U.S. FDA-approved indications",
    "FDA indication not yet curated",
    "FDA approval record",
    "drug-search",
    "drug-year",
    "data-analysis-year",
    "data-analysis-scope",
    "Explore this dashboard",
    "landscape-jump-nav",
    "landscape-analytics-details",
    "target-table-wrap",
    "drug-export",
    "drug_target_link_id",
    "target-scope",
    "Paper-comparable core",
    "clinical-export",
    "outcome_confidence",
    "data-analysis-target",
    "data-analysis-phase",
    "data-analysis-outcome",
    "AI-assisted extraction",
    "Data Resource",
    "social-card.png",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview-dir", type=Path, help="Keep the verified rendered site at this new directory for browser QA")
    args = parser.parse_args()
    source = ROOT / POST
    original = source.read_text(encoding="utf-8")
    if original.count("draft: true") > 1:
        raise SystemExit("Expected at most one draft: true flag in dashboard source")
    validation = json.loads((ROOT / "data/generated/validation.json").read_text(encoding="utf-8"))
    if validation["status"] != "pass" or validation["errors"]:
        raise SystemExit("Curated data validation must pass before site verification")

    quarto = shutil.which("quarto")
    if not quarto:
        raise SystemExit("Quarto is required for website verification")

    with tempfile.TemporaryDirectory(prefix="drug-target-site-verify-") as temporary:
        stage = Path(temporary)
        for name in ROOT_FILES:
            shutil.copy2(ROOT / name, stage / name)
        for name in ("posts", "assets"):
            shutil.copytree(ROOT / name, stage / name)
        data_dir = stage / "data/generated"
        data_dir.mkdir(parents=True)
        for name in GENERATED_FILES:
            shutil.copy2(ROOT / "data/generated" / name, data_dir / name)

        staged_source = stage / POST
        staged_source.write_text(original.replace("draft: true", "draft: false", 1), encoding="utf-8")
        try:
            result = subprocess.run(
                [quarto, "render", "--no-execute", "--log-level", "error"],
                cwd=stage,
                capture_output=True,
                text=True,
                timeout=240,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise SystemExit("Clean staged website render timed out after 240 seconds") from exc
        if result.returncode:
            raise SystemExit(f"Clean staged website render failed:\n{result.stdout}\n{result.stderr}")

        page = stage / "_site" / POST.with_suffix(".html")
        html = page.read_text(encoding="utf-8")
        missing = [marker for marker in REQUIRED_MARKERS if marker not in html]
        if missing:
            raise SystemExit(f"Rendered dashboard is missing: {', '.join(missing)}")
        if "target-export" in html or "Download matching target records" in html:
            raise SystemExit("Removed target CSV export remains in rendered dashboard")
        public_url = "https://ichunglo.github.io/posts/2026-10-02-drug-target-landscape/social-card.png"
        if f'<meta property="og:image" content="{public_url}">' not in html:
            raise SystemExit("Rendered Open Graph image does not use the dashboard social card")
        if f'<meta name="twitter:image" content="{public_url}">' not in html:
            raise SystemExit("Rendered Twitter image does not use the dashboard social card")
        if not (stage / "_site/posts/2026-10-02-drug-target-landscape/social-card.png").is_file():
            raise SystemExit("Rendered dashboard social card is missing")
        for listing in ("index.html", "writing.html", "index.xml"):
            listing_html = (stage / "_site" / listing).read_text(encoding="utf-8")
            if "2026-10-02-drug-target-landscape" not in listing_html or "Data Resource" not in listing_html:
                raise SystemExit(f"Dashboard listing or category missing from {listing}")
        if "Browse Data Resources" not in (stage / "_site/topics.html").read_text(encoding="utf-8"):
            raise SystemExit("Data Resource entry missing from Topics page")
        for name in GENERATED_FILES:
            source_bytes = (ROOT / "data/generated" / name).read_bytes()
            rendered_bytes = (stage / "_site/data/generated" / name).read_bytes()
            if source_bytes != rendered_bytes:
                raise SystemExit(f"Rendered data resource differs from source: {name}")
        if args.preview_dir:
            preview_dir = args.preview_dir.resolve()
            if preview_dir.exists():
                raise SystemExit(f"Preview directory already exists: {preview_dir}")
            shutil.copytree(stage / "_site", preview_dir)
            print(f"Verified browser preview: {preview_dir}")

    if source.read_text(encoding="utf-8") != original:
        raise SystemExit("Dashboard source changed during verification")
    print("Dashboard website verification: pass (temporary production-style full-site render; source unchanged)")


if __name__ == "__main__":
    main()
