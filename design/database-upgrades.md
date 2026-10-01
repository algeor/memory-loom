# SQLite Upgrade Safety

## Status

This is a **design decision** and tested reference behavior, not a production
durability guarantee. Memory Loom keeps user records in a separate SQLite file;
application code and database contents are upgraded independently.

## Early User Upgrade Flow

Keep `MEMORY_LOOM_DATABASE_PATH` unchanged between releases. For the current
repository-based distribution:

```zsh
git pull --ff-only
uv sync --python 3.14 --all-extras
uv run memory-loom migrate --database /absolute/path/to/memory-loom.db
```

Then restart the MCP host. The database file is ignored by Git, so a normal
pull does not replace it. Commands such as `git clean -x` can delete ignored
files and must not be used without an external backup.

## Migration Guarantees

When a newer release contains pending migrations, `memory-loom migrate` and
normal store startup:

1. acquire a SQLite write lock;
2. reject migration histories newer than the installed code;
3. create a consistent backup before changing an existing database;
4. apply pending numbered migrations in one transaction;
5. roll back the transaction if any statement fails.

Backups are written beside the database under `<database>.backups/`. No backup
is created when the database is already current.

## Release Rules

- Never edit a released migration; add the next numbered migration.
- Test upgrades from every previously distributed schema version.
- Do not support downgrades after a schema migration.
- Keep the database path outside replaceable package or virtual-environment directories.
- Preserve backups until the upgraded release has been exercised successfully.
