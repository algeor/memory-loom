# Memory Loom

[![CI](https://github.com/algeor/memory-loom/actions/workflows/ci.yml/badge.svg)](https://github.com/algeor/memory-loom/actions/workflows/ci.yml)
[![Release](https://github.com/algeor/memory-loom/actions/workflows/release.yml/badge.svg)](https://github.com/algeor/memory-loom/actions/workflows/release.yml)
[![License: GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](LICENSE)

**Local, approval-based memory for coding agents.**

Memory Loom gives Codex and Claude Code a small explicit memory store for
user-approved preferences and corrections. It is designed to make memory
inspectable, correctable, deletable, and testable instead of hidden in chat
history.

It is also a research project. The core question is deliberately narrow:

> Does a small store of explicit, user-approved preferences improve behavior across sessions compared with no memory, recent history, or a rolling summary?

This repository contains:

- a local SQLite-backed reference implementation;
- five MCP lifecycle tools: retrieve, propose, commit, discard, inspect;
- onboarding for Codex and Claude Code;
- deterministic replay and retrieval evaluation fixtures;
- a documented development pilot with inconclusive results.

Memory Loom does **not** contain a production memory service or confirmatory
evidence that memory improves coding-agent behavior.

## Try It

Install the tagged wheel with `uv`, then onboard the coding-agent host inside
the project where memory should be available:

```zsh
uv python install 3.14
uv tool install --python 3.14 \
  https://github.com/algeor/memory-loom/releases/download/v0.1.0/memory_loom-0.1.0-py3-none-any.whl
memory-loom onboard codex --project-id your-project
memory-loom doctor --database ~/.local/share/memory-loom/your-project.db
```

Claude Code is also supported:

```zsh
memory-loom onboard claude --project-id your-project
```

Read [`EARLY_TESTERS.md`](EARLY_TESTERS.md) before using real preferences.

## Current Maturity

| Item | State |
|---|---|
| Source-backed agent-harness patterns | Documented from one source repository |
| Research questions and hypotheses | Defined; exercised in one exploratory development pilot |
| Experimental protocol | Implemented and exercised with blinded model review |
| Reference implementation | SQLite memory core, retrieval, JSON/MCP lifecycle boundaries, and provider-backed runner implemented |
| Development pilot dataset | 24 synthetic scenarios across 6 template families |
| Client integration | Five model-neutral MCP 2.x tools, persistent JSON stdio fallback, and automated Codex/Claude onboarding implemented |
| Scientific conclusions | No confirmatory conclusion; development-pilot contrasts were inconclusive |

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
| [`design/project-guidance.md`](design/project-guidance.md) | Project-scoped conventions for internal languages, APIs, and workflows |
| [`design/provider-runner.md`](design/provider-runner.md) | Provider-backed experiment execution and isolation boundaries |
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

## Non-MCP Hosts

Hosts without MCP can start one persistent JSON-lines process:

```zsh
MEMORY_LOOM_USER_ID=default \
MEMORY_LOOM_PROJECT_ID=memory-loom \
MEMORY_LOOM_DATABASE_PATH=~/.local/share/memory-loom/memory-loom.db \
memory-loom json-stdio
```

The process exposes the same retrieve, propose, commit, discard, and inspect
operations. Scope remains host-controlled, and proposals remain non-durable
until a separate explicitly approved commit request. See
[`contracts/v1/json-stdio.md`](contracts/v1/json-stdio.md).

## Development Pilot

The repository includes provider-backed generation, condition-blind review,
and paired cluster-bootstrap analysis commands. The 24-scenario development
pilot completed 192 Claude CLI runs without a run failure. Its model-only review
estimated B3-B0 adherence at `0.2188`, with a simultaneous 95% interval of
`[-0.0625, 0.5000]`. Every B3 contrast interval included zero, so the run does
not distinguish structured memory from any baseline. It is exploratory and
cannot establish a confirmatory scientific result. See the
[`pilot workflow`](contracts/v1/pilot-workflow.md) and frozen
[`pilot report`](evaluation-runs/development-pilot-claude-001/REPORT.md).

## Early User Upgrades

Keep the configured database path stable, update the checkout, then run:

```zsh
uv run memory-loom migrate --database /absolute/path/to/memory-loom.db
```

Pending schema changes are backed up and applied transactionally. See
[`design/database-upgrades.md`](design/database-upgrades.md) before distributing
a new build to early users.

Manual recovery commands:

```zsh
memory-loom backup --database /absolute/path/to/memory-loom.db
memory-loom restore --from /absolute/path/to/backup.db \
  --database /absolute/path/to/memory-loom.db --yes
```

## Origin

The project began as an extraction of reusable coding-agent harness patterns from `pipeline-fl-control-plane`. Those observations remain in [`notes/`](notes/README.md), but they are supporting evidence—not proof of the Memory Loom hypothesis.

## License

See [`LICENSE`](LICENSE).
