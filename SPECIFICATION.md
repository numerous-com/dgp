# Decision Graph Protocol — DGP 0.1

Compatible optional amendment: [Jev harness profiles](profiles/jev-harness/PROFILE.md)
defines `assessment-batching@0.1` and `coding-tools@0.1`. They add no core changes,
atomic multi-commit, hypothetical live decision IDs, or reference-server support.

**Status:** Finalized experimental specification, authoring release 0.1; not an industry standard or an official TypeSafe, GraphQL, or MCP specification.  
**Version:** `0.1`  
**Date:** 19 September 2026  
**Lead application profile:** Farm Energy Calculator (specified, not an implemented simulator).  
**Runnable reference application:** ThreadDesk (HTTP + browser UI + controller CLI).  
**Primary client profile:** Jev-first decision runtime, with optional generative/reasoning services.  
**Normative machine definitions:** `schemas/dgp.schema.json` (unchanged core); `schemas/dgp.profiles.schema.json` (optional profiles).  
**Working name:** Decision Graph Protocol. No claim is made that the name or abbreviation is globally unique.

## Abstract

DGP lets an application publish what can be **judged, supplied, and committed** in its current state, independently of any graphical interface. A client receives an immutable decision frame containing evidence, bounded judgments, input schemas, available transitions, and execution constraints. An intelligent decision model can read the evidence directly and return typed judgments. When arbitrary text or additional reasoning is needed, its runtime can invoke an authorized service, supply the resulting input, and continue against a new frame.

DGP is one possible interface to an application, alongside a native UI, API, MCP tools, CLI, and GraphQL. It MAY cover only the decisions and inputs for which it is useful. A UI MAY render DGP, but need not be built on it. All interfaces share authoritative domain rules rather than being required to share an interaction sequence. The GUI is not the source from which a decision client must reconstruct application meaning.

The protocol distinguishes an assessment from an authorized effect. The application owns state, permissions, guards, and execution. A model is neither a security boundary nor the source of execution authority.

DGP 0.1 combines a small interoperable core with independently negotiated profiles for graph previews, rich evidence, services, interface discovery, projections, prepared operations, budgeted jobs, and events. HTTP/JSON is the reference binding; GraphQL is optional and MCP is a documented mapping. DGP does not require a new transport, a workflow engine, complete application coverage, or a complete decision tree.

---

## Contents

- Abstract
- 1. Requirements language and scope
- 2. Actors and trust boundaries
- 3. Core information model
- 4. Evidence and modalities
- 5. Judgments and arbitrary input
- 6. Assessments
- 7. Commit and receipt
- 8. Static and dynamic disclosure
- 9. Concurrency, dependencies, and serialization
- 10. Speculation and effect classification
- 11. Jev-first service-input profile
- 12. HTTP binding
- 13. Optional MCP mapping
- 14. Human interface profile
- 15. Security and operational requirements
- 16. Application examples
- 17. Conformance and evolution
- 18. Interface and capability catalogue profile
- 19. Frame projections and evidence hydration profile
- 20. Prepared operations profile
- 21. Budgeted asynchronous evaluations profile
- 22. Resumable event profile
- 23. Authorized cross-interface handoff profile
- 24. Optional GraphQL binding
- 25. Final release scope and implementation guidance
- References

## 1. Requirements language and scope

In this document, **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** express respectively an absolute requirement, absolute prohibition, recommended default, discouraged default, and optional behavior within this proposed protocol. They do not imply endorsement by a standards organization.

The JSON Schema defines record structure. This document defines semantic requirements that a structural validator cannot prove: freshness, authorization, idempotency, truth of provenance, and side-effect handling. Both are required for conformance. The self-contained schemas use JSON Schema Draft 2020-12. [S5]

### 1.1 Goals

DGP is designed to support:

- Direct consumption of structured and unstructured evidence by an intelligent decision model, including negotiated modalities.
- Bounded typed judgments **and** arbitrary schema-constrained inputs, including free text.
- A Jev-first control loop that selectively requests generation or deeper analysis without surrendering application authority.
- Static inspection and dynamic operation over the same application semantics.
- Concurrent assessment where useful, with explicit consistency checks before effects.
- Immutable records, reproducible references, and safe handling of speculative results.

### 1.2 Non-goals in 0.1

DGP 0.1 is not a model inference API, a reasoning algorithm, an optimizer, or a system for proving model answers correct. It does not standardize visual styling, arbitrary executable guard code, distributed transactions, external exactly-once effects, a general barrier/race orchestration language, or rollback of arbitrary real-world actions.

The core commits synchronous application transitions. A transition can enqueue long-running work, but the receipt must then describe **the enqueue**, not claim the external work completed. The optional budgeted-evaluation and resumable-event profiles (§§21–22) define a bounded job lifecycle, not a general distributed workflow engine.

### 1.3 Conformance profiles

| Feature identifier | Requirement | Meaning |
|---|---|---|
| `core@0.1` | Mandatory | Discovery, surfaces, current frames, text/JSON evidence, choice/input contracts, assessments, guarded commits, immutable receipts, errors. |
| `graph-preview@0.1` | Optional | Static templates and bounded/full disclosure of the declared graph. |
| `speculative-assessment@0.1` | Optional | Record hypothetical assessments without permission to commit them. |
| `service-input@0.1` | Optional | Named services that can fulfill declared input nodes. |
| `image-evidence@0.1` | Optional | Immutable image blobs with integrity metadata and capability-aware handling. |
| `judgment-rubrics@0.1` | Optional | Score and probability judgments. Defined in the shared schema; not emitted by ThreadDesk. |
| `interface-catalogue@0.1` | Optional | Application identity, available interfaces, partial coverage, and capability discovery (§18). |
| `frame-projections@0.1` | Optional | Named views of one immutable frame, with complete contracts/evidence before assessment (§19). |
| `prepared-operations@0.1` | Optional | Versioned, predeclared read/assessment/commit operation templates (§20). |
| `budgeted-evaluations@0.1` | Optional | Atomic batch admission, shared resource limits, immutable scenario jobs, and accounting (§21). |
| `resumable-events@0.1` | Optional | Cursor-based notifications and reconciliation after gaps (§22). |
| `interface-handoff@0.1` | Optional | Authorized, scoped continuation through another application interface (§23). |
| `graphql-binding@0.1` | Optional | GraphQL carriage of canonical DGP records and guarded mutations (§24). |

A producer MUST advertise supported features. A consumer MUST reject a frame whose `required_features` it cannot honor. A server MUST reject unsupported request `required_features` with `CAPABILITY_REQUIRED`. Unknown optional metadata inside `extensions` MAY be ignored; unknown security-critical semantics MUST NOT be hidden there without a corresponding required feature.

ThreadDesk implements the core and the graph-preview, speculative-assessment, service-input, and image-evidence profiles. Its Jev adapter additionally maps rubric/probability judgments, tested at the adapter boundary; its application only publishes choice and input nodes. The added profiles are specified with schemas, examples, and contract checks; ThreadDesk does NOT advertise or implement them. See `docs/CONFORMANCE.md`.

### 1.4 Multiple interfaces and deliberately partial coverage

An application MAY expose UI, HTTP API, MCP, CLI, GraphQL, and DGP interfaces simultaneously. None is required to be a wrapper around another. DGP conformance applies to the declared surfaces and advertised profiles, not to every application feature. An application MAY expose only configuration selection and scenario evaluation through DGP, while retaining map editing, bulk file upload, billing, exports, and administration elsewhere.

A DGP client MUST NOT infer that an unexposed capability is impossible or unavailable through another interface. It also MUST NOT infer permission to discover or invoke an undocumented endpoint. Native capabilities and DGP bindings are distinct: a native MCP tool can perform domain work; an MCP tool carrying `dgp_commit` is a transport for DGP semantics.

All effectful interfaces MUST enforce the application's authoritative domain invariants, scope and permissions, and shared resource accounting. Equivalent operations MUST NOT gain authority merely by changing transport. Different interfaces MAY use different interaction sequences and explicit assurance policies: an authenticated human UI operation need not create a model assessment. Hiding a DGP option is not sufficient protection if the same agent can bypass an intended restriction through a native API.

Every relevant native write MUST update the revisions/invariants checked by DGP, even when no DGP receipt exists for that write. If this integration cannot be guaranteed, an implementation MUST re-read authoritative state and revalidate under the commit consistency boundary, or decline the affected commit. An off-protocol result is not a DGP receipt.

### 1.5 Recommended minimum adoption

A small app can implement only discovery, one scoped frame, choice/input assessments, guarded commit, receipts, and core errors. It need not expose static graphs, speculation, services, a GUI, GraphQL, or asynchronous jobs. A calculator with a costly engine can add budgeted evaluations; an app with large evidence can add projections. Do not model ordinary arithmetic, known parameter binding, or every native field edit as a model decision.

## 2. Actors and trust boundaries

**Application publisher.** Owns the domain state and exposes decision surfaces. It controls which decisions exist, their current answer spaces, and their action bindings.

