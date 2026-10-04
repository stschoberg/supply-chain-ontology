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
