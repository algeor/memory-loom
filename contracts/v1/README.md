# Experiment Contracts v1

## Status

This directory documents implemented contract version `1.0.0`. Pydantic models in [`../../src/memory_loom/models.py`](../../src/memory_loom/models.py) are the runtime source of truth. Generated JSON Schemas live in [`../../schemas/v1/`](../../schemas/v1/).

The implementation validates and replays synthetic artifacts. It does not call a model or provide a persistent memory service.

## Artifacts

| Artifact | Schema | Purpose |
|---|---|---|
| Scenario | `scenario.schema.json` | Timeline, records, labels, and frozen retrieval decisions |
| Condition manifest | `condition-manifest.schema.json` | Tokenizer, serializer, budget, and B0-B3 construction |
| Run manifest | `run-manifest.schema.json` | Reproducibility and analysis configuration |
| Evidence event | `evidence-event.schema.json` | Approved, erasable source content with provenance |
| Memory record | `memory-record.schema.json` | Scoped and versioned preference state |
| Revision event | `revision-event.schema.json` | Append-only lifecycle transition metadata |
| Retrieval decision | `retrieval-decision.schema.json` | Per-record eligibility and selection trace |

## Replay Boundary

Replay uses frozen retrieval decisions, not outcome labels, to construct B3. This keeps the contract runner independent from future model output while Phase 1 retrieval is not yet implemented.

The initial tokenizer counts whitespace-delimited tokens. It is deliberately simple and versioned; provider-specific tokenizers can be introduced through a new manifest version.

## Commands

```bash
PYTHONPATH=src python3 -m memory_loom validate-all
PYTHONPATH=src python3 -m memory_loom export-schemas
PYTHONPATH=src python3 -m memory_loom replay \
  fixtures/scenarios/v1/scope-deletion-001.json \
  fixtures/manifests/v1/default-conditions.json \
  query-001
pytest
```

## Supporting Definitions

- [`labeling-guide.md`](labeling-guide.md)
- [`metrics.md`](metrics.md)
- [`analysis.md`](analysis.md)
