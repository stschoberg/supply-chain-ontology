"""Command-line entry point: `uv run sco --help`."""

from __future__ import annotations

import argparse
import sys

from sco import graph


def cmd_query(args: argparse.Namespace) -> int:
    g = graph.reasoned_scenario(args.scenario)
    result = graph.run_cq(g, args.cq)
    print(result.serialize(format="csv").decode())
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    rc = 0
    for name in args.scenarios or graph.scenario_names():
        conforms, text = graph.validate(graph.load_scenario(name))
        print(f"{name}: {'OK' if conforms else 'FAIL'}")
        if not conforms:
            print(text)
            rc = 1
    return rc


def cmd_list(_: argparse.Namespace) -> int:
    print("Competency questions:", ", ".join(graph.cq_ids()))
    print("Scenarios:", ", ".join(graph.scenario_names()))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="sco", description="Supply Chain Ontology tools")
    sub = parser.add_subparsers(required=True)

    p = sub.add_parser("query", help="run a competency question against a reasoned scenario")
    p.add_argument("cq", help="e.g. CQ-001")
    p.add_argument("--scenario", "-s", default="s01-single-source")
    p.set_defaults(func=cmd_query)

    p = sub.add_parser("validate", help="SHACL-validate scenarios")
    p.add_argument("scenarios", nargs="*")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("list", help="list CQs and scenarios")
    p.set_defaults(func=cmd_list)

    args = parser.parse_args()
    sys.exit(args.func(args))