**Controller runtime.** Discovers surfaces, obtains frames, selects evidence, invokes assessors or services, records results, and submits authorized requests. “Jev calls an LLM” means that Jev selects a service-request option and this runtime executes the corresponding allowed operation.

**Assessor.** Produces a bounded judgment. It may be Jev, another decision model, an LLM, a human, or deterministic code. Its identity is recorded separately from the authenticated submitter.

**Input producer/service.** Produces an open-ended value such as a draft, code artifact, analysis, or extracted structure. It does not acquire commit privileges by supplying a value.

**Effect executor.** Validates and performs a transition under application policy. It can be part of the publisher. It MUST NOT trust model output as evidence of permission.

**Human reviewer.** An authenticated principal with appropriate authority. A request body claiming `resolver.kind = "human"` is not human authentication.

The resulting control boundary is:

```text
Application state + trusted policy
              │
       immutable frame
              │
      controller runtime
              │
      intelligent assessor
              │
     assessment / service choice
              │
       guarded application commit
              │
      receipt + updated application state
```

Where a service is needed:

```text
Jev selects request_reasoning
              │
commit opens a declared analysis input node
              │
runtime invokes an authorized LLM service
              │
text supplied as derived evidence
              │
new frame → Jev makes the next bounded judgment
```

For generation:

```text
Jev selects draft_update → text input node → LLM draft
  → store draft → new review decision → authorized publication
```

The runtime MUST NOT give the LLM broader application credentials merely because it was invoked for reasoning or generation. The reference LLM adapter has no tools.

## 3. Core information model

### 3.1 Surface, graph, and frame

A **surface** is a stable, scoped place where an application publishes decisions: one coding thread, order, battery, document, or workstream.

A **graph** is a versioned description of possible node templates and known transitions. It may contain branches, joins, cycles, terminal states, or runtime expansion points. It is not a tree requirement.

A **frame** is an immutable observation of a surface at a particular state/policy revision. It materializes currently available decision instances. Re-entering a graph node creates a new instance, even when the template node ID is unchanged.

The relationships are:

```text
Graph template + current domain state + current policy
                            ↓
                     Decision frame
                            ↓
              Available decision instances
```

Graph inspection does not create action authority. Only a currently offered decision instance, accepted through the commit rules, can trigger a transition.

### 3.2 Required frame fields

| Field | Semantics |
|---|---|
| `dgp` | Exact protocol version, `"0.1"`. |
| `frame_id` | Opaque ID for an immutable record. |
| `surface_id` | Stable domain scope identifier. |
| `graph_id`, `graph_version` | Template identity; graph changes create a new version. |
| `policy_ref` | Policy identity/revision involved in this frame. |
| `created_at`, `expires_at` | UTC timestamps. Expiry limits commitment, not historical readability. |
| `read_set` | Resource/revision pairs against which a commit is checked. |
| `observations` | Evidence values or immutable blob references. |
| `decisions` | Currently offered instances, not predicted future questions. |
| `disclosure` | Actual disclosure level and optional graph preview. |
| `service_calls_remaining` | Remaining logical service-request allowance for the application workflow. Not a provider billing balance. |
| `required_features` | Features the client must understand before acting. |

A producer MUST include every domain resource or policy dependency relevant to commit validity in the read set, or enforce an equivalent current-state invariant at commit time. Merely attaching a timestamp does not establish concurrency safety.

Evidence IDs and decision IDs are interpreted relative to their frame. Long-lived cross-frame evidence references MUST include a frame ID or another immutable artifact identity. Blob digests refer to exact bytes.

The publisher MAY retain frames beyond expiry for audit. “Immutable” means a record is not silently edited while available; it does not mandate perpetual storage of personal data or prevent a documented retention/redaction process. A removed record SHOULD leave a tombstone rather than silently resolve to different content.

### 3.3 Decision instance fields

Each decision contains `decision_id`, `node_id`, `kind`, `question`, `evidence_ids`, `dispatch`, and `execution`, plus kind-specific fields.

`question` is trusted application-authored evaluation guidance. Evidence is not allowed to redefine it. `evidence_ids` identify the relevant observations. A publisher SHOULD avoid dumping the whole application into every question.

`dispatch = automatic` indicates work the normal controller loop should consider now. `on_request` indicates an available interaction, such as adding a human note, that should not be performed merely because it exists. This distinction prevents an agent from continually taking optional actions instead of reaching quiescence.

`execution.conflict_keys` describe coarse conflict domains. They are advisory scheduling aids, not locks issued to a client. `execution.depends_on` references prerequisite receipts already satisfied for a currently offered decision. A producer MUST NOT advertise an unsatisfied prerequisite as currently committable. Future dependencies belong in the preview graph.

## 4. Evidence and modalities

### 4.1 Rich evidence is first-class

DGP does not require an LLM to turn every paragraph into features. Text can be consumed directly by a capable decision model. Images can likewise be consumed directly by a capable multimodal decision model. The input modality is independent of the output contract.

An evidence item identifies its kind, MIME type, source, required/optional status, trust classification, and either inline content or an immutable blob reference. It MUST NOT contain both inline content and a blob reference.

Core evidence kinds are `text` and `json`. Image evidence is an optional profile. The schema reserves `audio`, `video`, `document`, and `timeseries` representations for negotiated profiles; their presence in the vocabulary does **not** mean every resolver or application supports them.

A JSON object can contain real numbers, booleans, strings, and arrays; text-only model input does not imply that numeric application state must first become a set of hand-engineered categories.

### 4.2 Provenance and trust

`source` records provenance. `trust` distinguishes:

| Value | Meaning |
|---|---|
| `observed` | Application-provided observation. This is a provenance category, not a proof that the world matches it. |
| `untrusted` | User-supplied or externally supplied content, including logs and screenshots. |
| `derived` | Interpretation, generated text, transformed evidence, prediction, or other inference. |

A generated analysis MUST remain distinguishable from a measurement or source document. Repeating an analysis through another model does not turn it into verified evidence. An artifact's `derived_from` references SHOULD identify its source observations.

Authentication proves who submitted a record, not whether the submitted account of its model or provenance is truthful. The reference server labels resolver claims `client_asserted`. Production deployments requiring stronger attribution SHOULD broker inference or issue signed service receipts.

### 4.3 Capability matching

The runtime MUST distinguish capabilities of the **protocol**, **application**, and **specific assessor**. An image-capable application does not make a text-only model image-capable.

Before inference, it MUST check the decision's required evidence against the chosen assessor. Unsupported required evidence results in `UNSUPPORTED_MODALITY`, an explicit approved transformation, or a switch to a capable assessor. It MUST NOT silently drop an image, serialize a URL and pretend it was viewed, or relabel a caption as the original evidence.

Optional evidence MAY be omitted, but the inference provenance SHOULD record the omission. Transformations such as image captioning produce additional derived evidence and require explicit application permission when used as substitutes for required originals.

**Current Jev adapter note:** TypeSafe's documentation, checked on 19 September 2026, describes Jev as accepting text/JSON state and not native image/audio/video input. The shipped adapter consequently supports text/JSON and rejects required image evidence. This is a provider limitation, not a limit on DGP's abstraction. [S1]

### 4.4 Binary evidence

The image profile uses `blob.href`, `blob.sha256`, and `blob.byte_length`, with `mime_type` on the evidence item. The digest covers the raw blob bytes.

Blob access MUST be authorized to the relevant scope. Clients MUST restrict fetching to trusted origins or an explicit allowlist, enforce content/size limits, and verify bytes against the advertised digest before use. URLs in untrusted text are not automatically fetch instructions. Inline tokens in URLs SHOULD be avoided.

ThreadDesk accepts PNG/JPEG/WebP uploads up to 256 KiB and checks the file signature. This is a demonstration limit, not a complete image-security boundary. A production binary processor needs appropriate decoding, dimensions/decompression limits, malware controls where relevant, and sandboxing.

## 5. Judgments and arbitrary input

### 5.1 `choice`

A choice asks one bounded question over an explicitly described option set. Every option has a stable `id`, human label, semantic `meaning`, `input_schema`, and effect description.

A choice answer is:

```json
{"choice":"retry","input":{}}
```

`input` carries any option-specific parameters. It can contain text, numbers, structures, or artifact references according to the option schema. Thus a choice is not restricted to a parameter-free button.

The server MUST reject a choice absent from the referenced frame. Option descriptions SHOULD distinguish alternatives sufficiently for a model to judge them. An uncertain/no-action path SHOULD be offered where the options do not exhaust the possible evidence.

### 5.2 `input`

An input node requests an arbitrary schema-constrained value rather than a classification. A text field is a normal input, not an escape hatch.

```json
{"value":{"text":"The simulated retry succeeded; the result awaits review."}}
```

A node's `input_schema` defines validation. Free text MAY be human-written, copied from an authorized artifact, or generated by an LLM. DGP does not require a decision model to generate it.

Input acceptance and subsequent publication are distinct transitions when the content needs review. An application SHOULD separate “store draft” from “publish draft” rather than smuggling publication into a form-field update.

