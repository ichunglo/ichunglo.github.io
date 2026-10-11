"""Build a publication-style SVG summary figure from the generated release JSON."""

from __future__ import annotations

import html
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "generated" / "landscape.json"
OUTPUT = ROOT / "data" / "generated" / "target-landscape-publication.svg"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def color(value: float, maximum: float, light_high: float = 82, light_low: float = 38) -> str:
    ratio = 0 if maximum <= 0 else max(0, min(1, value / maximum))
    lightness = light_high - ratio * (light_high - light_low)
    return f"hsl(198 58% {lightness:.1f}%)"


def text(x: float, y: float, value: object, size: int = 13, anchor: str = "start", weight: str = "400", fill: str = "#17324d") -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}px" font-family="Arial, sans-serif" font-weight="{weight}" text-anchor="{anchor}" fill="{fill}">{esc(value)}</text>'


def panel_title(x: float, y: float, label: str, subtitle: str) -> str:
    return text(x, y, label, 19, weight="600") + text(x, y + 22, subtitle, 12, fill="#657383")


def horizontal_bars(rows: list[tuple[str, int]], x: float, y: float, width: float, row_height: float, max_rows: int = 10, label_width: int = 145) -> str:
    rows = rows[:max_rows]
    maximum = max((value for _, value in rows), default=1)
    bar_width = width - label_width - 42
    parts = []
    for index, (label, value) in enumerate(rows):
        yy = y + index * row_height
        parts.append(text(x, yy + 13, label, 11, fill="#334e68"))
        parts.append(f'<rect x="{x + label_width:.1f}" y="{yy + 3:.1f}" width="{bar_width:.1f}" height="13" rx="2" fill="#edf2f5"/>')
        parts.append(f'<rect x="{x + label_width:.1f}" y="{yy + 3:.1f}" width="{max(2, bar_width * value / maximum):.1f}" height="13" rx="2" fill="{color(value, maximum)}"/>')
        parts.append(text(x + width, yy + 14, f"{value:,}", 11, anchor="end", weight="600"))
    return "".join(parts)


