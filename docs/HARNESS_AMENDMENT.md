# Optional harness-profile amendment — 20 September 2026

Core protocol remains **DGP 0.1**. Optional profiles
`assessment-batching@0.1` and `coding-tools@0.1` are proposal revision 0.1.
The owner supplied and authorized amendment of `DGP_0.1_Complete.zip`.

Archive SHA-256:
`8603b1c29d8aad015a906b61927aea619984f6d7b239d97bf88ea9b37bb60f01`.
The original upload was preserved. All 81 entries were checked before import:
fixed root, relative traversal-free names, no duplicates/symlinks/special files or
encrypted entries, bounded entry/aggregate sizes. No uploaded server or agent was
launched. `UPSTREAM_IMPORT.json` records original per-file hashes;
`UPSTREAM_BUNDLE_MANIFEST.json` and `UPSTREAM_SHA256SUMS.txt` preserve upstream
release evidence. Current `BUNDLE_MANIFEST.json` and `SHA256SUMS.txt` describe this
amended copy rather than pretending old checksums still apply.

## Actual validation

Run from this package directory:

```sh
uv run --no-project --with jsonschema==4.26.0 python -m unittest discover -s tests -p test_jev_harness_profiles.py
uv run --no-project --with jsonschema==4.26.0 python -m unittest discover -s tests
```

**106 tests passed**: all 91 original tests plus 15 new profile tests. Four new
examples validated. New Python files pass Ruff. The new tests cover exact
current-frame/evidence binding, absent/changed required evidence, duplicate IDs,
unoffered preview targets, partial result binding, speculative-mode preservation,
boolean-versus-integer immutable-content changes, unknown/duplicate/nonfinite cost,
fixed coding operation IDs, effectful tests/application, and relative artifact
preimages. Copied core definitions are asserted identical to the original schema.

The full regression run includes six temporary loopback HTTP fixture-server tests;
it never starts the token-printing server main. Historical browser reports remain
upstream evidence and were not rerun. No live provider, deployed HTTP server, real
coding tool, filesystem mutation executor or job scheduler was exercised. The
helpers check selected contracts; they do not prove authentication, transactional
partial admission, durable idempotency, quotas, safe execution or interoperability.

## Integration boundary

Keep the harness's existing Jev transport and cost ledger. The imported demo's
server prints demo tokens; its provider HTTP-error path can relay remote details.
Those files are retained unchanged for provenance and are not production adapters.
Use existing host authorization and sanitized provider errors when an adapter is
implemented. Schemas and proposed catalogue entries grant no access.