The core uses JSON Schema Draft 2020-12 for input contracts. Implementations MUST NOT pretend to support its full semantics while silently ignoring unsupported keywords. Remote schema resolution MUST be disabled unless explicitly secured. ThreadDesk only accepts server-authored, self-contained input schemas. [S5]

### 5.3 `score` and `probability`

The optional rubric profile adds:

- `score`: a finite value in `[0, N-1]` on an ordered list of `N` rubric descriptions. Fractional positions are allowed; they are not automatically physical units.
- `probability`: a finite number in `[0,1]` for an explicitly defined proposition. The proposition SHOULD specify its scope and time horizon where relevant.

Answers are respectively `{"score":1.6}` and `{"probability":0.84}`. A boolean is not a probability-valued answer. The application, not the model API, defines how a probability or score affects later decisions.

Jev's Choice, Score, and Noul map to these judgment shapes. Noul is a probability judgment, not an ordered severity scale. Questions that require a previous answer as new evidence require a subsequent frame/request; independent questions against the same evidence can be assessed together. [S2]

### 5.4 Probability semantics

Optional uncertainty data can contain a distribution, provider confidence, action-selection propensity, and calibration reference. These are different quantities.

A distribution over choices MUST contain exactly the offered option IDs; over score levels, exactly the zero-based level indices represented as strings. Values MUST be finite, in `[0,1]`, and sum to one within `1e-6`.

`provider_confidence` MUST preserve provider semantics. It MUST NOT be presented as the probability that an external operation succeeds. `selection_propensity` is the probability with which the controller policy actually selected the action; a model's belief over answers is not automatically that policy's sampling distribution.

No universal automatic-commit threshold is defined by DGP. A high-confidence answer can still be wrong, stale, unauthorized, or based on omitted evidence. TypeSafe documents its confidence as a statistic derived from the answer distribution. [S3]

## 6. Assessments

An assessment is an immutable claim about a decision frame. Recording it does not execute the selected application action.

Required request fields are `assessment_id`, `frame_id`, `decision_id`, `mode`, `resolver`, and `result`, plus `dgp`.

```json
{
  "dgp":"0.1",
  "assessment_id":"a-101",
  "frame_id":"f-101",
  "decision_id":"f-101:recovery",
  "mode":"live",
  "resolver":{"kind":"decision_model","provider":"typesafe","model":"jev-1.13.0"},
  "result":{"status":"answered","answer":{"choice":"retry","input":{}}}
}
```

The identifiers above are illustrative. Complete mutually consistent fixtures are in `examples/`.

`result.status` is `answered` or `abstain`. An abstention does not authorize a transition. It can carry a brief reason, but the protocol does not request or require hidden chain-of-thought.

The server appends `recorded_at`, `submitted_by`, and provenance status. Resolver claims do not replace the authenticated principal.

Reusing an assessment ID with the same principal and identical normalized content returns the original record. Reusing it with different content or another owner MUST fail with `ASSESSMENT_ID_REUSED`.

An assessment MAY be recorded after its frame expires or becomes stale for audit. That does not make it committable. Recording assessments changes audit storage, not the frame's domain read set.

## 7. Commit and receipt

### 7.1 Commit request

A commit refers to an already recorded assessment:

```http
POST /dgp/commits
Authorization: Bearer <application credential>
Content-Type: application/json
Idempotency-Key: k-101
```

```json
{
  "dgp":"0.1",
  "frame_id":"f-101",
  "decision_id":"f-101:recovery",
  "assessment_id":"a-101"
}
```

The client MUST preserve the exact body and idempotency key until the outcome is known. A timeout is not evidence that nothing happened.

DGP uses the frame's read set in the body-linked contract rather than misusing an HTTP `If-Match` precondition for some different resource. Ordinary HTTP conditional requests may be used where their semantics actually apply. [S6]

### 7.2 Required processing order

Within the application consistency boundary, a server MUST:

1. Authenticate the caller and check general access to the endpoint/scope.
2. Look up an existing result for this principal and idempotency key. For matching content, return the original receipt; for different content, reject.
3. Load the immutable frame and assessment and verify their binding and ownership.
4. Reject speculative or abstained assessments for commitment.
5. Check frame expiry, relevant resource revisions, graph/policy validity, and current transition availability.
6. Validate the answer and input against the offered contract, and check current authorization, deterministic guards, quotas, and any required human authority.
7. Apply the accepted domain transition and durably associate its receipt with the idempotency key.

Checks and the guarded local state transition MUST be atomic with respect to relevant concurrent local commits. Implementations MUST NOT check permissions/revisions, release their protection, and later execute without revalidation.

The exact order among independent validation checks may vary, but successful idempotent replay must not become a stale-frame failure simply because the original action changed the state.

### 7.3 Authority and effects

An assessor never supplies an executable function name, shell command, destination account, or scope that the publisher has not authorized. Application bindings resolve selected IDs to trusted handlers and fixed scope.

An authenticated human-required transition MUST reject an agent credential even when the payload says the resolver was human. In the reference core, a human reviews a current frame and submits their own assessment/commit. A reusable approval-grant protocol is deliberately not defined in 0.1.

A service result that merely claims “approved by user” is not approval. Changing the draft, target, or relevant policy requires a new review under the appropriate frame.

### 7.4 Receipt and external delivery

A receipt contains the accepted binding, authenticated submitter, outcome, resulting state revision, effect description, and a link to the next frame. It is immutable.

The core receipt status is `succeeded`, meaning the described **local transition** completed. Applications MUST be precise about the outcome. “Queued test run” is not “tests passed”; “submitted message to provider” is not proof of delivery.

For external services, a durable outbox, downstream idempotency, provider receipts, and reconciliation may be needed. Those are executor responsibilities, not guarantees supplied by DGP. An irreversible action MUST NOT be retried blindly after an unknown outcome.

ThreadDesk commits its simulated effects and deduplication records in one SQLite transaction. This does not establish exactly-once Git, CI, email, payment, or other network effects.

### 7.5 Error outcomes

A rejected core commit MUST NOT partially apply its local domain transition. Assessment/audit records can remain. An unexpected provider outcome should be represented by a separately tracked operation or reconciled executor state, not disguised as a guaranteed no-effect rejection.

Successful idempotency records MUST be retained for the advertised retention period. An expired/forgotten key cannot safely justify retrying an old uncertain action; recovery should inspect the application's outcome history.

## 8. Static and dynamic disclosure

Disclosure is independent of who makes the decision.

| Request | Response semantics |
|---|---|
| `next` | Current observations and actionable instances only. |
| `horizon` | Current frame plus a bounded graph-template preview. |
| `full` | Current frame plus the complete declared graph/template that the server can disclose. |

`horizon` uses a nonnegative edge-distance bound from the current template nodes. For cyclic graphs this bounds graph exploration, not a promise about the number of future runtime visits. A producer MUST report `provided` and a completeness value rather than silently claiming a complete future.

`full` does not mean all possible future evidence, all future model outputs, or an infinitely unrolled loop. `complete_template` means all declared template nodes are disclosed. Guards can still depend on live application state; on-request auxiliary interactions can preserve their enclosing phase. A genuinely runtime-extensible graph SHOULD advertise `partial` and explain what is omitted.

Static nodes are addressed by `node_id`; current instances use `decision_id`. Clients MUST NOT fabricate a current instance from a preview. The graph profile is descriptive, not an executable language for client-supplied predicates.

The runtime MAY inspect a full template once, cache by graph version, and use inexpensive `next` frames for routine operation. A deeper resolver MAY inspect a wider horizon when needed. These choices do not alter application authority.

## 9. Concurrency, dependencies, and serialization

### 9.1 Assessment parallelism is not effect parallelism

Several questions can be assessed simultaneously without permitting their actions to execute simultaneously. A runtime MUST separate:

- Evidence/assessment independence: whether one answer is needed to construct another question's evidence.
- Domain independence: whether two resulting effects commute or contend for shared invariants.

An application MAY expose several independent surfaces. Clients MAY assess them concurrently. ThreadDesk demonstrates two surfaces evaluated in parallel; commits are still serialized inside the local database and freshness is checked per relevant thread.

### 9.2 Baseline optimistic consistency

DGP core uses optimistic reads plus guarded commits. Two assessments can refer to the same revision. The first successful conflicting transition changes that revision; a later conflicting commit is rejected. A change to an unrelated resource does not need to invalidate the frame.

`conflict_keys` help a scheduler avoid wasted work, but omission of a conflict key MUST NOT bypass authoritative application checks. A publisher that cannot prove independence SHOULD use a coarser shared revision or exclusive executor scope.

“Single threaded” is therefore a scope policy, not a global protocol mode. Separate worktrees might permit parallel investigation; writes to the same worktree or a shared branch may require serialization. Real tests can have arbitrary effects and are **not** assumed read-only.

### 9.3 Joins, barriers, races, and exclusive alternatives

