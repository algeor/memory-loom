# Project-Scoped Guidance

## Status

This is a **design decision** for using the existing preference lifecycle. It
does not expand the first study beyond explicit, user-approved preferences and
direct corrections, and it is not an experimental result.

## Purpose

Project-scoped guidance records durable working conventions that should apply
only while an assistant is operating in one project. This can help when a
project uses an internal or uncommon language, framework, API, or workflow.

The stored statement should describe how the assistant should work, not attempt
to reproduce the project's entire reference corpus.

Suitable examples:

- "In this project, use `spawn_task` instead of the deprecated `start_task`."
- "When generating service code here, return `Result<T>` rather than throwing."
- "For this project's internal language, place imports before capability declarations."
- "Treat examples under `examples/canonical/` as the preferred module structure."

Unsuitable examples:

- complete language manuals or source trees;
- unreviewed notes inferred by the assistant;
- credentials, private keys, personal data, or raw operational logs;
- temporary instructions that matter only to the current task;
- claims that the guidance trains the model or guarantees correct code.

## Lifecycle

Project guidance uses the existing proposal, approval, correction, inspection,
retrieval, and deletion lifecycle:

1. The user explicitly states a durable project convention or correction.
2. The host proposes it as `kind=preference` or `kind=correction` with
   `scope_level=project` and an approval-time `rule_key`.
3. The assistant shows the proposal summary without treating it as committed.
4. The user explicitly approves or declines the unchanged proposal.
5. Approved guidance becomes eligible only for the configured user and project.
6. Later corrections create a new version; deletion makes the lineage
   ineligible and erases user-authored content according to the memory model.

## Retrieval Boundary

The assistant should query for guidance relevant to the current request. Scope
and lifecycle filters run before lexical ranking, and the current request keeps
priority over retrieved records.

This is durable scoped memory, not model training and not bulk document RAG.
Adding document ingestion, chunking, embeddings, or hybrid retrieval would be a
separate design and evaluation milestone.

## Authoring Guidance

- Keep one actionable convention per memory.
- Use concrete vocabulary likely to appear in future requests.
- Prefer a falsifiable instruction over broad background information.
- Use stable `rule_key` values so corrections target the same behavior.
- Store the narrowest applicable scope; project guidance should not become a
  user-wide rule.
- Link to canonical project documentation instead of copying large documents
  into memory.

