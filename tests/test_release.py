"""Build a data release from the committed fixtures and read it back through its catalog."""

import gzip
import json
import re
import subprocess

import duckdb
import pytest
from rdflib import OWL, RDF, RDFS, Graph
from rdflib.namespace import SKOS

from data import release
from data.lift import PROV
from sco import graph
from sco.namespaces import DATA, IOF, USAS

DLMS_SYNTH = [
    "activities", "due_ins", "shipment_notices", "acceptance_reports", "receipts",
    "discrepancy_reports", "requisitions", "release_orders", "issues",
]  # fmt: skip
FIXTURE_SNAPSHOT = graph.ROOT / "tests" / "fixtures" / "usaspending"


@pytest.fixture(scope="module")
def dist(tmp_path_factory):
    out = tmp_path_factory.mktemp("dist")
    release.main(
        ["build", "--tag", "data-test", "--out", str(out),
         "--snapshot", f"usaspending={FIXTURE_SNAPSHOT}"]
    )  # fmt: skip
    return out


def test_release_contains_parquet_catalog_raw_and_notes(dist):
    names = {p.name for p in dist.iterdir()}
    assert names == {
        "entities.parquet",
        "entities.csv",
        "stg_usaspending__awards.parquet",
        "stg_usaspending__awards.csv",
        *[f"dlms_synth__{table}.{ext}" for table in DLMS_SYNTH for ext in ("parquet", "csv")],
        "meta_build.parquet",
        "meta_build.csv",
        "meta_source_files.parquet",
        "meta_source_files.csv",
        "usaspending.nt.gz",
        "usaspending.schema.ttl",
        "dlms_synth.nt.gz",
        "dlms_synth.schema.ttl",
        "iof-scro.experimental.nt.gz",
        "iof-scro.schema.ttl",
        "catalog.duckdb",
        "RELEASE_NOTES.md",
        "SHA256SUMS",
        "raw-usaspending-usaspending.tar",
    }  # only models tagged `published`


