# System Architecture

## Decision Status

- **Proposed:** Reference implementation architecture.
- **Confidence:** High for the process boundaries; medium for the initial storage and embedding choices until benchmarked.

## Runtime Shape

```text
┌──────────────────── local machine ────────────────────┐
│                                                       │
│  Claude Code                 Codex CLI                │
│       │                          │                    │
│       └────── MCP over stdio ────┘                    │
│                       │                               │
│               memory-loom-mcp                         │
│                       │ Unix socket                   │
│                       ▼                               │
│                 memory-loomd                          │
│       ┌──────────┬────┼────────────┐                  │
│       ▼          ▼    ▼            ▼                  │
│  policy     de-identifier     retrieval     memory    │
│  engine                      engine         service   │
│       │          │    │            │                  │
│       └──────────┴────┼────────────┘                  │
│                       ▼                               │
│       SQLite + FTS5 + local vector index              │
│                       │                               │
│              local embedding model                    │
└───────────────────────┼───────────────────────────────┘
                        │ approved context only
                        ▼
             Anthropic or OpenAI model API
```

## Components

| Component | Responsibility | Network access |
|---|---|---|
| `memory-loomd` | Own policy, storage, retrieval, revisions, and audit events | Denied by default |
| `memory-loom-mcp` | Translate MCP calls into daemon requests | None |
| `memory-loom` | Local inspect, approve, correct, export, and forget commands | None |
| Policy engine | Decide capture, promotion, retrieval, and egress eligibility | None |
| De-identification engine | Detect and transform identifiers and sensitive data for each purpose | None |
| Retrieval engine | Perform lexical search, vector search, reranking, and budgeting | None |
| Embedding adapter | Produce vectors using a local model | None by default |
| Provider adapter | Optional extraction, consolidation, or generation calls | Restricted to configured provider |

## Process Boundaries

- The daemon binds to a user-owned Unix domain socket, not a public TCP port.
- MCP bridges are disposable child processes launched by each client.
- The daemon is the single writer; SQLite uses WAL mode for concurrent reads.
- All provider calls pass through one egress gateway that writes a manifest before sending.
- All durable storage, embedding, export, telemetry, and provider paths pass through the de-identification engine.
- Client adapters contain no memory policy and no provider-specific domain logic.

## Core Flows

### Retrieve

```text
task signal
  -> normalize locally
  -> authorize user/project scope
  -> lexical + vector candidate search
  -> status, sensitivity, and scope filters
  -> local reranking and token-budget selection
  -> context manifest
  -> MCP result
  -> client includes selected context in its model request
```

### Remember

```text
explicit statement or correction
  -> detect identifiers and secrets locally
  -> de-identify for storage and embedding
  -> classify sensitivity and memory type
  -> create candidate with evidence reference
  -> deterministic admission gates
  -> manual approval in MVP
  -> versioned memory record
  -> local indexes
```

### Forget

```text
forget request
  -> authorize scope
  -> tombstone memory immediately
  -> remove search and vector entries
  -> invalidate dependent candidates and derivations
  -> append deletion audit event
```

## Failure Behavior

- If the daemon is unavailable, both clients continue without memory.
- If retrieval exceeds its deadline, return no context rather than a partial unsafe result.
- If scope or consent is unknown, deny capture and retrieval.
- If local embedding fails, lexical retrieval remains available.
- If provider egress is disabled, remote extraction and consolidation remain unavailable.
- If required de-identification returns review or deny, capture and egress fail closed.

## Source-Specific Elements

- MCP configuration syntax differs between Claude Code and Codex CLI.
- Hook and plugin lifecycle events differ by client and remain adapter concerns.
- Provider retention and telemetry controls are external product settings, not properties of Memory Loom.

## Evidence Basis

- [Bounded tools and context shaping](../notes/06-bounded-tools-and-context-shaping.md)
- [Pluggable tool blueprint](../notes/09-pluggable-tool-blueprint.md)
- [Personalized-memory prototype](../notes/16-personalized-memory-prototype.md)
- [Anonymisation and pseudonymisation](07-de-identification.md)
- [Codex MCP documentation](https://developers.openai.com/codex/mcp/)
- [Claude Code MCP documentation](https://docs.anthropic.com/en/docs/claude-code/mcp)