A graph can describe these patterns, but DGP 0.1 does not define a general distributed scheduler for them. A publisher represents the result by exposing the next decision only once its domain conditions are met:

| Pattern | Publisher behavior in 0.1 |
|---|---|
| Ordered | Withhold downstream instances until prerequisites are satisfied. |
| Barrier/all | Expose the join decision after all required branches produce accepted outcomes. |
| Exclusive | First valid commitment consumes the alternative and changes shared state. |
| First-valid/race | The application atomically accepts an eligible winner, then invalidates competing commits. |
| Independent | Use distinct relevant read/write scopes; unrelated updates do not invalidate them. |

A race winner is not merely the first model response. It must meet the acceptance policy and commit checks. Cancellation of losers is best effort and does not undo requests already made or charges already incurred.

Clients MUST NOT infer atomic cross-surface transactions from a list of independently available decisions. Core submission is one assessment/transition at a time. A batching API would need an explicit negotiated profile with specified atomicity.

## 10. Speculation and effect classification

### 10.1 Speculative assessments

With `speculative-assessment@0.1`, an assessment can use `mode = speculative` and include explicit assumptions. It MAY explore a conditional interpretation while the actual world remains unchanged.

A speculative assessment MUST NOT be directly committed. Promotion requires a fresh live frame and a new live assessment after validating assumptions, evidence dependencies, policy, and permissions. A client MUST NOT simply relabel the old record or reuse its ID.

A trusted runtime may reuse cached computation only when its inference inputs, relevant state, decision contract, assessor configuration, and assumptions are genuinely equivalent. Different questions or a changed evidence set invalidate that equivalence.

The reference client supports speculative choice assessment on an existing frame and stops without committing. It does not run speculative external actions or a branch simulator.

### 10.2 Four execution stages

The broader architecture distinguishes:

| Stage | Meaning | 0.1 treatment |
|---|---|---|
| Assess | Produce a judgment without the selected domain effect. | Core assessments. |
| Simulate | Evaluate a hypothetical world state. | Assumptions can be recorded; no standard simulator service. |
| Prepare | Produce an isolated artifact or reserve resources. | An explicit application transition/input; no generic two-phase-commit token. |
| Commit | Apply an authorized domain transition. | Core commit endpoint. |

Creating a worktree, writing a draft, purchasing inference, or reading a remote API is not necessarily “pure” in the operational sense. A draft may be locally reversible while its contents have already been disclosed to a provider. Capability policy must account for both.

### 10.3 Effect descriptor

DGP avoids one misleading ordered `effect = pure|reversible|...` scale. It records separate dimensions:

| Field | Values |
|---|---|
| `world_mutation` | `none`, `internal`, `external` |
| `recovery` | `not_applicable`, `exact`, `compensatable`, `irreversible`, `unknown` |
| `data_egress` | `none`, `approved_provider`, `external` |
| `speculation` | `evaluation_only`, `sandbox_only`, `forbidden` |
| `required_actor` | `any_authorized`, `human` |
| `simulation` | Whether this implementation uses simulated rather than real domain effects. |

`exact` restoration is relative to an explicitly bounded domain; it does not undo elapsed time, resource usage, disclosure, or all external observations. Compensation is a new action with its own failure modes, not literal reversal of history. `unknown` MUST NOT be treated as harmless.

Inference/provider spending belongs to the service invocation's policy even when a selected application transition has `data_egress = none`. An effect descriptor is not a complete monetary budget contract.

An irreversible effect generally warrants stronger controls, but reversibility alone does not determine permissions. Production policy SHOULD consider impact, affected scope, external visibility, uncertainty, and human authorization independently.

## 11. Jev-first service-input profile

### 11.1 Contract

A service-input node includes:

```json
{
  "fulfillment":{
    "service_id":"llm.generate_text",
    "purpose":"Write a factual status-update draft. Never publish it.",
    "output_field":"text"
  },
  "input_schema":{
    "type":"object",
    "properties":{"text":{"type":"string","minLength":1,"maxLength":2000}},
    "required":["text"],
    "additionalProperties":false
  }
}
```

This is a node excerpt, not a complete decision record.

The application advertises a service's purpose, operation, input modalities, output kind, and output limit. The runtime maps a trusted service ID to an authorized local adapter. The ID is not a client-provided executable URL, prompt-injection escape, or grant of tool access.

The service produces a proposed value. The runtime validates it, records its provenance, and submits it through the normal assessment/commit path. The application can reject stale or invalid input exactly as it rejects a stale choice.

### 11.2 Bounded escalation

An implementation SHOULD bound service calls, model evaluations, recursion depth, context size, wall time, and spend where these can grow. The limits MUST be enforced by application/runtime logic rather than natural-language instructions to the model.

ThreadDesk permits at most one diagnostic service request and one draft request per workflow, under a total logical request ceiling of three. Its client also limits steps and service invocations per process. These do not constitute a durable provider-side billing quota: restarting a client can repeat an unfinished inference. A production host needs a durable inference ledger and budget reservations when that distinction matters.

The runtime MUST stop or escalate to a human when it cannot obtain a valid answer within policy. It MUST NOT repeatedly create “improvement” tasks just because optional capabilities remain available. Quiescence is a successful terminal condition.

### 11.3 Returning from the LLM

LLM output is not required to pass through Jev when it is merely completing an already selected generation task and deterministic schema checks suffice to store a draft. Before a new consequential judgment, however, the application SHOULD expose a new decision.

ThreadDesk therefore stores generated text, emits a fresh frame, and lets the decision resolver judge the draft. Its publication action still requires an authenticated human. This preserves Jev-first orchestration without implying that Jev verifies all generated claims or can grant permissions.

The optional OpenAI adapter uses the Responses API as a text-producing service, not as the protocol transport. [S9]

## 12. HTTP binding

The reference binding uses UTF-8 JSON over HTTPS. HTTP is allowed for explicitly local development. The experimental discovery path `/.well-known/dgp` is a project convention, not a registered well-known URI claim.

All private surfaces, frames, evidence, assessments, commits, and receipts MUST require appropriate authorization. Discovery MAY be public if it reveals no sensitive capability or tenant data.

| Method/path | Response/purpose |
|---|---|
| `GET /.well-known/dgp` | Manifest and supported features. |
| `GET /dgp/surfaces` | Authorized surface summaries and frame links. |
| `GET /dgp/surfaces/{id}/frame?disclosure=next` | New immutable frame of the current state. |
| `GET /dgp/surfaces/{id}/frame?disclosure=horizon&horizon=2` | Current frame and bounded template preview, when supported. |
| `GET /dgp/surfaces/{id}/frame?disclosure=full` | Current frame and full declared template disclosure. |
| `GET /dgp/frames/{frame_id}` | Retrieve the exact stored frame. |
| `POST /dgp/assessments` | Validate and register an assessment; no selected domain effect. |
| `GET /dgp/assessments/{assessment_id}` | Retrieve the immutable assessment. |
| `POST /dgp/commits` | Guard and apply the selected transition; requires `Idempotency-Key`. |
| `GET /dgp/receipts/{receipt_id}` | Retrieve the immutable outcome receipt. |
| `GET /dgp/graphs` and `/dgp/graphs/{id}` | Optional graph-template discovery/read. |
| `GET /dgp/services` | Optional service-input capability descriptions. |
| `GET /dgp/blobs/{scope}/{digest}` | Optional authorized binary evidence; exact paths are implementation-defined links. |

Servers MAY choose different route prefixes and expose them through links. Clients SHOULD use advertised links rather than assuming domain-specific action URLs. They MUST prevent credentials being forwarded to arbitrary linked origins.

State-bearing responses SHOULD use private/no-store caching unless an application explicitly implements scoped caching. The reference server uses `Cache-Control: no-store`. Frame creation on read is permitted as audit bookkeeping; it does not execute a selected application action.

Core collection responses use `{"dgp":"0.1","surfaces":[...]}`, `graphs`, or `services` respectively. Pagination and subscriptions are not standardized in 0.1; large producers should avoid claiming complete discovery when silently truncating results.

### 12.1 Errors

Errors use `application/problem+json` and RFC 9457 fields, plus `code` and `dgp`. [S7]

| Code | HTTP | Recovery |
|---|---:|---|
| `UNAUTHENTICATED` | 401 | Obtain valid credentials. |
| `FORBIDDEN` | 403 | Do not retry with fabricated role claims. |
| `HUMAN_APPROVAL_REQUIRED` | 403 | Human reviews and submits a current decision. |
| `NOT_FOUND` | 404 | Refresh discovery or reconcile retention. |
| `CAPABILITY_REQUIRED` | 406 | Negotiate supported features or use another client. |
| `STALE_FRAME` | 409 | Fetch a new frame and reassess. |
| `FRAME_EXPIRED` | 409 | Fetch a new frame and reassess. |
| `IDEMPOTENCY_KEY_REUSED` | 409 | Fix incorrect key reuse; never substitute a key to force the old action. |
| `ASSESSMENT_ID_REUSED` | 409 | Preserve immutability; create a genuinely new assessment. |
| `SPECULATIVE_ONLY` | 409 | Reassess against a live frame. |
| `ABSTAINED` | 409 | Gather evidence, choose a permitted service, or stop. |
| `BUDGET_EXHAUSTED` | 409 | Stop or obtain an authorized policy change. |
| `PAYLOAD_TOO_LARGE` | 413 | Use smaller authorized evidence or a supported blob mechanism. |
| `UNSUPPORTED_MEDIA_TYPE` | 415 | Use the advertised representation. |
| `INVALID_MESSAGE`, `INVALID_INPUT`, `INVALID_CHOICE` | 422 | Correct the contract violation; do not coerce silently. |
| `UNSUPPORTED_MODALITY` | 422 | Use a capable assessor or an explicitly approved transformation. |

