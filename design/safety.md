# Safety And Data Boundaries

## Status

These are design requirements for the prototype and test corpus. They are not a claim of production security, privacy, anonymity, or compliance.

## Data Boundary

The first experiment should use synthetic or explicitly consented data. Durable memory contains only the minimum preference statement, scope, evidence reference, and lifecycle state required by the study.

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

1. mark the record deleted in one transaction;
2. remove lexical index entries in the same operation;
3. exclude deleted evidence from future derived records;
4. retain only a non-content revision marker required for the test trace.

Backup, export, replicas, and cryptographic erasure are deferred because the initial design has none of those features.

## Provider Boundary

The experiment runner may send the current task and selected synthetic context to a configured model provider. Record exactly which context was sent.

This repository cannot make claims about the provider's retention, telemetry, account linkage, or client behavior. Those are external boundaries.

## Later Privacy Work

Real-user studies require a separate protocol covering participant consent, data management, retention, withdrawal, de-identification, access control, incident handling, and ethics review where applicable.

Pseudonymisation is not anonymisation. Stable tokens, rare phrases, timestamps, and embeddings may still permit linkage or re-identification.
