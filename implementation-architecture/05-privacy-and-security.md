# Privacy And Security Architecture

## Decision Status

- **Proposed:** Local-first privacy model with explicit provider egress manifests.
- **Confidence:** High for the controls; provider-side retention still depends on the user's provider account and product settings.

## Privacy Claim

The implementation may claim:

> Memory storage, indexing, retrieval, and policy evaluation run locally. Only the current request and explicitly selected context are sent to the configured model provider.

It must not claim that no other data leaves the machine. Claude Code and Codex CLI may send files, tool results, conversation context, diagnostics, or telemetry according to their own behavior and configuration.

## Trust Boundaries

| Boundary | Trusted data | Required control |
|---|---|---|
| Client to MCP bridge | Task signal and tool arguments | Schema validation and size limits |
| MCP bridge to daemon | Local authenticated request | User-owned socket permissions |
| Daemon to local store | Pseudonymised memory and minimized evidence | De-identification, encryption, transactions, scope checks |
| Daemon to embedding model | Sanitized memory text | Purpose check and local process only by default |
| Egress gateway to provider | Approved anonymised manifest subset | Allowlist, second-pass de-identification, audit, explicit mode |
| Memory context to model | Untrusted historical claims | Prompt labeling and instruction isolation |
| Model to tool executor | Untrusted proposed action | Independent authorization, allowlist, argument policy, and approval |

## Default Egress Policy

- `local_only`: no Memory Loom process may make network requests.
- Provider endpoints are empty unless the user enables a remote feature.
- Local embeddings are mandatory in `local_only` mode.
- Retrieval never calls a remote reranker.
- Remote extraction and consolidation are disabled by default.
- The MCP bridge never contacts Anthropic or OpenAI directly.

## Anonymisation Boundary

- Local ownership uses random pseudonymous subject IDs because retrieval requires stable linkage.
- Project scopes use keyed hashes so local paths are not stored in memory records or indexes.
- Durable statements, embeddings, logs, traces, and default exports exclude direct identifiers and secrets.
- Provider-bound context receives a second purpose-specific de-identification pass.
- Reversible mappings are exceptional, separately encrypted, excluded from search, and never sent to providers.
- Telemetry and evaluation data are anonymous or synthetic; stable production tokens are not reused.

The complete pipeline, contracts, re-identification threats, and acceptance criteria are defined in [Anonymisation and pseudonymisation](07-de-identification.md).

## Egress Manifest

Every optional remote call records this locally before transmission:

```yaml
id: uuid
provider: anthropic|openai
purpose: extraction|consolidation|generation_support
request_id: uuid
memory_ids: [uuid]
fields: [statement, scope, confidence]
redactions: integer
estimated_tokens: integer
policy_version: string
created_at: timestamp
```

Secret values and blocked sensitivity classes can never appear in a manifest.

## Threats And Controls

| Threat | Control |
|---|---|
| Prompt injection stored as memory | Treat memory as data; strip active markup; never execute embedded instructions |
| Unauthorized tool execution | Enforce tool allowlists, scope, argument schemas, and approval outside the model |
| Cross-project disclosure | Filter ownership and project scope before search |
| Secret persistence | Detect and reject credentials before candidate creation |
| Silent profiling | Require declared memory classes and visible consent state |
| Excessive provider disclosure | Hard context budget, purpose-specific de-identification, and egress manifest |
| Re-identification from combined attributes | Generalization, rare-value review, timestamp coarsening, and purpose-scoped tokens |
| Linkage across projects or exports | Distinct scope tokens and removal of stable internal IDs from exports |
| Compromised MCP caller | Socket permissions, request schema, caller identity, rate limits |
| Stale or contradicted memory | Status filters, validity windows, and contradiction penalties |
| Deleted data resurfacing | Immediate tombstone plus index and derivation cleanup |
| Local database theft | File permissions and optional SQLCipher encryption |

## Tool Authorization Boundary

- Model output is a proposal, never authorization.
- The MCP bridge validates tool name and input shape before forwarding.
- The daemon authorizes caller, user, project, operation, and target record independently.
- Read, write, export, and destructive capabilities use separate policy decisions.
- Retrieved memory cannot grant permissions or suppress an approval requirement.
- `memory_forget`, identifiable export, and policy changes always require an explicit user-approved path.
- Denied calls return a bounded reason and create a local audit event.

## User Controls

- `memory-loom status` shows storage location, network mode, model adapters, and consent state.
- `memory-loom list` shows durable memories and provenance.
- `memory-loom egress` shows what Memory Loom prepared for remote processing.
- `memory-loom disable` stops retrieval without deleting data.
- `memory-loom forget` removes selected memory and dependent indexes.
- `memory-loom export` produces an anonymised archive by default; identifiable export requires explicit confirmation.

## Verification

- Run integration tests with outbound networking denied.
- Assert identical retrieval behavior in `local_only` mode.
- Capture process-level network connections during end-to-end tests.
- Test prompt injection, scope confusion, deletion, and stale-index scenarios.
- Assert adversarial memory cannot trigger unauthorized tools or broaden allowed arguments.
- Assert identifiers never reach durable text, embeddings, logs, default exports, or provider egress.
- Run re-identification tests against exports and provider-bound manifests.
- Document separately what each client and provider may transmit or retain.

## Evidence Basis

- [LLM decision guardrails](../notes/07-llm-decision-guardrails.md)
- [Memory governance and safety](../notes/14-memory-governance-and-safety.md)
- [Personalized-memory evaluation](../notes/15-personalized-memory-evaluation.md)
- [Anonymisation and pseudonymisation](07-de-identification.md)