Transport/provider failures are not automatically domain rejections. Clients MUST reconcile uncertain commit outcomes using the same key. ThreadDesk keeps a local client trace with commit intent before sending the request.

## 13. Optional MCP mapping

DGP can be transported through ordinary MCP tools instead of direct HTTP. MCP already supplies tool schemas and structured results; DGP supplies the decision semantics. [S8]

Suggested **application tool names**, not additions to the MCP standard, are:

| Tool | DGP operation |
|---|---|
| `dgp_discover` | Read manifest. |
| `dgp_surfaces_list` | List surfaces. |
| `dgp_frame_read` | Obtain a current frame or fetch an immutable one. |
| `dgp_graph_read` | Inspect a template. |
| `dgp_assessment_record` | Register an assessment. |
| `dgp_commit` | Commit, carrying a logical idempotency key in tool arguments. |
| `dgp_receipt_read` | Reconcile the outcome. |

The wrapper MUST preserve authenticated caller identity, frame binding, idempotency, and authorization. It MUST NOT turn a tool annotation such as “read-only” into a security guarantee. A real wrapper must implement the selected MCP version's lifecycle and transport requirements, not merely name an HTTP endpoint `/mcp`.

An application SHOULD expose current choices inside frame data rather than dynamically rewriting the entire MCP tool catalogue for every step. The shipped reference app implements HTTP only; this section is a mapping, **not a claim that an MCP server is included**.

## 14. Human interface profile

A minimal interface MAY render surface summaries, evidence, choice labels, text inputs, and receipts. It MAY add styling, layout, filtering, and accessible controls. It MUST NOT change the semantic IDs, required constraints, or authorization requirements.

Clients SHOULD distinguish model recommendation, stored draft, required approval, commit acceptance, and observed outcome visibly. A recommendation should not look like an operation already executed.

Untrusted text MUST be rendered safely, without executable HTML by default. The reference UI uses text nodes rather than injecting model/user content into HTML. It keeps its bearer token only in page memory, rejects cross-origin access at the server, and exposes the raw immutable frame for inspection.

A UI rendering a DGP decision MUST preserve its guarded commit semantics. A native UI MAY instead invoke domain services directly, without producing DGP assessments, provided the shared authorization, invariants, accounting, and revision requirements in §1.4 hold. ThreadDesk deliberately uses the same DGP endpoints for its UI and agent; this is an example, not a protocol-wide architecture requirement. Hiding a button is never the sole enforcement of a restriction.

## 15. Security and operational requirements

**Prompt injection.** Logs, comments, documents, images, and model-generated analyses can contain instructions hostile to the intended task. They MUST remain data. Model-level instruction separation is useful but insufficient; deterministic authorization and scope checks remain mandatory.

**Scope and tenancy.** Surface IDs and artifact IDs are not authorization. Every read and write must enforce tenant/resource access. ThreadDesk is a single-tenant loopback demo with two roles; it is not a multi-tenant identity system.

**Secrets and egress.** Credentials MUST NOT enter model evidence or client-visible policy descriptions. Services should receive the minimum necessary evidence, under an egress policy. External origins and models must be chosen by trusted runtime configuration, not by untrusted evidence.

**Schema and content handling.** Reject duplicate JSON keys, malformed JSON, non-finite numbers, unexpected fields, oversized payloads, and dangerous schema-reference resolution. Generated text that exceeds a limit should be rejected or explicitly revised, not silently truncated into a potentially different statement.

**Immutability and retention.** Store frame/assessment/receipt history durably where audit/replay matters. Revisions are concurrency markers; content hashes identify bytes; neither is a cryptographic proof of truthful content. Retention policies, access logs, redaction handling, and backups remain deployment responsibilities.

**Cross-interface consistency.** A native UI, API, MCP tool, CLI command, or GraphQL resolver that changes relevant domain state must participate in the same revision/invariant boundary. A transport switch must not evade an exhausted budget, human approval requirement, or an uncertain-operation reconciliation. Adapter-specific tokens must not be embedded in frames.

**Recovery.** A receipt can only attest to what the executor actually observed. Unknown downstream outcomes require reconciliation. A database rollback cannot unsend a message, reverse provider disclosure, or cancel physical actuation.

**Production gap.** A production implementation requires hardened serving, identity/authorization, tenancy, distributed worker coordination where needed, persistence monitoring, bounded retention, inference budgets, and domain-specific external executors. The reference app is designed to demonstrate the boundary, not to claim those integrations are complete.

## 16. Application examples

### Ordinary application: Farm Energy Calculator

The lead domain example is a location-first wind/PV/battery calculator. It exposes a native map/form UI, ordinary domain services, and a partial DGP surface. Location is initially supplied by address or coordinates; a map click is another source of the same coordinate input. Once the application resolves location and produces an estimate using declared equipment assumptions, the surface exposes valid turbine, demand/PV, and stepped-battery inputs.

A study fixes consumption, existing PV, tariff, baseline, simulation basis, and the authorized search area. Location, turbine configuration, and discrete battery configuration are the search variables. The goal is to maximize a defined savings metric subject to at least 0.50 modeled self-sufficiency. The numeric engine validates constraints and ranks comparable results; Jev manages qualitative judgments, information gathering, search strategy, and stopping. An optional LLM generates explanations or other requested text.

Parallel evaluation creates independent immutable scenarios; it does not repeatedly edit the person's selected calculator. The budgeted-evaluations profile limits admission and work across all interfaces. A separate adoption action selects a result, with freshness checks against any intervening human edits. Automatic battery sizing is conditional on each candidate's location/turbine and fixed study basis; a manual override remains explicit.

`profiles/farm-energy/PROFILE.md` contains the full application specification, numerical definitions, fixed/search inputs, and examples. No energy simulator, farm map, tariff provider, geocoder, or production-calculator integration is included in this package.

### Runnable reference: ThreadDesk

ThreadDesk models two independent coding threads. It stores synthetic CI state and exposes the same application over DGP and a thin browser UI.

### 16.1 Workflow A: transient failure

```text
blocked
  → Jev chooses retry
  → guarded simulated retry → ready
  → Jev chooses draft_update
  → needs_draft input node
  → LLM generates text; normal commit stores it
  → new frame / Jev judges publication suitability
  → human-review barrier
  → authenticated human can publish to LOCAL bulletin
```

No real CI process is launched. The synthetic retry succeeds deterministically. Publication appends only to the demo database.

### 16.2 Workflow B: ambiguous failure

```text
blocked
  → Jev chooses request_reasoning
  → needs_analysis input node
  → LLM returns a diagnostic summary
  → normal commit stores derived evidence
  → fresh frame / Jev judges again
  → investigate or pause; autonomous loop becomes quiescent
```

### 16.3 Additional interactions

A user can add arbitrary free-text notes in any state. This changes the thread revision, deliberately invalidating an earlier conflicting action. A user can attach image evidence, causing a text-only resolver to stop rather than pretend to have consumed it.

Two threads can be assessed concurrently. Updating thread 73 does not invalidate a frame for thread 42, whereas a note or policy change affecting thread 42 does. Multiple identical successful commit requests return the same receipt across server restarts while the database is retained.

### 16.4 Jev and LLM adapters

The Jev adapter calls TypeSafe's documented `POST /v1/systemone` endpoint and maps the returned typed answer into an assessment. The version is configurable and defaults to the documented version available when this draft was prepared, `jev-1.13.0`. The actual returned model ID is recorded. Live operation needs a valid TypeSafe credential. [S4]

The optional OpenAI adapter returns text from a Responses API result. It is configured separately, has no application tools, and never publishes. No live provider calls were made while producing this package; both adapters were tested with controlled HTTP fixtures. [S9]

The no-key mode uses explicitly named deterministic/canned mocks. It demonstrates protocol behavior, not Jev quality, model reasoning quality, latency, or cost.

## 17. Conformance and evolution

The reference suite tests record schemas, free text, optional images, answer validity, immutability, expiry, policy changes, same-scope conflicts, independent scopes, idempotent replay/restart, principal separation, human-only publication, and mock HTTP controller flows.

Passing the suite does not prove all production security properties, mathematical model correctness, or conformance of an external effect executor. The test report and implementation matrix distinguish exercised behavior from unimplemented extensions.

