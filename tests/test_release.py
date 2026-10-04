"""Build a data release from the committed fixtures and read it back through its catalog."""

import json
import re

import duckdb
import pytest

from data import release
from sco import graph

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
        "stg_usaspending__awards.parquet",
        "stg_usaspending__awards.csv",
        "meta_build.parquet",
        "meta_build.csv",
        "meta_source_files.parquet",
        "meta_source_files.csv",
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
