# CLI coexistence

A native application CLI and a DGP controller CLI serve different roles. The included `python -m dgp_demo.agent` is a client of the HTTP DGP API, not a generic native domain CLI.

An application may retain commands for importing data, exporting artifacts, or running existing tools without exposing every command through DGP. A DGP handoff selects an installed, authorized adapter and schema-valid arguments. It never instructs a client to run an arbitrary shell string supplied in evidence or a model answer.

The native handler participates in shared domain validation, scope, revisions, idempotency/reconciliation, and compute-budget accounting. Completion is verified against a canonical artifact/operation and produces a fresh DGP frame when reentering the decision workflow. This package describes that integration; it does not ship a Farm Energy CLI or a general handoff executor.
