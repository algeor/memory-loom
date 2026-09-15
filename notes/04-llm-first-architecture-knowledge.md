---
id: AH-004
title: LLM-first architecture knowledge
status: initial
maturity: observed
source_repo: pipeline-fl-control-plane
source_commit: df513fa41484fc3e218d836d951ee46d0abc7513
---

# LLM-First Architecture Knowledge

## Use When

- A large architecture document is accurate but too broad for reliable task-level agent use.

## Core Pattern

Optimize architecture documentation for routing and bounded retrieval without discarding the full historical narrative.

## Focused Document Contract

Each focused architecture note answers, in scan order:

1. When should I read this?
2. When should I not read this?
3. What decision area does it own?
4. What happens today?
5. Who owns each boundary?
6. What contracts are stable?
7. How can it fail?
8. Which source files implement it?
9. Which tests verify it?
10. Which specs are related?
11. What changes require this document to be revisited?

## Lossless Migration Pattern

- Keep the legacy overview available during migration.
- Create a coverage map for every legacy section.
- Mark each section as migrated, retained, linked, appended, or deprecated with reason.
- Make focused docs authoritative only for their declared areas.
- Move long examples and diagrams deeper; keep routing facts near the top.

## Documentation As A Tested Interface

The source adds mechanical checks for:

- required headers;
- broken index links;
- route paths that do not exist;
- legacy-section coverage;
- index discoverability of focused docs;
- the instruction entrypoint pointing to the routing index.

The validator runs in pre-commit and CI with strict spec validation.

## Generalized Primitive

Treat knowledge documents like tools: each has a description, applicability conditions, boundaries, inputs, outputs, failure modes, implementation links, and update triggers.

## Plugin Implication

- Generate and validate focused-doc skeletons.
- Build a route index from metadata.
- Report uncovered legacy sections and broken evidence links.
- Assemble a task context pack from only the selected documents.

## Evidence

- `pipeline-fl-control-plane@df513fa4:openspec/changes/llm-first-architecture-docs/proposal.md` — rationale and scope.
- `pipeline-fl-control-plane@df513fa4:docs/design/templates/llm-first-architecture-doc.md` — focused document contract.
- `pipeline-fl-control-plane@df513fa4:docs/design/architecture-coverage.md` — lossless migration ledger.
- `pipeline-fl-control-plane@df513fa4:scripts/validate_architecture_docs.py` — structural validation.
- `pipeline-fl-control-plane@df513fa4:.github/workflows/architecture-docs-validation.yaml` — CI enforcement.

## Open Questions

- Can source and test links be validated semantically, not only for path existence?
