# Source Ledger: Continual Personalization Brief

## Snapshot

- Artifact: User-provided design and research brief.
- Received: 2026-09-14.
- Subject: External, evolving memory for long-term user adaptation and repeated-error correction.
- Evidence class: Proposed architecture and research direction; not an implemented source repository.

## Scope Rule

This brief is design input, not proof that the proposed mechanisms work. Notes derived from it use `maturity: proposed`. Existing source-backed harness patterns remain labeled observed or inferred.

## Coverage

| Brief concept | Extracted note |
|---|---|
| External memory instead of continuous weight updates | AH-010 |
| User personalization and repeated-error learning | AH-010 |
| Candidate extraction and admission factors | AH-011 |
| Episodic, semantic, procedural, and higher-order memory | AH-012 |
| Periodic or event-triggered consolidation | AH-012 |
| Confidence updates and contradiction handling | AH-012 |
| Filtered, reranked, budgeted retrieval | AH-013 |
| Privacy, deletion, consent, and training boundary | AH-014, proposed enhancement |
| Comparative baselines and longitudinal experiment | AH-015 |
| External memory versus fine-tuning | AH-015 |
| Python, FastAPI, PostgreSQL, pgvector, scheduler | AH-016 |

## Research Pointers To Verify

- Generative Agents, Reflexion, MemGPT, MemoryBank, LoCoMo, LongMemEval, and LOCCO.
- Reflective Memory Management for Long-term Personalized Dialogue Agents, PREMem, PRIME, *Hello Again!*, Persona-Plug, and *Learning to Remember User Conversations*.

These names are retained as a literature search queue. Claims, versions, authorship, and applicability have not been independently checked during this pass.

## Enhancements Added During Extraction

- Explicit user/tenant isolation and consent gates.
- Sensitive-data policy and prompt-injection treatment.
- Auditable deletion and derived-memory invalidation.
- Stage-level failure attribution and experiment reproducibility.
- A narrow first vertical slice for explicit communication preferences.

## Next Evidence Step

Verify the research pointers against primary papers, then attach each supported design choice to a precise citation or mark it as an original proposal.