This release finalizes the discussed 0.1 contracts while retaining experimental status. The core wire schema remains unchanged from the earlier package; added behaviors are opt-in profiles. Existing consumers can continue using core records. The profile schemas and checks do not constitute a production scheduler or an implementation of the farm calculator. Next implementation work should validate these contracts against an independent application and client, rather than assume specification alone proves interoperability. See `docs/RELEASE_NOTES.md` and `docs/CONFORMANCE.md`.

The stable conceptual boundary is:

> **Rich evidence and declared inputs enter. Typed assessments and proposed values return. The application decides whether and how their effects may be committed.**


## 18. Interface and capability catalogue profile

### 18.1 Discovery record

With `interface-catalogue@0.1`, the core manifest includes `extensions["dgp.discovery"]` containing an `application_id` and a `catalogue_href`. The manifest advertises the feature. The referenced `CapabilityCatalogue` identifies a versioned, authorization-filtered set of interfaces and capabilities; its retrieval MUST NOT launch domain computation.

The HTTP profile uses the advertised `catalogue_href`, conventionally `GET /dgp/catalogue`. Optional profile locations are advertised under the same `dgp.discovery` extension: `prepared_operations_href`, `prepared_execute_href`, `jobs_href`, `events_href`, and `handoffs_href`. Only supported features/links are advertised; a link alone is never a capability grant.

A catalogue declares its coverage as `partial` or `complete_declared_scope`, and describes the covered scope. “Complete” never means an exhaustive description of a hidden application, an unauthorized account, or the future. An interface entry has `interface_id`, `kind`, `description`, `descriptor_uri`, and `auth_ref`. Kinds include `ui`, `http_api`, `mcp`, `cli`, `dgp`, and `graphql`. References are locators for trusted runtime configuration or documentation, not credentials.

A capability entry has a stable `capability_id`, a description, associated interface IDs, and `dgp_support` of `native`, `handoff`, or `not_exposed`. `native` means represented directly by a DGP surface; it does not mean an operating-system native app. Optional `canonical_operation_id` identifies the underlying domain action across interfaces. Current authorization and live availability remain distinct from catalogue membership.

For the calculator, configuration and evaluation may be direct DGP capabilities; load-profile upload may be a handoff to an authorized API; billing may be explicitly outside DGP. No client is required to implement all advertised interfaces.

### 18.2 Semantics and boundaries

Schema-level discovery describes types and operations in general. A current frame describes offered decisions and valid runtime domains. Equipment choices normally remain runtime data rather than newly generated schema enums. No schema-valid request is automatically authorized or currently executable.

Interface addresses MUST come from authenticated application discovery or trusted configuration. A runtime MUST NOT execute CLI strings, browse arbitrary URLs, or forward credentials just because an interface descriptor exists. CLI invocation, when allowed, uses an installed adapter with fixed executable and validated argument construction, not interpolation into a model-generated shell command.

A runtime SHOULD select the simplest suitable interface for a task: a UI for visual interaction, an API for bulk data, a CLI for established local tooling, MCP for available tool integration, and DGP for state-dependent judgment/input contracts. This is application guidance, not a mandatory ranking of interfaces. Independent native work is permitted; returning to DGP requires a current frame after relevant changes.

The introspection idea is inspired by GraphQL, while domain authorization remains centralized rather than spread across presentation resolvers. [S12, S15]

## 19. Frame projections and evidence hydration profile

### 19.1 Two independent axes

Graph disclosure (`next`, `horizon`, `full`) describes which current/template decisions can be inspected. A **projection** selects data detail within a fixed frame. A full template can be viewed with minimal descriptions; a next decision can carry detailed evidence. Projection MUST NOT alter the frame's canonical identity, current answer space, expiry, read set, or policy.

`frame-projections@0.1` defines a separate `FrameProjection` record, not a partially valid core `Frame`. It contains:

| Field | Meaning |
|---|---|
| `projection_id`, `view_id`, `view_version` | Immutable projection and named view contract. |
| `frame_id`, `canonical_frame_href` | Exact source frame and how an authorized client obtains its canonical record. |
| `surface_id`, `graph_id`, `graph_version`, `policy_ref` | Source identities. |
| `created_at`, `expires_at`, `read_set` | Preserved canonical concurrency/expiry envelope. |
| `purpose` | `browse` or `assess`. |
| `decision_scope` | Explicit decision IDs covered by the projection. |
| `decisions`, `observations` | Materialized contracts/evidence; these are exact records, not rewritten summaries. |
| `evidence_manifest` | Evidence identity, per-decision requirement, and inclusion status. |
| `omitted_fields` | Explicit JSON Pointer paths omitted from canonical data. |
| `data` | Additional view data; not implicitly evidence supplied to an assessor. |
| `required_features` | Features needed to use the projection. |

HTTP implementations MAY expose `GET /dgp/frames/{frame_id}/views/{view_id}?version={view_version}` for views with no additional variables. More complex variables use the prepared-operation request in §20. The publisher advertises view IDs, versions, purpose, variables schemas, and required features through its prepared-operation catalogue or equivalent authenticated interface metadata.

Every evidence-manifest entry identifies `evidence_id`, `required_for`, and `status`: `included`, `reference`, `omitted`, `redacted`, or `unavailable`. A reference is a promise of discoverability, not proof of hydration. `browse` projections MAY omit answer contracts and required evidence. `assess` projections MUST include full contracts for all decisions in `decision_scope` and make required evidence either present or explicitly retrievable. Before actual assessment the runtime MUST hydrate all required evidence and validate modalities, or abstain/escalate. An unread blob URL does not count as consumed evidence.

A server SHOULD provide compact prepared views rather than require a decision model to generate an arbitrary query. Typical views are `farm.search_overview.v1`, `farm.candidate_details.v1`, and `farm.production_comparison.v1`. Fragments and selection sets are useful GraphQL mechanisms, not a new DGP query language. [S12, S13]

### 19.2 Assessment basis

An assessment using this profile lists it in `required_features` and carries `extensions["dgp.assessment_input"]` with an `AssessmentInputManifest`: source frame, projection IDs, assessed decision ID, actually consumed evidence IDs, explicitly omitted optional evidence IDs, and contract-completeness assertion. These are provenance claims, not cryptographic proof that a model perceived the input.

The runtime MUST check consumed evidence against the exact contract's requirements. A client MUST NOT combine an old decision contract with new live evidence under the old `frame_id`. New or transformed evidence requires publisher acceptance and a new frame, unless an explicitly equivalent immutable artifact was already referenced in the old frame.

`data` aggregates may inform browsing, but when used to make a live judgment they MUST be identified as observations in the assessed frame or incorporated into a new frame. Otherwise the audit would falsely claim the original frame was the complete basis.

Clients MUST distinguish omitted data from `null`, an empty list, zero, false, redaction, and a retrieval error. A projected recommendation with missing required input MUST NOT be treated as commit-ready. The application always checks the canonical frame at commit, regardless of what the client requested.

### 19.3 Pagination and caching

Paginated scenario/evidence views MUST bind cursor and membership/order to an immutable frame or comparison snapshot. Fetching page two from a changed live set without disclosing the change is prohibited. Dynamic feeds use §22 instead.

Cache keys MUST include application/tenant visibility, frame identity, view version, normalized variables, and relevant access policy. HTTP conditional retrieval MAY be used correctly for that representation. Private evidence MUST NOT leak through a shared public cache. A server can refuse costly views or redact data while explicitly reporting that a requested assessment basis is incomplete.

## 20. Prepared operations profile

`prepared-operations@0.1` publishes a `PreparedOperationCatalogue`. Each entry has immutable `operation_id` and `operation_version`, `kind` (`query`, `assessment`, `commit`), a description, JSON Schema `variables_schema`, `result_definition`, required features, and a declared maximum retrieval-cost class. IDs select trusted installed handlers or reviewed query documents; they are not arbitrary executable code.

The HTTP binding uses `GET /dgp/prepared-operations` for discovery and `POST /dgp/prepared-operations/execute` for requests, or the advertised equivalents. Errors use core Problem records; `OPERATION_NOT_FOUND` (404) and `OPERATION_VERSION_UNSUPPORTED` (409) distinguish missing and unsupported contracts.

A `PreparedOperationRequest` contains the exact ID/version and schema-valid variables. Unknown versions MUST fail rather than fall through to a similarly named operation. A runtime MAY deterministically populate variables from user input, frame IDs, and selected object IDs. Jev need only select the useful view/operation or assess the exposed question; it need not generate GraphQL, HTTP paths, or shell syntax.

A `query` operation MUST NOT submit new simulations or change business state. Normal access logs, metering of read cost, caching, and allocation of an immutable observation are allowed. An expensive upstream computation is an explicit offered transition, not a hidden field resolver. A read-cost quote is not a simulation-budget reservation.

An `assessment` operation is only an alternate entry point to core assessment recording. A `commit` operation MUST accept the core commit binding and a logical idempotency key and follow §7. It MUST NOT become an unrestricted alternate `evaluate` endpoint merely because the request template was approved. A trusted operation catalogue grants no authorization by itself.

