"""Check that research findings are complete and that their evidence links resolve."""

import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest
import yaml

from sco import graph

RESEARCH_DIR = graph.ROOT / "research"
FINDINGS = sorted((RESEARCH_DIR / "findings").glob("F-*.md"))
NOTEBOOKS = sorted((RESEARCH_DIR / "notebooks").glob("*.py"))
ADR_DIR = graph.ROOT / "docs" / "adr"

ALLOWED = {
    "attribution": {"bfo-forced", "iof-chosen", "scro-specific", "sco-chosen"},
    "enforcement": {"owl", "fol-annotation", "prose"},
    "verdict": {"clarifies", "costs", "mixed"},
}
REQUIRED = ["id", "title", "principle", *ALLOWED, "predicted", "found", "evidence"]


def frontmatter(path: Path) -> dict:
    text = path.read_text()
    assert text.startswith("---\n"), f"{path.name}: missing YAML frontmatter"
    return yaml.safe_load(text.split("---\n", 2)[1]) or {}


def known_ids() -> set[str]:
    cqs = {p.stem for p in graph.CQ_DIR.glob("CQ-*.md")}
    adrs = {f"ADR-{p.name[:4]}" for p in ADR_DIR.glob("[0-9][0-9][0-9][0-9]-*.md")}
    return cqs | adrs


def slug(heading: str) -> str:
    """GitHub's anchor for a markdown heading."""
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def notebook_anchors(path: Path) -> set[str]:
    """Anchors for the headings in a marimo notebook's `mo.md(...)` cells."""
    markdown = re.findall(r'mo\.md\(\s*r?"""(.*?)"""', path.read_text(), flags=re.DOTALL)
    return {
        slug(line.strip().lstrip("#"))
        for block in markdown
        for line in block.splitlines()
        if line.strip().startswith("#")
    }


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=[p.stem for p in NOTEBOOKS])
def test_notebook_runs(notebook):
    """Findings cite these notebooks, so they must run top to bottom against the pinned release."""
    result = subprocess.run(
        [sys.executable, str(notebook)], capture_output=True, text=True, timeout=300
    )
    assert result.returncode == 0, result.stderr[-2000:]


@pytest.mark.parametrize("finding", FINDINGS, ids=[p.stem for p in FINDINGS])
def test_finding_frontmatter_is_complete(finding):
    meta = frontmatter(finding)
    missing = [k for k in REQUIRED if not meta.get(k)]
    assert not missing, f"missing or empty: {missing}"
    assert meta["id"] == finding.stem
    for key, allowed in ALLOWED.items():
        assert meta[key] in allowed, f"{key}: {meta[key]!r} not in {sorted(allowed)}"
    assert isinstance(meta["predicted"], date) and isinstance(meta["found"], date)
    assert meta["predicted"] <= meta["found"], "the prediction must come before the finding"


@pytest.mark.parametrize("finding", FINDINGS, ids=[p.stem for p in FINDINGS])
def test_finding_evidence_resolves(finding):
    for ref in frontmatter(finding)["evidence"]:
        target, _, anchor = ref.partition("#")
        path = RESEARCH_DIR / target
        assert path.exists(), f"evidence {ref!r}: no file research/{target}"
        if anchor and path.parent.name == "notebooks":
            assert anchor in notebook_anchors(path), f"evidence {ref!r}: no such notebook heading"


@pytest.mark.parametrize("finding", FINDINGS, ids=[p.stem for p in FINDINGS])
def test_finding_informs_existing_cqs_and_adrs(finding):
    unknown = sorted(set(frontmatter(finding).get("informs") or []) - known_ids())
    assert not unknown, f"informs: {unknown} match no CQ-NNN or ADR-NNNN file"
