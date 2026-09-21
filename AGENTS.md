# Memory Loom Repository Instructions

This repository contains a **research specification**, a **reference design**, and **source-backed pattern notes**. Keep those artifacts separate.

## Start Here

- Read `README.md` for scope and maturity.
- Read `research/claims.md` before making or changing a claim.
- Read `STATUS.md` before continuing implementation or research work.
- Read only the smallest relevant design or evidence note.

## Evidence Rules

- Label claims as **observed**, **inferred**, **hypothesis**, **design decision**, or **result**.
- Never present a hypothesis or design decision as an empirical result.
- Cite repository, commit, path, and symbol or section for source observations.
- Cite primary literature for external research claims.
- Record contradictory or missing evidence instead of smoothing it over.
- Do not copy secrets, credentials, private keys, personal data, or raw operational logs.

## Editing Rules

- Use `apply_patch` for manual file edits.
- Keep one concept per evidence note.
- Keep the research protocol independent of implementation details.
- Put implementation choices under `design/`, not in the claim register.
- Update the relevant source ledger when evidence changes.
- Update `STATUS.md` after a meaningful milestone.
- Prefer concise claims, explicit assumptions, and falsifiable criteria.

## Required Boundaries

- `research/` defines what is being tested and how evidence will be judged.
- `design/` defines one replaceable system under test.
- `notes/` records reusable source-backed patterns.
- `sources/` records provenance and verification state.
