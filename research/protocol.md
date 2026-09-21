# Initial Experimental Protocol

## Protocol Status

- Version: draft 0.1
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

Record the labeling guide and reviewer disagreements. Synthetic data is acceptable for the first systems experiment but does not establish real-user validity.

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
- Treat H1 as the primary confirmatory comparison; label H2 and H3 secondary and H4 a safety invariant.
- Report absolute and relative differences with uncertainty intervals.
- Use paired bootstrap confidence intervals for aggregate paired metrics unless the final data structure requires another method.
- Report results by scenario type, scope, and memory dependency.
- Report all exclusions and failed runs.
- Treat model-judge scores as secondary unless calibrated against blinded human review.
- State how repeated stochastic runs are aggregated and retain run-level outcomes.
- Correct or clearly label multiplicity when testing additional confirmatory outcomes.
- Do not choose a success threshold after seeing held-out results.

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