def main() -> None:
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    targets = payload["targets"]
    links = payload["drug_targets"]
    approvals = payload["approvals"]
    programs = payload["programs"]

    class_counts = Counter(target.get("protein_group") or "Unclassified" for target in targets)
    target_by_id = {target["target_id"]: target for target in targets}
    primary_counts = Counter(link["target_id"] for link in links if link.get("target_role") == "primary")
    top_targets = []
    for target_id, count in primary_counts.most_common(10):
        target = target_by_id.get(target_id, {})
        top_targets.append((target.get("gene_symbol") or target.get("preferred_name", target_id), count))

    first_year_by_drug = {}
    for approval in approvals:
        year = (approval.get("approval_date") or "")[:4]
        if year.isdigit() and (approval["drug_id"] not in first_year_by_drug or year < first_year_by_drug[approval["drug_id"]]):
            first_year_by_drug[approval["drug_id"]] = year
    drugs_by_year = defaultdict(set)
    for drug_id, year in first_year_by_drug.items():
        drugs_by_year[year].add(drug_id)
    approval_years = {year: len(drugs) for year, drugs in drugs_by_year.items()}

    included_program_ids = {program["program_id"] for program in programs if program.get("inclusion_status") == "included"}
    outcomes = [outcome for outcome in payload["outcomes"] if outcome["program_id"] in included_program_ids]
    outcome_labels = {
        "endpoint_failure": "Endpoint failure",
        "biomarker_endpoint_met": "Biomarker endpoint met",
        "lead_in_futility": "Lead-in futility",
        "safety_failure": "Safety failure",
        "discontinuation": "Discontinuation",
        "risk_benefit_discontinuation": "Risk–benefit discontinuation",
        "regulatory_rejection": "Regulatory rejection",
        "strategic_discontinuation": "Strategic discontinuation",
        "cross_study_decision": "Cross-study decision",
        "withdrawal": "Withdrawal",
        "unknown": "Unknown",
    }
    outcome_counts = Counter(outcome.get("event_type") or "unknown" for outcome in outcomes)
    outcome_rows = [
        (outcome_labels.get(kind, kind.replace("_", " ").title()), count)
        for kind, count in outcome_counts.most_common()
    ]

    width = 1200
    height = max(900, 485 + len(outcome_rows) * 29 + 100)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="figure-title figure-desc"><title id="figure-title">Drug-target landscape release analysis</title><desc id="figure-desc">Four-panel summary of target classes, connected primary targets, distinct drugs by first documented approval year, and clinical outcome event labels.</desc><rect width="100%" height="100%" fill="#ffffff"/>']
    parts.append(text(48, 42, "Drug-target landscape: release analysis", 25, weight="600"))
    parts.append(text(48, 65, "Approved-drug baseline from The evolving landscape of drug targets, extended with registry-linked clinical data", 13, fill="#657383"))

    parts.append(panel_title(48, 105, "A  Targets by protein class", "Target records in the current release"))
    parts.append(horizontal_bars(sorted(class_counts.items(), key=lambda item: item[1], reverse=True), 48, 145, 500, 25, max_rows=len(class_counts)))

    parts.append(panel_title(642, 105, "B  Most connected primary targets", "Primary drug-target relationships"))
    parts.append(horizontal_bars(top_targets, 642, 145, 500, 27))

    parts.append(panel_title(48, 435, "C  Drugs by first documented approval year", "Each drug counted once at its earliest dated record"))
    chart_x, chart_y, chart_w, chart_h = 92, 485, 470, 255
    years = sorted(approval_years)
    values = [approval_years[year] for year in years]
    maximum = max(10, math.ceil(max(values or [1]) / 10) * 10)
    for tick in range(0, maximum + 1, max(1, maximum // 5)):
        yy = chart_y + chart_h - chart_h * tick / maximum
        parts.append(f'<line x1="{chart_x}" x2="{chart_x + chart_w}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="#edf0f2"/>')
        parts.append(text(chart_x - 9, yy + 4, tick, 10, anchor="end", fill="#657383"))
    if years:
        step = chart_w / max(1, len(years) - 1)
        points = []
        for index, (year, value) in enumerate(zip(years, values)):
            xx = chart_x + index * step
            yy = chart_y + chart_h - chart_h * value / maximum
            points.append(f"{xx:.1f},{yy:.1f}")
            if int(year) % 5 == 0:
                parts.append(text(xx, chart_y + chart_h + 22, year, 10, anchor="middle", fill="#657383"))
        parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="#2f6f8f" stroke-width="2.5"/>')
        for index, value in enumerate(values):
            xx = chart_x + index * step
            yy = chart_y + chart_h - chart_h * value / maximum
            parts.append(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="4" fill="{color(value, maximum)}" stroke="#ffffff" stroke-width="1"/>')
    parts.append(f'<line x1="{chart_x}" x2="{chart_x}" y1="{chart_y}" y2="{chart_y + chart_h}" stroke="#aebac3"/><line x1="{chart_x}" x2="{chart_x + chart_w}" y1="{chart_y + chart_h}" y2="{chart_y + chart_h}" stroke="#aebac3"/>')
    parts.append(text(chart_x + chart_w / 2, chart_y + chart_h + 43, "Approval year", 11, anchor="middle", fill="#334e68"))
    parts.append(f'<text transform="translate(53 {chart_y + chart_h / 2:.1f}) rotate(-90)" text-anchor="middle" font-size="11px" font-family="Arial, sans-serif" fill="#334e68">Distinct drugs</text>')

    parts.append(panel_title(642, 435, "D  Clinical outcome event labels", "Included registry-linked pilot programs only"))
    parts.append(horizontal_bars(outcome_rows, 642, 485, 500, 29, max_rows=len(outcome_rows), label_width=220))
    footer_y = max(838, 485 + len(outcome_rows) * 29 + 17)
    parts.append(text(642, footer_y, f"{len(outcomes)} records across {len(included_program_ids)} programs; not unique drug failures", 11, fill="#657383"))
    parts.append(text(48, height - 42, "Approval-year counts use the earliest dated paper-derived record per drug; not a complete global time series.", 11, fill="#657383"))
    parts.append(text(48, height - 22, "Sources: paper supplements; registry protocols, publications, sponsor and regulatory records for the clinical pilot.", 11, fill="#657383"))
    parts.append("</svg>")
    OUTPUT.write_text("".join(parts), encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "class_rows": len(class_counts), "top_targets": len(top_targets), "approval_years": len(years), "outcome_events": len(outcomes)}, indent=2))


if __name__ == "__main__":
    main()
