---
id: AH-009
title: Pluggable tool blueprint
status: proposed
maturity: proposed
source_repo: pipeline-fl-control-plane
source_commit: df513fa41484fc3e218d836d951ee46d0abc7513
---

# Pluggable Tool Blueprint

## Product Thesis

Build a local-first harness that composes repository instructions, focused knowledge, workflow state, runtime capabilities, validation, and learning without coupling them to one agent vendor.

## Proposed Modules

| Module | Responsibility | First useful output |
|---|---|---|
| Source scanner | Discover instructions, skills, commands, specs, code, and tests | Source inventory |
| Instruction router | Match task intent and paths to minimal guidance | Context route with reasons |
| Knowledge packer | Assemble bounded, authoritative context | Ordered context manifest |
| Task note store | Persist resumable state | Validated task note |
| Workflow adapter | Expose explore/propose/apply/archive-like actions | Artifact graph and status |
| Capability registry | Declare prompts, skills, tools, secrets, and runtime needs | Capability descriptor |
| Runtime adapter | Execute locally, in a container, or remotely | Structured result envelope |
| Validation planner | Map risk and contracts to focused checks | Executable validation plan |
| Evidence ledger | Track provenance, confidence, and extraction coverage | Auditable concept catalog |
| Retrospective engine | Promote repeated learning and clean safe residue | Promotion proposal |

## Minimal Common Contracts

### Instruction Route

```yaml
id: string
match: {intents: [], paths: []}
load: []
avoid: []
authority: string
```

### Capability Descriptor

```yaml
id: string
prompt: string
skills: []
tools: []
secrets: []
runtime: {kind: local|container|remote}
output_schema: string
```

### Result Envelope

```yaml
task_id: string
status: completed|failed|timed_out
completion: string|null
artifacts: []
usage: {input_tokens: null, output_tokens: null}
trace: {provider_run_id: null}
```

### Evidence Record

```yaml
claim: string
kind: observed|inferred|proposed
sources: []
confidence: high|medium|low
last_verified: date
```

## MVP Sequence

1. Parse depot front matter and validate links.
2. Scan one repository for instruction and architecture entrypoints.
3. Produce a minimal context manifest for a task description and changed paths.
4. Create or resume a task note from that manifest.
5. Emit a focused validation plan without executing it.

This sequence proves the knowledge and workflow layers before taking on remote execution, secrets, or autonomous cleanup.

## Explicit Non-Goals For MVP

- No agent vendor abstraction beyond a simple command adapter.
- No cloud service or multi-tenant control plane.
- No automatic deletion of ambiguous notes.
- No broad credential broker.
- No LLM-based route choice without deterministic explainability.

## Optional Personalized-Memory Extension

After the base contracts work, `AH-010` through `AH-016` add interaction capture, candidate admission, typed consolidation, adaptive retrieval, memory governance, and longitudinal evaluation. This extension should reuse the evidence ledger, bounded-context, LLM-policy, and validation primitives rather than create a second harness.

## Design Constraints

- Local-first and inspectable.
- Every loaded context item has a reason.
- Every automated decision has a fallback policy.
- Every plugin declares permissions and side effects.
- Product-specific adapters stay outside the core domain model.
- Source evidence remains distinguishable from synthesized recommendations.

## Evidence

- `pipeline-fl-control-plane@df513fa4:AGENTS.md` — router input.
- `pipeline-fl-control-plane@df513fa4:docs/design/architecture-index.md` — knowledge routing model.
- `pipeline-fl-control-plane@df513fa4:.agents/skills/long-task-notes/SKILL.md` — task-state model.
- `pipeline-fl-control-plane@df513fa4:.agents/skills/openspec-apply-change/SKILL.md` — workflow action model.
- `pipeline-fl-control-plane@df513fa4:docs/design/handler-model.md` — capability registry model.
- `pipeline-fl-control-plane@df513fa4:docs/design/mcp-architecture.md` — bounded tool model.
- `pipeline-fl-control-plane@df513fa4:.claude/commands/council-review.md` — review orchestration model.

## Next Design Question

Should the first executable artifact be a standalone CLI, a Codex plugin, or a core library with thin adapters for both?
