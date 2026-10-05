# Blinded Evaluation Contract v1

## Separation

`memory-loom blind-study` creates three artifacts:

- a review packet containing requests, behavior criteria, and responses;
- a separate blinding key mapping opaque item IDs to conditions;
- an unreviewed human-review template.

The packet excludes condition names, injected contexts, memory identifiers,
provider identifiers, token counts, costs, and the blinding seed. Reviewers must
not receive the key before submitting their review artifact.

## Rating

Every output receives one decision:

- `adheres`: required behavior is present and no listed violation occurs;
- `violates`: required behavior is absent or a listed violation occurs;
- `unclear`: the response cannot be classified reliably;
- `unreviewed`: placeholder value, rejected by analysis.

For the binary adherence metric, `unclear` is conservatively scored as zero so
paired observations are not removed selectively across conditions. Its count is
also reported separately.

Reviewers also label task success, current-request override failures, and
unsupported claims attributed to memory. Multiple completed reviews are
combined by majority decision; ties become `unclear`, and disagreement is
reported before aggregation.

## Analysis

`memory-loom analyze-study` joins reviews to conditions only through the hidden
key. It averages repeated scores within condition-query, averages queries within
scenario, gives scenarios equal weight, and resamples template-family clusters.

The three B3 contrasts receive one simultaneous interval based on the 95th
percentile of the maximum absolute bootstrap error. This implementation is for
exploratory pilot diagnostics. A confirmatory analysis requires a frozen
minimum effect, sample-size justification, held-out dataset, and completed
human review.

The pilot artifact counts forbidden memory IDs that reached assembled B3
context. Full pre-budget retrieval safety remains the responsibility of the
separate versioned retrieval evaluator.
