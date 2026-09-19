# Consolidated validation summary

Release: finalized experimental DGP 0.1, 19 September 2026.

## Performed for this consolidated bundle

| Check | Result |
|---|---|
| Original core/reference-app Python tests | 50 passed. |
| Added optional-profile contract tests | 41 passed. |
| Combined unittest run | 91 passed. |
| Core wire-example records | 11 validated. |
| Added profile/example records | 14 validated. |
| Farm frame examples | 2 validated. |
| Embedded farm input cases | 12 positive/negative cases passed. |
| JavaScript syntax | Browser app and optional GraphQL validation script passed `node --check`. |
| Core schema compatibility | SHA-256 identical to earlier ThreadDesk package. |

The 27 JSON records are structural examples, not 27 real-world executions. The 41 new tests exercise selected contract invariants such as projection binding, required evidence, budget snapshot limits, job transitions, event-page consistency, and handoff record requirements. They do not demonstrate production jobs, distributed quotas, or an actual alternate-interface executor.

Captured output: `TEST_RESULTS.txt` and `BUNDLE_VALIDATION.txt`. Reproduce with `python tools/validate_bundle.py` after installing the root Python requirements.

Core schema SHA-256:

```text
eed597237cbb0b87fb956643f6f0428d3cb179bedb9a8acb672a00a6ab95bcd9
```

## Not performed

No paid/live Jev or OpenAI calls; no actual wind, PV, battery, tariff, or economic simulation; no live Farm Energy application; no MCP or GraphQL server execution; no production authorization/load/security certification.

The optional GraphQL dependency could not be installed in this environment. Its SDL and operation validator is provided, but GraphQL parsing/type validation was not run. JSON equivalents and the validator script's JavaScript syntax were checked. See `bindings/graphql/README.md` for the optional reproduction command.

The retained browser screenshot and `BROWSER_CHECK.txt` come from the previous reference build's offline browser-renderer test. That test was not rerun here. This consolidation reran the actual local HTTP integration tests as part of the original 50 tests.

## Interpretation

“Finalized” describes this version of the specification and consolidated deliverable. It does not mean all optional profiles are implemented, the proposal is standardized, or model/energy outputs have been validated in production. See `CONFORMANCE.md`.
