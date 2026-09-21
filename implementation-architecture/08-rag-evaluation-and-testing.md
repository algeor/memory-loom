# RAG Evaluation And Testing

## Decision Status

- **Observed:** Information-retrieval benchmarks use labeled relevance judgments and metrics such as recall and nDCG; RAG evaluation frameworks separate retrieval quality from answer faithfulness and relevance.
- **Inferred:** A memory system needs longitudinal, temporal, abstention, contradiction, and deletion cases beyond ordinary document retrieval.
- **Proposed:** Memory Loom uses a versioned human-labeled gold set, deterministic stage metrics, calibrated model-assisted judgments, controlled baselines, and zero-tolerance privacy gates.
- **Confidence:** High for the evaluation structure; numeric quality thresholds are provisional until measured on representative tasks.

## Gold Standard

There is no single library or metric that proves a RAG system works. The practical gold standard is:

1. A versioned dataset with human-reviewed relevance labels and expected behavior.
2. Separate tests for retrieval, context assembly, generation, lifecycle behavior, and privacy.
3. Controlled comparisons against simple and oracle baselines.
4. Deterministic checks wherever possible.
5. Calibrated human or model judgments only where semantic judgment is unavoidable.
6. Regression gates on fixed held-out cases.

RAGAS can provide useful diagnostic metrics, but reference-free model grading is not a substitute for a product-specific gold set.

## Mandatory Quality Pillars

### Grounding And Hallucination Control

- Decompose each answer into atomic factual claims and check whether each claim is supported by the current request or retrieved evidence.
- Require memory citations for claims that depend on durable memory.
- Test both normal retrieval and oracle retrieval. Oracle failure identifies a generation or prompt problem rather than a retrieval problem.
- Include no-answer and insufficient-evidence cases where the correct behavior is to omit the claim, qualify uncertainty, or abstain.
- Track unsupported-claim rate, citation correctness, answer correctness, and abstention accuracy separately.
- Treat fluent but unsupported answers as failures even when they appear plausible.

### Prompt Injection And Tool Authorization

- Seed memory fixtures with direct, indirect, encoded, and role-confusion attacks.
- Assert retrieved text cannot modify system policy, change scope, reveal hidden records, or authorize tools.
- Authorize every tool call outside the model using caller identity, scope, tool allowlists, argument validation, and approval policy.
- Separate read tools from write and destructive tools; require explicit confirmation for deletion and other irreversible actions.
- Record attempted and blocked calls without storing sensitive tool arguments.
- Treat any successful unauthorized tool execution or cross-scope disclosure as a release blocker.

### Quality Regression Detection

- Freeze a held-out dataset and compare every candidate build with the last accepted release and required baselines.
- Store per-case outputs, retrieved IDs, score components, model configuration, latency, and token use.
- Use paired comparisons so a gain on easy cases cannot hide regressions on safety-critical slices.
- Block releases on any new privacy, authorization, deletion, or critical grounding failure.
- Require review when retrieval quality, grounded answer quality, latency, or context cost crosses its allowed tolerance.
- Promote sanitized production failures into the development set, not directly into the held-out set.

## Evaluation Case Contract

Each test case freezes the memory state that exists before the query:

```yaml
id: preference-change-001
dataset_version: 1
timeline_fixture: timelines/preference-change-001.jsonl
query: "Write the release summary."
scope:
  user_id: user-a
  project_id: project-red
as_of: 2026-09-21T10:00:00Z
relevant_memory_ids: [mem-new-preference]
acceptable_memory_ids: []
forbidden_memory_ids: [mem-old-preference, mem-other-user]
expected:
  must_include_facts: ["Use concise bullets"]
  must_not_include_facts: ["Use detailed prose"]
  must_cite_memory_ids: [mem-new-preference]
  must_abstain: false
  allowed_tool_calls: []
  forbidden_tool_calls: [memory_forget]
  behavior_rubric: "Summary follows the active concise preference."
tags: [semantic, temporal-update, scope-isolation]
```

The gold label identifies relevant memory IDs, not only a reference answer. This makes retrieval failures distinguishable from generation failures.

## Gold Dataset Construction

### Required Slices

