# Finalized 0.1 release notes — 19 September 2026

This is the consolidated authoring release of the experimental proposal, not an industry standard. It supersedes the separately supplied earlier specification and farm-profile notes in this conversation.

## Changes

DGP is explicitly one interface among UI, API, MCP, CLI, and GraphQL. Coverage can be deliberately partial, and a native UI need not render DGP or use its assessment sequence. Equivalent actions share domain invariants, scope, budget accounting, and state revisions. Authorized handoff is distinct from credential delegation or proof of completion.

GraphQL-inspired optional profiles add capability introspection, named projections, evidence hydration, prepared operations, typed results, and demand-control requirements. An optional GraphQL SDL demonstrates canonical DGP records alongside a native location edit. DGP does not require a new query language or generated GraphQL from Jev.

The farm evaluation profile is finalized with atomic all-or-nothing admission, immutable jobs/scenarios, budget reservation/settlement, explicit cancellation/reconciliation, and separate adoption of a selected design. Events define scoped cursors, retained replay, gaps, and rebootstrap rather than assuming a subscription is durable.

## Compatibility

`schemas/dgp.schema.json` is byte-for-byte unchanged from the earlier ThreadDesk package. New features are opt-in and have explicit profile IDs plus a separate self-contained schema. The previous farm identifier `budgeted-evaluations@0.1-draft` is replaced with `budgeted-evaluations@0.1`; clients must implement the finalized semantics before advertising it. Metadata is carried in named `extensions` and negotiated required features.

ThreadDesk source behavior is retained. It does not advertise the new profile features. Existing launch instructions and core fixtures remain valid. The new optional-profile examples are synthetic records, not a trace from ThreadDesk or an energy simulator.

## Validation and exclusions

The original 50 tests and 41 new contract tests pass. The farm validator separately checks two frames and twelve input cases. See `VALIDATION_SUMMARY.md` and captured logs for full details. Paid model calls, GraphQL parsing/execution, live MCP transport, and real energy calculations were not tested.

Public repository update, 20 September 2026: released under the MIT License, Copyright (c) 2026 Numerous ApS. Dependencies retain their own licenses. Original archive manifests remain historical provenance.
