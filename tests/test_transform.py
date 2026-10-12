"""Build the dbt project against small committed fixtures, so transforms run without network."""

import json

import duckdb
import pytest
from dbt.cli.main import dbtRunner

from sco import graph

TRANSFORM_DIR = graph.ROOT / "data" / "transform"
FIXTURES = graph.ROOT / "tests" / "fixtures"


@pytest.fixture(scope="module")
def warehouse(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("warehouse")
    path = tmp / "warehouse.duckdb"
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("SCO_WAREHOUSE", str(path))
        result = dbtRunner().invoke(
            [
                "build",
                "--quiet",
                "--project-dir", str(TRANSFORM_DIR),
                "--profiles-dir", str(TRANSFORM_DIR),
                "--target-path", str(tmp / "target"),
                "--log-path", str(tmp / "logs"),
                "--vars", json.dumps({"usaspending_snapshot": str(FIXTURES / "usaspending")}),
            ]
        )  # fmt: skip
    assert result.success, result.exception or [r.message for r in result.result or []]
    with duckdb.connect(str(path)) as con:  # same config as dbt's still-open connection
        yield con


def awards(con, *columns):
    rows = con.sql(f"select piid, {', '.join(columns)} from stg_usaspending__awards").fetchall()
    return {piid: values[0] if len(values) == 1 else tuple(values) for piid, *values in rows}


def test_awards_are_deduplicated_across_fiscal_year_files(warehouse):
    # 11 fixture rows; three awards appear in both the FY2023 and FY2024 files.
    assert len(awards(warehouse, "award_key")) == 8


def test_nsn_is_extracted_in_each_format_seen(warehouse):
    nsn = awards(warehouse, "nsn")
    assert nsn["SPRTA123P0105"] == "3110009898923"  # "NSN: 3110-00-989-8923 P/N:..."
    assert nsn["SPE4A121P0654"] == "3120001305324"  # "3120001305324 BEARING,SLEEVE"
    assert nsn["FA820323P0025"] == "3120015096267"  # "... NSN: 3120015096267LE"
    assert nsn["SPMYM123P0797"] is None  # "N4215830672984" is a document number


def test_dla_descriptions_split_into_reference_number_and_item_name(warehouse):
    split = awards(warehouse, "dla_reference_number", "item_name", "nsn")
    assert split["SPE4A022P0831"] == ("8509067712", "BEARING,SLEEVE", None)


def test_places_and_dates_are_typed(warehouse):
    place = awards(
        warehouse, "recipient_city", "recipient_state", "recipient_country",
        "place_of_performance_city", "place_of_manufacture", "recipient_is_manufacturer",
    )  # fmt: skip
    assert place["SPE4A121P0654"] == (
        "HOUSTON", "TX", "UNITED STATES", "HOUSTON", "MFG IN U.S.", True
    )  # fmt: skip
    window = awards(warehouse, "performance_start_date", "performance_end_date")["SPE4A121P0654"]
    assert tuple(map(str, window)) == ("2021-03-19", "2021-09-30")
    windows = awards(warehouse, "performance_start_date", "performance_end_date")
    assert all(first <= last for first, last in windows.values())


def test_entities_are_one_per_uei_across_recipients_and_parents(warehouse):
    entities = dict(warehouse.sql("select uei, name from entities").fetchall())
    assert len(entities) == 11  # 8 recipients, 3 of them with a different corporate parent
    assert entities["ZBR7R1G1MGB3"] == "THE TIMKEN CORPORATION"  # a recipient
    assert entities["H4FZBFXLJ636"] == "THE TIMKEN COMPANY"  # its parent, never a recipient here


# ---------------------------------------------------------------- dlms_synth, the generated source

DLMS_INBOUND = ["due_ins", "shipment_notices", "acceptance_reports", "receipts"]
DLMS_OUTBOUND = ["requisitions", "release_orders", "issues"]


def columns(con, table):
    return {row[0] for row in con.sql(f"describe {table}").fetchall()}


def test_synthetic_tables_say_so_in_every_row(warehouse):
    for table in [*DLMS_INBOUND, *DLMS_OUTBOUND, "discrepancy_reports", "activities"]:
        total, flagged = warehouse.sql(
            f"select count(*), count(*) filter (synthetic) from dlms_synth__{table}"
        ).fetchone()
        assert total == flagged, table
    assert warehouse.sql("select count(*) from dlms_synth__receipts").fetchone()[0] >= 8


def test_only_awards_that_bought_something_get_synthetic_records(warehouse):
    bought = warehouse.sql(
        "select count(*) from stg_usaspending__awards where total_obligated_amount > 0"
    ).fetchone()[0]
    assert warehouse.sql("select count(*) from dlms_synth__due_ins").fetchone()[0] == bought


def test_inbound_records_name_an_award_and_outbound_ones_never_do(warehouse):
    for table in DLMS_INBOUND:
        assert "award_key" in columns(warehouse, f"dlms_synth__{table}")
    for table in DLMS_OUTBOUND:
        # Stock on the shelf isn't tied to the purchase that put it there.
        assert not {"award_key", "piid"} & columns(warehouse, f"dlms_synth__{table}")


def test_synthetic_events_happen_in_a_possible_order(warehouse):
    impossible = warehouse.sql("""
        select count(*)
        from dlms_synth__shipment_notices s
        join stg_usaspending__awards a using (award_key)
        join dlms_synth__receipts r using (tcn)
        join dlms_synth__acceptance_reports c using (tcn)
        where s.ship_date < a.performance_start_date
           or r.receipt_date <= s.ship_date
           or (c.acceptance_date < s.ship_date) != (s.acceptance_point = 'ORIGIN')
           or r.quantity_received > s.quantity_shipped
    """).fetchone()[0]
    assert impossible == 0
    out_of_order = warehouse.sql("""
        select count(*)
        from dlms_synth__requisitions q
        join dlms_synth__release_orders o using (document_number)
        join dlms_synth__issues i using (document_number)
        where o.release_date <= q.requisition_date or i.issue_date < o.release_date
    """).fetchone()[0]
    assert out_of_order == 0


def test_a_depot_never_issues_more_of_an_item_than_it_received(warehouse):
    overdrawn = warehouse.sql("""
        with received as (
            select storage_activity, coalesce(nsn, psc) as item, sum(quantity_received) as quantity
            from dlms_synth__receipts group by all
        ), issued as (
            select storage_activity, coalesce(nsn, psc) as item, sum(quantity_issued) as quantity
            from dlms_synth__issues group by all
        )
        select count(*) from issued left join received using (storage_activity, item)
        where received.quantity is null or issued.quantity > received.quantity
    """).fetchone()[0]
    assert overdrawn == 0


def test_identifiers_have_the_dod_shapes(warehouse):
    shapes = warehouse.sql("""
        select
            (select bool_and(length(tcn) = 17) from dlms_synth__shipment_notices),
            (select bool_and(length(document_number) = 14) from dlms_synth__requisitions),
            (select bool_and(length(activity_code) = 6 and activity_code like 'Z%')
             from dlms_synth__activities)
    """).fetchone()
    assert shapes == (True, True, True)
