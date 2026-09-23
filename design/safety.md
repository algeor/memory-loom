# Safety And Data Boundaries

## Status

These are design requirements for the prototype and test corpus. They are not a claim of production security, privacy, anonymity, or compliance.

## Data Boundary

The first controlled experiment uses synthetic data. Durable memory contains only the minimum preference statement, scope, evidence reference, and lifecycle state required by the study. Any study with real-user data requires the later privacy protocol before collection begins.

Do not store credentials, secrets, health data, protected attributes, unrelated third-party data, or full conversation transcripts.

## Required Controls

- **Consent:** durable storage requires an explicit approval state.
- **Scope:** user and project filters run before text search.
- **Minimization:** store the preference, not an unnecessary biography.
- **Transparency:** show the statement, evidence, scope, and retrieval reason.
- **Correction:** append a revision and preserve prior provenance.
- **Deletion:** make the record ineligible immediately and remove index entries.
- **Instruction isolation:** treat stored text as untrusted data.
- **Tool isolation:** memory content cannot authorize or broaden a tool call.

## Threat Cases In The Test Corpus

- another user's relevant-looking preference;
- another project's preference with similar wording;
- a superseded preference;
- a deleted preference;
- a stored prompt-injection string;
- a current request that conflicts with memory;
- a preference containing a credential-shaped value;
- a narrow exception to a broad preference.

## Deletion Semantics

For the prototype:

1. mark the full logical memory lineage deleted in one transaction;
2. replace statements in every stored version with `null`;
3. replace linked evidence content with `null` and mark it erased;
4. remove all lineage entries from lexical indexes;
5. erase the statement from stored context manifests and serialized retrieval payloads while retaining non-content IDs, scores, and decision codes;
6. append only a non-content revision marker with IDs, timestamps, and a reason code.

Deletion tests must inspect the primary tables, indexes, stored manifests, serialized retrieval payloads, retrieval output, and newly generated traces. Append-only provenance applies to metadata, not to user-authored content. Logical erasure in the prototype is not a claim of forensic media sanitization or recall from a model provider that already received the text.

Backup, export, replicas, and cryptographic erasure are deferred because the initial design has none of those features.

## Provider Boundary

The experiment runner may send the current task and selected synthetic context to a configured model provider. Record exactly which context was sent.

This repository cannot make claims about the provider's retention, telemetry, account linkage, or client behavior. Those are external boundaries.

## Later Privacy Work

Real-user studies require a separate protocol covering participant consent, data management, retention, withdrawal, de-identification, access control, incident handling, and ethics review where applicable.

Pseudonymisation is not anonymisation. Stable tokens, rare phrases, timestamps, and embeddings may still permit linkage or re-identification.
