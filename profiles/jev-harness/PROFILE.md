# Jev harness profiles for DGP 0.1

Status: optional compatible profile proposal, revision 0.1. Core DGP remains 0.1.
Schemas, examples and selected offline contract tests are supplied. Neither profile
is implemented by ThreadDesk or advertised by its manifest. These profiles are
assessor-neutral despite their motivating Jev use case.

## Assessment batching (`assessment-batching@0.1`)

Groups independent assessments of **currently offered decisions in one immutable
canonical frame**. It differs from budgeted-evaluations, where one input decision
submits multiple computation variants. It adds no batch commit or executor.

An `AssessmentBatchRequest` contains a stable `batch_id`, exact `frame_id`,
`shared_basis`, and 1–32 ordinary core assessment requests. Each retains its own
assessment ID, offered decision ID, resolver and result. This is assessment
registration, **not a provider inference endpoint**. Results may originate from one
native multi-question call, separate calls, deterministic code or a human.

The shared basis names the publisher-computed frame SHA-256 plus included evidence
IDs and SHA-256 hashes of canonical observation records. The publisher advertises
its hash encoding contract through trusted discovery; ThreadDesk's local `stable()`
encoding is not an interoperable JSON canonicalization claim. Blob metadata hashes
do not prove blob consumption. Required evidence/modalities must be hydrated and
supported before inference. All included records must match the canonical frame;
required evidence for every item must be present. Optional omissions are explicit
through the applicable assessment-input manifest. One item's answer cannot be an
input to another item in the same inference batch.

Authenticate and check visibility, feature negotiation, frame/basis binding,
bounded size and unique assessment/decision IDs before processing items. Then
validate and register each independently using core rules. Invalid items return
per-item Problems; valid items may still be recorded. A response contains exactly
one result per submitted item, in order, including assessment/frame/decision IDs
even on error, and either a recorded assessment or a Problem. Whole-envelope
failures may reject all items before processing. Registration is **not atomic**
across items and applies no domain effects. Accepted assessments still require
individual guarded commits; no atomic multi-commit is implied. Stale assessments
may remain audit records but cannot bypass freshness or permission checks.

Retries reuse the same batch ID and identical content. A stored batch ID is bound
to principal and normalized request content; conflicting reuse fails. Core
assessment IDs provide per-item deduplication. Transport failure may leave a
recorded subset: reconcile the same IDs rather than inventing new ones. Inference
is a separate potentially billable operation. Registration replay does not promise
inference replay, refunds, exactly-once billing or durable budget reservations.

Optional batch-level usage provenance uses unique provider call IDs. A shared call
is represented **once**, not copied into each item as separate spending. Multiple
calls remain distinct; unknown tokens/cost are `null`, not zero. Reported versus
estimated cost use separate fields and estimates declare their basis. The host
ledger remains authoritative and deduplicates across interfaces. Assessment or
usage provenance is a client claim unless independently attested by the host.

### Conditional previews and cached computation

Full/horizon templates are not current decision instances. This profile does not
allow fabricated descendant `decision_id` values. Publisher-issued hypothetical
contracts and their representation are explicitly deferred. Controller-private
conditional exploration may continue without registering imaginary live targets.

Speculative assessments are noncommittable. Promotion requires a fresh live frame
and a new live assessment ID. Cached computation may be reused only after trusted
checks establish exact equivalence of answer/question contract and schema, consumed
evidence, relevant state, policy, model/version/configuration and explicit
assumptions. Preserve provenance; never relabel an old speculative record. New
evidence requires a new round. Assessment parallelism grants no effect parallelism.

## Coding tools (`coding-tools@0.1`)

A deliberately partial capability catalogue with fixed installed handlers:

| Canonical operation | Contract |
| --- | --- |
| `repo.inventory` | Bounded metadata/file listing under an authorized host root. |
| `repo.read` | Bounded path/range read with content hash and explicit omissions. |
| `repo.search` | Bounded literal search, validated filters and match limit. |
| `repo.gitstatus` | Fixed status adapter, no arbitrary Git subcommands/arguments. |
| `patch.prepare` | Isolated reviewable proposal artifact, never application. |
| `patch.apply` | Separate guarded application of an exact reviewed artifact. |
| `tests.run` | Explicit effectful bounded execution in an authorized sandbox. |

IDs select trusted adapters, not shell strings, executable URLs or model-authored
code. Variables follow publisher-authored schemas. Discovery grants no authority.
Executors enforce roots, traversal, symlink confinement, ignored/secret-file rules
and current grants. Lexical path checks alone are insufficient. Pagination binds
to immutable membership/order; truncation and missing data remain explicit.

Native UI/API/CLI/MCP may coexist, sharing principal, guards, revisions and budgets.
Native calls need no fabricated DGP assessments. Read results bind repository,
revision and relevant content hashes: a Git commit alone does not identify dirty
files. Newly retrieved evidence enters a fresh frame unless its exact immutable
artifact was already referenced. Local-read authority is not model-egress authority.

`patch.prepare` returns an immutable artifact hash/reference, repository/base
binding, touched paths, preimage hashes and planned ownership. Writing artifacts
or creating worktrees is an internal mutation; generation also spends money and
may disclose data. `patch.apply` rechecks exact artifact, preimages, scope, ownership,
policy and authorization at application time. Executors handle recovery and
ambiguous outcomes; DGP alone does not guarantee atomic filesystem edits or undo.
Preparation never implies permission to apply, merge, push or publish.

Tests execute repository code and may write files, access networks, spawn processes
or disclose credentials. Their adapter fixes command identity and sandbox policy,
time/resources/output bounds and permitted effects, without inherited model
credentials. Cancellation is not proof all work stopped. Status reads launch no
tests. A build command has the same effectful classification, not read-only status.

Asynchronous executors MAY negotiate budgeted-evaluations jobs with reservations
and reconciliation. Otherwise declare the supported synchronous/native job
interface; this profile does not imply an implemented job server. Admission
receipts mean **accepted/queued**, never “tests passed”. Completion requires a bound
runner result with command/sandbox identity, revision, exit status and bounded logs.
Model confidence and client strings are not execution evidence.

## Adoption and implementation boundary

Start with a core frame/assessment/receipt facade around existing read-only repo
handlers, then optional batch registration. Keep the existing Jev transport,
model-identity validation, host cost ledger, grouped menus and per-call trace.
Patch/test adapters follow only with real isolation and recovery contracts.

The accompanying helpers check selected structural and semantic invariants. They
do not authenticate, persist, execute, fetch blobs, infer, reserve budgets or
provide a job/MCP server. ThreadDesk remains simulated and unchanged.
