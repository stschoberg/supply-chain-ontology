"""Check the hand-written fuel records in data/mappings/fuel_records/tables/ agree with each other.

The records are invented, so nothing else checks them: these tests stand in for the consistency a
real system of record would enforce.
"""

import csv
from collections import defaultdict

import pytest

from sco import graph

TABLES_DIR = graph.ROOT / "data" / "mappings" / "fuel_records" / "tables"
TABLES = sorted(TABLES_DIR.glob("*.csv"))
# (table, column) -> (table, column) it refers to.
FOREIGN_KEYS = {
    ("tanks", "dfsp"): ("activities", "code"),
    ("appointments", "dfsp"): ("activities", "code"),
    ("account_transfers", "dfsp"): ("activities", "code"),
    ("account_transfers", "outgoing"): ("appointments", "person"),
    ("account_transfers", "incoming"): ("appointments", "person"),
    ("account_transfers", "tank"): ("tanks", "tank"),
    ("certificates", "issuer"): ("activities", "code"),
    ("certificates", "sample"): ("samples", "sample_number"),
    ("certificate_sources", "certificate"): ("certificates", "certificate"),
    ("certificate_sources", "source_batch"): ("certificates", "batch_number"),
    ("shipments", "ship_from"): ("activities", "code"),
    ("shipments", "ship_from_tank"): ("tanks", "tank"),
    ("shipments", "ship_to"): ("activities", "code"),
    ("shipments", "certificate"): ("certificates", "certificate"),
    ("receipts", "shipment"): ("shipments", "document_number"),
    ("receipts", "tank"): ("tanks", "tank"),
    ("additive_injections", "tank"): ("tanks", "tank"),
    ("grade_changes", "tank"): ("tanks", "tank"),
    ("grade_changes", "sample"): ("samples", "sample_number"),
    ("grade_changes", "approved_by"): ("activities", "code"),
    ("samples", "taken_by"): ("appointments", "person"),
    ("samples", "laboratory"): ("activities", "code"),
    ("test_results", "sample_number"): ("samples", "sample_number"),
    ("ledger_transactions", "dfsp"): ("activities", "code"),
    ("ledger_transactions", "reverses"): ("ledger_transactions", "entry"),
    ("sales", "tank"): ("tanks", "tank"),
    ("sales", "customer"): ("activities", "code"),
}
# Ledger entry types that add to, and take from, a grade's book inventory (DoDM 4140.25 Vol. 9 G.2).
INCREASES = {"receipt", "regrade in"}
DECREASES = {"shipment", "sale", "regrade out"}


def read(name: str) -> list[dict]:
    with open(TABLES_DIR / f"{name}.csv", newline="") as f:
        return list(csv.DictReader(f))


def book(dfsp: str, grade: str, on: str) -> int:
    """Book inventory of one grade at one DFSP at the end of a day, starting from zero."""
    entries = {e["entry"]: e for e in read("ledger_transactions")}
    reversed_ = {e["reverses"] for e in entries.values() if e["reverses"]}
    total = 0
    for e in entries.values():
        if (
            (e["dfsp"], e["grade"]) != (dfsp, grade)
            or e["transaction_date"] > on
            or e["entry"] in reversed_
        ):
            continue
        if e["type"] in INCREASES:
            total += int(e["gallons"])
        elif e["type"] in DECREASES:
            total -= int(e["gallons"])
    return total


@pytest.mark.parametrize("path", TABLES, ids=[p.stem for p in TABLES])
def test_every_row_is_synthetic_and_cites_its_source(path):
    rows = read(path.stem)
    assert rows, f"{path.name} is empty"
    for row in rows:
        assert row["synthetic"] == "true", f"{path.name}: {row}"
        assert row["follows"].strip(), f"{path.name}: a row cites no manual section: {row}"


@pytest.mark.parametrize(
    ("ref", "target"), FOREIGN_KEYS.items(), ids=[f"{t}.{c}" for t, c in FOREIGN_KEYS]
)
def test_foreign_keys_resolve(ref, target):
    (table, column), (target_table, target_column) = ref, target
    known = {row[target_column] for row in read(target_table)}
    missing = {row[column] for row in read(table) if row[column] and row[column] not in known}
    assert not missing, f"{table}.{column} not in {target_table}.{target_column}: {sorted(missing)}"


def test_receipt_variance_is_against_the_shipped_net_quantity():
    shipped = {s["document_number"]: int(s["net_gallons"]) for s in read("shipments")}
    for r in read("receipts"):
        expected = round(
            100 * (int(r["net_gallons"]) - shipped[r["shipment"]]) / shipped[r["shipment"]], 3
        )
        assert float(r["variance_pct"]) == expected, r["receipt"]
        assert int(r["closing_net_gallons"]) - int(r["opening_net_gallons"]) == int(
            r["net_gallons"]
        )


def test_receipt_variance_is_within_tolerance():
    # Vol. 12 §5.3.d: research variations over 0.5 percent. The story has none.
    assert all(abs(float(r["variance_pct"])) <= 0.5 for r in read("receipts"))


def test_dd_2920_totals_match_the_book_inventory():
    by_grade = defaultdict(int)
    for row in read("account_transfers"):
        by_grade[(row["dfsp"], row["grade"], row["transfer_date"])] += int(row["net_gallons"])
    for (dfsp, grade, on), gallons in by_grade.items():
        assert book(dfsp, grade, on) == gallons


def test_every_grade_change_has_its_regrade_entries():
    entries = read("ledger_transactions")
    for change in read("grade_changes"):
        types = {(e["grade"], e["type"]) for e in entries if e["document"] == change["change"]}
        assert types == {(change["grade_from"], "regrade out"), (change["grade_to"], "regrade in")}


def test_regrade_and_downgrade_turn_on_the_same_test():
    # The regrade and the downgrade go from JP-5 to JP-8. What separates them is whether the product
    # met its own specification, which only the sample's flash point result records.
    changes = {c["kind"]: c for c in read("grade_changes")}
    results = {
        r["sample_number"]: r for r in read("test_results") if r["property"] == "flash point"
    }
    regrade, downgrade = changes["regrade"], changes["downgrade"]
    assert (regrade["grade_from"], regrade["grade_to"]) == (
        downgrade["grade_from"],
        downgrade["grade_to"],
    )
    assert results[regrade["sample"]]["meets_spec"] == "true"
    assert results[downgrade["sample"]]["meets_spec"] == "false"
