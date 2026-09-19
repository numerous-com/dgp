# Optional GraphQL binding

The normative mapping is in SPECIFICATION.md §24. The SDL is an illustrative combined application schema: it exposes DGP records alongside a native application location operation. It is not a running endpoint.

`record: JSON!` carries the complete canonical core/profile record, validated with the bundled JSON Schema. Convenience-field selections alone are not assessment-ready DGP records. A projection must preserve the canonical frame and evidence requirements. Queries may read existing results; they must not secretly start simulations.

`nativeFarmSetLocation` deliberately does not create a DGP assessment. It calls the same authorized domain service and changes revisions so old conflicting DGP commits fail. `commit` MUST retain the normal DGP assessment binding and idempotency behavior.

`LocationInput @oneOf` follows the September 2025 GraphQL specification. Latitude/longitude range, compatibility, authorization, and quotas require additional domain checks. The JSON equivalent is tested as `ExclusiveLocationInput` in the optional-profile schema.

Optional structural validation:

```bash
cd bindings/graphql
npm install
npm test
```

The external `graphql` package was unavailable in this artifact-build environment. Accordingly, the supplied GraphQL validator was **not run** and no GraphQL execution/transport test is claimed. The validator script's JavaScript syntax and the equivalent JSON contracts are checked locally. Dependencies are not vendored. This does not affect running ThreadDesk or the Python tests.

Source: GraphQL September 2025 edition, https://spec.graphql.org/September2025/ .
