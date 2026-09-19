# HTTP/JSON binding

The runnable ThreadDesk implementation follows SPECIFICATION.md §12. Additional profile routes below are specified only, not implemented there.

| Route | Core/profile |
|---|---|
| `GET /.well-known/dgp` | Core discovery. |
| `GET /dgp/surfaces/{id}/frame` | Current core frame. |
| `GET /dgp/frames/{id}` | Immutable core frame. |
| `POST /dgp/assessments` | Core assessment recording. |
| `POST /dgp/commits` | Core guarded commit with `Idempotency-Key`. |
| `GET /dgp/receipts/{id}` | Core immutable receipt. |
| `GET /dgp/catalogue` | Optional interface/capability catalogue. |
| `GET /dgp/prepared-operations` | Optional operation catalogue. |
| `POST /dgp/prepared-operations/execute` | Execute a named/versioned operation, retaining its declared semantics. |
| `GET /dgp/frames/{id}/views/{view_id}?version={version}` | Optional named frame projection. |
| `GET /dgp/jobs/{id}` | Optional latest immutable job snapshot. |
| `GET /dgp/jobs/{id}/revisions/{revision}` | Optional historical job snapshot. |
| `GET /dgp/evaluation-policies/{id}` | Optional authorized budget/policy snapshot. |
| `GET /dgp/events?after={cursor}&limit={n}` | Optional resumable events. |

Advertised discovery links are authoritative; applications may mount these paths under a base prefix. Variables beyond simple view identity are supplied through prepared-operation execution, avoiding a new URL query language. Reads cannot start new paid simulations. Submission and cancellation are explicit guarded effects, not side effects of status retrieval.
