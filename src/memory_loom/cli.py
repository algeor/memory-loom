from __future__ import annotations

import argparse
import json
from pathlib import Path

from memory_loom.contracts import (
    ContractValidationError,
    export_schema_catalog,
    validate_all_fixtures,
    validate_path,
    validate_schema_catalog,
)
from memory_loom.replay import replay_query_contexts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="memory-loom")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="validate one artifact")
    validate_parser.add_argument("path", type=Path)

    subparsers.add_parser("validate-all", help="validate every JSON fixture")
    subparsers.add_parser(
        "export-schemas", help="regenerate JSON Schemas from Pydantic models"
    )

    replay_parser = subparsers.add_parser(
        "replay", help="reconstruct all condition contexts for one query"
    )
    replay_parser.add_argument("scenario", type=Path)
    replay_parser.add_argument("condition_manifest", type=Path)
    replay_parser.add_argument("query_id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate":
            validate_path(args.path)
            print(f"valid: {args.path}")
        elif args.command == "validate-all":
            schemas = validate_schema_catalog()
            paths = validate_all_fixtures()
            print(f"valid: {len(schemas)} schemas and {len(paths)} fixture artifacts")
        elif args.command == "export-schemas":
            paths = export_schema_catalog()
            print(f"exported: {len(paths)} schemas")
        elif args.command == "replay":
            scenario = validate_path(args.scenario)
            condition_manifest = validate_path(args.condition_manifest)
            contexts = replay_query_contexts(
                scenario, condition_manifest, args.query_id
            )
            print(json.dumps([context.to_dict() for context in contexts], indent=2))
    except (ContractValidationError, ValueError) as error:
        print(f"error: {error}")
        return 1
    return 0
