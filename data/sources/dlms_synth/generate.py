"""Generate the dlms_synth source: synthetic DoD logistics records for real awards.

One table per kind of DLMS transaction. Where other sources fetch, this one generates.

Usage:
  uv run python -m data.sources.dlms_synth.generate AWARDS.csv OUT_DIR   # make generate-dlms-synth

USAspending says who agreed to supply what, from where, by when. It has no shipments. This invents
what would follow an award, so the parts of a supply chain ontology that awards can't reach have
something to describe. EVERYTHING HERE BEYOND THE AWARD IS MADE UP. The suppliers, agencies,
contracts, places of performance, and contract dates are real; every record below is invented,
says so in its `synthetic` column, and is never mixed into the real tables or graphs.

The concepts are the DoD's, not ours. Each table is one transaction of the Defense Logistics
Management Standards (DLMS), and the tables follow three end-to-end processes of the DoD Business
Enterprise Architecture. See TABLES and the README. Only the transactions' concepts and main data
elements are followed, not the implementation conventions segment by segment.

Nothing is random at run time. Every invented value is derived from a hash of the award's key, so
the same awards always give the same tables.
"""

import argparse
import csv
import hashlib
from datetime import date, timedelta
from pathlib import Path

DCMA = "Defense Contract Management Agency"
# DLA's two primary distribution centers. Awards are sent to the nearer coast.
DEPOTS = {"east": "DLA Distribution Susquehanna", "west": "DLA Distribution San Joaquin"}
WESTERN_STATES = set("AK AZ CA CO HI ID MT NM NV OR UT WA WY".split())
# table -> (DLMS implementation convention, its title, end-to-end process, step in that process)
TABLES = {
    "due_ins": (
        "527D", "Pre-positioned Materiel Receipt (PMR) and Due-in Actions",
        "Plan-to-Stock", "Determine Source",
    ),
    "shipment_notices": (
        "856P", "Procurement Advance Shipment Notice (ASN)",
        "Procure-to-Pay", "Perform Receipt, Acceptance, and Return",
    ),
    "acceptance_reports": (
        "861P", "Procurement Acceptance Report",
        "Procure-to-Pay", "Perform Receipt, Acceptance, and Return",
    ),
    "receipts": (
        "527R", "Physical Receipt and Materiel Receipt Acknowledgement (MRA)",
        "Plan-to-Stock", "Receive, Accept and Warehouse Inventory",
    ),
    "discrepancy_reports": (
        "842A/W", "Standard Supply Discrepancy Report (SDR) Notifications",
        "Procure-to-Pay", "Perform Receipt, Acceptance, and Return",
    ),
    "requisitions": ("511R", "Requisition", "Order-to-Cash", "Accept Orders"),
    "release_orders": ("940R", "Materiel Release Order (MRO)", "Order-to-Cash", "Fulfill Orders"),
    "issues": ("867I", "Issue", "Order-to-Cash", "Fulfill Orders"),
}  # fmt: skip


def draw(award_key: str, purpose: str) -> float:
    """A number in [0, 1) that depends only on the award and what it is for."""
    digest = hashlib.sha256(f"{award_key}/{purpose}".encode()).digest()
    return int.from_bytes(digest[:8]) / 2**64


