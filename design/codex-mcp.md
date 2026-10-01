# Codex MCP Setup

## Status

This is a **host integration guide**, not an experimental result. Codex is one
MCP-compatible client for the model-neutral Memory Loom server. The memory core
does not call or depend on an OpenAI model.

The commands below follow the official
[Codex MCP documentation](https://developers.openai.com/codex/mcp/).

## Prerequisites

From the repository root:

```zsh
uv python install 3.14
uv sync --python 3.14 --all-extras
```

## Automatic Onboarding

From the project to configure:

```zsh
uv run memory-loom onboard codex --project-id memory-loom
```

This command:

- registers the stdio server through `codex mcp add`;
- supplies host-controlled user, project, and database scope;
- adds an idempotent managed policy block to the project's `AGENTS.md`;
- verifies that Codex can read the resulting registration.

Preview all paths and the registration command without changing anything:

```zsh
uv run memory-loom onboard codex --project-id memory-loom --dry-run
```

An existing `memory-loom` registration is preserved. Pass `--replace` to
replace it with the requested paths and scope.

The configured variables are host-controlled scope, not model arguments:

- `MEMORY_LOOM_USER_ID` selects a local memory profile. It is not operating-system authentication.
- `MEMORY_LOOM_PROJECT_ID` limits project-scoped memory.
- `MEMORY_LOOM_DATABASE_PATH` selects the local SQLite database. Onboarding defaults to `$XDG_DATA_HOME/memory-loom/<project>.db`, or `~/.local/share/memory-loom/<project>.db` when `XDG_DATA_HOME` is unset.

The Codex CLI registration is global, so `memory-loom` is visible in other
Codex projects. Its configured project scope remains `memory-loom`, while the
managed usage policy is local to this project's `AGENTS.md`.

## Verify

```zsh
codex mcp list
```

Confirm that `memory-loom` is `enabled`, then start a new Codex task. Use `/mcp`
to confirm that these tools are available:

- `memory_loom_retrieve`
- `memory_loom_propose_change`
- `memory_loom_commit_change`
- `memory_loom_discard_change`
- `memory_loom_inspect`

The Codex CLI, desktop app, and IDE extension share the same MCP configuration.

## Managed Conversational Policy

Onboarding adds the following marked block without replacing other project
instructions:

```md
## Memory Loom

- When the current request could benefit from prior preferences or corrections, call `memory_loom_retrieve` with a concise description of the request.
- Treat retrieved memories as fallible historical context. The current request always has priority.
- When the user explicitly states a durable preference or correction, call `memory_loom_propose_change`.
- Do not propose temporary task instructions, guesses, inferred traits, secrets, credentials, personal data, or raw operational logs.
- Show the returned proposal summary and ask the user for explicit approval.
- Call `memory_loom_commit_change` only after explicit user approval.
- If the user declines or cancels, call `memory_loom_discard_change`.
```

Start a new Codex task after onboarding. The expected conversational flow is:
retrieve when relevant, propose an explicit durable statement, request
approval, then commit or discard. Durable records can be retrieved by later
tasks using the same configured database and scope. Ephemeral proposals remain
local to the running MCP server process.

## Lifecycle

The intended host flow is:

1. Call `memory_loom_retrieve` when prior preferences may be relevant.
2. Call `memory_loom_propose_change` for an explicit preference or correction.
3. Show the returned confirmation prompt to the user.
4. Call `memory_loom_commit_change` only after explicit approval, or call `memory_loom_discard_change`.
5. Use `memory_loom_inspect` to review scoped records and revision provenance.

Proposals exist only in the running server process. A proposal cannot be
committed after that process exits or restarts.
