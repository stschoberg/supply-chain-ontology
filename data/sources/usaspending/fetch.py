"""Fetch DoD contract award summaries for a product/service code (PSC) group from USAspending.gov.

Usage: uv run python -m data.sources.usaspending.fetch [--psc 31] [--fy 2023 2024 2025] [--force]

For each fiscal year, this submits an async download job to /api/v2/download/awards, polls it,
and saves the zip unchanged to data/sources/usaspending/raw/<snapshot>/, next to a manifest
recording the request, the server's echo of it, checksums, and row counts. The CSVs are also
extracted to raw/<snapshot>/<stem>/ for DuckDB, which can't read inside zips. No API key is needed.

Don't use /api/v2/bulk_download/awards: it has no PSC filter and silently ignores one, exporting
everything.
"""

import argparse
import csv
import hashlib
import io
import shutil
import time
import zipfile
from datetime import UTC, date, datetime
from pathlib import Path

from sco import fetching, graph

API = "https://api.usaspending.gov/api/v2"
RAW_DIR = Path(__file__).parent / "raw"
LICENSE = "Public domain (U.S. Government work, 17 U.S.C. 105)"

AGENCY = {"type": "awarding", "tier": "toptier", "name": "Department of Defense"}
CONTRACT_TYPES = [
    "A",
    "B",
    "C",
    "D",
]  # BPA call, purchase order, delivery order, definitive contract

# Columns the staging step relies on. A missing one means USAspending changed its schema.
REQUIRED_COLUMNS = {
    "contract_award_unique_key",
    "award_id_piid",
    "parent_award_id_piid",
    "recipient_uei",
    "recipient_name",
    "recipient_parent_uei",
    "recipient_parent_name",
    "cage_code",
    "product_or_service_code",
    "prime_award_base_transaction_description",
    "total_obligated_amount",
    "award_base_action_date",
    "awarding_sub_agency_name",
    "extent_competed",
    "number_of_offers_received",
    "other_than_full_and_open_competition",
    "country_of_product_or_service_origin",
    "domestic_or_foreign_entity",
    "last_modified_date",
}
PRIME_FILE_PREFIX = "Contracts_PrimeAwardSummaries"


class FetchError(RuntimeError):
    pass


def psc_path(code: str) -> list[str]:
    """Path to a product PSC in USAspending's PSC tree: a 2-digit group or a 4-digit class."""
    if not (code.isdigit() and len(code) in (2, 4)):
        raise ValueError(f"expected a 2-digit product group or 4-digit class, got {code!r}")
    return ["Product", code[:2]] if len(code) == 2 else ["Product", code[:2], code]


def request_body(psc: str, fy: int) -> dict:
    return {
        "filters": {
            "agencies": [AGENCY],
            "award_type_codes": CONTRACT_TYPES,
            "psc_codes": {"require": [psc_path(psc)]},
            # Federal fiscal year N runs Oct 1 (N-1) to Sep 30 (N). Matches awards with any action
            # in that window, so a multi-year award appears in each year's file; staging dedupes.
            "time_period": [{"start_date": f"{fy - 1}-10-01", "end_date": f"{fy}-09-30"}],
        },
        "file_format": "csv",
    }


def check_echo(sent: dict, echoed: dict) -> None:
    """Fail if the server dropped or changed a filter we sent; it ignores unknown ones silently."""
    problems = [
        f"{key}: sent {value!r}, server used {echoed.get(key)!r}"
        for key, value in sent.items()
        if echoed.get(key) != value
    ]
    if problems:
        raise FetchError(
            "USAspending did not apply the request as sent:\n  " + "\n  ".join(problems)
        )


def wait_for(file_name: str, timeout: float = 1800) -> dict:
    """Poll a download job until it finishes. Returns the final status."""
    deadline, delay = time.monotonic() + timeout, 5
    while True:
        status = fetching.request_json(f"{API}/download/status?file_name={file_name}")
        if status["status"] == "finished":
            return status
        if status["status"] == "failed":
            raise FetchError(f"download job failed: {status.get('message')}")
        if time.monotonic() > deadline:
            raise FetchError(f"download job still {status['status']!r} after {timeout:.0f}s")
        print(f"    {status['status']} ({float(status['seconds_elapsed']):.0f}s)", end="\r")
        time.sleep(delay)
        delay = min(delay * 1.5, 30)


