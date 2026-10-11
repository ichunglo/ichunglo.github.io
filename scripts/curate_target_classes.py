"""One-time, conservative protein-class audit for the 139 unclassified rows.

The paper's target identity and landscape scope are never changed here. Broad,
mixed, or non-protein labels receive the explicit Unresolved class instead of a
speculative single-protein assignment. The saved audit is checked on reruns.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGETS = ROOT / "data" / "curated" / "targets.csv"
AUDIT = ROOT / "data" / "curated" / "target-class-audit.csv"

ENZYME_PREFIXES = (
    "7,8-dihydro-", "ATP synthase", "Alanine racemase", "Beta-1,3-glucan synthase",
    "Beta-lactamase", "Bifunctional dihydrofolate", "Cyclooxygenase",
    "Cytochrome P450", "D-alanine", "D-alanyl", "DNA gyrase", "DNA polymerase",
    "DNA terminase", "DNA topoisomerase", "DNA-directed RNA polymerase",
    "Dihydrofolate reductase", "Dihydropteroate", "Enoyl-",
    "Hepatitis C virus serine protease", "Integrase", "Isoleucine--tRNA ligase",
    "Lanosterol", "Leucine-tRNA ligase", "NS5B protein", "Neuraminidase",
    "Ornithine decarboxylase", "Penicillin-binding protein", "Peptidoglycan",
    "Phosphodiesterase", "Polymerase acidic", "Probable arabinosyltransferase",
    "Probable fatty acid synthase", "Pyruvate:ferredoxin", "Reverse transcriptase",
    "Serine/threonine protein kinase", "Soluble guanylate cyclase",
    "Squalene epoxidase", "Thymidine kinase", "Thymidylate synthase",
    "Topoisomerase IV", "Toxin B", "UDP-N-acetylglucosamine",
    "cAMP-specific", "cGMP-inhibited",
)
ION_PREFIXES = (
    "GABA A receptor", "GABA-A receptor", "Glutamate receptor ionotropic",
    "Glutamate-gated chloride channel", "Glycine receptor",
    "High voltage-activated calcium channel", "Matrix protein 2",
    "Muscle-type nicotinic acetylcholine receptor", "Neuronal acetylcholine receptor",
    "Nicotinic acetylcholine receptor", "Sodium channel", "Sulfonylurea receptor",
    "Voltage-gated",
)
GPCR_PREFIXES = ("Adrenergic receptor", "GABA-B receptor", "Muscarinic acetylcholine receptor")
RECEPTOR_PREFIXES = (
    "Cytokine receptor common subunit gamma",
    "Granulocyte macrophage colony-stimulating factor receptor",
    "Integrin alpha-IIb/beta-3", "Interferon alpha/beta receptor",
    "Interleukin-2 receptor", "T-cell surface glycoprotein CD3",
)
TRANSPORTER_PREFIXES = (
    "L-type amino acid transporter", "Potassium-transporting ATPase",
    "Sodium/potassium-transporting ATPase",
)
OTHER_PREFIXES = (
    "Cytochrome b", "Envelope glycoprotein", "Envelope protein", "Fusion glycoprotein",
    "Gag polyprotein", "Protective antigen", "Spike glycoprotein",
    "Transmembrane glycoprotein", "Tubulin",
)
UNRESOLVED_NAMES = {
    "Acetylcholine receptor",  # Could be a GPCR or a ligand-gated ion channel.
    "Immediate early protein IE1 mRNA",  # The named target is an RNA, not a protein.
}
UNRESOLVED_PREFIXES = ("Genome polyprotein", "Pol polyprotein", "Replicase polyprotein")
CONTEXT_RESOLVED = {
    "alpha3/beta4": ("Ion channels", "Nicotinic acetylcholine receptor subunits, supported by linked mecamylamine", "https://www.guidetopharmacology.org/GRAC/ObjectDisplayForward?objectId=464"),
    "alpha4/beta2": ("Ion channels", "Nicotinic acetylcholine receptor subunits, supported by linked nicotine", "https://www.guidetopharmacology.org/GRAC/FamilyIntroductionForward?familyId=76"),
    "brain (Types I, II, III)": ("Ion channels", "Brain sodium-channel types I-III, supported by linked local anesthetics", "https://drugs.ncats.io/substances?q=comments%3A%22Physiological%20Effects%20%5BPE%5D%7COrgan%20System%20Specific%20Effects%20%5BPE%5D%7CNervous%20System%20Activity%20Alteration%20%5BPE%5D%7CPeripheral%20Nervous%20System%20Activity%20Alteration%20%5BPE%5D%7CSensory%20System%20Activity%20Alteration%20%5BPE%5D%22"),
    "Protein P": ("Enzymes", "Hepatitis B polymerase/reverse transcriptase, supported by linked antiviral drugs", "https://www.uniprot.org/uniprotkb/P17100/entry"),
}


def classify(name: str) -> tuple[str, str]:
    if name in CONTEXT_RESOLVED:
        return CONTEXT_RESOLVED[name][:2]
    if name in UNRESOLVED_NAMES or name.startswith(UNRESOLVED_PREFIXES):
        return "Unresolved", "Broad, mixed, or non-protein paper label; no safe single protein class"
    for group, prefixes in (
        ("Enzymes", ENZYME_PREFIXES),
        ("Ion channels", ION_PREFIXES),
        ("GPCRs", GPCR_PREFIXES),
        ("Receptors", RECEPTOR_PREFIXES),
        ("Transporters", TRANSPORTER_PREFIXES),
        ("Other proteins", OTHER_PREFIXES),
    ):
        if name.startswith(prefixes):
            return group, f"Explicit protein family or function in paper label ({group})"
    if name == "Thyroid hormone receptor":
        return "Nuclear hormone receptors", "Explicit nuclear hormone receptor family in paper label"
    raise ValueError(f"No audited class rule for {name!r}")


def main() -> None:
    with TARGETS.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        assert fields is not None
        targets = list(reader)
    if AUDIT.exists():
        with AUDIT.open(encoding="utf-8", newline="") as handle:
            audited = list(csv.DictReader(handle))
        by_id = {row["target_id"]: row for row in targets}
        assert len(audited) == 139 and len({row["target_id"] for row in audited}) == 139
        for row in audited:
            assert by_id[row["target_id"]]["protein_group"] == row["audited_group"]
            assert classify(row["preferred_name"])[0] == row["audited_group"]
        assert all(row["protein_group"] for row in targets)
        print(f"Target class audit verified: {len(audited)} original review rows")
        return

    missing = [row for row in targets if not row["protein_group"]]
    assert len(missing) == 139, f"Expected 139 original review rows, found {len(missing)}"
    audit = []
    for row in missing:
        group, basis = classify(row["preferred_name"])
        row["protein_group"] = group
        audit.append({
            "target_id": row["target_id"],
            "preferred_name": row["preferred_name"],
            "audited_group": group,
            "audit_basis": basis,
            "landscape_scope": row["landscape_scope"],
            "target_status": row["target_status"],
            "paper_source_row": row["paper_source_row"],
            "evidence_url": CONTEXT_RESOLVED.get(row["preferred_name"], ("", "", ""))[2],
        })
    audit.sort(key=lambda row: row["target_id"])
    with TARGETS.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(targets)
    with AUDIT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(audit[0]))
        writer.writeheader()
        writer.writerows(audit)
    print(f"Target class audit applied: {len(audit)} rows; groups={dict(Counter(row['audited_group'] for row in audit))}")


if __name__ == "__main__":
    main()