Operation hashes used for transport caching are not equivalent to an allowlist. Implementations claiming trusted documents MUST reject unknown/unapproved document identities, not register arbitrary submitted queries on a cache miss. [S14]

## 21. Budgeted asynchronous evaluations profile

### 21.1 Immutable study basis and independent work

`budgeted-evaluations@0.1` adds a server-owned job protocol. It does not provide a numerical optimizer, graph scheduler, or physical safety controller. Inputs to each accepted scenario MUST be immutable and versioned, including every relevant model/data/configuration assumption. A fingerprint MUST cover the semantic input identity, not just a display label or rounded capacity.

A workspace's selected design, a study's fixed assumptions, a candidate scenario, and an evaluation job are separate objects. Evaluating a scenario MUST NOT silently adopt it. Updating a human's demand/PV assumptions invalidates adoption/recommendations based on the old study, but need not cancel useful calculations already admitted for that old basis.

### 21.2 Admission and limits

A currently offered input/choice accepts an explicit finite batch of variants, or a bounded optimization operation with an advertised maximum expansion. Its contract references an immutable evaluation policy. The live budget snapshot is advisory: the server rechecks and reserves atomically at admission. Quota counters need not invalidate every unrelated frame, but policy changes or changed study assumptions must be handled correctly.

`EvaluationPolicy` declares policy identity/version, scope (application, tenant, workspace), batch/running/queue limits, and a budget unit and ceiling. Its `consumed`, `reserved`, and `as_of` values describe a point-in-time ledger snapshot. A producer MUST specify whether cache hits consume units. Under the 0.1 flag, a charged cache hit costs exactly one declared unit; variable cache pricing requires a separately declared policy extension. Example values of four running jobs, sixteen variants per request, and 240 full-scenario units are illustrative, not defaults.

Normative accounting rules are:

1. Check ownership, current policy, fixed inputs, variant compatibility, and idempotency before admitting work.
2. Reserve a conservative bounded maximum cost for all new work in the same authoritative transaction as batch admission and receipt creation. `consumed + reserved` MUST remain within the declared budget.
3. Share capacity and accounting across UI, API, CLI, MCP, GraphQL, and DGP calls in the same policy scope. Multiple agents or sessions do not create separate allowances.
4. Charge expanded work, not merely transport requests. A battery optimization that runs six simulations accounts for up to six units under a full-scenario unit policy.
5. An identical idempotent replay returns the original admission/jobs without charging again. Verified cache reuse follows the declared cache-cost policy and scope isolation.
6. A worker MUST NOT exceed its reservation. It must first obtain an atomic authorized increase or stop within the reserved boundary. Actual consumption is settled, unused reservation released, and failures/cancellation charged according to published policy.
7. Uncertain execution/accounting is reconciled; resources MUST NOT be released merely because a client timed out or a worker lease disappeared.

The 0.1 batch mode is **all-or-nothing admission**. If capacity or budget is insufficient, no new job or budget reservation in that batch is accepted. This is not all-or-nothing computation: admitted jobs may subsequently succeed or fail independently. Batch limits count all submitted variants, including cache hits; queue limits count newly admitted work only.

A success receipt attests to admission, not simulation completion. `extensions["dgp.evaluations"]` contains an `EvaluationAdmission` record: batch ID, policy reference, canonical operation ID, and one mapping per submitted scenario to either a job ID or a reusable result reference. The frame/request requires the profile. Opaque references are not authorization.

### 21.3 Job snapshots and transitions

Every read returns an immutable `EvaluationJob` snapshot with `job_id`, monotonic `job_revision`, scenario/study references, source frame, admission receipt, state, timestamps, and cost accounting. Each persisted change increments `job_revision` by one. Polling clients can observe gaps and MUST NOT treat nonadjacent snapshots as a complete transition history. A stable job URL resolves the current snapshot; historical snapshots must not be edited silently. Expiry of the admission frame does not cancel already accepted jobs.

| Current state | Permitted next state |
|---|---|
| `queued` | `running`, `cancelled`, `failed` |
| `running` | `succeeded`, `failed`, `cancel_requested`, `reconciling` |
| `cancel_requested` | `cancelled`, `succeeded`, `failed`, `reconciling` |
| `reconciling` | `running`, `succeeded`, `failed`, `cancelled` |
| `succeeded`, `failed`, `cancelled` | No state change; a retry is a new job linked to the previous one. |

Cancellation is a request, not proof of stopped work, refunded spending, or reversal. A race between cancellation and completion may legitimately end in `succeeded`. A lease/fencing mechanism or equivalent protection MUST prevent obsolete workers from overwriting an accepted newer outcome. Queue/worker implementation details are not standardized.

A successful job MUST supply an immutable result reference and no failure object. A failed job MUST supply an explicit error and no success result. Terminal snapshots MUST have settled accounting with zero remaining reservation; otherwise the job remains `reconciling` until accounting can be settled. Pending/failed/missing metrics are not zero. A successful simulation may be economically or physically infeasible under the study constraint; that is a result classification, not an execution failure. `constraint_status` is `satisfied`, `not_satisfied`, or `unknown` in the farm example.

### 21.4 Results, caches, and stopping

Result identity SHOULD include engine/model/data versions, unit definitions, weather/time basis, demand/PV/tariff references, equipment configuration, dispatch strategy, numerical settings, and seeds where used. Reusing a generation profile for different batteries is encouraged when those inputs are independent; reusing financial results across changed tariffs without recalculation is not.

A comparison MUST report eligible, pending, failed, excluded, and unevaluated counts as applicable. An incomplete search MUST be described as best found within the evaluated domain and budget, not a guaranteed global optimum. Constraints are evaluated by trusted calculation/validation code, not inferred from model confidence.

The controller SHOULD wait for job progress without repeatedly invoking the model on unchanged state. An exhausted budget, no feasible result, cancellation, or a user pause is a valid stopping outcome. DGP does not promise that additional reasoning will improve the physical or financial estimate.

### 21.5 HTTP profile binding and errors

The optional binding adds authenticated reads of `/dgp/jobs/{job_id}`, `/dgp/jobs/{job_id}/revisions/{revision}`, and `/dgp/evaluation-policies/{policy_id}`. Submission remains a core commit of an offered batch input. Cancellation is a separately offered guarded action; a bare job ID is insufficient authority.

Recommended Problem codes are `BUDGET_EXHAUSTED` (409), `QUEUE_CAPACITY_EXCEEDED` (429), `BATCH_TOO_LARGE` (422), `INVALID_VARIANT` (422), and `JOB_NOT_FOUND` (404). A retry hint is advisory, not a reservation. Normal read throttling may use 429 independently of job capacity. Backpressure MUST NOT trigger an automatic transport switch to bypass limits.

## 22. Resumable event profile

`resumable-events@0.1` supplies notifications of changed resources. Event kinds include `frame_available`, `job_updated`, and `budget_updated`. Each event carries `event_id`, `stream_id`, increasing stream-local `sequence`, timestamp, resource reference/revision, and optional correlation ID. It announces what to read; it does not by itself prove a job succeeded or authorize a commit.

An `EventPage` includes stream identity, events, an opaque `next_cursor`, and `has_more`. HTTP uses authenticated `GET /dgp/events?after={cursor}&limit={n}`; a null/absent starting cursor begins from a documented snapshot watermark, not an unspecified historical point. A server MUST describe event retention and snapshot/replay behavior. The first bootstrap response includes or identifies the matching state snapshot/watermark so clients can reconcile without losing intervening events.

Delivery is at least once within the advertised retained stream. Clients deduplicate event IDs and may see repeated pages after reconnect. Ordering is per stream, not a global transaction order across every resource. Cursors MUST be bound to tenant, visibility, and filter scope; changing a filter or principal requires revalidation/rebootstrap.

An expired cursor returns `CURSOR_EXPIRED` (410) with instructions to obtain a current authorized snapshot and restart from its watermark. A server MUST NOT silently skip a gap and claim continuous delivery. Streaming transports, including server-sent events or GraphQL subscriptions, preserve these semantics; subscription transport alone does not add durable replay.

Within one immutable comparison snapshot, paginated collections use stable cursors (§19.3), not event cursors. Existing result reads remain available without subscriptions; clients MAY poll using server guidance. Jobs and events are distinct profiles so small deployments can implement durable jobs with polling only.

MCP Tasks in the dated 2025-11-25 specification provide related asynchronous machinery, but that version labels Tasks experimental. A wrapper MUST explicitly negotiate and implement its chosen MCP version; this document does not assume identical task or stream behavior across MCP versions. [S16]

## 23. Authorized cross-interface handoff profile

`interface-handoff@0.1` is optional; applications may simply document alternate interfaces. When a live DGP transition deliberately pauses for work elsewhere, its receipt MAY reference a `Handoff` record with origin frame/decision, capability and canonical operation IDs, target interface ID, scoped arguments, expected result schema, application-issued correlation ID, expiry, and read-versus-write declaration.

