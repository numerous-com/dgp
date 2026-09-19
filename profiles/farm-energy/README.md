# Farm Energy Calculator application profile

Read [PROFILE.md](PROFILE.md), then the root [SPECIFICATION.md](../../SPECIFICATION.md) §§18–24 for the generic optional contracts.

This directory supplies a worked ordinary-app design, two core frame examples, and twelve input-validation cases. It is not a running energy calculator. The single consolidated bundle includes the core schema, optional-profile definitions and examples, and the runnable ThreadDesk reference app.

From the repository root:

```bash
python profiles/farm-energy/validate_examples.py
python tools/validate_bundle.py
```

The study fixes real/declared demand and existing PV while exploring location, turbine, and discrete battery configurations. Results are hypothetical calculations, not edits to the selected design. Numerical comparison enforces the 50% self-sufficiency constraint and the explicitly selected economic objective; Jev directs exploration and judgments rather than inventing results.
