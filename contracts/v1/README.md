# Experiment Contracts v1

## Status

This directory documents implemented contract version `1.0.0`. Pydantic models in [`../../src/memory_loom/models.py`](../../src/memory_loom/models.py) are the runtime source of truth. Generated JSON Schemas live in [`../../schemas/v1/`](../../schemas/v1/).

The implementation validates and replays synthetic artifacts, persists memory in SQLite, and executes all baseline conditions through a synchronous model-adapter interface. The included adapter is deterministic and does not call a model provider.

## Artifacts

| Artifact | Schema | Purpose |
|---|---|---|
| Scenario | `scenario.schema.json` | Timeline, records, labels, and frozen retrieval decisions |
| Condition manifest | `condition-manifest.schema.json` | Tokenizer, serializer, budget, and B0-B3 construction |
| Run manifest | `run-manifest.schema.json` | Reproducibility and analysis configuration |
| Run artifact | `run-artifact.schema.json` | Exact prompts, contexts, outputs, latency, and attributable failures |
| Evidence event | `evidence-event.schema.json` | Approved, erasable source content with provenance |
| Memory record | `memory-record.schema.json` | Scoped and versioned preference state |
| Revision event | `revision-event.schema.json` | Append-only lifecycle transition metadata |
| Retrieval decision | `retrieval-decision.schema.json` | Per-record eligibility and selection trace |

## Replay Boundary

Replay uses the SQLite store and live lexical retrieval by default. It never uses outcome labels to construct B3. Pass `--frozen-retrieval` only when checking a fixture's recorded retrieval trace.

The initial tokenizer counts whitespace-delimited tokens. It is deliberately simple and versioned; provider-specific tokenizers can be introduced through a new manifest version.

## Commands

```bash
PYTHONPATH=src python3 -m memory_loom validate-all
PYTHONPATH=src python3 -m memory_loom export-schemas
PYTHONPATH=src python3 -m memory_loom replay \
  fixtures/scenarios/v1/scope-deletion-001.json \
  fixtures/manifests/v1/default-conditions.json \
  query-001
PYTHONPATH=src python3 -m memory_loom replay \
  fixtures/scenarios/v1/scope-deletion-001.json \
  fixtures/manifests/v1/default-conditions.json \
  query-001 --frozen-retrieval
PYTHONPATH=src python3 -m memory_loom run \
  fixtures/scenarios/v1/scope-deletion-001.json \
  fixtures/manifests/v1/default-conditions.json \
  fixtures/manifests/v1/contract-replay-run.json \
  --output evaluation-runs/contract-replay-001.json
pytest
```

## Supporting Definitions

- [`labeling-guide.md`](labeling-guide.md)
- [`metrics.md`](metrics.md)
- [`analysis.md`](analysis.md)
