# Anonymisation And Pseudonymisation

## Decision Status

- **Proposed:** Pseudonymise identifiers needed for local operation and anonymise data when identity is not required.
- **Confidence:** High for the purpose-specific boundary; identifier detectors and re-identification risk require continuous testing.

## Core Decision

Memory Loom cannot fully anonymise every durable memory because personalization must associate a record with the correct user and scope. It therefore uses two distinct controls:

- **Pseudonymisation** replaces identifying values with stable local tokens when controlled linkage is required.
- **Anonymisation** irreversibly removes or generalizes identifying values for telemetry, evaluation, default exports, and provider egress when identity is unnecessary.

Encryption protects stored values but does not make them anonymous. Redaction removes a span but does not by itself prevent linkage through surrounding text, metadata, or embeddings.

## Data Flow

```text
input
  -> normalize locally
  -> deterministic secret and identifier detection
  -> local entity recognition
  -> sensitivity and purpose policy
  -> drop | generalize | tokenize | deny
  -> sanitized memory candidate
  -> sanitized embedding and indexes
  -> purpose-specific retrieval or export
  -> second de-identification pass before optional egress
  -> redaction manifest and audit event
```

No raw input may reach durable memory, embeddings, logs, or provider egress before this pipeline returns an allow decision.

## Purpose Profiles

| Purpose | Identity treatment | Default behavior |
|---|---|---|
| Local memory | Pseudonymise required ownership and scope identifiers | Store the smallest reusable claim |
| Local evidence | Minimize, encrypt, and expire | Do not store full transcripts by default |
| Embedding | Remove direct identifiers and secrets | Embed only the sanitized statement |
| Retrieval context | Use pseudonymous scope internally; omit identifiers from returned text | Return only task-relevant sanitized claims |
| Provider egress | Anonymise unless an approved purpose requires a specific field | Deny when detection or policy is uncertain |
| Logs and metrics | Anonymise and aggregate | Never record memory text or identity mappings |
| Default export | Anonymise and omit reversible mappings | Require explicit confirmation for identifiable export |
| Evaluation fixtures | Synthetic or irreversibly anonymised | Never reuse production records directly |

## Identifier Strategy

- Generate a random installation-local `subject_id`; do not derive it from an email, username, account ID, or machine name.
- Represent project identity with `HMAC-SHA-256(scope_key, canonical_project_identity)` rather than a plaintext local path.
- Keep any required client-to-subject mapping in a separate encrypted identity store.
- Store the identity-store key and the HMAC scope key in the operating-system credential store.
- Never expose stable internal identifiers to providers, telemetry, or public exports.
- Rotate tokens by creating new mappings and reindexing affected records; do not silently change ownership semantics.

For the single-user MVP, one random subject ID is sufficient. Multi-user identity federation remains deferred.

## Detection Layers

1. **Deterministic detectors** identify credentials, emails, phone numbers, IP addresses, account numbers, URLs with secrets, and local paths.
2. **Local entity recognition** identifies people, organizations, addresses, and locations that deterministic patterns miss.
3. **Policy classification** blocks protected, sensitive, or unnecessary third-party data according to purpose.
4. **Optional model review** may identify additional risk only after local deterministic processing. It cannot override a deny decision.

Detectors return typed spans, confidence, and provenance. Low-confidence results may be stored only after explicit review; optional provider egress fails closed.

## Transformations

Apply the least reversible transformation compatible with the purpose:

- **Drop:** Remove unnecessary identifiers, credentials, and unrelated third-party data.
- **Generalize:** Replace precise values with a useful category, such as a city with a region when location detail is unnecessary.
- **Tokenize:** Replace an identifier with a scoped token such as `[PERSON_1]` only when stable local linkage is required.
- **Vault:** Store a reversible mapping only when a declared feature requires restoration. Vault entries are encrypted, separately authorized, and excluded from search.
- **Deny:** Reject capture or egress when safe transformation cannot preserve the required meaning.

A preferred memory statement is `Prefers concise answers`, not `Alex Smith prefers concise answers`.

## De-identification Contract

```yaml
request_id: uuid
purpose: storage|embedding|retrieval|egress|export|telemetry|evaluation
input_ref: ephemeral-reference
findings:
  - category: person|email|phone|credential|path|location|organization|other
    action: drop|generalize|tokenize|vault|deny
    confidence: 0..1
output_text: string|null
decision: allow|review|deny
policy_version: string
detector_versions: {}
```

The redaction manifest persists categories, actions, counts, policy version, and detector versions. It must not persist removed values or raw input text.

## Component Interface

```python
deidentify(text, purpose, scope) -> sanitized_text, findings, decision
```

All storage, embedding, retrieval-context, export, telemetry, and provider adapters call this interface. Adapters cannot bypass a deny or review decision.

## Storage Additions

| Table | Purpose | Content restriction |
|---|---|---|
| `identity_mappings` | Map local client identity to random subject IDs | Encrypted and excluded from search |
| `redaction_manifests` | Audit transformations and policy decisions | Categories and counts only |
| `sensitive_value_vault` | Exceptional reversible token mappings | Disabled by default and separately encrypted |
| `deletion_jobs` | Track cleanup across records, indexes, exports, and backups | No deleted content |

The memory database references only pseudonymous IDs. Embeddings are generated after sanitization and are rebuilt when detector or policy changes invalidate prior output.

## Deletion And Rotation

- Tombstone memories and remove lexical and vector entries immediately.
- Delete associated reversible mappings when no surviving record needs them.
- Re-evaluate derived memories that depended on deleted evidence.
- Track cleanup of exports and backups according to retention policy.
- Support cryptographic erasure of encrypted backup generations by destroying their wrapped keys.
- Preserve only a non-content completion marker when audit policy requires proof of deletion.

## Re-identification Threats

- Quasi-identifiers can identify a person when combined even after names are removed.
- Stable tokens can allow activity correlation across projects or exports.
- Rare phrases and exact timestamps can identify source conversations.
- Embeddings can retain information about sanitized text and must remain protected derived data.
- External model providers may combine submitted context with account or telemetry information outside Memory Loom's boundary.

Mitigations include purpose-scoped tokens, timestamp coarsening, minimum necessary context, rare-value review, strict scope separation, short evidence retention, and no cross-purpose identifier reuse.

## Verification

- Maintain deterministic fixtures for credentials, emails, phones, paths, people, organizations, addresses, and third-party references.
- Assert raw identifiers never appear in memory rows, FTS indexes, vector source text, logs, traces, default exports, or egress payloads.
- Test that the same person receives different tokens across scopes unless linkage is explicitly required.
- Test false negatives, false positives, Unicode variants, encoded values, and prompt-injection attempts targeting the detector.
- Run re-identification tests against exported and provider-bound datasets.
- Reprocess or quarantine affected memories after detector, policy, or tokenizer changes.

## MVP Acceptance Criteria

- Explicit preferences can be stored and retrieved without retaining the user's name or client account identifier in memory text.
- Secrets and blocked sensitivity classes fail closed before persistence and egress.
- Embeddings and indexes are derived only from sanitized text.
- Default exports cannot be linked back through stable internal tokens.
- Every transformation is explainable through a non-content redaction manifest.
- Deletion removes memory, indexes, and unnecessary identity mappings.

## Evidence Basis

- [Memory governance and safety](../notes/14-memory-governance-and-safety.md)
- [Storage and data model](02-storage-and-data-model.md)
- [Privacy and security architecture](05-privacy-and-security.md)
- [Personalized-memory evaluation](../notes/15-personalized-memory-evaluation.md)
