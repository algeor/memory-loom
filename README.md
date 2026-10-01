# Memory Loom

Memory Loom is a research project about **external memory for coding assistants**.

The first question is deliberately narrow:

> Does a small store of explicit, user-approved preferences improve behavior across sessions compared with no memory, recent history, or a rolling summary?

This repository contains a research protocol, a reference design, and a local reference implementation for controlled experiments. It does **not** contain a production memory service or experimental results.

## Current Maturity

| Item | State |
|---|---|
| Source-backed agent-harness patterns | Documented from one source repository |
| Research questions and hypotheses | Defined, not yet tested |
| Experimental protocol | Specified, not yet run |
| Reference implementation | Phase 0-2 contracts, SQLite memory core, retrieval, and baseline runner implemented |
| Development pilot dataset | 24 synthetic scenarios across 6 template families |
| Client integration | Five model-neutral MCP 2.x stdio tools and automated Codex/Claude onboarding implemented; JSON CLI fallback pending |
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
| [`design/codex-mcp.md`](design/codex-mcp.md) | Reproducible Codex MCP host setup |
| [`design/claude-code-mcp.md`](design/claude-code-mcp.md) | Reproducible Claude Code MCP host setup |
| [`design/database-upgrades.md`](design/database-upgrades.md) | SQLite backup and upgrade procedure |
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

## Deterministic Baseline Run

```bash
PYTHONPATH=src python3 -m memory_loom run \
  fixtures/scenarios/v1/scope-deletion-001.json \
  fixtures/manifests/v1/default-conditions.json \
  fixtures/manifests/v1/contract-replay-run.json \
  --output evaluation-runs/contract-replay-001.json
```

This uses the no-model adapter. It verifies the complete B0-B3 execution and artifact pipeline without producing experimental evidence.

## Lexical Retrieval Evaluation

Evaluate live SQLite FTS5 retrieval against the frozen scenario labels without
calling a model:

```zsh
uv run memory-loom evaluate-retrieval \
  fixtures/scenarios/v1 \
  --output evaluation-runs/retrieval-fixtures.json \
  --min-recall-at-k 1 \
  --min-mrr 1 \
  --max-no-memory-fpr 0
```

The versioned artifact separates raw ranked IDs from budgeted context IDs and
reports recall, precision, MRR, nDCG, abstention accuracy, false positives,
forbidden hits, and context-token cost. This command evaluates all 25 scenario
fixtures, including the standalone contract fixture; it is engineering
validation, not a scientific result for the 24-scenario pilot.

## MCP Host Setup

After installation, onboard a supported host with one command:

```zsh
uv run memory-loom onboard codex --project-id memory-loom
# or
uv run memory-loom onboard claude --project-id memory-loom
```

See the [Codex](design/codex-mcp.md) and
[Claude Code](design/claude-code-mcp.md) guides for scope and verification.
Memory Loom remains model-independent; onboarding configures hosts rather than
adapting the memory core to an LLM.

## Early User Upgrades

Keep the configured database path stable, update the checkout, then run:

```zsh
uv run memory-loom migrate --database /absolute/path/to/memory-loom.db
```

Pending schema changes are backed up and applied transactionally. See
[`design/database-upgrades.md`](design/database-upgrades.md) before distributing
a new build to early users.

## Origin

The project began as an extraction of reusable coding-agent harness patterns from `pipeline-fl-control-plane`. Those observations remain in [`notes/`](notes/README.md), but they are supporting evidence—not proof of the Memory Loom hypothesis.

## License

See [`LICENSE`](LICENSE).
