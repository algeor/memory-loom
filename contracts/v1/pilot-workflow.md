# Development Pilot Workflow v1

## Status

This workflow is a **design decision** for the 24-scenario development pilot.
Its outputs are exploratory and cannot establish a confirmatory result.

## Freeze

The executed manifest is
[`../../fixtures/manifests/v1/development-pilot-claude.json`](../../fixtures/manifests/v1/development-pilot-claude.json).
It excludes the legacy `scope-deletion-001` contract fixture, runs two repeats,
and deterministically shuffles condition order by scenario and repeat.

The provider model is an alias rather than a dated snapshot because a snapshot
was not verified as available to the configured account. Record this as a pilot
limitation and use a dated model snapshot before confirmatory evaluation.

## Generate

```zsh
uv run memory-loom run-study \
  fixtures/scenarios/v1 \
  fixtures/manifests/v1/default-conditions.json \
  fixtures/manifests/v1/development-pilot-claude.json \
  --provider claude-cli \
  --output-directory evaluation-runs/development-pilot-claude-001/raw \
  --jobs 4 \
  --resume
```

The Claude CLI adapter uses safe mode, disables tools and MCP servers, replaces
the system prompt, accepts the task through stdin, and disables session
persistence. The CLI reports the actual model, usage, and cost. It does not
expose temperature, top-p, seed, or output-token controls; that is a recorded
pilot deviation.

An OpenAI Responses API manifest is also available at
[`../../fixtures/manifests/v1/development-pilot-openai.json`](../../fixtures/manifests/v1/development-pilot-openai.json).
It requires a valid `OPENAI_API_KEY`.

## Blind

```zsh
uv run memory-loom blind-study \
  fixtures/scenarios/v1 \
  evaluation-runs/development-pilot-claude-001/raw \
  --packet evaluation-runs/development-pilot-claude-001/review-packet.json \
  --key evaluation-runs/development-pilot-claude-001/blinding-key.json \
  --review-template evaluation-runs/development-pilot-claude-001/review-human.json \
  --packet-id development-pilot-claude-001 \
  --reviewer-id reviewer-001 \
  --seed 20261005
```

Keep the key hidden from reviewers until all review artifacts are complete.
Reviewers may see the request, required behavior, violating behaviors, and model
response, but never the condition, injected context, or selected memory IDs.

## Optional Model Review

```zsh
uv run memory-loom review-study \
  evaluation-runs/development-pilot-claude-001/review-packet.json \
  --provider claude-cli \
  --model haiku \
  --reviewer-id model-reviewer-001 \
  --output evaluation-runs/development-pilot-claude-001/review-model.json \
  --jobs 4 \
  --resume
```

A model review is secondary and does not replace calibration against blinded
human review.

## Analyze

```zsh
uv run memory-loom analyze-study \
  evaluation-runs/development-pilot-claude-001/blinding-key.json \
  evaluation-runs/development-pilot-claude-001/raw \
  evaluation-runs/development-pilot-claude-001/review-model.json \
  --output evaluation-runs/development-pilot-claude-001/analysis.json \
  --report evaluation-runs/development-pilot-claude-001/REPORT.md \
  --bootstrap-samples 10000 \
  --seed 20261005
```

The analysis averages repeats within condition-query, gives scenarios equal
weight, and resamples template-family clusters. It reports simultaneous
intervals for B3-B0, B3-B1, and B3-B2 plus safety counts, failures, latency,
token usage, and estimated cost.

The frozen development package is versioned at
[`../../evaluation-runs/development-pilot-claude-001/`](../../evaluation-runs/development-pilot-claude-001/).
Its 192 runs completed without a model failure. All three simultaneous 95%
intervals for B3 preference-adherence contrasts included zero, so this pilot
does not distinguish B3 from any baseline. The result is model-reviewed,
synthetic, exploratory, and not evidence of effectiveness for real users.

`review-human.json` is an unreviewed template. Do not include it in analysis
until a condition-blind human has completed every rating. A blinded human
review is required before using this pilot to calibrate model-review judgments.
