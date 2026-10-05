# Development Pilot Package

## Status

This is a frozen **exploratory development result**, not confirmatory evidence.

## Contents

- `raw/`: 24 scenario artifacts containing 192 completed B0-B3 runs.
- `review-packet.json`: shuffled condition-hidden outputs and rubrics.
- `blinding-key.json`: the separately generated condition key.
- `review-model.json`: 192 completed ratings from one blinded model reviewer.
- `review-human.json`: an unreviewed human-review template; it was not analyzed.
- `analysis.json`: deterministic metrics and paired cluster-bootstrap intervals.
- `REPORT.md`: concise human-readable results and limitations.
- `SHA256SUMS`: integrity hashes for every other file in this package.

## Supported Conclusion

All simultaneous 95% intervals for B3 preference-adherence contrasts include
zero. This run therefore does not distinguish structured memory from no memory,
recent history, or rolling summary.

The run also recorded zero model-invocation failures, zero forbidden context
inclusions, and zero no-memory false-positive retrievals. Those counts apply
only to this synthetic corpus.

## Reproduce Analysis

```zsh
uv run memory-loom analyze-study \
  evaluation-runs/development-pilot-claude-001/blinding-key.json \
  evaluation-runs/development-pilot-claude-001/raw \
  evaluation-runs/development-pilot-claude-001/review-model.json \
  --output /tmp/memory-loom-analysis.json \
  --report /tmp/memory-loom-report.md \
  --bootstrap-samples 10000 \
  --seed 20261005
```

## Limits

- Outputs are synthetic and model-reviewed, with no blinded human calibration.
- One reviewer cannot estimate reviewer disagreement.
- Claude CLI did not expose the requested decoding controls.
- The provider model was reported as `claude-haiku-4-5`, but the requested
  manifest model was the `haiku` alias.
- The manifest records `working-tree-2026-10-05`, not an exact commit. The raw
  run is auditable, but exact provider-level regeneration is not guaranteed.
