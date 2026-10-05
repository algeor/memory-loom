from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from memory_loom import __version__
from memory_loom.blinded_evaluation import (
    analyze_pilot,
    create_blinded_review,
    render_pilot_report,
)
from memory_loom.claude_provider import ClaudeCliAdapter
from memory_loom.contracts import (
    ContractValidationError,
    export_schema_catalog,
    load_json,
    validate_all_fixtures,
    validate_path,
    validate_schema_catalog,
)
from memory_loom.maintenance import backup_database, diagnose, restore_database
from memory_loom.model_reviewer import review_packet_with_model
from memory_loom.json_stdio import serve_json_lines
from memory_loom.onboarding import onboard_host
from memory_loom.openai_provider import OpenAIResponsesAdapter
from memory_loom.replay import replay_query_contexts, replay_query_contexts_live
from memory_loom.retrieval_evaluation import evaluate_retrieval, threshold_failures
from memory_loom.runner import NoModelAdapter, run_scenario
from memory_loom.store import MemoryStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="memory-loom")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="validate one artifact")
    validate_parser.add_argument("path", type=Path)

    subparsers.add_parser("validate-all", help="validate every JSON fixture")
    subparsers.add_parser(
        "export-schemas", help="regenerate JSON Schemas from Pydantic models"
    )
    subparsers.add_parser(
        "json-stdio",
        help="serve the memory lifecycle as newline-delimited JSON",
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

    study_parser = subparsers.add_parser(
        "run-study",
        help="run a scenario set through a configured model provider",
    )
    study_parser.add_argument("scenarios", type=Path)
    study_parser.add_argument("condition_manifest", type=Path)
    study_parser.add_argument("run_manifest", type=Path)
    study_parser.add_argument("--output-directory", type=Path, required=True)
    study_parser.add_argument(
        "--provider", choices=("openai", "claude-cli"), required=True
    )
    study_parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    study_parser.add_argument(
        "--base-url", default="https://api.openai.com/v1"
    )
    study_parser.add_argument("--input-cost-per-million", type=float)
    study_parser.add_argument("--output-cost-per-million", type=float)
    study_parser.add_argument("--frozen-retrieval", action="store_true")
    study_parser.add_argument("--resume", action="store_true")
    study_parser.add_argument("--jobs", type=int, default=1)

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
        help="SQLite path; defaults to the user data directory",
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

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="check the local runtime and database without reading memory content",
    )
    doctor_parser.add_argument(
        "--database",
        type=Path,
        default=Path("memory-loom.db"),
    )

    backup_parser = subparsers.add_parser(
        "backup",
        help="create a consistent SQLite backup",
    )
    backup_parser.add_argument(
        "--database",
        type=Path,
        default=Path("memory-loom.db"),
    )
    backup_parser.add_argument("--output", type=Path)
    backup_parser.add_argument("--force", action="store_true")

    restore_parser = subparsers.add_parser(
        "restore",
        help="restore and migrate a validated SQLite backup",
    )
    restore_parser.add_argument("--from", dest="backup", type=Path, required=True)
    restore_parser.add_argument(
        "--database",
        type=Path,
        default=Path("memory-loom.db"),
    )
    restore_parser.add_argument(
        "--yes",
        action="store_true",
        help="confirm replacement when the destination database exists",
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

    blind_parser = subparsers.add_parser(
        "blind-study",
        help="create a condition-blind review packet and separate key",
    )
    blind_parser.add_argument("scenarios", type=Path)
    blind_parser.add_argument("run_directory", type=Path)
    blind_parser.add_argument("--packet", type=Path, required=True)
    blind_parser.add_argument("--key", type=Path, required=True)
    blind_parser.add_argument("--review-template", type=Path, required=True)
    blind_parser.add_argument("--packet-id", required=True)
    blind_parser.add_argument("--reviewer-id", required=True)
    blind_parser.add_argument("--seed", type=int, required=True)

    analyze_parser = subparsers.add_parser(
        "analyze-study",
        help="analyze blinded reviews with paired cluster bootstrap",
    )
    analyze_parser.add_argument("key", type=Path)
    analyze_parser.add_argument("run_directory", type=Path)
    analyze_parser.add_argument("reviews", type=Path, nargs="+")
    analyze_parser.add_argument("--output", type=Path, required=True)
    analyze_parser.add_argument("--report", type=Path)
    analyze_parser.add_argument("--bootstrap-samples", type=int, default=10_000)
    analyze_parser.add_argument("--seed", type=int, default=0)

    judge_parser = subparsers.add_parser(
        "review-study",
        help="produce a condition-blind model review for an existing packet",
    )
    judge_parser.add_argument("packet", type=Path)
    judge_parser.add_argument("--output", type=Path, required=True)
    judge_parser.add_argument("--reviewer-id", required=True)
    judge_parser.add_argument(
        "--provider", choices=("openai", "claude-cli"), required=True
    )
    judge_parser.add_argument("--model", required=True)
    judge_parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    judge_parser.add_argument("--base-url", default="https://api.openai.com/v1")
    judge_parser.add_argument("--batch-size", type=int, default=8)
    judge_parser.add_argument("--jobs", type=int, default=1)
    judge_parser.add_argument("--seed", type=int, default=0)
    judge_parser.add_argument("--resume", action="store_true")
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
        elif args.command == "json-stdio":
            return serve_json_lines()
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
        elif args.command == "run-study":
            run_manifest = validate_path(args.run_manifest)
            adapter = (
                OpenAIResponsesAdapter(
                    run_manifest["model"],
                    api_key_env=args.api_key_env,
                    base_url=args.base_url,
                    input_cost_per_million=args.input_cost_per_million,
                    output_cost_per_million=args.output_cost_per_million,
                )
                if args.provider == "openai"
                else ClaudeCliAdapter(run_manifest["model"])
            )
            scenario_paths = (
                sorted(args.scenarios.glob("*.json"))
                if args.scenarios.is_dir()
                else [args.scenarios]
            )
            scenario_documents = [validate_path(path) for path in scenario_paths]
            selected_scenarios = {
                scenario["scenario_id"]: scenario
                for scenario in scenario_documents
                if scenario["scenario_id"] in run_manifest["scenario_ids"]
            }
            missing = set(run_manifest["scenario_ids"]) - set(selected_scenarios)
            if missing:
                raise ValueError(
                    "run manifest scenarios are missing: "
                    + ", ".join(sorted(missing))
                )
            if args.jobs < 1:
                raise ValueError("jobs must be positive")
            args.output_directory.mkdir(parents=True, exist_ok=True)
            condition_manifest = validate_path(args.condition_manifest)
            completed = 0
            pending = []
            for scenario_id in run_manifest["scenario_ids"]:
                scenario = selected_scenarios[scenario_id]
                output_path = args.output_directory / f"{scenario['scenario_id']}.json"
                if output_path.exists() and args.resume:
                    validate_path(output_path)
                    completed += 1
                    continue
                if output_path.exists():
                    raise ValueError(f"output already exists: {output_path}")
                pending.append((scenario, output_path))
            with ThreadPoolExecutor(max_workers=args.jobs) as executor:
                futures = {
                    executor.submit(
                        run_scenario,
                        scenario,
                        condition_manifest,
                        run_manifest,
                        adapter,
                        frozen_retrieval=args.frozen_retrieval,
                    ): (scenario, output_path)
                    for scenario, output_path in pending
                }
                for future in as_completed(futures):
                    scenario, output_path = futures[future]
                    artifact = future.result()
                    output_path.write_text(
                        artifact.model_dump_json(indent=2) + "\n",
                        encoding="utf-8",
                    )
                    completed += 1
                    print(f"{artifact.status}: {scenario['scenario_id']}")
            print(f"study complete: {completed} scenario artifacts")
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
        elif args.command == "doctor":
            report = diagnose(args.database)
            print(report.to_json())
            if report.status == "error":
                return 1
        elif args.command == "backup":
            backup_path = backup_database(
                args.database,
                args.output,
                overwrite=args.force,
            )
            print(f"backup: {backup_path}")
        elif args.command == "restore":
            restored = restore_database(
                args.backup,
                args.database,
                confirmed=args.yes,
            )
            print(
                f"restored: {restored.database_path} "
                f"(schema {restored.schema_version})"
            )
            if restored.safety_backup_path is not None:
                print(f"previous database backup: {restored.safety_backup_path}")
            if restored.migration_backup_path is not None:
                print(f"pre-migration backup: {restored.migration_backup_path}")
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
        elif args.command == "blind-study":
            packet, key, template = create_blinded_review(
                args.scenarios,
                args.run_directory,
                packet_id=args.packet_id,
                seed=args.seed,
                reviewer_id=args.reviewer_id,
            )
            for path, artifact in (
                (args.packet, packet),
                (args.key, key),
                (args.review_template, template),
            ):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    artifact.model_dump_json(indent=2) + "\n", encoding="utf-8"
                )
            print(f"blinded: {len(packet.items)} items in {args.packet}")
            print(f"key: keep {args.key} hidden from reviewers")
            print(f"review template: {args.review_template}")
        elif args.command == "analyze-study":
            analysis = analyze_pilot(
                load_json(args.key),
                [load_json(path) for path in args.reviews],
                args.run_directory,
                bootstrap_samples=args.bootstrap_samples,
                seed=args.seed,
            )
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                analysis.model_dump_json(indent=2) + "\n", encoding="utf-8"
            )
            if args.report is not None:
                args.report.parent.mkdir(parents=True, exist_ok=True)
                args.report.write_text(render_pilot_report(analysis), encoding="utf-8")
            print(f"analyzed: {analysis.reviewed_items} blinded outputs")
            print(f"status: {analysis.status}")
        elif args.command == "review-study":
            if args.output.exists() and not args.resume:
                raise ValueError(f"output already exists: {args.output}")
            adapter = (
                OpenAIResponsesAdapter(
                    args.model,
                    api_key_env=args.api_key_env,
                    base_url=args.base_url,
                )
                if args.provider == "openai"
                else ClaudeCliAdapter(args.model)
            )
            review = review_packet_with_model(
                load_json(args.packet),
                adapter,
                reviewer_id=args.reviewer_id,
                batch_size=args.batch_size,
                jobs=args.jobs,
                seed=args.seed,
                existing_review_document=(
                    load_json(args.output)
                    if args.output.exists() and args.resume
                    else None
                ),
                checkpoint_path=args.output,
                progress=lambda completed, total: print(
                    f"reviewed: {completed}/{total}", flush=True
                ),
            )
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                review.model_dump_json(indent=2) + "\n", encoding="utf-8"
            )
            print(f"reviewed: {len(review.ratings)} blinded outputs")
    except (ContractValidationError, OSError, RuntimeError, ValueError) as error:
        print(f"error: {error}")
        return 1
    return 0


def _format_metric(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.4f}"
