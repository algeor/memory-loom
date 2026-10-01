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
from memory_loom.onboarding import onboard_host
from memory_loom.replay import replay_query_contexts, replay_query_contexts_live
from memory_loom.retrieval_evaluation import evaluate_retrieval, threshold_failures
from memory_loom.runner import NoModelAdapter, run_scenario
from memory_loom.store import MemoryStore


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

    onboard_parser = subparsers.add_parser(
        "onboard",
        help="register Memory Loom with a supported MCP host",
    )
    onboard_parser.add_argument("host", choices=("codex", "claude"))
    onboard_parser.add_argument("--project-root", type=Path, default=Path.cwd())
    onboard_parser.add_argument("--user-id", default="default")
    onboard_parser.add_argument("--project-id")
    onboard_parser.add_argument(
        "--database",
        type=Path,
        default=Path("memory-loom.db"),
    )
    onboard_parser.add_argument("--server-command", type=Path)
    onboard_parser.add_argument(
        "--replace",
        action="store_true",
        help="replace an existing Memory Loom host registration",
    )
    onboard_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the registration plan without changing files or host config",
    )

    migrate_parser = subparsers.add_parser(
        "migrate",
        help="upgrade a SQLite database with an automatic pre-migration backup",
    )
    migrate_parser.add_argument(
        "--database",
        type=Path,
        default=Path("memory-loom.db"),
    )

    evaluation_parser = subparsers.add_parser(
        "evaluate-retrieval",
        help="evaluate lexical retrieval against frozen scenario labels",
    )
    evaluation_parser.add_argument("scenarios", type=Path)
    evaluation_parser.add_argument(
        "--condition-manifest",
        type=Path,
        default=Path("fixtures/manifests/v1/default-conditions.json"),
    )
    evaluation_parser.add_argument("--output", type=Path, required=True)
    evaluation_parser.add_argument("--limit", type=int, default=5)
    evaluation_parser.add_argument("--min-recall-at-k", type=float)
    evaluation_parser.add_argument("--min-mrr", type=float)
    evaluation_parser.add_argument("--max-no-memory-fpr", type=float)
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
        elif args.command == "onboard":
            result = onboard_host(
                args.host,
                project_root=args.project_root,
                user_id=args.user_id,
                project_id=args.project_id,
                database_path=args.database,
                server_command=args.server_command,
                replace=args.replace,
                dry_run=args.dry_run,
            )
            print(f"onboarded: {result.host} ({result.registration})")
            print(f"database: {result.database_path}")
            print(f"instructions: {result.instruction_path}")
            if result.registration == "dry-run":
                print(f"command: {' '.join(result.add_command)}")
            else:
                print("restart the host, then inspect its MCP tools")
        elif args.command == "migrate":
            database_path = args.database.expanduser().resolve()
            with MemoryStore(database_path) as store:
                print(f"ready: {database_path} (schema {store.schema_version})")
                if store.last_backup_path is not None:
                    print(f"backup: {store.last_backup_path}")
                else:
                    print("backup: not needed")
        elif args.command == "evaluate-retrieval":
            artifact = evaluate_retrieval(
                args.scenarios,
                args.condition_manifest,
                limit=args.limit,
            )
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                artifact.model_dump_json(indent=2) + "\n",
                encoding="utf-8",
            )
            metrics = artifact.metrics
            print(
                f"evaluated: {metrics.total_queries} queries; "
                f"recall@{artifact.limit}={_format_metric(metrics.recall_at_k)}; "
                f"MRR={_format_metric(metrics.mean_reciprocal_rank)}; "
                "no-memory FPR="
                f"{_format_metric(metrics.no_memory_false_positive_rate)}; "
                f"forbidden hits={metrics.forbidden_hit_count}"
            )
            failures = threshold_failures(
                artifact,
                min_recall_at_k=args.min_recall_at_k,
                min_mrr=args.min_mrr,
                max_no_memory_false_positive_rate=args.max_no_memory_fpr,
            )
            if failures:
                for failure in failures:
                    print(f"failure: {failure}")
                return 1
    except (ContractValidationError, ValueError) as error:
        print(f"error: {error}")
        return 1
    return 0


def _format_metric(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.4f}"