def test_catalog_reads_the_parquet_files(dist, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # the catalog must not depend on the working directory
    with duckdb.connect() as con:
        con.sql(f"attach '{dist / 'catalog.duckdb'}' as sco (read_only)")
        assert con.sql("select count(*) from sco.stg_usaspending__awards").fetchone()[0] == 8
        assert con.sql("select release_tag from sco.meta_build").fetchone()[0] == "data-test"


def test_catalog_describes_tables_and_columns(dist):
    with duckdb.connect() as con:
        con.sql(f"attach '{dist / 'catalog.duckdb'}' as sco (read_only)")
        view = con.sql(
            "select comment from duckdb_views() where view_name = 'stg_usaspending__awards'"
        ).fetchone()[0]
        columns = dict(
            con.sql(
                "select column_name, comment from duckdb_columns() "
                "where database_name = 'sco' and table_name = 'stg_usaspending__awards'"
            ).fetchall()
        )
    assert view.startswith("USAspending.gov contract award summaries")
    assert "not an item identifier" in columns["dla_reference_number"].lower()
    assert all(columns.values())  # every column, including those with quotes in their text


def test_release_notes_include_the_dictionary(dist):
    notes = (dist / "RELEASE_NOTES.md").read_text()
    assert "### stg_usaspending__awards" in notes
    assert "| `recipient_uei` | varchar |" in notes


def test_each_graph_ships_with_its_schema_and_is_listed(dist):
    notes, sums = (dist / "RELEASE_NOTES.md").read_text(), (dist / "SHA256SUMS").read_text()
    pairs = {
        "usaspending.nt.gz": "usaspending",
        "dlms_synth.nt.gz": "dlms_synth",
        "iof-scro.experimental.nt.gz": "iof-scro",
    }
    for graph_file, name in pairs.items():
        assert f"| `{graph_file}` |" in notes and f"| `{name}.schema.ttl` |" in notes
        assert f"  {graph_file}\n" in sums and f"  {name}.schema.ttl\n" in sums
        assert len(Graph().parse(dist / f"{name}.schema.ttl")) > 0
    assert "Experimental model: every source mapped into `iof-scro` terms" in notes
    assert "| **Synthetic** source: `dlms_synth` in its own terms |" in notes


def load(path):
    return Graph().parse(data=gzip.decompress(path.read_bytes()), format="nt")


def test_source_graph_defines_its_own_terms_and_names_its_release(dist):
    g = load(dist / "usaspending.nt.gz")
    undefined = {
        term
        for s, p, o in g
        for term in (p, o if p == RDF.type else None)
        if term and str(term).startswith(str(USAS)) and not g.value(term, SKOS.definition)
    }
    assert not undefined
    (header,) = g.subjects(RDF.type, OWL.Ontology)  # one ontology per file, for OWL tools
    assert header == DATA["graph/usaspending"]
    assert str(g.value(header, OWL.versionInfo)) == "data-test"


def test_model_graph_includes_its_schema_and_points_at_its_sources(dist):
    g = load(dist / "iof-scro.experimental.nt.gz")
    assert len(set(g.subjects(RDF.type, IOF.PurchaseOrder))) == 8
    assert str(g.value(IOF.PurchaseOrder, RDFS.label)) == "purchase order"
    assert not [p for p in g.predicates() if str(p).startswith(str(USAS))]  # IOF terms only
    (header,) = g.subjects(RDF.type, OWL.Ontology)
    derived_from = set(g.objects(header, PROV.wasDerivedFrom))
    assert DATA["graph/usaspending"] in derived_from
    assert any("industrialontologies.org" in str(origin) for origin in derived_from)


def test_synthetic_tables_are_marked_everywhere_a_reader_meets_them(dist):
    notes = (dist / "RELEASE_NOTES.md").read_text()
    assert "**Tables marked Synthetic are invented.**" in notes
    assert notes.count("| **Synthetic** |") == len(DLMS_SYNTH)
    # The connect examples point at real data, though the biggest tables are synthetic.
    assert "from sco.dlms_synth__" not in notes and "dlms_synth__receipts.csv" not in notes
    with duckdb.connect() as con:
        con.sql(f"attach '{dist / 'catalog.duckdb'}' as sco (read_only)")
        comments = dict(
            con.sql(
                "select view_name, comment from duckdb_views() where database_name = 'sco'"
            ).fetchall()
        )
    for table in DLMS_SYNTH:
        assert comments[f"dlms_synth__{table}"].startswith("Synthetic: invented")
    assert not comments["stg_usaspending__awards"].startswith("Synthetic")


def test_csv_matches_parquet(dist):
    with duckdb.connect() as con:

        def rows(path):
            return con.sql(f"select count(*) from '{path}'").fetchone()[0]

        for parquet in dist.glob("*.parquet"):
            assert rows(parquet.with_suffix(".csv")) == rows(parquet)


def test_checksums_cover_every_other_file(dist):
    listed = {line.split()[1] for line in (dist / "SHA256SUMS").read_text().splitlines()}
    assert listed == {p.name for p in dist.iterdir()} - {"SHA256SUMS"}


def test_row_counts_match_through_the_catalog(dist):
    assert release.row_counts(str(dist / "catalog.duckdb")) == release.row_counts(str(dist))


@pytest.fixture
def fake_github(monkeypatch):
    """Record publish's steps instead of calling GitHub."""
    calls = []
    monkeypatch.setattr(release, "gh", lambda *args: calls.append(("gh", *args)))
    monkeypatch.setattr(release, "release_exists", lambda tag: tag == release.LATEST_TAG)
    monkeypatch.setattr(release, "write_catalog", lambda out, url: calls.append(("catalog", url)))
    monkeypatch.setattr(release, "verify", lambda tag, expected: calls.append(("verify", tag)))
    return calls


def test_publish_uploads_parquet_before_building_the_catalog(dist, fake_github):
    release.main(["publish", "--out", str(dist), "--allow-dirty"])
    steps = [c[:3] if c[0] == "gh" else c for c in fake_github]
    assert steps == [
        ("gh", "release", "create"),  # data-test, with the Parquet files
        ("catalog", f"{release.release_url('data-test')}"),
        ("gh", "release", "upload"),  # catalog.duckdb + SHA256SUMS
        ("verify", "data-test"),
        ("gh", "release", "delete"),  # the old data-latest
        ("gh", "release", "create"),  # the new data-latest
    ]
    first_upload = {a.rsplit("/", 1)[-1] for a in fake_github[0] if str(dist) in a}
    assert "stg_usaspending__awards.parquet" in first_upload
    assert "catalog.duckdb" not in first_upload


def test_publish_refuses_an_existing_tag(dist, fake_github, monkeypatch):
    monkeypatch.setattr(release, "release_exists", lambda tag: True)
    with pytest.raises(SystemExit, match="already exists"):
        release.main(["publish", "--out", str(dist), "--allow-dirty"])
    assert fake_github == []


def test_example_notebook_runs_against_a_release(dist):
    """Run the notebook's code cells against the fixture release instead of GitHub."""
    notebook = json.loads((graph.ROOT / "data" / "examples" / "explore.ipynb").read_text())
    code = [
        line
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
        for line in "".join(cell["source"]).splitlines()
        if not line.startswith("%")  # notebook magics, e.g. %pip install
    ]
    source = "\n".join(code)
    assert 'BASE = f"https://github.com/' in source
    source = re.sub(r"^BASE = .*$", f"BASE = {str(dist)!r}", source, flags=re.MULTILINE)
    namespace = {}
    exec(compile(source, "explore.ipynb", "exec"), namespace)
    assert len(namespace["awards"]) == 8


def test_next_tag_adds_a_suffix_for_later_releases_the_same_day(monkeypatch):
    taken = {"data-2026-10-04", "data-2026-10-04.2"}
    monkeypatch.setattr(release, "release_exists", lambda tag: tag in taken)
    assert release.next_tag("2026-10-04") == "data-2026-10-04.3"
    assert release.next_tag("2026-10-05") == "data-2026-10-05"


@pytest.mark.parametrize(
    ("returncode", "stderr", "expected"),
    [(0, "", True), (1, "release not found\n", False)],
)
def test_release_exists_reads_gh(monkeypatch, returncode, stderr, expected):
    done = subprocess.CompletedProcess([], returncode, stdout="", stderr=stderr)
    monkeypatch.setattr(release.subprocess, "run", lambda *a, **kw: done)
    assert release.release_exists("data-2026-10-04") is expected


def test_release_exists_fails_when_gh_cannot_answer(monkeypatch):
    done = subprocess.CompletedProcess([], 4, stdout="", stderr="gh auth login required\n")
    monkeypatch.setattr(release.subprocess, "run", lambda *a, **kw: done)
    with pytest.raises(SystemExit, match="can't check"):
        release.release_exists("data-2026-10-04")
