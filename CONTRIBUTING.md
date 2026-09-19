# Contributing to DGP

Start with [the specification](SPECIFICATION.md), [AGENTS.md](AGENTS.md), and
[conformance status](docs/CONFORMANCE.md). Keep core compatibility explicit and
separate profile proposals from implemented runtime behavior.

Run the offline checks with Python 3.11+ and uv:

```sh
uv run --no-project --with 'jsonschema==4.26.0' python tools/validate_bundle.py
```

Tests use synthetic data and temporary loopback fixtures. Do not add real API
credentials or real user evidence. Live provider experiments must remain opt-in.
New protocol behavior needs examples and focused positive/negative tests.
Update the specification and implementation-status document together.

Open a GitHub issue for a concrete bug or proposal, or a pull request explaining
the behavior, compatibility impact, and validation performed. Contributions are
provided under the repository's MIT License.
