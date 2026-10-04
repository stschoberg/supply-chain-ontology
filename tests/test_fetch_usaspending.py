"""Offline tests for the USAspending fetcher: request building and the checks on what comes back."""

import csv
import io
import zipfile

import pytest

from data.sources.usaspending import fetch


def test_psc_path_accepts_groups_and_classes():
    assert fetch.psc_path("31") == ["Product", "31"]
    assert fetch.psc_path("3110") == ["Product", "31", "3110"]
    with pytest.raises(ValueError):
        fetch.psc_path("AC11")  # service codes aren't supported


def test_request_covers_the_federal_fiscal_year():
    body = fetch.request_body("31", 2025)
    assert body["filters"]["time_period"] == [
        {"start_date": "2024-10-01", "end_date": "2025-09-30"}
    ]


def test_check_echo_ignores_fields_the_server_adds():
    sent = fetch.request_body("31", 2025)["filters"]
    fetch.check_echo(sent, {**sent, "limit": 500000})


def test_check_echo_fails_when_the_server_drops_a_filter():
    # What /bulk_download/awards did with a PSC filter: accepted the request, echoed it without one.
    sent = fetch.request_body("31", 2025)["filters"]
    echoed = {k: v for k, v in sent.items() if k != "psc_codes"}
    with pytest.raises(fetch.FetchError, match="psc_codes"):
        fetch.check_echo(sent, echoed)


def make_zip(path, prime_columns, prime_rows=2, sub_rows=1):
    def table(columns, n):
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(columns)
        writer.writerows([["x"] * len(columns)] * n)
        return buf.getvalue()

    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("Contracts_PrimeAwardSummaries_1.csv", table(sorted(prime_columns), prime_rows))
        zf.writestr("Contracts_Subawards_1.csv", table(["subaward_number"], sub_rows))
    return path


def test_inspect_zip_counts_rows_per_file(tmp_path):
    path = make_zip(tmp_path / "ok.zip", fetch.REQUIRED_COLUMNS)
    members = fetch.inspect_zip(path, expected_rows=3)
    assert members["Contracts_PrimeAwardSummaries_1.csv"]["rows"] == 2
    assert members["Contracts_Subawards_1.csv"]["rows"] == 1


def test_inspect_zip_fails_on_row_count_mismatch(tmp_path):
    path = make_zip(tmp_path / "short.zip", fetch.REQUIRED_COLUMNS)
    with pytest.raises(fetch.FetchError, match="3 rows; the job reported 4"):
        fetch.inspect_zip(path, expected_rows=4)


def test_inspect_zip_fails_on_schema_drift(tmp_path):
    path = make_zip(tmp_path / "drift.zip", fetch.REQUIRED_COLUMNS - {"cage_code"})
    with pytest.raises(fetch.FetchError, match="cage_code"):
        fetch.inspect_zip(path, expected_rows=3)
