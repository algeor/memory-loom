---
id: AH-005
title: Declarative agent runtime
status: initial
maturity: inferred
source_repo: pipeline-fl-control-plane
source_commit: df513fa41484fc3e218d836d951ee46d0abc7513
---

# Declarative Agent Runtime

## Use When

- Multiple agent behaviors must run through one platform without hardcoding each behavior into the orchestrator.

## Core Pattern

Declare a task's prompt, capabilities, matching rules, execution mode, secrets, and output semantics separately from the runtime that executes it.

## Observed Implementation

- A declarative handler selects `agent_task` or `custom_runtime` execution.
- Agent tasks identify task text, skill paths, MCP configuration paths, repository coordinates, and declared secrets.
- Configuration lives in a registry repo; custom executable logic lives in an implementation repo; the control plane owns stable contracts and orchestration.
- Jobs receive a scoped environment and run in isolated Kubernetes workloads.
- Pydantic request/result models validate runtime boundaries.
- Results capture completion text, optional repository diff, token counts, and trace/run identifiers.
- Result reporting is a separate client boundary rather than hidden inside the agent SDK.
- Logical capability identity is stable while concrete handler versions can compete by applicability specificity.

## Reusable Contracts

```yaml
capability:
  id: stable-logical-id
  execution:
    type: agent_task
    prompt: analyze the selected failure
    skills: [path/to/skill.md]
    tools: [path/to/mcp.json]
  inputs:
    repository: required
    context_scope: inspection
  secrets:
    - name: SERVICE_TOKEN
      required: false
  output:
    description: factual contents and interpretation guidance
```

## Design Lessons

- The orchestrator should know **how to execute**, not domain-specific analysis logic.
- Capability descriptors need stable logical IDs and independently versioned implementations.
- Missing optional telemetry should not invalidate a useful primary result.
- Resource sizing, timeout, scheduling, and cleanup belong to runtime policy.
- Result transport should be idempotent where retries are expected.

## Portability Limits

- Kubernetes and the specific agent SDK are replaceable adapters, not core concepts.
- Environment variables are one transport; a local process or remote worker may use another.
- Open-ended JSON output increases flexibility but requires a factual output description and preserved raw evidence.

## Plugin Implication

- Capability registry with typed descriptors.
- Runtime adapters for local process, container job, and remote agent service.
- Secret-provider interface with explicit required/optional semantics.
- Result envelope with primary output, artifacts, telemetry, and trace identity.

## Evidence

- `pipeline-fl-control-plane@df513fa4:docs/design/handler-model.md` — declarative model and ownership boundaries.
- `pipeline-fl-control-plane@df513fa4:fl_shared/cr_models.py#ExecutionSpec` — typed capability declaration.
- `pipeline-fl-control-plane@df513fa4:engineering_agent/app/models.py#AgentTaskRequest` — runtime input contract.
- `pipeline-fl-control-plane@df513fa4:engineering_agent/app/agent_task_runner.py#run` — adapter sequencing and result extraction.
- `pipeline-fl-control-plane@df513fa4:engineering_agent/app/client_reporter.py#report_result` — explicit result boundary.

## Open Questions

- Should plugins declare execution topology directly, or only requirements that a scheduler resolves?
