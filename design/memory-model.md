# Memory Model

## Status

Design decision for the initial experiment. Field names may change during implementation.

## Records

### Evidence Event

An append-only metadata record for the interaction in which the user stated a preference or correction. Event identity and provenance are immutable; user-authored content remains erasable.

```yaml
id: uuid
scenario_id: string
source_event_id: string|null
kind: explicit_preference|direct_correction
content: string|null
content_state: present|erased
user_scope: string
project_scope: string|null
task_scope: string|null
recorded_at: timestamp
consent: approved
```

### Memory Record

The user-approved statement available for retrieval.

```yaml
id: uuid
rule_key: string
statement: string|null
kind: preference|correction
user_scope: string
project_scope: string|null
task_scope: string|null
status: active|superseded|deleted
evidence_ids: [uuid]
created_at: timestamp
valid_from: timestamp
valid_until: timestamp|null
version: integer
```

### Revision Event

Every change appends an immutable transition.

```yaml
id: uuid
memory_id: uuid
operation: approve|correct|supersede|delete
from_version: integer|null
to_version: integer|null
evidence_ids: [uuid]
actor: user|research_fixture
reason_code: string
approval_event_id: string|null
created_at: timestamp
```

### Retrieval Decision

The trace needed to evaluate retrieval independently from generation.

```yaml
query_id: uuid
memory_id: uuid
eligible: boolean
decision: selected|scope_filtered|state_filtered|specificity_filtered|conflict_filtered|lexical_filtered|budget_filtered
lexical_score: number|null
reason_code: string
position: integer|null
```

## State Rules

- New evidence is not durable until explicitly approved. A declined candidate remains ephemeral and creates no evidence event.
- Correction creates a new version; it does not mutate history in place.
- A newer explicit preference may supersede an older one in the same scope.
- A narrower exception coexists with a broader preference and wins only in its scope.
- `id` identifies one logical memory lineage; `version` increments within that lineage.
- `rule_key` is a non-sensitive fixture or approval-time identifier for records that govern the same behavior. The initial system does not infer it autonomously.
- Active and superseded versions require a statement. Deletion makes the entire lineage ineligible, erases its statements and evidence content, and removes its index entries while retaining non-content tombstone metadata.
- Experiment fixtures may simulate approval but must record that actor explicitly.

## Scope Resolution

Resolve scope before lexical ranking. Group eligible records by `rule_key`, then keep only records at the most specific matching scope:

1. user + project + task;
2. user + project;
3. user only.

Broader records in the same group receive `specificity_filtered` decisions and cannot compete in ranking. If distinct, equally specific active records in a group have different statements, return none of them with `conflict_filtered` decisions and flag the case for review. Byte-identical duplicates may collapse deterministically. Only surviving records proceed to lexical ranking.

Evidence content belongs to one logical memory lineage in the initial prototype. This keeps deletion deterministic; shared evidence requires a later retention and reference-counting design.

## Deferred Admission Research

Later studies may evaluate inferred preferences, facts, procedures, or agent lessons. Those candidates need different evidence thresholds rather than one universal score:

- explicit statements may require one attributable event;
- inferred preferences require repeated independent observations;
- sensitive attributes must not be inferred automatically;
- agent lessons must remain separate from claims about the user;
- task-only instructions remain task state unless the user marks them durable.

Deterministic consent, secret, sensitivity, evidence, and scope gates must precede any model judgment. A failed hard gate cannot be overridden by frequency or an LLM score.

## Deferred Revision Research

Later consolidation may support reinforce, refine, split, merge, weaken, dispute, and expire operations. Apparent contradictions should first be classified as temporal change, scope difference, exception, source disagreement, extraction error, or unresolved conflict.

That extension requires a separate labeled evaluation of transition accuracy, scope preservation, provenance completeness, and deletion propagation. It is not part of the first experiment.
