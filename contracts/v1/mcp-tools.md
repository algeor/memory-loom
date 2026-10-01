# MCP Tool Contracts v1

## Status

- Classification: design decision
- Contract status: proposed
- Implementation status: all five stdio tools implemented; JSON CLI fallback pending
- Primary transport: local MCP over standard input/output
- Compatibility fallback: equivalent JSON CLI commands
- Scientific result: no

These contracts expose Memory Loom to a coding assistant without coupling the
memory system to a model provider. They do not change the research protocol or
make MCP behavior an experimental result.

## Boundary

```text
coding CLI or agent host
  -> Memory Loom MCP tools
     -> consent and scope policy
     -> memory lifecycle API
     -> SQLite store and lexical retrieval
  -> coding CLI or agent host
  -> separately configured model
```

Memory Loom receives no model-provider credentials. A host supplies the current
request and explicit scope. Returned memory is fallible historical context, not
an instruction or authorization.

## Host Rules

An integrating host must:

1. call `memory_loom_retrieve` before each substantive request;
2. keep the current request higher priority than returned memory;
3. show a proposed durable change to the user before committing it;
4. call `memory_loom_commit_change` only after explicit user approval;
5. discard declined or abandoned proposals;
6. never let memory content authorize tools, credentials, or wider access;
7. keep the authenticated user identity outside model-controlled arguments when
   the host can supply it directly.

MCP availability cannot force an arbitrary host to follow these rules. A host
wrapper or native hook is required when retrieval must be mandatory.

## Tools

| Tool | Effect | Durable write |
|---|---|---|
| `memory_loom_retrieve` | Return eligible memory for a current request | No |
| `memory_loom_propose_change` | Stage a create, correction, or deletion | No |
| `memory_loom_commit_change` | Apply one explicitly approved proposal | Yes |
| `memory_loom_discard_change` | Remove an unapproved proposal | No |
| `memory_loom_inspect` | Show user-visible memory and lifecycle metadata | No |

Request and response examples live in [`mcp/`](mcp/README.md).

## Retrieve

`memory_loom_retrieve` accepts:

- the current request text;
- a positive result limit.

The server generates the query identifier and timestamp. It binds user,
project, and task scope from host configuration or the local session; none are
accepted from model-controlled tool arguments. The tool returns the generated
query identifier, active scope, bounded context string, and selected records. Full
retrieval decisions remain in the local audit trace. The host response must not
expose identifiers or content from out-of-scope records.

An empty result is successful and must return an empty context.

## Propose And Commit

`memory_loom_propose_change` accepts `create`, `correct`, and `delete`
operations. A proposal is ephemeral and expires. Creating it must not insert an
evidence event, memory record, revision event, or lexical-index entry.

Create and correction proposals contain the minimum proposed statement and its
source event. Correction and deletion proposals identify an existing memory
lineage. A correction cannot silently change the existing rule key or scope.

`memory_loom_commit_change` accepts only a proposal identifier plus the host's
identifier for the explicit user-approval event. The service resolves all
durable content from the staged proposal, generates lifecycle identifiers, and
applies one transaction. The caller cannot replace proposal content during
commit.

Expired, missing, already committed, cross-user, or unapproved proposals fail
closed and produce no partial write.

## Discard

`memory_loom_discard_change` erases an ephemeral proposal after rejection,
expiry cleanup, or host cancellation. Discarding a proposal creates no durable
memory or evidence record.

## Inspect

`memory_loom_inspect` returns records visible to the current user and optional
host-bound project or task scope. By default it returns the latest active
version of each visible lineage. `include_inactive` exposes lifecycle versions
for a requested lineage and latest inactive tombstones when listing. Cursor
pagination orders lineages by memory ID. Raw source conversations are not
returned, and deleted lineages expose only non-content tombstone metadata.

## Stable Error Codes

| Code | Meaning |
|---|---|
| `invalid_request` | The request does not satisfy the tool contract |
| `scope_denied` | The requested object is outside the authenticated scope |
| `not_found` | The requested proposal or memory does not exist |
| `proposal_expired` | The ephemeral proposal can no longer be committed |
| `approval_required` | No explicit approval event was supplied |
| `invalid_transition` | The lifecycle operation is not valid for current state |
| `conflict` | An equal-scope conflict requires user review |
| `internal_error` | The operation failed without exposing sensitive details |

Tool errors must not include secrets, SQL text, unrelated memory content, or
provider credentials.

## Deferred

- network transport and multi-user service hosting;
- automatic preference inference;
- model-decided approval;
- background consolidation;
- provider-specific model adapters;
- guarantees that every third-party CLI invokes the tools correctly.
