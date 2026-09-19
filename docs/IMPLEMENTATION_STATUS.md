# Implementation and validation status

Date: 19 September 2026. This is an experimental specification plus a local reference demonstrator, not a deployed service or a published standard.

20 September amendment: optional assessment-batching and coding-tools profiles
have separate schemas/examples and selected offline tests. They add no server,
provider adapter, real repo operation or runtime feature advertisement. See
[HARNESS_AMENDMENT.md](HARNESS_AMENDMENT.md) for current validation and provenance.

## Implemented

| Area | Included behavior |
|---|---|
| Protocol | Manifest, surfaces, current/historical frames, assessment registration, guarded commits, immutable receipts, structured errors. |
| Records | Self-contained JSON Schema Draft 2020-12; server validation plus semantic checks. |
| State | SQLite persistence, per-thread revision read sets, shared policy revision, frame expiry. |
| Concurrency | Concurrent controller processing of separate surfaces; atomic local state validation/commit; stale conflict rejection. |
| Replay | Same successful request/key returns the same receipt, including after database reopening. |
| Text | Arbitrary schema-constrained note, analysis, and draft inputs. |
| Images | Authenticated blob storage/read, signature/size limit, SHA-256 metadata, browser integrity verification. |
| Disclosure | Next, bounded horizon, and full declared graph template. |
| Speculation | Speculative assessment records; server refuses their commitment. |
| Jev-first flow | Choice of reasoning/generation → input fulfillment → new frame → bounded reassessment. |
| Human barrier | Different authenticated roles; agent cannot publish by claiming `resolver.kind=human`. |
| UI | Minimal browser renderer using the same assessment and commit endpoints. |
| Adapters | Real TypeSafe HTTP adapter; optional OpenAI Responses text adapter; explicitly labeled offline mocks. |
| Tests | Unit tests, database/concurrency tests, HTTP integration flows, controlled provider-contract fixtures. |

## Deliberately limited or absent

The app simulates CI and publication. It does not call Git, execute code, launch CI tests, send mail, or control hardware. The internal state-transition recovery metadata is conservative (`unknown`) except where explicitly identified; a generic undo/compensation endpoint is not implemented.

No provider API credentials were available or used for live testing. Real-provider adapters are implemented and fixture-tested, but their availability, permissions, production behavior, and task quality remain unverified in a live account.

The Jev adapter follows the current text-only API. Required images produce a capability error. The OpenAI service adapter in this package is also limited to text/JSON; no image-captioning or native multimodal decision adapter was exercised.

The shared schema includes score/probability judgments, and the Jev adapter maps them, but ThreadDesk itself publishes only choice/input. The browser renders the demo's single-text inputs, not all possible JSON Schema form layouts.

The app is single-tenant and loopback-only, with one human and one agent role. It uses a standard-library HTTP demo server, not a hardened production deployment. The SQLite connection is protected by a process lock and local transactions, not a distributed scheduler. Binary validation is limited and is not a complete image-processing security boundary.

Inference is outside the application's database transaction. The logical service-request cap is not a durable billing quota. Client invocation budgets reset after restart; a production host should broker/deduplicate inference and maintain durable spending limits. A live provider may charge for a request whose output is later rejected as stale.

Frames and traces grow without automated retention/compaction. Assessment resolver metadata is explicitly client-asserted, not cryptographically verified. Redaction, multi-tenant access control, credential lifecycle management, provider-policy enforcement, and production logging are deployment work.

The runnable app has no real MCP/GraphQL server, subscriptions, paginated projection server, general barrier/race scheduler, sandboxed branch simulator, two-phase prepare/promote API, asynchronous job/event executor, or external exactly-once guarantee. Optional profiles are now specified and have selected schema/contract tests, but their server implementations are absent. See `CONFORMANCE.md`.

## Validation record

See `TEST_RESULTS.txt` for the captured unittest output. Tests operate on synthetic data and local fixture services. A separate browser smoke check and fixture-schema audit are recorded below when executed.

### Completed checks

- **91 automated tests passed (50 original tests and 41 added profile-contract tests)**, including real local HTTP client/server integration and fixture-based provider contracts. See `TEST_RESULTS.txt`.
- **11 complete JSON example records validated** against the bundled schema. See `examples/fixture-index.json`.
- JavaScript syntax checked with `node --check web/app.js`.
- In the earlier reference build, the browser renderer was checked with Chromium using in-memory DGP responses: both cards, draft review, UI assessment/commit payloads, local publication, Unicode notes, safe script-like text rendering, full disclosure, and a 390-pixel viewport. No JavaScript errors were observed in that earlier run. The browser check was not rerun for this consolidation; see retained `BROWSER_CHECK.txt`.
- This environment's browser policy blocked direct navigation to the local HTTP server. Therefore the browser check was an **offline renderer test**, not a live-browser network end-to-end test. The actual HTTP boundary was exercised separately by the automated Python integration tests.
- Consolidation test environment: Python 3.13.5; jsonschema 4.26.0.

`UI_PREVIEW.png` is a screenshot of the offline-rendered review state.