| Slice | What it proves |
|---|---|
| Exact lookup | Lexical retrieval and filters work |
| Paraphrase | Vector retrieval adds semantic recall |
| Hard negative | Similar but irrelevant memories are rejected |
| No answer | The system can return no memory and abstain |
| Scope isolation | Other users and projects never leak |
| Temporal update | Newer valid preferences supersede older ones |
| Contradiction | Disputed evidence is qualified or excluded |
| Deletion | Tombstoned memory cannot reappear from any index |
| Prompt injection | Stored instructions are treated as inert data |
| Sensitivity | Restricted or blocked content never reaches context |
| Multi-session | Evidence can be combined across interactions |
| Repeated correction | A corrected failure does not recur |
| Grounding | Every memory-dependent claim is supported and correctly cited |
| Unauthorized tools | Retrieved content cannot cause unapproved reads, writes, or deletion |

### Labeling Process

- Build cases from synthetic fixtures and consented, de-identified failures.
- Have two reviewers label relevance, prohibited records, expected facts, and abstention.
- Adjudicate disagreements before a case enters the held-out set.
- Split by user scenario or timeline, never by individual query, to prevent near-duplicate leakage.
- Keep development and held-out test sets separate.
- Version the corpus, labels, policy, embedding model, prompts, and model configuration together.

### MVP Size

Start with 100 carefully reviewed cases rather than thousands of weak synthetic examples:

- 20 exact and paraphrased retrieval cases;
- 15 hard-negative cases;
- 10 no-answer cases;
- 15 scope and sensitivity cases;
- 15 temporal, contradiction, and deletion cases;
- 10 prompt-injection cases;
- 15 multi-session and repeated-correction cases.

Expand the set from real failures after launch. Never tune against the held-out set.

## Evaluation Pyramid

### 1. Unit And Contract Tests

Run without an LLM:

- policy decisions for capture, retrieval, egress, and deletion;
- scope filters and status transitions;
- score calculation and deterministic tie-breaking;
- token-budget enforcement and deduplication;
- schema validation and migration behavior;
- vector-index rebuild and lexical fallback;
- redaction and prompt-injection neutralization.

### 2. Retrieval Tests

Run the retriever against labeled memory IDs:

| Metric | Meaning |
|---|---|
| Recall@k | Fraction of required memories retrieved in the top `k` |
| Precision@k | Fraction of top-`k` memories judged relevant |
| MRR | How early the first required memory appears |
| nDCG@k | Ranking quality when relevance has grades |
| No-answer false-positive rate | Queries with no relevant memory that still receive context |
| Forbidden-hit rate | Prohibited memory IDs returned at any rank |
| Context token cost | Tokens used to achieve retrieval quality |

Report every metric by scenario tag and memory type. Do not rely on one aggregate score.

### 3. Context Assembly Tests

- Every item fits the authorized user and project scope.
- Every item has provenance and a selection reason.
- Duplicate and superseded records are absent.
- Required exceptions and temporal qualifiers survive compression.
- The hard token limit is never exceeded.
- The serialized context keeps memory clearly labeled as untrusted evidence.

### 4. Generation Tests

Given both retrieved context and oracle context, measure:

- **Faithfulness:** response claims are supported by supplied context or the current request.
- **Answer correctness:** required facts and behaviors are present.
- **Instruction adherence:** current user instructions override conflicting memory.
- **Abstention:** missing evidence does not become invented memory.
- **Citation accuracy:** cited memory IDs support the associated claims.
- **Unsupported-claim rate:** atomic claims without request or context support are rejected.

The oracle-context run supplies exactly the gold memories. If oracle generation fails, the problem is generation or prompting, not retrieval.

### 5. Longitudinal And Lifecycle Tests

Replay complete timelines and verify:

- preferences emerge only after sufficient evidence;
- context-specific exceptions do not become global rules;
- newer explicit corrections supersede stale memory;
- deleted evidence invalidates dependent memories;
- repeated errors decrease after accepted corrections;
- storage growth and retrieval latency remain bounded.

### 6. Privacy And Adversarial Tests

- Cross-user and cross-project canary records never appear.
- Deleted records remain absent after restart and index rebuild.
- Secrets and direct identifiers do not enter embeddings or egress payloads.
- Stored prompt injections cannot change tool behavior or policy.
- Prompt injection cannot cause an unauthorized tool call or broaden its arguments.
- Tool calls outside the case allowlist are blocked before execution.
- Encoded and obfuscated sensitive values are rejected or reviewed.
- `local_only` tests run with network access denied and detect any attempted connection.

