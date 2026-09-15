---
id: AH-006
title: Bounded tools and context shaping
status: initial
maturity: observed
source_repo: pipeline-fl-control-plane
source_commit: df513fa41484fc3e218d836d951ee46d0abc7513
---

# Bounded Tools And Context Shaping

## Use When

- Agents need access to large or sensitive operational data without receiving broad credentials or entire datasets in the prompt.

## Core Pattern

Give the agent small, task-shaped tools that resolve scoped context into actionable references.

## Observed Implementation

- Job-local MCP servers use `stdio`, so they expose no network listening port.
- Tool configuration is inspection-scoped and validated at startup.
- The initial context includes an inspection ID, connection material, and optional matched-stage context.
- Agents call `get_failure_focus()` to translate orchestration context into stage directories and normalized log references.
- Tools expose summaries, inventories, slices, windows, and exact reads rather than forcing full-data reads.
- Stage-scoped context must resolve deterministically; malformed or ambiguous state fails fast.
- Tool methods are read-only even when the enclosing job identity may also support a separate write path.
- Secret values use protected types and are unwrapped only at actual use sites.

## Context-Shaping Lessons

- Internal database IDs are good audit keys but often bad agent affordances.
- A tool should return values that are directly valid inputs to the next tool.
- Start with a brief or index, then let the agent drill down.
- Bound large payloads by slices, windows, summaries, and explicit size caps.
- Preserve provenance so a summary points back to exact evidence.

## Generalized Primitive

A **context resolver** turns platform state into an agent-facing navigation graph:

```text
task scope -> focus summary -> evidence references -> bounded reads -> exact artifact
```

## Portability Limits

- MCP is one tool protocol; the same contract can be implemented through function calling or an RPC layer.
- Process-local read-only tools do not automatically imply least-privilege process credentials.
- Tool names and storage layouts are product-specific; the progressive access pattern is portable.

## Plugin Implication

- Tool manifests should declare scope, mutability, input/output schemas, payload limits, and credential needs.
- A context-pack builder should prefer summaries and references over raw evidence.
- A policy check should compare declared tool mutability with actual credential capability.

## Evidence

- `pipeline-fl-control-plane@df513fa4:docs/design/mcp-architecture.md` — bounded tool architecture.
- `pipeline-fl-control-plane@df513fa4:fl_mcp_servers/generic/settings.py#McpSettings` — fail-fast scoped configuration.
- `pipeline-fl-control-plane@df513fa4:fl_mcp_servers/generic/pipeline_data_mcp.py` — progressive evidence tools and payload cap.
- `pipeline-fl-control-plane@df513fa4:docs/design/handler_match_context_mcp_plan.md` — actionable references instead of raw IDs.

## Open Questions

- How can the tool verify real backend authorization rather than trusting a plugin's declared `read_only` flag?
