"""Guard against outcome bars colliding with the publication figure footnotes."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET

import build_publication_figure as figure


def main() -> None:
    figure.main()
    root = ET.parse(figure.OUTPUT).getroot()
    height = int(root.attrib["viewBox"].split()[-1])
    texts = list(root.iter("{http://www.w3.org/2000/svg}text"))
    summary = next(node for node in texts if "not unique drug failures" in "".join(node.itertext()))
    sources = next(node for node in texts if "Sources: paper supplements" in "".join(node.itertext()))
    payload = json.loads(figure.INPUT.read_text(encoding="utf-8"))
    included = {row["program_id"] for row in payload["programs"] if row["inclusion_status"] == "included"}
    outcome_types = {row["event_type"] for row in payload["outcomes"] if row["program_id"] in included}
    last_bar_bottom = 485 + (len(outcome_types) - 1) * 29 + 16
    assert last_bar_bottom < float(summary.attrib["y"]), "Outcome bars overlap their summary"
    assert float(summary.attrib["y"]) < float(sources.attrib["y"]) < height, "Figure footnotes exceed the canvas"
    assert "registry protocols, publications, sponsor and regulatory records" in "".join(sources.itertext())
    print("Publication figure layout and source caption: pass")


if __name__ == "__main__":
    main()
