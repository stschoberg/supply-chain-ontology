"""The dlms_synth source: synthetic DLMS-shaped tables generated for the example awards."""

import csv
from collections import Counter

import pytest

from data.sources.dlms_synth import generate as dlms
from sco import graph

EXAMPLE = graph.ROOT / "data" / "sources" / "dlms_synth" / "example"
INBOUND = ["due_ins", "shipment_notices", "acceptance_reports", "receipts", "discrepancy_reports"]
OUTBOUND = ["requisitions", "release_orders", "issues"]


def read(path):
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def awards():
    return {a["award_key"]: a for a in read(EXAMPLE / "awards.csv")}


@pytest.fixture(scope="module")
def tables():
    return {path.stem: read(path) for path in sorted((EXAMPLE / "tables").glob("*.csv"))}


def test_example_is_up_to_date_with_the_generator(awards, tables, tmp_path):
    dlms.write(dlms.tables(list(awards.values())), tmp_path)
    rebuilt = {path.stem: read(path) for path in sorted(tmp_path.glob("*.csv"))}
    assert rebuilt == tables, "run `make generate-dlms-synth` and commit"


def test_every_table_is_a_dlms_transaction_and_every_row_says_it_is_synthetic(tables):
    assert set(tables) - {"activities"} <= set(dlms.TABLES)
    assert {"due_ins", "shipment_notices", "receipts", "requisitions", "issues"} <= set(tables)
    for rows in tables.values():
        assert rows and all(row["synthetic"] == "true" for row in rows)


def test_inbound_records_name_a_real_award_and_outbound_ones_never_do(awards, tables):
    for table in INBOUND:
        for row in tables.get(table, []):
            assert row["award_key"] in awards and row["piid"] == awards[row["award_key"]]["piid"]
    for table in OUTBOUND:
        assert "award_key" not in tables[table][0], "stock on the shelf isn't tied to a purchase"


def test_records_refer_to_shipments_and_activities_that_exist(tables):
    shipped = {row["tcn"] for row in tables["shipment_notices"]}
    assert all(len(tcn) == 17 for tcn in shipped)
    for table in ("acceptance_reports", "receipts", "discrepancy_reports"):
        assert {row["tcn"] for row in tables.get(table, [])} <= shipped
    known = {row["activity_code"] for row in tables["activities"]}
    for rows in tables.values():
        for row in rows:
            named = {v for k, v in row.items() if k.endswith("activity") or k == "requisitioner"}
            assert named <= known


def test_things_happen_in_a_possible_order(awards, tables):
    shipment = {row["tcn"]: row for row in tables["shipment_notices"]}
    for row in tables["shipment_notices"]:
        assert row["ship_date"] >= awards[row["award_key"]]["performance_start_date"]
    for row in tables["receipts"]:
        assert row["receipt_date"] > shipment[row["tcn"]]["ship_date"]
    for row in tables["acceptance_reports"]:
        at_origin = shipment[row["tcn"]]["acceptance_point"] == "ORIGIN"
        assert (row["acceptance_date"] < shipment[row["tcn"]]["ship_date"]) == at_origin
    issued = {row["document_number"]: row for row in tables["issues"]}
    for row in tables["requisitions"]:
        assert len(row["document_number"]) == 14
        assert issued[row["document_number"]]["issue_date"] > row["requisition_date"]


def test_a_depot_never_issues_more_of_an_item_than_it_received(tables):
    def stock(rows, quantity):
        totals = Counter()
        for row in rows:
            totals[row["storage_activity"], row["nsn"] or row["psc"]] += int(row[quantity])
        return totals

    received = stock(tables["receipts"], "quantity_received")
    for shelf, quantity in stock(tables["issues"], "quantity_issued").items():
        assert quantity <= received[shelf], shelf
