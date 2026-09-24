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
from memory_loom.replay import replay_query_contexts, replay_query_contexts_live
from memory_loom.runner import NoModelAdapter, run_scenario


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
    replay_parser.add_argument(
        "--frozen-retrieval",
        action="store_true",
        help="use fixture retrieval decisions instead of running SQLite FTS",
    )

    run_parser = subparsers.add_parser(
        "run", help="execute all conditions for every query in a scenario"
    )
    run_parser.add_argument("scenario", type=Path)
    run_parser.add_argument("condition_manifest", type=Path)
    run_parser.add_argument("run_manifest", type=Path)
    run_parser.add_argument("--output", type=Path, required=True)
    run_parser.add_argument(
        "--frozen-retrieval",
        action="store_true",
        help="use fixture retrieval decisions instead of running SQLite FTS",
    )
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
            replay = (
                replay_query_contexts
                if args.frozen_retrieval
                else replay_query_contexts_live
            )
            contexts = replay(scenario, condition_manifest, args.query_id)
            print(json.dumps([context.to_dict() for context in contexts], indent=2))
        elif args.command == "run":
            artifact = run_scenario(
                validate_path(args.scenario),
                validate_path(args.condition_manifest),
                validate_path(args.run_manifest),
                NoModelAdapter(),
                frozen_retrieval=args.frozen_retrieval,
            )
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                artifact.model_dump_json(indent=2) + "\n", encoding="utf-8"
            )
            print(
                f"{artifact.status}: {len(artifact.results)} condition runs written "
                f"to {args.output}"
            )
    except (ContractValidationError, ValueError) as error:
        print(f"error: {error}")
        return 1
    return 0
