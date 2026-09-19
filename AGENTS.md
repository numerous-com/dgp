# Coding-agent handoff

## Purpose

Maintain a small, inspectable DGP 0.1 reference package. The specification is the primary deliverable; ThreadDesk demonstrates the contract, not a production agent platform.

## Architecture invariants

The domain owns permissions, guards, state, and effects. Jev is an intelligent assessor, not a rules engine and not an authorization authority. Text/JSON evidence can go directly to Jev. Unsupported required images must not disappear silently. Arbitrary text inputs are supported through explicit input contracts and optional generation services.

All interfaces must share authoritative domain guards, revisions, and accounting. A DGP-rendering UI uses DGP commits; a native UI/API/CLI may use native operations without fabricated assessments. In ThreadDesk specifically, UI and controller use the same DGP endpoints. Assessments, frames, and receipts are immutable while retained. A replay of a successful commit returns the same receipt before freshness checks. Model confidence and client-asserted provenance are not credentials.

Do not put real shell/Git/CI/email operations in the existing simulated handlers. A real executor needs a distinct design for authorization, durability, idempotency, ambiguous outcomes, and external side effects. Do not advertise an HTTP endpoint as MCP without implementing the selected MCP transport/lifecycle contract.

## Working commands

```bash
python tools/validate_bundle.py
python schemas/build_schema.py
python -m dgp_demo.server
python -m dgp_demo.agent --help
```

The tests use no real model API keys. Keep live-provider tests separate and opt-in. Never commit a provider credential, a local database, or real user evidence. Agent traces may contain submitted text; treat them accordingly.

## Definition of done for this version

The documented HTTP flows work, the shipped schemas/fixtures validate, tests pass, both mock flows stop appropriately, stale actions fail, and an agent cannot publish using a human-labeled payload. Documentation must accurately distinguish implementation from proposal. Once these criteria are met, stop; do not expand into a general workflow engine or repeatedly add speculative hardening to claim completion.

## Next useful implementation work, outside the completed release

The strongest next validation would be implementing the included Farm Energy profile against the existing calculator and a generic client that consumes both apps. Retain the calculator's native interfaces and reuse its actual domain engine; do not fabricate physical results. After that, select one concrete need: a production domain executor, durable service-call budgeting, or a standards-compliant MCP wrapper. Do not implement all of them merely because the protocol can describe their future roles.

## Optional-profile implementation rule

Read `docs/CONFORMANCE.md` before claiming runtime support. New schemas/examples are not servers. Core compatibility is intentional. Do not add missing workers, GraphQL/MCP transports, model-budget brokers, and production identity all at once merely because they are described. Implement and test only the selected integration.
