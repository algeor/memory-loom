# Claude Code MCP Setup

## Status

This is a **host integration guide**, not an experimental result. Claude Code is
one MCP-compatible client for the model-neutral Memory Loom server. The memory
core does not call or depend on an Anthropic model.

The commands below follow the official
[Claude Code MCP documentation](https://code.claude.com/docs/en/mcp).

## Prerequisites

From the repository root:

```zsh
uv python install 3.14
uv sync --python 3.14 --all-extras
```

## Automatic Onboarding

From the project to configure:

```zsh
uv run memory-loom onboard claude --project-id memory-loom
```

This command:

- creates a project-local registration through `claude mcp add`;
- supplies host-controlled user, project, and database scope;
- adds an idempotent managed policy block to the project's `CLAUDE.md`;
- verifies that Claude Code can read the resulting registration.

Preview all paths and the registration command without changing anything:

```zsh
uv run memory-loom onboard claude --project-id memory-loom --dry-run
```

An existing `memory-loom` registration is preserved. Pass `--replace` to
replace it with the requested paths and scope.

The configured variables are host-controlled scope, not model arguments:

- `MEMORY_LOOM_USER_ID` selects a local memory profile. It is not operating-system authentication.
- `MEMORY_LOOM_PROJECT_ID` limits project-scoped memory.
- `MEMORY_LOOM_DATABASE_PATH` selects the local SQLite database. Repository `*.db` files are ignored by Git.

## Verify

```zsh
claude mcp get memory-loom
claude mcp list
```

Confirm that `memory-loom` reports `Connected`, then start a new Claude Code
session and use `/mcp` to inspect the available tools.

## Remove

```zsh
claude mcp remove memory-loom --scope local
```

The lifecycle and approval behavior are identical to the Codex integration in
[`codex-mcp.md`](codex-mcp.md). Proposals exist only in the server process that
created them.
