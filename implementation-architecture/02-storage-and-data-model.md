# Storage And Data Model

## Decision Status

- **Proposed:** SQLite is the default local store for the first implementation.
- **Confidence:** High for the relational model; medium for the vector extension until platform packaging is tested.

## Storage Choice

- SQLite provides a single inspectable local file, transactions, migrations, and low operational overhead.
- FTS5 provides lexical retrieval without another service.
- A vector adapter uses `sqlite-vec` when available and a bounded in-process cosine scan as the small-dataset fallback.
- WAL mode supports multiple client readers while the daemon remains the single writer.
- Encryption uses SQLCipher when enabled; the key is stored in the operating-system credential store, never beside the database.

## Logical Tables

| Table | Purpose | Retention |
|---|---|---|
| `interaction_events` | Minimal source event and consent state | Short, configurable |
| `memory_candidates` | Unapproved extracted claims | Until decision or expiry |
| `memories` | Current typed record | Until expiry or deletion |
| `memory_revisions` | Immutable history of state changes | Audit policy |
| `memory_evidence` | Links records to source evidence | Follows evidence policy |
| `memory_embeddings` | Local vector representation | Rebuilt on model change |
| `retrieval_decisions` | Selected and filtered result trace | Short, configurable |
| `feedback_events` | Outcome tied to response and memories | Evaluation policy |
| `egress_manifests` | Exact metadata for provider-bound calls | Audit policy |
| `identity_mappings` | Encrypted local identity to pseudonymous subject mapping | While required for ownership |
| `redaction_manifests` | Categories and actions applied during de-identification | Audit policy |
| `sensitive_value_vault` | Exceptional reversible token mappings | Disabled by default; shortest viable retention |
| `deletion_jobs` | Cleanup status across records, indexes, mappings, and backups | Audit policy |
| `schema_metadata` | Schema and embedding model versions | Permanent |

## Memory Record

```yaml
id: uuid
subject: user|agent
type: episodic|semantic|procedural|metacognitive
statement: string
scope:
  user_id: string
  project_id: string|null
  domain: string|null
  task_kind: string|null
confidence: 0..1
importance: 0..1
sensitivity: normal|restricted|blocked
status: active|disputed|superseded|expired|deleted
evidence_refs: [uuid]
contradiction_refs: [uuid]
supersedes: [uuid]
version: integer
created_at: timestamp
last_confirmed_at: timestamp|null
valid_until: timestamp|null
```

## Required Invariants

- Every memory has at least one evidence reference.
- Every mutation creates an immutable revision.
- Active records cannot reference deleted evidence without being re-evaluated.
- Deleted, expired, disputed, and superseded records are excluded before ranking.
- Scope filters execute before lexical or vector similarity can expose content.
- Embeddings are derived data and never the only representation of a memory.
- Memory statements, embedding source text, indexes, and logs contain only purpose-approved sanitized text.
- The memory database references pseudonymous subject and project identifiers; reversible mappings remain separately encrypted and excluded from search.
- Embedding rows record model name, dimensions, and normalization version.

## Identity And De-identification

- Generate random subject IDs instead of deriving identifiers from account attributes.
- Represent project identity with a keyed HMAC rather than a plaintext local path.
- Store redaction categories, actions, and detector versions without storing removed values.
- Generate embeddings only after the de-identification decision allows the embedding purpose.
- Quarantine or reprocess records when a detector or policy update invalidates prior sanitization.
- Keep reversible token mappings disabled unless a declared feature requires restoration.

## Versioning

Memory updates use optimistic concurrency:

1. Read the current record and version.
2. Propose a typed transition: create, reinforce, refine, split, merge, weaken, supersede, expire, or delete.
3. Validate evidence, policy, and expected version.
4. Append a revision and update the current projection in one transaction.
5. Rebuild affected lexical and vector index entries.

## Deletion

- Tombstone synchronously so the record becomes immediately ineligible.
- Delete vector and lexical index entries in the same transaction.
- Queue dependent-memory invalidation.
- Remove raw evidence according to retention policy.
- Preserve only the minimum non-content audit marker required to prove completion.

## Backup And Export

- Backups are opt-in, local, encrypted, and include schema metadata.
- Exports default to human-readable JSON Lines without embeddings.
- Default exports are anonymised and omit internal stable tokens and reversible mappings.
- Identifiable exports require explicit confirmation, authorization, and a dedicated audit event.
- Import validates schema, scope ownership, provenance, and duplicate IDs.
- Deleted records are not restored unless the user explicitly imports them as new evidence.

## Evidence Basis

- [Memory candidate admission](../notes/11-memory-candidate-admission.md)
- [Typed evolving memory](../notes/12-typed-evolving-memory.md)
- [Memory governance and safety](../notes/14-memory-governance-and-safety.md)
- [Anonymisation and pseudonymisation](07-de-identification.md)
