# Initial Experimental Protocol

## Protocol Status

- Version: draft 0.2
- Study type: controlled offline evaluation
- Registration: not preregistered
- Data: not yet created
- Runs: none

## Objective

Estimate whether explicit, user-approved structured memory changes later assistant behavior relative to simpler context strategies.

## Experimental Conditions

| ID | Condition |
|---|---|
| B0 | No cross-session memory |
| B1 | Most recent conversation history within the same token budget |
| B2 | Rolling summary within the same token budget |
| B3 | Approved structured memory using deterministic lexical retrieval |

Vector retrieval, autonomous consolidation, and fine-tuning are later experiments. They are not part of the initial comparison.

### Condition Construction

Each scenario contains one immutable timeline of prior interactions and lifecycle events. Every condition reads the same timeline up to the current query. The approval interaction is present in that source timeline for every condition; B3 does not receive an additional approval message at generation time.

The condition manifest must freeze the tokenizer, serializer, truncation rules, and maximum injected-context budget:

- **B0:** inject no cross-session context.
- **B1:** select the newest complete prior messages by walking backward until the budget is full, then serialize the selected messages in their original chronological order. Never include a partial message.
- **B2:** inject the latest rolling summary that existed before the current query. Generate summaries only from prior timeline events using a versioned prompt, model, decoding configuration, and update schedule. Freeze summaries before outcome generation; they must not access future queries, expected-memory labels, or held-out outcomes.
- **B3:** inject only records selected by the approved structured-memory pipeline. Raw approval messages are not separately injected.

The budget is a shared maximum, not a requirement to pad contexts to equal length. Token counts apply to the exact serialized injected context. Record B2 summarization cost separately from answer-generation cost.

## Dataset

Create versioned longitudinal scenarios containing:

- an explicit preference or correction;
- at least one later query where that information matters;
- matched queries where it does not matter;
- scope exceptions;
- preference changes;
- deletion events;
- hard negatives from another project or synthetic user.

Split scenarios by template family into development and held-out sets. Do not create near-duplicate variants across the split.

Human reviewers label:

- whether memory is needed;
- which record is relevant, acceptable, or forbidden;
- the required behavior;
- behaviors that would violate the active preference;
- whether abstention or no memory context is correct.

Record the labeling guide and reviewer disagreements. Use synthetic data for the first systems experiment; it does not establish real-user validity.

## Sample Size

Use the development set for a pilot that estimates outcome variance, model nondeterminism, annotation disagreement, and the frequency of memory-dependent cases.

Before running the held-out set:

- define the smallest effect on preference adherence that would justify the added memory mechanism;
- document the sample-size or precision calculation for the paired design;
- freeze the number of scenarios and repeated model runs;
- freeze exclusion and missing-run rules;
- do not use held-out outcomes to revise the calculation.

If the available benchmark fixes the sample size, report the resulting interval precision rather than claiming adequate power after the fact.

## Controls

Keep constant across conditions:

- model and model version;
- system and task prompts, except the injected context;
- available tools;
- context-token budget;
- decoding parameters where exposed;
- scenario order or randomized order assignment;
- evaluation code and label version.

Condition-specific context headers may identify the artifact as history, summary, or fallible memory, but their exact text must be frozen in the condition manifest. No header may contain scenario-specific guidance.

Store provider, model, prompt hash, dataset version, code revision, seed, time, and raw output for every run.

Randomize or counterbalance condition execution order. Shuffle outputs and hide condition labels from human reviewers. If generation is stochastic, run the preregistered number of repeats for every condition-scenario pair.

## Outcomes

### Primary

**Preference adherence:** proportion of memory-dependent queries whose adjudicated response follows the active preference without violating the current request.

### Secondary

- repeated-error rate after correction;
- task success;
- relevant-memory recall and precision;
- no-memory false-positive rate;
- irrelevant context tokens;
- total context tokens;
- latency and provider cost;
- unsupported claims attributed to memory;
- reviewer disagreement.

### Safety Invariants

Count these directly; do not hide them in an average:

- out-of-user or out-of-project retrieval;
- retrieval of deleted or superseded records;
- memory overriding the current user request;
- stored text authorizing a tool call;
- sensitive or secret data entering an unauthorized artifact.

## Analysis

- Compare conditions on the same scenarios.
- Treat H1 as one confirmatory family containing the predeclared B3-B0, B3-B1, and B3-B2 contrasts; label H2 and H3 secondary and H4 a safety invariant.
- Report absolute and relative differences with uncertainty intervals.
- For each condition-query pair, aggregate repeated stochastic runs using the frozen rule. Then aggregate memory-dependent queries within each scenario so scenarios receive equal weight.
- Estimate every contrast within the same scenario. Resample the highest independent scenario-construction unit—template family when scenarios share a template, otherwise scenario—while carrying all conditions, queries, and repeated runs together.
- Do not bootstrap individual queries or model repeats as independent observations.
- Use simultaneous confidence intervals or a frozen multiplicity adjustment for the three H1 contrasts. State before held-out evaluation whether H1 requires improvement over every baseline or uses another global decision rule.
- Report results by scenario type, scope, and memory dependency.
- Report all exclusions and failed runs.
- Treat model-judge scores as secondary unless calibrated against blinded human review.
- State how repeated stochastic runs are aggregated and retain run-level outcomes.
- Correct or clearly label multiplicity when testing additional confirmatory outcomes.
- Do not choose a success threshold after seeing held-out results.

The run manifest must name the repeat aggregation rule, scenario weighting rule, independent resampling unit, confidence-interval method, multiplicity method, and H1 decision rule. If the realized data structure invalidates the preregistered analysis, report the deviation and treat the replacement analysis as exploratory.

A pilot should estimate variance and reveal annotation problems. It should not be reported as confirmatory evidence.

## Failure Attribution

Assign one primary failure stage:

1. capture;
2. approval or admission;
3. record revision;
4. retrieval;
5. context assembly;
6. generation;
7. evaluation label or judge.

This prevents retrieval tuning from masking a generation or dataset problem.

## Reproducibility Package

Every reported experiment must include:

- dataset and labeling-guide versions;
- condition configuration;
- prompts and schemas;
- code revision;
- model/provider identifiers;
- raw outputs and retrieval traces;
- metric implementation;
- analysis script;
- exclusions and deviations;
- limitations and conflicts of interest.

## Interpretation Limits

- Synthetic scenarios may overstate preference clarity.
- Coding tasks do not represent all assistant use.
- Provider models can change despite stable names.
- Preference adherence is not equivalent to overall answer quality.
- A zero observed safety failure does not prove safety outside the evaluated corpus.
