# Analysis Contract v1

## Aggregation

1. Average repeated runs within each condition-query pair.
2. Average memory-dependent queries within each scenario.
3. Give each scenario equal weight.
4. Compute B3-B0, B3-B1, and B3-B2 within the same scenario.

## Uncertainty

Resample template families when scenarios share a template; otherwise resample scenarios. Carry every condition, query, and repeated run in the sampled cluster.

Use simultaneous bootstrap intervals for the three H1 contrasts. The initial decision rule requires the preregistered minimum effect against all three baselines.

## Deviations

The run manifest freezes aggregation, clustering, interval, multiplicity, and H1 decision rules. Any replacement after held-out outcomes are visible is exploratory.
