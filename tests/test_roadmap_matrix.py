"""Guard rdflib coverage matrix: no stray 'planned' status in ROADMAP table."""

from __future__ import annotations

import re
from pathlib import Path

ROADMAP = Path(__file__).resolve().parents[1] / "docs" / "ROADMAP.md"


def test_roadmap_matrix_has_no_planned_cells():
    text = ROADMAP.read_text(encoding="utf-8")
    start = text.index("## Oxigraph / pyoxigraph coverage matrix")
    end = text.index("Before **1.0.0**", start)
    table = text[start:end]
    # Version column must not contain standalone "planned" targets.
    for line in table.splitlines():
        if not line.startswith("|") or line.startswith("| rdflib"):
            continue
        if "planned" in line.lower() and "**planned**" not in line:
            # Allow column header "planned" in legend only (outside table body)
            if re.search(r"\|\s*0\.\d+\s+planned", line, re.I):
                raise AssertionError(f"Matrix row still planned: {line.strip()}")
