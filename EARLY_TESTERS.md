# Early Tester Guide

## Status

Memory Loom `0.1.0` is a **local research prototype**, not a production memory
service. Early testing evaluates usability and failure modes; it does not
establish that memory improves assistant performance.

## Supported Setup

- Python `3.14`
- `uv`
- Codex or Claude Code with local stdio MCP support
- macOS or Linux

Gemini CLI onboarding, Windows validation, remote hosting, and the non-MCP JSON
CLI are deferred.

## Install

```zsh
uv python install 3.14
uv tool install --python 3.14 \
  https://github.com/algeor/memory-loom/releases/download/v0.1.0/memory_loom-0.1.0-py3-none-any.whl
memory-loom --version
```

From the project where the assistant should use memory:

```zsh
memory-loom onboard codex --project-id your-project
# or
memory-loom onboard claude --project-id your-project
```

By default, records are stored outside the checkout at
`$XDG_DATA_HOME/memory-loom/<project>.db`, falling back to
`~/.local/share/memory-loom/<project>.db`. Keep the path printed by onboarding.

Restart the host, inspect its MCP tools, then try one explicit preference. The
assistant must show a proposal and receive explicit approval before committing
it.

## Diagnose

```zsh
memory-loom doctor --database /absolute/path/to/project.db
```

The report includes versions, SQLite integrity, schema compatibility, FTS5
availability, path writability, and supported host availability. It does not
read or print memory statements.

## Backup And Restore

Stop Codex and Claude Code before restoring a database.

```zsh
memory-loom backup --database /absolute/path/to/project.db
memory-loom restore \
  --from /absolute/path/to/backup.db \
  --database /absolute/path/to/project.db \
  --yes
```

Restore creates a safety backup before replacing an existing database and then
applies any pending migrations.

## Upgrade

Back up the database, install the wheel URL for the new release, and migrate:

```zsh
memory-loom backup --database /absolute/path/to/project.db
uv tool install --force --python 3.14 <new-release-wheel-url>
memory-loom migrate --database /absolute/path/to/project.db
memory-loom doctor --database /absolute/path/to/project.db
```

Downgrading after a schema migration is unsupported. Restore the pre-upgrade
backup instead.

## Privacy Limits

- Memory is local but **not encrypted** by Memory Loom.
- Do not save secrets, credentials, personal data, or raw operational logs.
- Only explicit preferences and direct corrections belong in the current store.
- Retrieval output is fallible context; the current request remains authoritative.
- Deletion erases stored user-authored content from the live database, but it does not erase independent filesystem backups.

## Report Feedback

Use the repository's early-tester issue template. Include the `doctor` output,
host name, operating system, reproduction steps, and expected behavior.

Do **not** attach a database, memory text, credentials, personal data, or raw
conversation logs. Replace examples with synthetic content.

## Uninstall

```zsh
codex mcp remove memory-loom
claude mcp remove memory-loom --scope local
uv tool uninstall memory-loom
```

Remove the marked Memory Loom block from the project's `AGENTS.md` or
`CLAUDE.md`. Uninstalling the tool intentionally leaves SQLite databases and
backups in place; delete them manually only after confirming they are no longer
needed.
