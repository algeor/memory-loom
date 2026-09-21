# Client Integrations

## Decision Status

- **Observed:** Claude Code and Codex CLI can launch local MCP servers.
- **Proposed:** Both clients use the same MCP bridge and tool schemas.
- **Confidence:** High for MCP portability; client lifecycle automation must be validated per release.

## Portable Integration Layer

The shared local MCP server exposes a deliberately small tool surface:

| Tool | Mutability | Purpose |
|---|---|---|
| `memory_context` | Read-only | Return a bounded context manifest for the current task |
| `memory_remember` | Writes candidate | Record an explicit preference, correction, fact, or lesson |
| `memory_feedback` | Writes event | Mark retrieved memory useful, irrelevant, incorrect, or harmful |
| `memory_forget` | Destructive | Delete a record and invalidate dependent state |
| `memory_explain` | Read-only | Explain provenance, status, retrieval, and egress use |

`memory_forget` requires client confirmation. `memory_remember` creates a candidate by default; it does not silently create durable memory.

## Shared Server Command

Both clients launch the same bridge:

```text
memory-loom-mcp --socket ~/.local/share/memory-loom/daemon.sock
```

The bridge contains no database credentials and cannot bypass daemon policy.

## Codex CLI Adapter

- Register `memory-loom-mcp` as a local STDIO MCP server.
- Package optional skills that teach when to retrieve, remember, explain, and request deletion.
- Use MCP tool approval settings to keep writes and deletion visible.
- Keep project instructions limited to tool-selection guidance; memory content is returned only by tools.

Example configuration shape:

```toml
[mcp_servers.memory_loom]
command = "memory-loom-mcp"
args = ["--socket", "~/.local/share/memory-loom/daemon.sock"]
```

Exact configuration fields must be checked against the installed Codex version.

## Claude Code Adapter

- Register `memory-loom-mcp` as a local STDIO MCP server at user or project scope.
- Package optional plugin content for commands, skills, and hook configuration.
- Use hooks only for task metadata and outcome signals after the user enables them.
- Do not ingest complete transcripts by default.

Example command shape:

```text
claude mcp add --transport stdio memory-loom -- memory-loom-mcp
```

Exact command flags and scope options must be checked against the installed Claude Code version.

## Client-Neutral Usage Flow

1. The client asks `memory_context` for relevant local context.
2. The bridge returns a bounded, labeled context manifest.
3. The client sends that manifest with the current task to its configured model provider.
4. The client optionally records explicit corrections through `memory_remember`.
5. The user can inspect or delete the record with either MCP tools or the local CLI.

## Compatibility Rules

- MCP schemas are versioned independently from client packaging.
- Unknown client metadata is ignored, not persisted automatically.
- A client capability matrix records support for hooks, prompts, resources, and approvals.
- Core correctness never depends on a vendor-specific hook.
- If a client stops supporting an adapter feature, manual MCP tools continue to work.

## Evidence Basis

- [Codex MCP documentation](https://developers.openai.com/codex/mcp/)
- [Claude Code MCP documentation](https://docs.anthropic.com/en/docs/claude-code/mcp)
- [Declarative agent runtime](../notes/05-declarative-agent-runtime.md)
- [Pluggable tool blueprint](../notes/09-pluggable-tool-blueprint.md)
