# Start here

**Everything from this protocol work is consolidated in this one bundle.**

Read `SPECIFICATION.md` for the finalized experimental DGP 0.1. The essential boundary is that DGP is one optional, possibly partial interface to shared application services—not a replacement for UI, API, MCP, CLI, or GraphQL.

Read `profiles/farm-energy/PROFILE.md` for the ordinary calculator example: location-first interaction, turbine and stepped battery choices, existing PV/demand, an explicit 50% self-sufficiency constraint, an economic objective, and bounded parallel evaluations.

Use `README.md` to run the ThreadDesk demonstrator. Consult `docs/CONFORMANCE.md` before assuming a specified optional feature is implemented. `docs/RELEASE_NOTES.md` explains the consolidation. `docs/VALIDATION_SUMMARY.md` records what was actually checked.

The schemas and examples are local. The GraphQL and MCP bindings are not runtime implementations, and the farm profile does not include an energy engine. No paid API key is needed for the ThreadDesk mock flow or Python tests.
