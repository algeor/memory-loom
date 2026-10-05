# Provider-Backed Experiment Runner

## Status

This is an implemented **design decision** for development pilots. It does not
turn a pilot outcome into a scientific result.

## Boundary

Provider adapters receive only the frozen system prompt, current-request prompt,
model identifier, and decoding configuration. They do not read or write the
Memory Loom database. Retrieval and context assembly finish before invocation.

The run artifact records:

- requested provider and model;
- provider-reported canonical model when available;
- exact system prompt, user prompt, and injected context;
- condition, scenario, query, repeat, and seed;
- latency, token usage, cost when reported, and provider response identifier;
- attributable context, invocation, or output-capture failures.

## OpenAI Responses API

The `openai` adapter calls the Responses API with `store=false`, sends the
frozen system prompt as `instructions`, and parses every `output_text` item
rather than assuming a fixed output-array position. This follows the
[official OpenAI text-generation guidance](https://developers.openai.com/api/docs/guides/text).

The API key is read from an environment variable and is never accepted as a CLI
argument or written to an artifact. The model and optional per-million-token
prices remain run configuration.

## Claude CLI

The `claude-cli` adapter invokes a preinstalled authenticated Claude Code CLI in
noninteractive safe mode with:

- an explicit replacement system prompt;
- no tools;
- an empty strict MCP configuration;
- no session persistence;
- stdin-only task input;
- execution from the operating-system temporary directory.

The adapter records the canonical model, usage, and cost returned by the CLI.
Claude CLI does not expose the manifest's temperature, top-p, seed, or output
token limit flags. A pilot using this adapter must record that limitation and
must not describe those values as enforced provider controls.

## Failure Behavior

Provider errors become `model_invocation` failures and do not discard completed
condition runs. Authentication errors are sanitized so credentials cannot enter
run artifacts or console output.

