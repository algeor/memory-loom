---
id: AH-014
title: Memory governance and safety
status: proposed
maturity: proposed
source_artifact: design enhancement to continual-personalization brief
source_date: 2026-09-14
---

# Memory Governance And Safety

## Use When

- A system stores personal information or behavior-shaping lessons across sessions.

## Core Pattern

Make memory inspectable, scoped, revocable, and policy-controlled from capture through retrieval and deletion.

## Problem It Solves

- Personalization can become covert profiling.
- Raw conversation evidence may contain secrets or unrelated third-party data.
- Retrieved text can carry prompt injection or obsolete instructions.
- Fine-tuning can make deletion and correction harder than external storage.

## Source Implementation Status

- The brief motivates mutable external memory but does not define a complete governance implementation.
- This note adds the controls required to make that proposal responsibly implementable.

## Required Controls

- **Consent:** declare what is remembered and for which purpose.
- **Minimization:** store the smallest claim and evidence reference needed.
- **Isolation:** enforce user and tenant boundaries before semantic search.
- **Sensitivity:** block or require review for secrets, credentials, health, identity, or other protected data.
- **Transparency:** let users inspect why a memory exists and where it was used.
- **Control:** support correct, dispute, forget, export, and disable-personalization actions.
- **Retention:** expire raw evidence and stale memories under explicit policy.
- **Audit:** version changes and record admission, retrieval, and deletion decisions.
- **Training boundary:** require separate opt-in before exporting memories as fine-tuning data.

## Safety Pipeline

```text
capture policy
  -> redact and minimize
  -> authorize storage
  -> isolate and encrypt
  -> authorize retrieval
  -> label as untrusted memory context
  -> audit use
  -> correct | expire | delete
```

## Deletion Semantics

- Tombstone immediately so deleted records cannot be retrieved.
- Remove derived indexes and queued candidates.
- Recompute or dispute consolidated memories that depended on deleted evidence.
- Track completion across replicas and backups according to product policy.

## Generalized Primitive

A **memory policy engine** evaluates capture, promotion, retrieval, export, and deletion independently. Authorization is required at every stage, not only when data is first stored.

## Portability Limits

- Legal requirements vary by jurisdiction and product.
- Encryption does not replace data minimization or access control.
- Complete deletion from model weights is materially harder than deletion from external memory.

## Plugin Implication

- Policy hooks for `before_capture`, `before_promote`, `before_retrieve`, `before_export`, and `on_delete`.
- User-facing memory inventory and provenance view.
- Deny retrieval when user scope, consent, or policy state is unavailable.

## Evidence And Confidence

- **Observed:** `AH-002` prohibits secrets in notes; `AH-006` favors scoped tools; `AH-007` treats untrusted context as data.
- **Proposed enhancement:** The end-to-end governance model closes safety gaps not developed in the brief.
- **Confidence:** High that these controls are required; implementation details remain product-specific.

## Open Questions

- Which derived memories must be invalidated when only part of their supporting evidence is deleted?