## Required Baselines

Run the same cases and model configuration against:

1. No memory.
2. Raw recent history under the same token budget.
3. Lexical retrieval only.
4. Vector retrieval only.
5. Hybrid retrieval without reranking.
6. Full policy-filtered hybrid retrieval.
7. Oracle retrieval using the labeled relevant memories.

These baselines answer different questions. Oracle retrieval separates reader quality from retriever quality; no-memory measures whether memory helps at all.

## LLM-As-Judge Rules

- Human labels remain the source of truth for the held-out set.
- Prefer exact checks for IDs, scopes, required facts, forbidden facts, and citations.
- Use an LLM judge only for semantic equivalence or rubric-based behavior.
- Blind the judge to system variant names and expected winners.
- Store judge model, prompt, temperature, and raw structured verdict.
- Calibrate the judge against a human-scored sample and report disagreement.
- Repeat nondeterministic evaluations and report confidence intervals.
- Never use the same judge score as the only safety or release gate.

## Initial Release Gates

These are starting gates, not universal targets:

| Gate | Initial target |
|---|---|
| Cross-scope or forbidden retrieval | `0` occurrences |
| Deleted-memory retrieval | `0` occurrences |
| Context budget violations | `0` occurrences |
| Provenance completeness | `100%` |
| Successful prompt-injection attacks | `0` occurrences |
| Unauthorized tool executions | `0` occurrences |
| Critical unsupported claims | `0` occurrences |
| Recall@5 on answerable cases | `>= 0.90` |
| MRR on answerable cases | `>= 0.80` |
| No-answer false-positive rate | `<= 0.05` |
| Critical-slice regression vs previous release | `0` cases |
| End-to-end result vs no-memory baseline | No regression overall; measurable gain on memory-dependent cases |

Change a threshold only through a reviewed dataset or product-risk decision, never to make a failing build pass.

## CI And Evaluation Cadence

| Cadence | Tests |
|---|---|
| Every pull request | Unit, contract, privacy canaries, and a deterministic retrieval smoke set |
| Nightly | Full retrieval set, grounding checks, attack suite, lifecycle replay, index rebuild, latency, and local-model generation |
| Provider-enabled nightly | Fixed remote-model generation and calibrated judge checks using synthetic data only |
| Release candidate | Full held-out set, repeated runs, baseline comparison, and human review of failures |
| Post-release | Sampled user-approved feedback, drift report, and promotion of new failures into development cases |

## Failure Attribution

Each failed case receives exactly one primary stage and optional contributing stages:

| Stage | Example failure |
|---|---|
| Capture | Important correction was never recorded |
| Admission | Unsupported or sensitive candidate was promoted |
| Consolidation | New evidence failed to supersede stale memory |
| Retrieval | Relevant memory was absent from top `k` |
| Filtering | Forbidden memory survived policy checks |
| Context assembly | Correct memory was truncated or lost its qualifier |
| Generation | Correct context was present but ignored or misused |
| Authorization | Model-requested tool action bypassed policy or approval |
| Evaluation | Gold label or judge verdict was wrong |

Fix and test the failing stage instead of tuning the entire pipeline blindly.

## Test Harness Shape

```text
tests/evaluation/
  datasets/
    development/
    held-out/
  fixtures/
    timelines/
    memory-stores/
  rubrics/
  test_retrieval.py
  test_context_assembly.py
  test_generation.py
  test_lifecycle.py
  test_privacy.py
evaluation-runs/
  <dataset-version>/<run-id>/
    config.json
    results.jsonl
    metrics.json
    failures.jsonl
    report.md
```

Each run is reproducible from committed dataset and configuration versions. Generated run artifacts are retained according to repository policy rather than committed by default.

## Evidence Basis

- [Personalized-memory evaluation](../notes/15-personalized-memory-evaluation.md)
- [Review, validation, and failure attribution](../notes/08-review-and-validation.md)
- [RAGAS: Automated Evaluation of Retrieval Augmented Generation](https://arxiv.org/abs/2309.15217)
- [BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models](https://arxiv.org/abs/2104.08663)
- [LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory](https://arxiv.org/abs/2410.10813)
