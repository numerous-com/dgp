# Conformance and implementation matrix

This matrix describes the contents of this bundle, not every possible DGP implementation.

| Area | Normative spec | Schema/examples | Exercised executable behavior | Reference server |
|---|---|---|---|---|
| Core frames/assessments/commits | Yes | Yes | 50 original tests, including HTTP/SQLite/concurrency | ThreadDesk |
| Assessment batching amendment | Optional profile | Separate schema and examples | Selected offline binding/partial-response checks | Not implemented |
| Coding tools amendment | Optional profile | Separate schema and examples | Selected operation/effect/artifact checks | Not implemented |
| Graph previews and speculative records | Yes | Yes | Original tests | ThreadDesk |
| Text/service inputs and image evidence | Yes | Yes | Fixture-based providers and image guards | ThreadDesk |
| Rubric/probability judgments | Yes | Yes | Adapter/result-contract tests | Adapter support; app emits choice/input only |
| Partial coverage and interface catalogue | Yes | Yes | Catalogue-reference/uniqueness tests | Not implemented |
| Frame projections and assessment basis | Yes | Yes | Canonical-binding, altered/missing evidence checks | Not implemented |
| Prepared operation catalogue | Yes | Yes | Schema/variables examples | Not implemented |
| Budgeted evaluation/admission/jobs | Yes | Yes | Budget snapshots and job lifecycle contract tests | No scheduler/worker/ledger server |
| Resumable events | Yes | Yes | Page order/stream/duplication checks | No live/replay event server |
| Cross-interface handoff | Yes | Yes | Record/result requirements | No handoff executor |
| GraphQL | Optional binding | SDL and example documents | JS validator script syntax only; parser dependency unavailable | No server |
| MCP | Mapping | Tool mapping documentation | No MCP transport tests | No server |
| Farm Energy Calculator | Application profile | Two frames plus expanded profile examples | Twelve embedded-input cases; no numerical calculations | Not implemented |

The new 41 profile tests are selected contract tests. They do **not** demonstrate distributed quota enforcement, actual evidence fetching, secure identity delegation, durable jobs, event replay, or numerical optimality. Those need an implementation and integration tests.

Native UI/API/CLI functions are allowed to bypass the DGP interaction sequence, but not underlying domain authorization, relevant revision updates, or shared accounting. They need not fabricate DGP assessments or receipts for native operations.

Conformance claims must enumerate supported features and bindings. A final specification is not a production certification or a claim that every optional feature is runnable.
