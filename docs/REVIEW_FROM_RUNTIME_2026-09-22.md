# DGP 0.1 reviewed against a runtime built on it — 22 September 2026

Three days of building and using `dgp-runtime` (a decision-first runtime for software work: Jev decides, deterministic
code acts, generation small and gated; used on a real Go/Swift project through an orchestration UI and on itself)
tested the protocol's ideas against practice. This note records what held, what the runtime had to add that the
protocol does not name, and what that means for the next revision. Numbers are the runtime's own measurements with
their cohort sizes; none is a benchmark claim about Jev.

## 1. What held

- **The boundary.** "Rich evidence and declared inputs enter; typed assessments and proposed values return; the
  application decides whether and how effects are committed" (§25) is exactly the shape every runtime routine took:
  code proposes options with bound arguments → one typed assessment over all of them → code resolves by rule.
  No model ever held a tool handle; effects (branch, apply, commit, record) are typed, guarded and leave receipts.
- **Assessment ≠ effect (§6, §7).** Keeping the decision record apart from the guarded commit is what made review,
  auto-apply and owner gates composable: a candidate can be judged, blocked, repaired and re-judged without touching
  the workspace.
- **Idempotent commit with a preserved body (§7.1–7.2).** The runtime's apply is guarded by base revision, patch digest
  and a recheck on a moved head; a base the workspace never had is refused unless declared foreign and rechecked.
  §7.2's ordering was the template.
- **Bounded escalation (§11.2).** Budgets on decision requests, model calls, container runs and child invocations,
  enforced by code and attenuated for children, held every runaway the runtime would otherwise have had. "Quiescence
  is a successful terminal state" was needed twice (a stop decision after an exhausted ladder).
- **Trust categories (§4) and `derived_from`.** The runtime refined them (below) but never had to contradict them.

## 2. What the runtime needed that the protocol does not name

Each item names the runtime mechanism, the evidence, and the protocol gap.

### 2.1 The unit of assessment is a flattened batch over one state, not one decision

Every runtime decision is one request carrying a JSON state document and up to 64 questions pointing into it
(Jev's limit), answered at a flat ~0.3 s. Measured: flattening was the single most decisive design choice
(24 repository questions: flattened Jev 22/24 at $0.0007 and 3.9 s per question vs an LLM agent loop 23/24 at
$0.0015 and 7.5 s; Jev picking one action per step only 17/24). Prompt decomposition into a needs array: 4.2 requests
per prompt vs 7.9 separate, 25/27 parts right vs 11/27 undecomposed.

`assessment-batching@0.1` covers registration of 1–32 assessments over one frame. Gaps: the cap should be the
assessor's (64 for Jev); the **shared state document** the questions point into should be a first-class basis
(the profile hashes evidence records, which is close, but a runtime's state is a *projection* of evidence with labels
— label quality decided decision quality in every experiment); and a rule that a batch is the *default* unit, with
single-decision assessments the special case.

### 2.2 Ratings, not only the chosen answer

The runtime keeps every option's probability from every request: for confidence shown to the caller, for the
"ask the owner when the top two are close" rule, for silence rules, for later measurement of decisions against
outcomes (escalation: 6 decisions in 4 jobs so far — too few; the record exists so the number can grow). §5.4's
optional distribution is the right field; it should be **required** when the resolver is a decision model that
returns one, and recorded alongside `choice_not_maximal` (the assessor's own flag that the returned choice was not
its argmax — Jev sets it occasionally; the runtime records it every time).

### 2.3 Decisions made by rule, without a request

Roughly a third of the runtime's decisions are made deterministically ("only one action is possible → no request";
"under 5 s and 1 KB of new output → do not judge progress yet"). They are still decisions and are recorded with
`decided_by: rule`. §2 lists "deterministic code" as an assessor; the assessment record should carry
`resolver.kind = "rule"` with the rule's identifier, so that audits and measurements can separate the two.

### 2.4 Provenance as a graph walk with a grade

The runtime extended §4's three trust values to six origins — `observed`, `computed`, `decided`, `ranked`,
`generated`, `stated` — with ranks, and defines a record's **grade** as the weakest origin reachable through
`derived_from`, with `verified_by` lifting a generated node that an observation later confirmed. A one-line summary
(`L o0 d2 v0 u1 s1`) sits on every reply; `w r3.q1` prints the walk. What this caught: a definition of done resting
on generated tests grades as generated until an observation (a real run) qualifies it; a composed report that passed
a contradiction check still graded `stated` for a paragraph no fact supported.

Proposal: an optional `provenance-lineage@0.1` profile: `origin` on evidence and assessment records, `derived_from`
and `verified_by` as record references, a normative grade function (weakest link; verification lifts by one rank
at most), and a summary shape. This composes with §4 rather than replacing it (`observed` and `derived` map
directly; `untrusted` becomes `stated`).

### 2.5 Qualification of generated artifacts as a conformance mechanism

For generated code the runtime never trusts "tests pass". A contract document is authority; a cheap model drafts the
tests against a stub (they must collect and **fail** on the stub); a *different* model implements; code breeds
one-line mutants the tests must kill; a strengthening round targets survivors. Record:
`{status, fails_on_stub, passes_independent, mutants, killed, survivors[{path,line,what}], writer, implementer}`.
Measured: it caught a test file that passed but killed 1/11 mutants (genuinely weak); on Sentinel S1b, 10/12 → 12/12
after one strengthening round for $0.0037; tests that faked the runtime bred wrong implementations three times, so
the brief now forbids fakes of the thing under test.