The handoff is an authorized intention/continuation record, not a bearer credential, executable program, or assertion of completion. The host must have an independently configured and appropriately authorized adapter for the target interface. It MUST validate destination and arguments, bind scope, and retain the same underlying principal/approved delegation. Credential negotiation, OAuth, UI login, and operating-system execution policies remain external to DGP.

A target-side write MUST enforce current domain policy and shared budget. If it represents the same logical action already attempted via another binding, it MUST resolve through a shared canonical operation/idempotency namespace or be explicitly reconciled before retry. A client MUST NOT repeat an uncertain operation through CLI or API simply because DGP timed out.

Returned artifacts MUST be validated against the expected schema and bound to the operation/scope. A client-written string saying “completed” is not trusted execution evidence. The publisher may inspect a canonical domain artifact, validate a provider receipt, or record the returned claim as untrusted/derived evidence. On reentry it issues a fresh frame with authoritative current state; the old handoff is not permission to replay an old DGP commit.

For the calculator, a farm load CSV could be uploaded through a native API, validated and versioned by the app, then referenced in a new DGP study. The expensive candidate evaluations could remain DGP-native. A final chart/report export might use a native UI/CLI instead. A conforming app need not turn upload, chart styling, account administration, and every export into DGP nodes.

A `Handoff` state is `offered`, `completed`, `expired`, or `cancelled`. State changes create new revisions. `completed` means the publisher accepted a result reference, not that it certified a user's factual claims. Authorization cannot be inferred from a model-reported state.

## 24. Optional GraphQL binding

### 24.1 Role and representation

GraphQL is an optional carrier and application read interface, not DGP's graph execution engine. The binding is inspired by schema discovery, selection sets, fragments, typed inputs, explicit mutations, and partial-error responses. [S12, S13, S17] `bindings/graphql/schema.graphql` defines an illustrative application schema with canonical DGP record fields and typed convenience fields. `operations.graphql` contains named example documents. The package validates the JSON profile contracts and supplies an optional GraphQL validator. The external GraphQL parser dependency was unavailable during packaging, so neither GraphQL document validation nor resolver execution is claimed. It does not ship a running GraphQL server.

GraphQL fields representing canonical records expose them through a `record: JSON!` scalar. The JSON value MUST validate against the indicated DGP record schema. Typed convenience fields MUST represent the corresponding canonical values without loss. Bindings MUST NOT round, truncate, or coerce large integers silently; use a lossless custom scalar or reject values outside an explicitly documented supported range. Partial selections of convenience fields are views, not complete protocol records. A controller obtains either the full record or a conforming §19 projection before assessment. Implementations MAY provide richer typed mappings while preserving these semantics.

Queries read manifests, catalogues, frames/views, jobs, and events. `recordAssessment` records a core assessment. `commit` accepts frame/decision/assessment IDs plus an explicit `idempotencyKey`; it dispatches through §7. A GraphQL transport failure or partial response is not proof that a mutation did not execute. Reconcile using the same key and canonical receipt history.

### 24.2 Native operations alongside DGP

The same GraphQL schema MAY also contain ordinary native application operations. The example includes a location update taking an exclusive address/coordinate input, expected workspace revision, and idempotency key. It is a native interface example, not an alternative DGP commit. Its resolver must invoke the same authoritative domain service so a native edit invalidates relevant old DGP frames.

GraphQL's September 2025 specification defines OneOf input objects. Implementations without that capability must enforce the equivalent exclusive-input rule at their binding boundary rather than silently accepting ambiguous input. Coordinate ranges and runtime equipment compatibility still require domain validation. [S13]

### 24.3 Parallelism, costs, and incomplete data

GraphQL's serial execution of top-level mutation fields within one operation is not a distributed transaction or global lock. Independent requests still contend under application concurrency rules. Query field parallelism does not grant permission for additional simulation jobs. One guarded batch-admission mutation can create independently scheduled jobs under §21. [S13]

An implementation MUST enforce appropriate depth, breadth, alias, pagination, batch, payload, retrieval-cost, and execution limits. Cheap projection does not imply cheap computation. Expensive simulations MUST not hide behind a query resolver. Resolvers SHOULD batch/cache repeated authorized dependency reads rather than refetching wind/resource data once for every candidate. These controls follow GraphQL demand-control and performance guidance. [S14, S18]

Partial results and errors MUST be preserved. A missing scalar cannot be substituted with zero, false, an empty feasible set, or a successful result. Result state should be explicit; the example schema distinguishes succeeded, pending, failed, cancelled, and reconciling evaluation outcomes. DGP errors can appear as canonical Problem records or binding errors with a preserved DGP code. [S17]

### 24.4 Evolution and compatibility

Catalogue IDs, view IDs/versions, schema/input definitions, metric definitions, and prepared operation versions are stable contracts. Adding optional fields does not license changing an existing metric's meaning. A change from gross bill savings to net annualized savings requires a new semantic metric/version, not merely a renamed label. GraphQL deprecation metadata may advertise replacements without silently changing existing behavior. [S13]

Core unknown mandatory features fail closed. Profile records use a separate schema and explicit `record_type`; they must never be passed off as an old core record. Old optional metadata may be ignored only where no required feature depends on it. A deployment MUST advertise supported profiles and bindings accurately: publishing an SDL file does not mean a GraphQL server is available, and defining tool names does not mean MCP transport is implemented.

## 25. Final release scope and implementation guidance

The finalized 0.1 scope is **rich evidence + typed judgments/inputs + guarded application effects**, optionally enriched with discoverability, projections, bounded jobs, and alternate interfaces. It is not a requirement to rewrite every app, route every action through Jev, or replace existing APIs.

A practical implementation sequence is: place domain validation/revisions/budget accounting behind shared services; expose one useful partial DGP surface; retain the native UI/API; validate core state/commit behavior; then add only the optional profiles justified by actual payload size, compute costs, or integration needs. Deterministic code should continue doing numerical optimization, parameter binding, scheduling, and policy enforcement where appropriate.

This package's implementation matrix separates normative specification, validated structural examples, executable contract helpers, and actual server behavior. The runnable ThreadDesk app demonstrates core semantics only. The Farm Energy profile is a worked integration design, not a tested energy model or an implemented production optimization service. No claims are made about Jev's live accuracy, performance, or paid-provider availability.

## References

References provide background and provider/API grounding. They do not imply that the organizations endorse DGP. Accessed 19 September 2026.

[S1] TypeSafe AI, **State** — accepted state shapes and current input-modality limits. <https://docs.typesafe.ai/concepts/state>

[S2] TypeSafe AI, **Primitives (Questions)** — Choice, Score, Noul, and independent/dependent evaluation. <https://docs.typesafe.ai/primitives>

[S3] TypeSafe AI, **Confidence** — provider-defined confidence and probability semantics. <https://docs.typesafe.ai/confidence>

[S4] TypeSafe AI, **API reference** and **Models** — HTTP evaluation endpoint, answer shapes, versioning. <https://docs.typesafe.ai/api> and <https://docs.typesafe.ai/models>

[S5] JSON Schema, **Draft 2020-12** — schema dialect used for record/input contracts. <https://json-schema.org/draft/2020-12>

[S6] IETF, **RFC 9110: HTTP Semantics**, June 2022. <https://www.rfc-editor.org/rfc/rfc9110.html>

[S7] IETF, **RFC 9457: Problem Details for HTTP APIs**, July 2023. <https://www.rfc-editor.org/rfc/rfc9457.html>

[S8] Model Context Protocol, **Tools**, specification version 2026-07-28. <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>

[S9] OpenAI, **Text generation**, Responses API examples and output handling. <https://developers.openai.com/api/docs/guides/text>

[S10] W3C, **Web of Things Thing Description 1.1** — interaction-affordance precedent, not DGP's wire format. <https://www.w3.org/TR/wot-thing-description/>

[S11] W3C, **MBUI — Abstract User Interface Models**, Working Group Note, 2014 — separation of interaction semantics from concrete presentation. <https://www.w3.org/TR/abstract-ui/>

[S12] GraphQL Foundation, **Introspection** — schema/type discovery. <https://graphql.org/learn/introspection/>

[S13] GraphQL Specification, **September 2025 Edition** — selection sets, fragments, OneOf inputs, mutations, and schema evolution. This is a pinned edition, not a claim about the latest working draft. <https://spec.graphql.org/September2025/>

[S14] GraphQL Foundation, **Security** — trusted documents and demand-control guidance. <https://graphql.org/learn/security/>

[S15] GraphQL Foundation, **Authorization** — domain/business-layer authorization rather than independent resolver rules. <https://graphql.org/learn/authorization/>

[S16] Model Context Protocol, **Tasks**, version 2025-11-25 — pinned asynchronous-task precedent; experimental in that edition. <https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/tasks>

[S17] GraphQL Foundation, **Response** — partial data, errors, and extensions. <https://graphql.org/learn/response/>

[S18] GraphQL Foundation, **Performance** — backend fetch batching and caching. <https://graphql.org/learn/performance/>
