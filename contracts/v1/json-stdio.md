# JSON Stdio Contract v1

## Status

This is a **design decision** and implemented fallback for hosts that cannot use
MCP. It exposes the same lifecycle operations and does not change the research
claim or memory model.

## Transport

Start one persistent process with host-controlled environment variables:

```zsh
MEMORY_LOOM_USER_ID=user-a \
MEMORY_LOOM_PROJECT_ID=example-project \
MEMORY_LOOM_DATABASE_PATH=/absolute/path/to/memory.db \
memory-loom json-stdio
```

The host writes one JSON request per line and reads one JSON response per line.
The process must remain alive between proposal and commit so unapproved
proposals stay ephemeral and process-local.

## Request

```json
{"id":"request-001","method":"memory_loom_retrieve","params":{"query":"Review this code.","limit":5}}
```

`id` is a caller-generated correlation identifier. `method` is one of the five
v1 lifecycle operations. `params` matches the corresponding MCP tool contract.
User, project, task, database, and approval state are never accepted as
model-controlled scope parameters.

## Response

Success:

```json
{"id":"request-001","ok":true,"result":{"query_id":"json-generated","scope":{"user_id":"user-a","project_id":"example-project","task_id":null},"context":"","selected":[]}}
```

Failure:

```json
{"id":"request-001","ok":false,"error":{"code":"invalid_request","message":"request does not satisfy the JSON CLI contract"}}
```

Errors are bounded to the stable codes in [`mcp-tools.md`](mcp-tools.md) and do
not expose SQL, unrelated memory content, or credentials. A malformed request
does not terminate the process.

## Approval Boundary

The host must display the unchanged proposal summary and obtain explicit user
approval before sending `memory_loom_commit_change`. Commit accepts only the
proposal identifier, approval event identifier, and `approved_by=user`; durable
content cannot be replaced during commit.

