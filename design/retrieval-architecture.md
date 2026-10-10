# Retrieval Architecture

## Status

- Classification: design decision
- Implementation status: implemented for scoped lexical retrieval with pluggable reranking
- Boundary: local MCP or JSON stdio from host into SQLite
- Scientific result: no

This document shows how Memory Loom retrieves approved memory for a current
assistant request. The current request remains higher priority than any returned
memory.

## Architecture

```mermaid
flowchart LR
    Request[Current user request]
    Host[Agent host]
    Retrieve[memory_loom_retrieve]
    Scope[Host-bound scope\nuser/project/task]
    Store[(SQLite memory store)]
    Policy[Eligibility filters]
    Lexical[FTS5 lexical search\nBM25 score]
    Rerank[Candidate reranker]
    Budget[Context budget]
    Context[Bounded memory context]
    Model[Assistant model]
    Trace[(Retrieval trace)]

    Request --> Host
    Host --> Retrieve
    Scope --> Retrieve
    Retrieve --> Store
    Store --> Policy
    Policy --> Lexical
    Lexical --> Rerank
    Rerank --> Budget
    Budget --> Context
    Context --> Model
    Policy --> Trace
    Lexical --> Trace
    Rerank --> Trace
    Budget --> Trace
```

## Eligibility And Ranking

```mermaid
flowchart TB
    All[Latest memory records]
    ScopeFilter{Scope matches?}
    StateFilter{Active at request time?}
    RuleGroup[Group by rule_key]
    Specificity[Keep narrowest matching scope]
    Conflict{Equal-scope conflict?}
    Search[FTS5 MATCH over eligible statements]
    Rerank[Pluggable reranker]
    Select[Select top N]

    All --> ScopeFilter
    ScopeFilter -->|no| ScopeOut[scope_filtered]
    ScopeFilter -->|yes| StateFilter
    StateFilter -->|no| StateOut[state_filtered]
    StateFilter -->|yes| RuleGroup
    RuleGroup --> Specificity
    Specificity -->|broader rule| SpecificityOut[specificity_filtered]
    Specificity --> Conflict
    Conflict -->|yes| ConflictOut[conflict_filtered]
    Conflict -->|no| Search
    Search -->|no match| LexicalOut[lexical_filtered]
    Search -->|matched candidates| Rerank
    Rerank --> Select
    Select -->|inside limit| Selected[selected]
    Select -->|outside limit| BudgetOut[budget_filtered]
```

## Retrieval Sequence

```mermaid
sequenceDiagram
    participant H as Host
    participant M as Memory API
    participant DB as SQLite
    participant R as Reranker
    participant A as Assistant model

    H->>M: retrieve(query, limit)
    M->>M: Bind configured scope
    M->>DB: Load latest memory records
    M->>M: Apply scope, state, specificity, conflict filters
    M->>DB: FTS5 search eligible statements
    DB-->>M: lexical candidates + BM25 scores
    M->>R: rerank(query, candidates)
    R-->>M: ordered candidates + rerank scores
    M->>DB: Persist retrieval trace
    M-->>H: context + selected records + evidence_ids
    H->>A: Current request + fallible memory context
```

## Provenance Path

```mermaid
flowchart LR
    Selected[Selected memory]
    EvidenceId[evidence_ids]
    Evidence[Evidence event]
    Revision[Revision history]
    Trace[Retrieval trace]
    Demo[Conference demo view]

    Selected --> EvidenceId
    EvidenceId --> Evidence
    Evidence --> Revision
    Selected --> Trace
    Trace --> Demo
    Revision --> Demo
```

## Output Shape

```mermaid
flowchart TB
    Response[Retrieve response]
    QueryId[query_id]
    Scope[active scope]
    Context[serialized context]
    Selected[selected records]
    Evidence[evidence_ids]
    Reason[reason_code]

    Response --> QueryId
    Response --> Scope
    Response --> Context
    Response --> Selected
    Selected --> Evidence
    Selected --> Reason
```

## Conference Summary

Memory Loom retrieves only records that pass policy filters before ranking. It
then separates candidate search from reranking, records the full decision trace,
and returns selected memories with provenance IDs so the host can explain why a
memory appeared.
