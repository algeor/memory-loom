---
id: AH-008
title: Review, validation, and failure attribution
status: initial
maturity: inferred
source_repo: pipeline-fl-control-plane
source_commit: df513fa41484fc3e218d836d951ee46d0abc7513
---

# Review, Validation, And Failure Attribution

## Use When

- A change needs more than a generic test run or one undifferentiated reviewer.

## Core Pattern

Shape review and validation from the change's risk profile, then synthesize evidence into one accountable verdict.

## Observed Review Pattern

- Understand author intent and blast radius before judging implementation.
- Classify changed files to activate relevant specialist roles.
- Run specialist reviews independently and in parallel.
- Require each finding to follow a common schema with location, impact, evidence, and recommendation.
- Deduplicate by location and category; consensus raises confidence but is not required.
- Cross-reference existing review discussion to distinguish new, recurring, and already-resolved findings.
- Adversarially verify findings before publishing them because reviewers can hallucinate or miss context.

## Observed Validation Pattern

- Start with the smallest focused test for the changed subsystem.
- Expand only as confidence and blast radius require.
- Validate documentation structure and links mechanically.
- For live integration checks, derive scenarios from architecture contracts.
- Attribute failures as harness/deployment issue, application bug, or infrastructure issue.
- Preserve failed environments when they contain necessary debugging evidence; clean up successful disposable environments.

## Generalized Primitive

A **validation planner** takes changed paths and declared contracts, then returns:

```yaml
reviewers: [security, python, data]
checks:
  - command: focused-test-command
    proves: contract-id
    cost: low
escalation:
  on_failure: classify
  broader_gate_after: focused-pass
```

## Portability Limits

- More agents do not guarantee better review; role overlap and weak synthesis create noise.
- Live environments may be expensive or destructive and need explicit lifecycle policy.
- File classification is a heuristic; contract metadata is a stronger long-term signal.

## Plugin Implication

- Reviewer registry keyed by risk and file type.
- Structured finding schema and deduplication engine.
- Evidence challenges before final publication.
- Test-plan generator mapping contracts to checks.
- Failure attribution taxonomy to stop application debugging when the harness itself is broken.

## Evidence

- `pipeline-fl-control-plane@df513fa4:.claude/commands/council-review.md` — specialist dispatch, synthesis, and adversarial verification.
- `pipeline-fl-control-plane@df513fa4:.claude/commands/council-test.md` — architecture-derived integration scenarios and failure attribution.
- `pipeline-fl-control-plane@df513fa4:docs/QUALITY.md` — focused-first validation policy.
- `pipeline-fl-control-plane@df513fa4:scripts/validate_architecture_docs.py` — domain-specific static validation.

## Open Questions

- What evidence threshold should suppress a low-confidence finding automatically versus label it for human review?
