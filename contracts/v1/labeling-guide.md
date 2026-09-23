# Labeling Guide v1

## Unit

Label one query at its declared scenario time. Reviewers may inspect only timeline events and lifecycle state that existed before that query.

## Memory Labels

- **Relevant:** required to produce the preferred behavior for this query.
- **Acceptable:** safe and applicable context, including every relevant memory.
- **Forbidden:** deleted, superseded, out-of-user, out-of-project, out-of-task, or otherwise disallowed context.
- **Neither:** eligible but unnecessary context, including a broader rule displaced by a narrower rule.

`relevant_memory_ids` must be a subset of `acceptable_memory_ids`. Acceptable and forbidden IDs must not overlap.

## Behavior Labels

- `required_behavior` states the observable response property needed for adherence.
- `violating_behaviors` list concrete failures rather than judging style generally.
- `abstention_correct` is true when no memory context should be supplied.

## Review Process

Reviewers must not see condition IDs during outcome adjudication. Record disagreements before adjudication and retain the original labels.
