# Memory Loom Implementation Architecture

This folder translates the proposed memory patterns into an implementable, local-first system for Claude Code and Codex CLI.

## Architecture Goal

Run storage, indexing, retrieval, policy checks, and audit history on the user's machine. Send only the current request and the smallest approved context manifest to the configured model provider.

```text
Claude Code ─┐
             ├─ local MCP bridge ─► Memory Loom daemon
Codex CLI ───┘                       ├─ policy engine
                                     ├─ hybrid retriever
                                     ├─ local embedding model
                                     └─ encrypted local store
```

## Documents

1. [System architecture](01-system-architecture.md) — components, trust boundaries, and runtime flows.
2. [Storage and data model](02-storage-and-data-model.md) — local persistence, versioning, and deletion.
3. [Retrieval and context](03-retrieval-and-context.md) — local RAG, ranking, and context budgets.
4. [Client integrations](04-client-integrations.md) — shared MCP contract and thin client adapters.
5. [Privacy and security](05-privacy-and-security.md) — egress controls, consent, and threat model.
6. [Delivery plan](06-delivery-plan.md) — vertical slices, acceptance gates, and deferred work.
7. [Anonymisation and pseudonymisation](07-de-identification.md) — purpose-specific identity handling, redaction, and re-identification controls.
8. [RAG evaluation and testing](08-rag-evaluation-and-testing.md) — gold datasets, layered metrics, baselines, CI gates, and failure attribution.

## Decision Status

- **Observed:** Claude Code and Codex CLI support local MCP servers over standard input/output.
- **Inferred:** One shared MCP contract avoids coupling the memory core to either client.
- **Proposed:** A local daemon, SQLite-backed storage, local embeddings, and explicit egress manifests form the reference implementation.

## Governing Constraints

- Local storage is the source of truth.
- Raw history is not automatically durable memory.
- Memory is evidence, never executable instruction.
- Identifiers are pseudonymised locally and anonymised when linkage is unnecessary.
- Every model-bound context item has a reason and provenance.
- Deletion blocks retrieval immediately and cleans derived state.
- Remote extraction or consolidation is opt-in and visible.
- Retrieval and generation changes must pass a versioned held-out evaluation set.
- Grounding, prompt-injection resistance, tool authorization, and regression detection are release-blocking quality gates.

## Related Concepts

- [Pluggable tool blueprint](../notes/09-pluggable-tool-blueprint.md)
- [Continual personalized memory](../notes/10-continual-personalized-memory.md)
- [Adaptive memory retrieval](../notes/13-adaptive-memory-retrieval.md)
- [Memory governance and safety](../notes/14-memory-governance-and-safety.md)
- [Personalized-memory prototype](../notes/16-personalized-memory-prototype.md)
