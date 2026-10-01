# MCP Request And Response Templates

## Status

These are synthetic contract examples for the proposed MCP boundary. They are
not runtime fixtures and are not evidence that an MCP server exists.

## Templates

- [`retrieve.json`](retrieve.json)
- [`propose-change.json`](propose-change.json)
- [`commit-change.json`](commit-change.json)
- [`discard-change.json`](discard-change.json)
- [`inspect.json`](inspect.json)

All examples use synthetic identifiers and content. Implementations may wrap
the structured response in the MCP SDK's content envelope, but the represented
fields and lifecycle behavior must remain stable for contract version `1.0.0`.