def inspect_zip(path: Path, expected_rows: int) -> dict[str, dict]:
    """Count rows per CSV and check them against the job status and REQUIRED_COLUMNS."""
    members = {}
    with zipfile.ZipFile(path) as zf:
        for name in sorted(zf.namelist()):
            with zf.open(name) as raw:
                reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline=""))
                header = next(reader, [])
                rows = sum(1 for _ in reader)
            with zf.open(name) as raw:
                digest = hashlib.file_digest(raw, "sha256").hexdigest()
            members[name] = {"rows": rows, "columns": len(header), "sha256": digest}
            if name.startswith(PRIME_FILE_PREFIX):
                if missing := REQUIRED_COLUMNS - set(header):
                    raise FetchError(f"{name} is missing columns: {sorted(missing)}")
    if not any(name.startswith(PRIME_FILE_PREFIX) for name in members):
        raise FetchError(f"no {PRIME_FILE_PREFIX}*.csv in {path.name}: {sorted(members)}")
    if (total := sum(m["rows"] for m in members.values())) != expected_rows:
        raise FetchError(f"{path.name} has {total} rows; the job reported {expected_rows}")
    return members


def extract(zip_path: Path, dest: Path, replace: bool = False) -> None:
    """Unzip the CSVs into `dest`, unless already there."""
    if replace:
        shutil.rmtree(dest, ignore_errors=True)
    if not dest.exists():
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(dest)


def fetch_year(psc: str, fy: int, snapshot_dir: Path, force: bool) -> None:
    stem = f"dod-psc{psc}-fy{fy}"
    zip_path, manifest_path = snapshot_dir / f"{stem}.zip", snapshot_dir / f"{stem}.manifest.json"
    if manifest_path.exists() and not force:
        print(f"  {stem}: already fetched; use --force to refetch")
        extract(zip_path, snapshot_dir / stem)
        return

    print(f"  {stem}: submitting")
    body = request_body(psc, fy)
    job = fetching.request_json(f"{API}/download/awards/", body)
    check_echo(body["filters"], job["download_request"]["filters"])
    status = wait_for(job["file_name"])
    print(f"  {stem}: {status['total_rows']} rows ready, downloading")
    fetching.download(job["file_url"], zip_path)
    members = inspect_zip(zip_path, status["total_rows"])

    fetching.write_manifest(
        manifest_path,
        {
            "source": "USAspending.gov",
            "license": LICENSE,
            "endpoint": f"{API}/download/awards/",
            "request": body,
            "echoed_request": job["download_request"],
            "file_url": job["file_url"],
            "retrieved_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "job_status": {k: status[k] for k in ("total_rows", "total_columns", "total_size")},
            "file": zip_path.name,
            "sha256": fetching.sha256(zip_path),
            "members": members,
        },
    )
    extract(zip_path, snapshot_dir / stem, replace=True)
    print(f"  {stem}: wrote {zip_path.relative_to(graph.ROOT)}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--psc", default="31", help="product PSC group or class (31 = bearings)")
    parser.add_argument(
        "--fy", type=int, nargs="+", default=[2023, 2024, 2025], help="fiscal years"
    )
    parser.add_argument(
        "--snapshot", default=date.today().isoformat(), help="snapshot directory name"
    )
    parser.add_argument("--force", action="store_true", help="refetch files that already exist")
    args = parser.parse_args(argv)

    snapshot_dir = RAW_DIR / args.snapshot
    print(f"USAspending: DoD awards, PSC {args.psc}, FY{', FY'.join(map(str, args.fy))}")
    for fy in args.fy:
        fetch_year(args.psc, fy, snapshot_dir, args.force)


if __name__ == "__main__":
    try:
        main()
    except FetchError as e:
        raise SystemExit(f"error: {e}") from e
