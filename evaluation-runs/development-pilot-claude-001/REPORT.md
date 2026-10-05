# Development Pilot Report

## Status

**Exploratory pilot observation, not a confirmatory scientific result.**

- Blinded outputs reviewed: 192
- Reviewer types: model
- Generation models: claude-cli:claude-haiku-4-5
- Reviewer models: claude-cli:haiku
- Pairwise reviewer disagreements: 0 (not estimable with one reviewer)
- Failed model runs: 0
- Forbidden context inclusions: 0
- No-memory false-positive retrievals: 0
- Current-request override failures: 10
- Unsupported memory claims: 12

## Condition Metrics

| Condition | Memory-needed n | Unclear | Adherence | Task success | Overrides | Unsupported claims | Context tokens | Latency ms | Cost USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B0 | 32 | 10 | 0.3438 | 0.2500 | 0 | 0 | 0.0000 | 5948.8783 | 0.166526 |
| B1 | 32 | 11 | 0.5625 | 0.3333 | 4 | 8 | 58.7917 | 6136.1810 | 0.173027 |
| B2 | 32 | 9 | 0.6250 | 0.4583 | 5 | 2 | 25.4583 | 5753.9767 | 0.157173 |
| B3 | 32 | 10 | 0.5625 | 0.4167 | 1 | 2 | 25.8333 | 6276.7758 | 0.174369 |

## Paired Contrasts

| Contrast | Estimate | Simultaneous 95% interval |
|---|---:|---:|
| B3-B0 | 0.2188 | [-0.0625, 0.5000] |
| B3-B1 | 0.0000 | [-0.2812, 0.2812] |
| B3-B2 | -0.0625 | [-0.3438, 0.2188] |

## Limitations

- This development pilot is exploratory and not confirmatory evidence.
- Synthetic scenarios may overstate preference clarity.
- Model reviews are secondary and are not calibrated against blinded human review.
- A single reviewer cannot estimate inter-reviewer disagreement.
- Claude CLI did not expose temperature, top-p, seed, or output-token controls.
- At least one generation used an alias or lacked a provider-reported model version.

## Interpretation

These numbers describe this frozen synthetic development run only. They must not be generalized to real users, other models, or a held-out dataset.

All simultaneous 95% intervals include zero. This pilot therefore does not distinguish B3 from any baseline on preference adherence.