def code(text: str, length: int) -> str:
    """An identifier-shaped string of letters and digits that depends only on `text`."""
    alphabet = "0123456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    number = int.from_bytes(hashlib.sha256(text.encode()).digest()[:8])
    return "".join(alphabet[(number // len(alphabet) ** i) % len(alphabet)] for i in range(length))


def activity_code(name: str) -> str:
    """A code shaped like a DoD Activity Address Code (six characters). The real ones are not
    used: these start with Z and are derived from the activity's name."""
    return "Z" + code(name, 5)


def document_number(activity: str, day: date, serial: str) -> str:
    """Shaped like a MILSTRIP document number: activity code, year digit and day of year, serial."""
    return f"{activity}{day.year % 10}{day.timetuple().tm_yday:03d}{serial}"


def records(award: dict) -> dict[str, list[dict]]:
    """The invented records that follow one real award: its inbound shipments, then one
    requisition against the stock they put on the shelf."""
    key = award["award_key"]
    start = date.fromisoformat(award["performance_start_date"])
    due = date.fromisoformat(award["performance_end_date"])
    coast = "west" if (award["place_of_performance_state"] or "") in WESTERN_STATES else "east"
    depot = activity_code(DEPOTS[coast])
    customer = activity_code(award["awarding_sub_agency"])
    at_origin = draw(key, "inspection point") < 0.35
    # An invented unit price turns the real obligated amount into an invented quantity.
    unit_price = 25 + draw(key, "unit price") * 1975
    ordered = max(1, round(abs(float(award["total_obligated_amount"])) / unit_price))
    count = 2 if ordered > 1 and draw(key, "split") < 0.4 else 1
    # What every record about this purchase repeats: the real contract and the item it buys.
    line = {"award_key": key, "piid": award["piid"], "clin": "0001"}
    item = {"nsn": award["nsn"], "psc": award["psc"], "unit_of_issue": "EA"}
    made = {table: [] for table in TABLES}

    made["due_ins"].append(
        {**line, **item, "storage_activity": depot, "supplier_cage": award["cage_code"],
         "quantity_due": ordered, "estimated_delivery_date": due}
    )  # fmt: skip
    stocked, last_receipt = 0, start
    for n in range(1, count + 1):
        part = f"shipment {n}"
        shipped_units = ordered // count + (ordered % count if n == 1 else 0)
        # Ships between halfway through the period of performance and a tenth past its end.
        shipped = start + timedelta(days=round((due - start).days * (0.5 + draw(key, part) * 0.6)))
        received = shipped + timedelta(days=2 + round(draw(key, f"{part} transit") * 7))
        short = shipped_units > 1 and draw(key, f"{part} short") < 0.1
        received_units = shipped_units - (max(1, shipped_units // 10) if short else 0)
        # Transportation control number: 17 characters, built on the shipper's document number.
        tcn = document_number(activity_code(award["cage_code"]), shipped, code(f"{key}/{n}", 4))
        tcn += "XXX"
        made["shipment_notices"].append(
            {**line, "shipment_number": n, "tcn": tcn, "supplier_cage": award["cage_code"],
             "ship_from_city": award["place_of_performance_city"] or award["recipient_city"],
             "ship_from_country": award["place_of_performance_country"]
             or award["recipient_country"],
             "ship_to_activity": depot, "quantity_shipped": shipped_units, "ship_date": shipped,
             "acceptance_point": "ORIGIN" if at_origin else "DESTINATION"}
        )  # fmt: skip
        # Acceptance is the government taking title: by DCMA before shipment, or at the depot.
        made["acceptance_reports"].append(
            {**line, "tcn": tcn,
             "accepting_activity": activity_code(DCMA) if at_origin else depot,
             "quantity_accepted": shipped_units if at_origin else received_units,
             "acceptance_date": shipped - timedelta(days=1) if at_origin
             else received + timedelta(days=1 + round(draw(key, f"{part} accept") * 4))}
        )  # fmt: skip
        made["receipts"].append(
            {**line, **item, "tcn": tcn, "storage_activity": depot,
             "quantity_received": received_units, "receipt_date": received,
             # A: serviceable, issuable without qualification.
             "supply_condition_code": "A"}
        )  # fmt: skip
        if short:
            made["discrepancy_reports"].append(
                {**line, "tcn": tcn, "reporting_activity": depot,
                 "report_date": received + timedelta(days=1), "discrepancy": "SHORTAGE",
                 "quantity_shipped": shipped_units, "quantity_received": received_units}
            )  # fmt: skip
        stocked, last_receipt = stocked + received_units, max(last_receipt, received)

    # Later, the customer draws on that stock. A requisition names an item and a quantity, never
    # the award that bought it: once on the shelf, units from different purchases are one stock.
    requested = last_receipt + timedelta(days=10 + round(draw(key, "requisition") * 80))
    wanted = max(1, round(stocked * (0.2 + draw(key, "requisition quantity") * 0.6)))
    number = document_number(customer, requested, code(f"{key}/requisition", 4))
    order = {"document_number": number, **item}
    made["requisitions"].append(
        {**order, "requisitioner": customer, "quantity_requisitioned": wanted,
         "requisition_date": requested, "priority": f"{1 + round(draw(key, 'priority') * 14):02d}"}
    )  # fmt: skip
    released = requested + timedelta(days=1 + round(draw(key, "release") * 3))
    made["release_orders"].append(
        {**order, "storage_activity": depot, "ship_to_activity": customer,
         "quantity_to_release": wanted, "release_date": released}
    )  # fmt: skip
    made["issues"].append(
        {**order, "storage_activity": depot, "quantity_issued": wanted,
         "issue_date": released + timedelta(days=round(draw(key, "issue") * 2)),
         "supply_condition_code": "A"}
    )  # fmt: skip
    return made


def activities(awards: list[dict]) -> list[dict]:
    """The DoD activities the records refer to. Their names are real; their codes are invented."""
    names = {*DEPOTS.values(), DCMA, *(award["awarding_sub_agency"] for award in awards)}
    return [{"activity_code": activity_code(name), "name": name} for name in sorted(names)]


def tables(awards: list[dict]) -> dict[str, list[dict]]:
    made = {"activities": activities(awards), **{table: [] for table in TABLES}}
    for award in sorted(awards, key=lambda a: a["award_key"]):
        for table, rows in records(award).items():
            made[table].extend(rows)
    return {table: [{**row, "synthetic": "true"} for row in rows] for table, rows in made.items()}


def write(made: dict[str, list[dict]], out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for stale in out.glob("*.csv"):
        stale.unlink()
    for table, rows in made.items():
        if not rows:
            continue  # e.g. no shipment was short, so there are no discrepancy reports
        with (out / f"{table}.csv").open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("awards", type=Path, help="rows of stg_usaspending__awards, as CSV")
    parser.add_argument("out", type=Path, help="directory to write one CSV per table into")
    args = parser.parse_args(argv)
    with args.awards.open(newline="") as fh:
        awards = list(csv.DictReader(fh))
    made = tables(awards)
    write(made, args.out)
    for table, rows in made.items():
        print(f"  {table:20} {len(rows):>4} synthetic rows")


if __name__ == "__main__":
    main()
