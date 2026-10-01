# Development Dataset Plan v1

## Status

- Purpose: Phase 3 pilot only
- Split: development
- Data: synthetic
- Template creation: complete
- Scenarios: 24 across 6 families
- Scientific result: no

## Pilot Shape

The development set contains 24 scenarios:

- 6 independent template families;
- 4 surface variants per family;
- at least one memory-dependent query per scenario;
- matched no-memory queries where appropriate.

Variants may change wording, project names, and task content. They must not change the lifecycle mechanism being tested.

## Template Families

| ID | Mechanism | Expected behavior |
|---|---|---|
| global-preference | Approved user-wide preference | Retrieve and follow the active preference |
| project-exception | Project rule overrides a broader rule | Retrieve only the more specific applicable rule |
| direct-correction | User corrects failed behavior | Apply the correction on a later related task |
| preference-change | New preference supersedes an old one | Retrieve the new record; forbid the superseded one |
| deletion | User deletes an approved preference | Retrieve nothing from the deleted lineage |
| hard-negative | Similar but inapplicable memory exists | Supply no memory context |

## Construction Rules

- Keep one primary mechanism per family.
- Use unique UUIDs across all scenarios.
- Keep all user content synthetic.
- Never use future events or labels to construct context.
- Label relevant, acceptable, and forbidden memory IDs explicitly.
- Keep condition construction identical across scenarios.
- Treat the existing `scope-deletion-001` fixture as a contract fixture, not a pilot observation.

## Pilot Limit

The 24 scenarios estimate variance, annotation problems, and failure modes. They do not provide confirmatory evidence or determine held-out conclusions.

## Engineering Validation

Observed on 2026-09-30:

- all 24 pilot scenarios pass contract validation;
- each family contains exactly four scenarios;
- no UUID is reused across pilot scenarios;
- live B3 retrieval matches the labeled relevant IDs for all 24 queries;
- the repository test suite passes with 13 tests.

These checks establish fixture integrity only. They are not model evaluations or scientific results.
