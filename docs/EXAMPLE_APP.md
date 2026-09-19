# ThreadDesk: one app, two interfaces

ThreadDesk is a small coding-thread board. It publishes decision surfaces in addition to a conventional human interface. The UI is not scraped; the agent receives the underlying semantic contract directly.

## Layering

```text
SQLite application state + policy
               │
       DGP publisher/executor
          /              \
     Browser UI      Controller runtime
                          │
                   Jev decision adapter
                          │
                  optional text service
```

`engine.py` owns the application state and guards. `server.py` exposes the HTTP binding. `agent.py` consumes only that interface; it cannot edit the database directly. `providers.py` isolates model APIs and mock fixtures. `web/app.js` is a thin human client of those same protocol operations.

The local bulletin is a domain read view. Its read endpoint is an application convenience, not a new protocol execution path.

## State and decisions

Each thread has its own revision, status, log, retry count, service-request counters, notes, derived analysis, optional draft, and image evidence. A shared policy revision is also included in every frame's read set.

| State | Primary node | Possible next state |
|---|---|---|
| `blocked` | `recovery` choice | `ready`, `needs_analysis`, `investigating`, or `paused`. |
| `needs_analysis` | `analysis_result` text input | `blocked`, now with derived analysis. |
| `ready` | `update` choice | `needs_draft` or `done`. |
| `needs_draft` | `draft_result` text input | `review`. |
| `review` | `review` choice | `published`, `held`, or `done`. |
| Terminal/held states | No automatic node | Optional human notes and images remain available. |

Every state also offers `note` and `attach_image` as `on_request` inputs. An autonomous controller does not repeatedly fill optional forms simply because they are visible.

## Walkthrough A: retry and write an update

Read the current frame for thread 42. Its first decision asks which immediate recovery route fits a timeout before assertions. The runtime sends the relevant evidence and described options to the decision adapter.

The mock chooses `retry`; a real Jev result can differ. The runtime records an assessment. Nothing has retried yet. It then submits a commit using an idempotency key. The backend checks the frame/read set and selected option, and changes the fixture to `ready`. The receipt explicitly says no tests were run.

A fresh frame asks whether to prepare a status update. Choosing `draft_update` opens a declared text-input node. The runtime invokes the configured text producer. It submits the draft as an input assessment, then commits it to the app. This only stores a draft.

The following frame asks whether the exact draft is suitable for publication. The mock recommends `publish`, but the runtime stops because that option requires a human. Even a deliberately malicious agent submitting the commit directly would receive `HUMAN_APPROVAL_REQUIRED` from the backend.

A human refreshes the UI, reads the draft, and commits their own publication choice. The app appends to its local bulletin. It does not send a message to any third party.

## Walkthrough B: ask for analysis, then judge again

Thread 73 starts with an ambiguous runner failure. The mock selects `request_reasoning`. The application opens `analysis_result`, and the runtime obtains text from its configured service.

The text is stored with `trust = derived`, not promoted to an observed fact. A new recovery frame includes that text alongside the original log. The decision adapter evaluates again. The mock selects `investigate`, which ends autonomous recovery.

This is a real two-stage protocol flow even in fixture mode: service request, text fulfillment, new evidence, new bounded judgment. The mocks demonstrate the mechanics, not the quality of the reasoning.

## Walkthrough C: text is genuinely open-ended

Use **Add a free-text note** in either card. The request is an input answer:

```json
{"value":{"text":"Before another retry, check whether the DB migration finished."}}
```

The text need not be one of a known set of labels. Unicode is accepted. Content is rendered as text rather than HTML. Schema constraints reject empty/oversized values and unexpected extra fields.

The note changes that thread's revision. A previously assessed recovery action based on the older frame will fail with `STALE_FRAME`. A decision for the other thread is unaffected.

## Walkthrough D: image evidence is not silently converted

Attach a small PNG/JPEG/WebP image in the UI. The backend stores the bytes and returns a SHA-256-addressed blob in subsequent frames. The UI verifies its size and hash before displaying it.

The image is marked required. The included Jev adapter is text-only, so its next attempt stops with `UNSUPPORTED_MODALITY`. The record still contains the original image. An image-native decision adapter could consume it directly; an approved captioning service would instead need to create explicitly derived evidence and negotiate whether that projection is sufficient.

This package does not falsely claim that current Jev sees pixels, and does not automatically route every non-text input through an LLM.

## Static, dynamic, parallel, and speculative behavior

**Dynamic:** `disclosure=next` returns the actual current node instances.

**Static:** `GET /dgp/graphs/thread-recovery` returns the declared template. A full frame includes the complete declared template; that does not enable future transitions before their guards are satisfied.

**Hybrid:** `disclosure=horizon&horizon=2` supplies a bounded preview with the same current frame.

**Parallel:** `--parallel 2` allows different surfaces to be assessed concurrently. SQLite serializes local commits, while resource-specific read sets avoid invalidating unrelated decisions. Two conflicting commits against the same original revision cannot both succeed.

**Speculative:** `--speculative` records a judgment and stops. The server rejects direct commitment of that record. There is no simulated filesystem, speculative external executor, or automatic promotion implemented.

## Failure handling to try

Open the app in two tabs using the human token. In one, add a note; in the other, submit an action from the old frame. The old action is rejected. Refresh to obtain a new frame.

Use the agent token in the UI, then attempt publication of a ready draft. The server rejects it regardless of the visible button or the payload's human resolver label.

The test suite also deliberately replays successful commits, changes policy revisions, restarts a persisted database, races conflicting submissions, and injects malformed message/input fields.

## Adapting an existing app

Identify a stable domain scope and the meaningful judgments in its current state. Bind each offered choice to existing trusted application operations rather than an arbitrary model-generated command. Publish the relevant evidence and input schema; make those same operations available through the DGP commit boundary.

Keep the first adapter narrow. For a real coding supervisor, one thread/repository scope and a simulated recovery operation are enough to verify client interoperability before enabling actual writes. The benefit should come from removing bespoke UI interpretation, not from replacing proven domain safeguards with model prompts.
