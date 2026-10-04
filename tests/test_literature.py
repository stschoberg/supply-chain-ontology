"""Check that literature notes, the Zotero bibliography, and CQs/ADRs stay linked."""

import re
from pathlib import Path

import pytest
import yaml

from sco import graph

LITERATURE_DIR = graph.ROOT / "docs" / "literature"
BIB_FILE = LITERATURE_DIR / "library.bib"
NOTES = sorted((LITERATURE_DIR / "notes").glob("*.md"))
ADR_DIR = graph.ROOT / "docs" / "adr"

# Known mismatches awaiting a fix in Zotero. strict=True makes the test fail once the fix lands,
# as a reminder to delete the entry here.
KNOWN_BAD_CITEKEYS = {
    "morrowDevelopingBasicFormal2021": "Zotero item has no year, so its citekey lacks '2021'",
}


def bib_keys() -> set[str]:
    return set(re.findall(r"^@\w+\{([^,\s]+),", BIB_FILE.read_text(), flags=re.MULTILINE))


def frontmatter(path: Path) -> dict:
    text = path.read_text()
    assert text.startswith("---\n"), f"{path.name}: missing YAML frontmatter"
    return yaml.safe_load(text.split("---\n", 2)[1]) or {}


def known_ids() -> set[str]:
    cqs = {p.stem for p in graph.CQ_DIR.glob("CQ-*.md")}
    adrs = {f"ADR-{p.name[:4]}" for p in ADR_DIR.glob("[0-9][0-9][0-9][0-9]-*.md")}
    return cqs | adrs


def note_param(path: Path):
    reason = KNOWN_BAD_CITEKEYS.get(path.stem)
    marks = [pytest.mark.xfail(reason=reason, strict=True)] if reason else []
    return pytest.param(path, id=path.stem, marks=marks)


@pytest.mark.parametrize("note", [note_param(p) for p in NOTES])
def test_note_citekey_is_in_bib_and_matches_filename(note):
    citekey = frontmatter(note).get("citekey")
    assert citekey == note.stem, f"frontmatter citekey {citekey!r} != file name {note.stem!r}"
    assert citekey in bib_keys(), f"{citekey!r} not in {BIB_FILE.name}; check the Zotero item"


@pytest.mark.parametrize("note", NOTES, ids=[p.stem for p in NOTES])
def test_note_informs_existing_cqs_and_adrs(note):
    informs = frontmatter(note).get("informs") or []
    unknown = sorted(set(informs) - known_ids())
    assert not unknown, f"informs: {unknown} match no CQ-NNN or ADR-NNNN file"


def test_citations_in_cqs_and_adrs_are_in_bib():
    docs = [*graph.CQ_DIR.glob("CQ-*.md"), *ADR_DIR.glob("*.md")]
    cited = {
        (doc.name, key)
        for doc in docs
        for key in re.findall(r"\[@([A-Za-z0-9_:-]+)", doc.read_text())
    }
    missing = sorted((name, key) for name, key in cited if key not in bib_keys())
    assert not missing, f"citations not in {BIB_FILE.name}: {missing}"
