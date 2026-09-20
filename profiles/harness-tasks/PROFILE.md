# Durable harness tasks profile 0.1

Status: optional application profile, `harness-tasks@0.1`. DGP core remains 0.1. This amendment defines durable task records and selected conformance checks; it does not turn ThreadDesk into a coding agent server.

## Prepared decisions and admission

A host supporting this profile advertises `core@0.1` and `harness-tasks@0.1` in frame required features. Supported operations are `task.start`, `task.steer`, `task.stop`, and `artifact.apply`. Each preparation binds one operation and its exact arguments in required evidence. The single ordinary core choice decision offers `execute` and `stop`; both accept only an empty input object. The frame extension binds task identity, operation, task revision and SHA-256 of arguments. Argument hashing uses sorted compact UTF-8 JSON, unescaped Unicode and no nonfinite numbers, matching the existing profile fingerprint helper.

A live core assessment records the selected choice. It does not execute work. A core commit plus a host idempotency key admits only the already prepared operation. Hosts MUST independently enforce identity, grants, current policy, argument binding, expiration and relevant workspace/task revisions. Untrusted prompt text, model output and command output never grant authority. Speculative assessments cannot authorize effects. Unsupported features fail closed.

Task identity is reserved at preparation. The host binds identities to its principal and workspace; controls use the existing task surface. Task start binds the workspace snapshot even before the task has running state. Steer binds the active worker turn/call identity. Stop requests cancellation; neither disconnect nor watching a task implies stopping it.

Successful receipts bind the original frame and assessment. Their profile extension records `queued`, `requested`, `applied` or `declined`. A queued/requested receipt means admission only, not completion, correctness, test success or calibrated confidence. `applied` is reserved for exact artifact application. A host may reject a stop assessment without committing an effect.

## Durability and reads

`TaskSnapshot` exposes host/task identity, revision, request digest, lifecycle status and nullable result. Statuses are queued, running, completed, failed, cancelled and interrupted. Completed means the runtime returned; clients must inspect its result for verification and evidence. A crash must not automatically repeat generation or ambiguous file mutations. On recovery, unfinished work becomes interrupted unless an explicit safe recovery protocol proves otherwise.

`TaskWatchPage` exposes a task-scoped stream, contiguous increasing event sequences and an opaque resume cursor. Consumers must bind cursors to host, task and stream. Events are actual runtime event objects, not fabricated assessments. Watch and get-result are reads and need no fake commit. Empty pages are valid. Retention implementations must explicitly report a gap requiring bootstrap; silently skipping events is forbidden. A bounded implementation may instead fail closed before pruning. Snapshot remains the authoritative terminal result if event capacity is exhausted.

Commit replay checks a durable successful receipt before freshness while still enforcing present authorization. Reusing an idempotency key with a different binding fails. Once a frame is consumed, a different key must not repeat it. An ambiguous reserved commit is not a success and must not be replayed blindly.

## Exact artifact application

`TaskArtifact` describes a task-bound immutable artifact digest, repository identity, base revision and unique relative file preimages. Hosts may expose an equivalent existing repository artifact format if they verify those same bindings; this schema is a portable optional view, not permission to apply arbitrary wire contents. An apply operation references the exact registered artifact. Host grants, repository/preimage checks and existing transaction recovery remain authoritative. Assessment or a completed coding task alone never applies files.

## Transports and implementation scope

DGP records are the core interface. Local stdio or a host-owned Unix socket may transport prepare/assess/commit and task reads. CLI attachment, message projections and optional thin MCP tools must share the same task state, authorization and event log; they are not alternative agent runtimes. A daemon owns work independently of attached client lifetimes. Shutting down the owning host may cancel or interrupt work explicitly.

The accompanying schema, synthetic examples and Python validators exercise selected record consistency. They do not prove authorization, crash safety, provider quality or cost. Claudestrate provides a separate local implementation and runtime integration tests. The updated bundle manifest identifies this optional amendment; original imported release provenance remains preserved separately.
