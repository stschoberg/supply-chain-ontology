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
    assert "awards.parquet" in first_upload and "catalog.duckdb" not in first_upload


def test_publish_refuses_an_existing_tag(dist, fake_github, monkeypatch):
    monkeypatch.setattr(release, "release_exists", lambda tag: True)
    with pytest.raises(SystemExit, match="already exists"):
        release.main(["publish", "--out", str(dist), "--allow-dirty"])
    assert fake_github == []