Proposal: an optional `artifact-qualification@0.1` profile with that record and the two rules that matter:
tests must fail on the stub, and the implementer must not be the test writer.

### 2.6 Review as bounded typed findings, then one repair

Review = deterministic signals + at most six cheap-model findings tied to added lines + one Jev request on whether
each finding is supported, with **closed blocking categories** (shell injection, secret exposure, destructive effect,
contract bypass). Measured: 16/16 planted defects blocked, 1/4 clean patches wrongly blocked (owner override
`reviewed`). A blocking finding is feedback first: one repair rung with the findings as feedback, then one more
review; the second verdict stands. §11.2's "must not repeatedly create improvement tasks" is honoured by the
hard count.

Proposal: a review record shape and the "one repair before a block is final" rule in the harness profile.

### 2.7 Gates and rewind

A slice runs choose → branch → contract doc → **gate** → qualify → **gate** → review → apply → commit → record.
Gates are owner approvals with options (`freeze` vs `strengthen`); `rewind(state, step, why)` reopens an earlier
step, clearing later fields and approvals and keeping the reason. Used once on S1b: the first contract draft quoted
sentences the specification did not contain; rewound, redrafted with the named sections as excerpts, and a
deterministic verbatim-quote check now refuses any quote not in the sources.

§3.1 ("re-entering a node creates a new instance") allows this; the profile should name the rewind receipt and the
gate approval record (who, when, options chosen), since both are audit facts an owner asks about.

### 2.8 Progress screening over a stream

For a running worker, Jev judges snapshots of the streaming check output (progressing / stalled / failing / done
plus custom states) on a cadence decided by code (every 5 s or 1 KB, at most 4 judgments per check); a `Screen`
contract says when to alert (wake on, keep quiet below, spend, seconds, patterns). Two channels: the output channel
always gets the resolution; the alert channel only what the screen asked for. Every judgment is recorded.

`harness-tasks@0.1`'s `TaskWatchPage` carries the events; the judgment over them, its cadence policy and the
screen contract are the missing part. Proposal: `progress-screening@0.1`.

### 2.9 Context selection is a decision, and it decided outcomes

On one real task (Sentinel T02d4) eight attempts with one-hop context failed while the first attempt with
reference-following context rated by Jev passed ($0.0055). Context is proposed by code (follow references from the
task and tests), rated by Jev, packed by budget. §3.3's "avoid dumping the whole application into every question"
is the right instinct; the profile should name context selection as an assessable decision with its own record
(candidates, ratings, packed set, budget), because it is where most of the cost and most of the failures were.

### 2.10 Compact text binding for agent callers

Agents talking to the runtime use a line protocol (`c` claim, `q` question, `t` task, `k` constraint, `h` hint,
`x` expand, `v` size, `m` more, `w` why, `o` options, `s` steer; one status line back:
`# r7 ok 3/3 5 jev 1.2s $0.0004 L o0 d3 v0 u0`) because tokens are the cost. This is a binding like §12/§24, not
core; worth documenting as an optional text binding once stable.

## 3. Evidence that bears on the Jev-first claim (§11)

- Cheap-first-then-escalate beat predictive routing: Jev's complexity rating from the prompt predicts a cheap
  model's failure at AUROC 0.64–0.76 (spec length 0.52–0.58) — a useful prior for the starting tier, not a gate;
  where a check exists, trying the cheap model and escalating on evidence was cheaper and never lost a solve.
- Ladder + ratchet: DeepSeek V4.1 Flash wrote most modules first or second attempt for $0.001–0.005 each; where it
  plateaued (280/283 three times) the decided escalation to Sonnet finished it. A failed rung leaves its best draft
  and the next rung continues from it.
- A composed report from a chronological log passed a per-fact contradiction check and was still wrong about the
  present: a later fact superseding an earlier one is not a contradiction *within* the facts. Checkers need a
  supersession rule; the protocol's "assessment over a frame" framing makes this a frame-construction duty.

## 4. Recommended versioning

The core wire schema can stay **0.1** — every change above is additive or a profile:

**0.1.1 (additive, now):**
- §5.4: `distribution` required when the resolver returns one; add `choice_not_maximal`.
- §6: `resolver.kind = "rule"` with `rule_id`.
- `assessment-batching`: cap = assessor's limit (64 for Jev); shared state document as basis.
- New optional profiles: `provenance-lineage@0.1`, `artifact-qualification@0.1`, `progress-screening@0.1`.
- `harness-tasks`: review record, one-repair rule, gate approval and rewind receipts, context-selection record,
  foreign-base apply (declared + rechecked).

**0.2 (breaking, when the profiles have a second implementation):**
- A flattened batch over one state document becomes the canonical assessment; a single-decision assessment is a
  batch of one.
- Origin (six values, graded) replaces the three trust values.
- Every commit receipt carries the grade of what it rested on.

## 5. Not claimed

No benchmark of Jev against other assessors; cohorts of 3–27; one real project; one runtime implementation. The
escalation-outcome measurement is too small to rate (6 decisions; ~30 per option needed). The runtime is not yet
public; this note is the evidence it can offer today.
