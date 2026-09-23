# Memory Loom

Memory Loom is a research project about **external memory for coding assistants**.

The first question is deliberately narrow:

> Does a small store of explicit, user-approved preferences improve behavior across sessions compared with no memory, recent history, or a rolling summary?

This repository currently contains a research protocol and a reference design. It does **not** contain a working memory service or experimental results.

## Current Maturity

| Item | State |
|---|---|
| Source-backed agent-harness patterns | Documented from one source repository |
| Research questions and hypotheses | Defined, not yet tested |
| Experimental protocol | Specified, not yet run |
| Reference implementation | Phase 0 contracts implemented; memory core not implemented |
| Scientific conclusions | None |

Do not cite this repository as evidence that personalized memory improves an agent. That is the hypothesis under test.

## Scope

The first study includes only:

- explicit communication or workflow preferences;
- direct corrections to prior assistant behavior;
- user approval before durable storage;
- scoped retrieval with provenance;
- correction and deletion;
- controlled comparison against simpler baselines.

The first study excludes:

- inferred personal traits;
- autonomous memory promotion;
- psychological profiling;
- continuous fine-tuning;
- multi-user hosting;
- claims of production security or legal compliance.

## Repository Map

| Area | Authority |
|---|---|
| [`research/`](research/README.md) | Questions, hypotheses, claims, and experimental protocol |
| [`design/`](design/README.md) | Minimal system being proposed for evaluation |
| [`notes/`](notes/README.md) | Reusable patterns extracted from source systems |
| [`sources/`](sources/README.md) | Provenance and literature ledgers |
| [`schemas/`](schemas/v1/) | Versioned machine-readable experiment contracts |
| [`contracts/`](contracts/v1/README.md) | Labeling, metrics, analysis, and replay documentation |
| [`fixtures/`](fixtures/) | Synthetic scenarios and frozen manifests |
| [`src/memory_loom/`](src/memory_loom/) | Contract validation and deterministic context replay |
| [`STATUS.md`](STATUS.md) | Current work, decisions, and next milestone |

These layers are intentionally separate:

- **Evidence** records what a source actually demonstrates.
- **Inference** generalizes across observations.
- **Hypothesis** states a falsifiable expected effect.
- **Design decision** defines the system to test.
- **Result** requires completed experiments and does not exist yet.

## Start Here

1. Read the [research overview](research/README.md).
2. Check the [claim register](research/claims.md) before repeating a claim.
3. Use the [experiment protocol](research/protocol.md) for study design.
4. Use the [reference design](design/README.md) only when implementing the system under test.

## Contract Replay

```bash
PYTHONPATH=src python3 -m memory_loom validate-all
PYTHONPATH=src python3 -m memory_loom replay \
  fixtures/scenarios/v1/scope-deletion-001.json \
  fixtures/manifests/v1/default-conditions.json \
  query-001
pytest
```

## Origin

The project began as an extraction of reusable coding-agent harness patterns from `pipeline-fl-control-plane`. Those observations remain in [`notes/`](notes/README.md), but they are supporting evidence—not proof of the Memory Loom hypothesis.

## License

See [`LICENSE`](LICENSE).
