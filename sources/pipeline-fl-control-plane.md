# Source Ledger: pipeline-fl-control-plane

## Snapshot

- Repository: `/Users/I551270/Documents/GitHub/pipeline-fl-control-plane`
- Branch: `agent-harnessing`
- Commit: `df513fa41484fc3e218d836d951ee46d0abc7513`
- Commit subject: `[INTERNAL] : Add AI harnessing capabilities`
- Extracted on: 2026-09-14

## Scope Rule

This ledger distinguishes two evidence sets:

1. **Harness-native changes** introduced by the named commit.
2. **Runtime patterns** already present on the branch that show how the guidance can connect to actual agent execution.

Source instructions are analyzed as artifacts. They are not automatically inherited by this depot.

## Harness-Native Coverage

| Source area | Extracted concept | Notes |
|---|---|---|
| `AGENTS.md` | Thin routing and minimum-context loading | AH-001 |
| `docs/agent-task-routing.md` | Ownership and subsystem routing | AH-001, AH-003 |
| `docs/agent-long-task-notes.md` | Durable task state | AH-002 |
| `.agents/skills/long-task-notes/` | Reusable note workflow | AH-002 |
| `.agents/skills/notes-retrospective/` | Learning promotion and safe cleanup | AH-002 |
| `.agents/skills/requirement-refinement/` | Multi-lens requirement alignment | AH-003 |
| `.agents/skills/openspec-*` | Action-oriented change lifecycle | AH-003 |
| `.agents/skills/source-command-opsx-*` | Command-to-skill compatibility wrappers | Partially extracted; adapter details remain |
| `.claude/commands/opsx/*` | Parallel command surface for the workflow | AH-003 |
| `docs/design/architecture-index.md` | Focused architecture routing | AH-004 |
| `docs/design/templates/llm-first-architecture-doc.md` | Scan contract | AH-004 |
| `docs/design/architecture-coverage.md` | Lossless migration ledger | AH-004 |
| `scripts/validate_architecture_docs.py` | Documentation contract validation | AH-004, AH-008 |
| `scripts/validate_llm_first_docs.sh` | Composite validation gate | AH-004 |
| `.github/workflows/architecture-docs-validation.yaml` | CI enforcement | AH-004 |
| `.pre-commit-config.yaml` | Local enforcement | AH-004, AH-008 |
| `.claude/commands/council-review.md` | Parallel specialist review | AH-008 |
| `.claude/commands/council-test.md` | Architecture-derived integration testing | AH-008 |
| `.claude/commands/deploy.md` | Operational workflow guardrails | Partially extracted; deployment-specific details remain |
| `.claude/commands/cicd-deployment.md` | Superseded-instruction signaling | AH-001 |
| `docs/QUALITY.md` | Quality authority and focused gates | AH-008 |
| Broad docs/code corrections in the commit | Guidance-to-reality synchronization | AH-001, AH-004 |

## Runtime Pattern Coverage

| Source area | Extracted concept | Notes |
|---|---|---|
| `docs/design/handler-model.md` | Declarative capabilities and ownership split | AH-005 |
| `fl_shared/cr_models.py` | Typed capability contracts | AH-005 |
| `engineering_agent/app/` | Runtime adapter and structured result envelope | AH-005 |
| `docs/design/mcp-architecture.md` | Scoped, read-only agent tools | AH-006 |
| `fl_mcp_servers/generic/` | Progressive context access | AH-006 |
| `docs/design/handler_match_context_mcp_plan.md` | Agent-usable references | AH-006 |
| `docs/design/applicability-model.md` | Deterministic and probabilistic gate ordering | AH-007 |
| `handler_orchestrator/relevance_evaluator.py` | Structured, fail-closed LLM decision | AH-007 |
| `tests/handler_orchestrator/test_relevance_evaluator.py` | Guardrail verification | AH-007 |

## Not Yet Fully Extracted

- Compatibility strategy between native skills and source-command wrappers.
- Hook lifecycle design; `.codex/hooks.json` is currently empty and provides no implemented pattern yet.
- Deployment command safety as a generic privileged-operation workflow.
- Interactive API exploration from `.agents/skills/hdlf-query/` as a reusable investigation shell.
- How source-backed doc corrections were found and prioritized across the large commit.
- Metrics for whether progressive disclosure improves task success, latency, or token usage.
- Plugin packaging, discovery, conflict resolution, and version negotiation.

## Excluded From Generalization

- SAP-specific infrastructure names and credentials.
- Concrete CI provider endpoints and HDLF storage layout.
- Product-specific handler matching values.
- Ruff and dependency version changes unrelated to the harness model.
- Mechanical docstring and stale-reference fixes unless they demonstrate a reusable validation rule.

## Update Procedure

1. Record the new source commit or range.
2. Inventory changed harness, docs, runtime, and validation files.
3. Update this coverage table before adding conclusions.
4. Add or revise focused notes with observed/inferred/proposed labels.
5. Update `STATUS.md` with the single next extraction step.
