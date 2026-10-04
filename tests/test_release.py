"""Build a data release from the committed fixtures and read it back through its catalog."""

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
    assert {"awards.parquet", "meta_build.parquet", "meta_source_files.parquet"} <= names
    assert {
        "catalog.duckdb",
        "RELEASE_NOTES.md",
        "SHA256SUMS",
        "raw-usaspending-usaspending.tar",
    } <= names
    assert "stg_usaspending__awards.parquet" not in names  # staging is internal, not published


def test_catalog_reads_the_parquet_files(dist, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # the catalog must not depend on the working directory
    with duckdb.connect() as con:
        con.sql(f"attach '{dist / 'catalog.duckdb'}' as sco (read_only)")
        assert con.sql("select count(*) from sco.awards").fetchone()[0] == 8
        assert con.sql("select release_tag from sco.meta_build").fetchone()[0] == "data-test"


def test_checksums_cover_every_other_file(dist):
    listed = {line.split()[1] for line in (dist / "SHA256SUMS").read_text().splitlines()}
    assert listed == {p.name for p in dist.iterdir()} - {"SHA256SUMS"}
