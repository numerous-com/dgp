# DGP 0.1 — Farm Energy Calculator and Budgeted Evaluations

**Status:** Finalized example application profile for experimental DGP 0.1. This is an integration design, not an implemented calculator.  
**Date:** 19 September 2026.  
**Negotiated extension:** `budgeted-evaluations@0.1`; optional projections, discovery, and handoff profiles are defined in the main specification.  
**Application:** A location-first wind, existing-PV, electricity-demand, and stepped-battery calculator.  
**Primary controller:** Jev-first, with optional authorized LLM reasoning or generation.

## 1. Purpose

This example is deliberately an ordinary calculator, not an agent-management application. A person operates it through an address field, map, turbine selector, demand/PV fields, and battery steps. A controller operates the same domain through typed inputs, available operations, immutable scenarios, and numerical results.

The application should wrap its existing calculation engine rather than create a separate agent-only implementation. The UI and DGP publisher share validation, derived-input rules, calculation models, tariffs, equipment catalogues, and result definitions. A purpose-built map and charts are permitted: the common contract concerns meaning and effects, not identical interaction mechanics.

The user's task is:

> Around my farm at this address, which location, turbine, and battery give the greatest savings while achieving at least 50% self-sufficiency?

This becomes a constrained study over locations, approved turbine configurations, and allowed battery configurations. It must not become a search over arbitrary electricity demand or existing PV, which are facts or explicitly labelled assumptions about the farm.

## 2. The ordinary interaction

### Stage 1: location only

The initial live frame offers only a location input. A user may type an address, enter coordinates, or click a map. Map selection and coordinate entry produce the same canonical location representation; their difference is provenance/presentation, not a distinct energy calculation.

An address query does not by itself become a precise site. The application's geocoder resolves it, and an ambiguous match produces a bounded choice among matches. The model must not invent coordinates. Coordinates specify the reference system explicitly; use named latitude/longitude fields for this input to avoid tuple-order mistakes.

A farm address establishes an origin, not ownership or an approved search polygon. The later search must use a user-approved area, authenticated parcel association, or an explicitly assumed radius. An assumed radius is not evidence of property rights or installation feasibility.

The static graph may disclose later stages, but they are not available for commitment before their prerequisites hold.

### Stage 2: production estimate

After location resolution, the application computes site/resource information and an initial wind-production estimate. If an actual turbine energy estimate is shown before the user chooses a model, the application must publish the default turbine and hub height used. It must not present model-independent wind resource as a turbine-specific yield.

The first screen may be useful before electricity-demand or PV data are known. In that case it presents production only, or labels economics and battery recommendations as preliminary assumptions. A final self-sufficiency-constrained recommendation requires a defined load profile, existing-PV configuration, dispatch policy, and economic basis.

Calculation is application code. DGP does not require Jev to decide that a deterministic prerequisite should now be calculated.

### Stage 3: system configuration and automatic battery

After prerequisites resolve, the application exposes turbine choices, electricity demand, existing PV, and battery mode. A battery is represented by a configuration, not merely a number: nominal/usable energy, charge/discharge power, losses, and limits must be known to the evaluator.

For illustration, permitted energy steps are 0, 10, 20, 30, 40, and 50 kWh. These are invented example steps, not product specifications. In production, valid configurations come from the server's catalogue, including inverter compatibility and any nonuniform steps.

Battery mode is one of:

- `auto`: optimize among permitted configurations for the published objective and constraints;
- `manual`: evaluate the selected permitted configuration without silently changing it.

Changing demand, PV, the turbine, tariffs, or the optimization target may change the automatic recommendation. A manual value remains manual until explicitly changed, even if it stops satisfying the target. The UI should display that failure and offer a return to auto, not conceal it by replacing the user's value.

Zero battery is a legitimate candidate. The application must also be able to report that no permitted configuration meets the target.

### Stage 4: results and exploration

The UI displays wind/PV production, direct use, battery flows, imports, exports, curtailment, losses, self-sufficiency, costs, and savings. It may expose time-series drill-down and a simple comparison view.

The DGP client receives the same metric definitions and numerical results. It can ask for additional scenarios without changing the design currently displayed to the person.

## 3. Separate workspace, study, scenario, and evaluation

**Workspace.** Mutable presentation/selection state, including the selected scenario and a revision. It is not the shared mutable input object for every calculation.

**Study basis.** An immutable reference containing fixed farm facts, accepted assumptions, baseline, objective, constraint definitions, data/model versions, and approved search scope. A changed load profile or savings definition creates a new basis rather than silently mixing comparisons.

**Scenario.** A fully resolved immutable configuration or immutable base-plus-patch whose exact resolved inputs are recoverable. A scenario contains or references its location, turbine configuration, battery configuration, and study basis.

**Evaluation.** The execution of a named versioned evaluator against a scenario. Its state changes through events; its final result is an immutable artifact. Mutable latest-status projections are permitted, provided history is not silently rewritten.

**Search record.** An immutable or event-versioned record of considered candidates, search policy, evaluated/rejected/unexplored counts, stopping reason, and supported optimality claim.

**Adoption.** A separate guarded update of the workspace's selected scenario. Producing a result does not automatically adopt it.

These distinctions allow four evaluations to run concurrently without four writers racing to change the same location or battery slider.

## 4. What the application exposes

The application provides semantic operations, mapped to DGP input/choice nodes and trusted handlers. Suggested names below are application identifiers, not new core DGP methods.

| Operation | Purpose | State/effect boundary |
|---|---|---|
| `provide_location` | Address query or explicit point | Update location workflow; address resolution may disclose data to an approved provider |
| `select_address_match` | Choose a returned geocoder candidate | Establish normalized origin |
| `configure_system` | Supply turbine, demand, PV, battery mode | Create a new configuration; do not overwrite prior scenarios |
| `set_study_goal` | Select objective, constraints, and search area | Create a study basis/revision |
| `create_candidates` | Materialize approved spatial/configuration alternatives | Bounded internal work; candidate eligibility is explicit |
| `evaluate_variants` | Evaluate configurations derived from an immutable base | Admit jobs under current authorization and budgets |
| `optimize_battery` | Optional server-side discrete optimization | Uses the same evaluator, goal, and budget; exposes how many configurations were considered |
| `compare_results` | Filter/rank comparable completed results | Deterministic numerical comparison; may use paging or summaries |
| `adopt_scenario` | Display/select a result in the workspace | Guarded workspace write; not purchase, installation, or equipment control |

Small applications need not provide a dedicated optimizer. A controller can enumerate configurations through `evaluate_variants`. Larger applications may offer both low-level evaluation and a bounded optimization operation.

A primitive form update does not require model inference. Values already supplied by the person or returned by a trusted service can pass through ordinary schema validation and authorized submission. Jev is used where a judgment is useful.

## 5. Search-space description

A runtime descriptor should identify which inputs are fixed, editable, generated candidates, or search variables. It should publish units, domains, constraints, dependencies, and the metric schema.

Example study semantics:

```yaml
fixed:
  consumption_profile_ref: load-profile-v3
  existing_pv_ref: existing-pv-v2
  baseline_ref: existing-system-baseline-v1
  weather_bundle_ref: weather-v1
  tariffs_ref: tariffs-v4
  dispatch_policy_ref: dispatch-v2
variables:
  location:
    domain_ref: approved-candidate-sites-v1
  turbine:
    domain_ref: compatible-turbine-catalogue-v1
  battery:
    domain_ref: compatible-battery-configurations-v1
constraint:
  metric: self_sufficiency_fraction
  operator: gte
  value: 0.50
  scope: declared_simulation_period
objective:
  metric: annualized_net_savings_dkk
  direction: maximize
  definition_ref: economics-v2
```

The metric above is a proposed explicit interpretation of "biggest savings", not an inference that the user necessarily intended lifecycle economics. An application should expose annual bill reduction separately and make the selected optimization metric visible. When the alternatives materially differ, the controller can request an objective choice.

A spatial candidate list is not a proof that every point is suitable. Candidates need screening status and reasons; unknown suitability must remain unknown.

## 6. Correct numerical semantics

### 6.1 Objective and fixed context

For fixed study context `c`, select location `l`, turbine `t`, and battery configuration `b`:

`maximize savings(l, t, b; c)`

subject to `self_sufficiency(l, t, b; c) >= 0.50` and all declared feasibility constraints.

Do not optimize battery capacity once for a default turbine and reuse it as the optimum for other sites or turbines. Evaluate the battery dimension jointly, or solve a battery subproblem for every site/turbine pair.

The baseline should normally retain the farm's existing PV and existing demand, with only the proposed additions removed. Do not attribute existing-PV savings to a newly proposed turbine. Baseline and alternatives must share weather, demand, tariff treatment, currency, taxes where applicable, and period assumptions.

Annual bill reduction and annualized net savings are different metrics. A net-savings definition may subtract incremental operating expenses and an annualized representation of investment/replacement costs. Its discount rate, lifetime, residual treatment, and price basis must be declared, not inferred from a model's prose. This is a modelling contract, not a financial recommendation.

### 6.2 Self-sufficiency

Define self-sufficiency as:

`onsite renewable energy actually delivered to the farm's native electrical demand / total native electrical demand`.

The numerator includes direct wind/PV delivery and battery delivery attributable to previously stored onsite renewable energy. It excludes exports, storage losses, and grid-origin battery discharge. If grid charging is permitted, use explicit source attribution or a compatible accounting method; do not call all battery discharge renewable self-supply.

Annual generation divided by annual demand is not this metric. Annual production may exceed demand while the farm still imports during non-generating periods. Export credits change economics but do not make exported energy physically self-supplied.

Use synchronized generation, PV, and demand time series at the declared resolution. An annual/monthly yield or marginal wind-speed distribution cannot by itself establish temporal matching or storage benefit. A derived/synthetic temporal model may be used, but its provenance and limitations must be reported. Initial and terminal battery state must be consistent, for example by equal boundary states or explicit accounting for stored-energy changes; an initially full battery must not provide unaccounted free renewable supply.

A modelled 50% result applies to its simulated period and assumptions. It is not a guarantee about every future year. A multi-year minimum, probability constraint, or uncertainty margin requires a separate explicit policy and an appropriate physical uncertainty model. Jev confidence is not that physical uncertainty model.

SAM's battery model is useful precedent for separating dispatch, time-varying prices, losses/degradation, and financial analysis. This profile does not mandate SAM or replace the application's existing engine. [R3, R4]

### 6.3 Result metadata

Every result should identify scenario, basis, evaluator version, model/data versions, time resolution, simulation period, dispatch policy, and assumptions. Metrics carry definitions and units. Constraint outcomes distinguish `satisfied`, `violated`, and `unknown`.

A failed job is not an infeasible design. A missing load profile is not zero load. An unavailable result is not zero savings. Partial calculations must advertise which outputs are unavailable or provisional.

## 7. Budgeted asynchronous evaluation profile

DGP 0.1 supports input schemas, immutable frames, read sets, guarded commits, and internal effects. The finalized optional budgeted-evaluations and resumable-events profiles are defined in main specification §§21–22. This application profile specializes them for calculator work. These runtime features are not implemented in ThreadDesk. [R1]

A producer that requires these semantics advertises `budgeted-evaluations@0.1` and includes it in the relevant frame's `required_features`. Extension information is carried in the existing `extensions` object. A client that does not implement the profile must reject, rather than ignore, the required capability.

### 7.1 Admission and lifecycle

A DGP assessment chooses or supplies an evaluation request. Its guarded commit validates the scenario parameters, current authority, catalogue restrictions, and budget; atomically reserves permitted resources; and creates or finds the job.

The synchronous commit receipt attests to job admission, not finished energy calculation. It references an evaluation/job ID. Readiness is obtained through authorized status reads or events. The normative job states and permitted transitions are in main specification §21.3. The ordinary successful path is:

`queued → running → succeeded | failed`; cancellation/reconciliation use `cancel_requested`, `cancelled`, and `reconciling`. Terminal snapshots settle accounting. Retention expiry is not a job-success/failure state.

A cancellation request is not confirmation of cancellation. A calculation already completed may still produce a result. Expired access/retention and expired compute deadlines should be distinguished in the application's detailed status.

Core frames may publish completed results as evidence and expose subsequent choices. The extension defines status/result references; it does not need to make a simulation worker an assessor or invent a judgment at every timestep.

The MCP 2025-11-25 Tasks specification is relevant transport precedent: task-augmented requests, status polling, and deferred result retrieval. It calls its task mechanism experimental. A future MCP binding should negotiate a specific supported version and map these semantics, not claim support merely by adding an endpoint named MCP. [R5]

### 7.2 Limits

Illustrative policy (values are not platform promises):

```yaml
scope: workspace-and-tenant
max_running_evaluations: 4
max_variants_per_submission: 16
max_queued_evaluations: 32
simulation_budget:
  limit: 240
  consumed: 0
  reserved: 0
  unit: full_scenario_simulation
cache_hits_consume_simulation_budget: false
idempotent_replays_consume_simulation_budget: false
```

The policy also needs a bounded work/cost rule for expensive resource preprocessing, retries, and internal batch expansion. Counting only HTTP calls is insufficient: one request must not bypass the limit by expanding into thousands of simulations. Where evaluator costs vary, publish weighted compute units or enforce separate resource-class budgets, with rate limits on lookup and cache traffic as appropriate.

`remaining` and `running` in a frame are informational snapshots, not reservations or authority. Admission checks are atomic and server-enforced across browser tabs, agents, subprocesses, and clients in the quota scope. Additional tenant/provider/global limits may further constrain admission.

Do not put a rapidly changing global queue counter into every scenario's freshness read set. This would make unrelated admissions invalidate each other. Keep invariant basis/policy checks and current atomic capacity checks distinct.

The server may queue admitted jobs up to its limit. Otherwise it returns a machine-readable temporary-capacity response with a retry hint, or a distinct budget-exhaustion result. The controller waits for progress or follows bounded polling; it need not invoke Jev repeatedly while nothing has changed.

Reserve enough budget to bound execution before starting. Settle actual usage at completion according to a documented charging policy. An idempotent replay must not charge again. A cancelled job cannot refund work already performed unless the policy explicitly grants such a refund. Cancellation is not rollback.

### 7.3 Cache and dependency reuse

A result-cache key covers the fully resolved inputs plus evaluator, model, data, and dispatch versions. Authorization remains necessary for cache access; matching inputs do not grant cross-tenant access.

Reuse site resource computations, generation profiles, PV/load profiles, and economics where their declared dependency sets permit it. For example, changing battery size should not trigger an identical wind-resource download. Changing tariff assumptions should not invalidate a physical wind estimate, though it can invalidate dispatch/economics when dispatch depends on price.

Illustratively, 12 sites × 3 turbine configurations × 6 batteries yield 216 configuration evaluations. There are at most 36 distinct site/turbine generation combinations; site weather inputs may be shared further only where height/model/data dependencies actually match. A bounded worker pool can execute these without exposing 216 screen mutations or asking a model to select every pair.

## 8. Jev-first search controller

Jev receives the user's request, the available application operations, relevant evidence, candidate summaries, numerical results, missing inputs, and remaining resource allowances. It makes bounded judgments about what to do next. Its runtime performs authorized operations and invokes an LLM only where generation or extended reasoning is needed.

Useful choices include `resolve_location`, `request_missing_profile`, `evaluate_offered_batch`, `refine_region`, `compare`, `report`, and `stop`. Their availability depends on the current frame. Exact names and grouping belong to the application/controller policy.

Code should handle known values, schema checks, combinations, arithmetic, constraint comparisons, sorting, cache hits, queue waiting, and hard stop conditions. A model should not guess which of two numbers is larger or substitute confidence for an unevaluated energy result.

TypeSafe documents Choice, Score, and Noul, and independent evaluation of questions against a common state. The model may directly judge rich text evidence it supports; an LLM is not mandatory to interpret every paragraph. Independent screening questions can be batched, whereas a judgment that needs newly computed results must wait for those results. [R2]

For free-form values not directly available from the user or a trusted source, the runtime can use an authorized extraction/generation service and validate its output. Selecting among generated spatial candidates is different from hallucinating a coordinate.

A practical search can be exhaustive over a small finite domain, or coarse-to-fine when the area is large. A coarse pass may rank candidates heuristically. Such ranking does not justify claiming that all discarded candidates are mathematically dominated. A "first satisfactory result" race is insufficient for the user's request for greatest savings unless the user explicitly accepts a satisficing search.

The final report states one of:

- best among all evaluated candidates in the declared finite grid;
- best found before a stated budget/time limit, with unexplored scope;
- a solver-certified result with an explicit bound/gap;
- no feasible design found in the explored set;
- insufficient data to evaluate the constraint.

An exhausted search budget is a legitimate terminal outcome. It is not permission to relax the 50% target silently or request extra resources indefinitely.

## 9. Concurrency, speculation, and UI reconciliation

Candidate evaluations from the same immutable basis may run in parallel. Their results append to the study and do not move the user's map pin or battery selection.

If the user changes consumption while old jobs run, those jobs still describe the old basis correctly. They may finish for comparison or be cancelled under policy. They must not silently populate the new design as if their inputs matched. Adoption compares the current workspace revision and relevant current basis/goal references; a mismatch requires explicit reconciliation.

The UI should distinguish selected design, best result found for the active study, automatic battery suggestion, and manual override. A completion handler must not use "last response wins" to overwrite a more recent user edit. Debounce slider-driven evaluations and, if appropriate, reserve capacity for interactive requests.

A hypothetical design evaluated with exact frozen inputs produces a real calculation result about that hypothetical design. It is not a speculative assessment that can bypass authorization. Scheduling it consumes compute and may disclose coordinates to an external provider. Its physical model may be pure, but job admission, logging, data retrieval, and billing have effects.

Adopting a scenario only selects it in the calculator. Ordering equipment, commissioning it, submitting an application, or controlling a battery would be separate effects with separate authority. No such effects are implied by this profile.

## 10. Example trace

1. Read the initial frame: only location input is actionable.
2. Submit the address; resolve/choose a match using the application service.
3. Run the initial production estimate under a declared turbine default, or obtain site resource results.
4. Establish farm boundary/search region and supply or explicitly accept demand, existing PV, and economic assumptions.
5. Create immutable study basis and baseline; publish valid search variables.
6. Obtain 12 candidate sites, 3 turbine configurations, and 6 battery steps; this is an illustrative 216-case domain.
7. Submit at most 16 variants per batch. Admit/run them within shared limits, reusing upstream artifacts.
8. Read completed results; deterministically filter by the 50% constraint and rank by the selected savings metric.
9. Jev judges whether the remaining budget should refine the search, request missing evidence, or stop. Optional LLM service produces a user explanation tied to result IDs.
10. Present the best supported result, comparisons, fixed assumptions, search coverage, and limitations. Adopt it in the UI only through the authorized selection operation.

## 11. Deliverable and validation boundaries

The accompanying files contain two illustrative DGP frames and a validation script using the consolidated root core schema. Both frames and twelve embedded-input cases are validated. The root package also contains finalized optional-profile schemas, synthetic admission/job/projection/catalogue/handoff records, and selected semantic contract tests.

Machine definitions are in `schemas/dgp.profiles.schema.json` at the bundle root. Checks exercise record and selected lifecycle invariants, not a distributed scheduler or actual simulations. No wind, battery, geocoding, price, or savings calculations were run. No working Farm Energy server, map UI, task queue, live Jev integration, or connection to the existing wind calculator is included. ThreadDesk remains the separately runnable reference application. The main specification is the consolidated finalized 0.1 edition.

## 12. Multiple interfaces and projections

DGP is deliberately partial. A native UI can handle map interaction and charts; an API/CLI can handle load-profile upload and bulk export; MCP can expose existing tools; GraphQL can serve selected results; DGP can expose configuration decisions and budgeted evaluation. These are choices of application design, not six mandatory implementations. The same domain services enforce configuration validity, revisions, accounting, and permissions.

An agent can import a consumption profile through an authorized native API, then fetch a fresh DGP frame that references the resulting immutable profile. It cannot pretend an import succeeded based only on an LLM claim or reuse a stale study frame. A DGP rejection must not trigger a transport switch intended to bypass the same domain restriction.

A compact Jev view might include fixed assumptions, current candidate summaries, the next decision, and the remaining budget. A human view can additionally request geometry and chart series. Both refer to the same frame/study basis; no paid simulation is started merely by selecting another result field. A view's aggregated summaries must be actual identified evidence before they are used in a live assessment.

The bundled capability catalogue declares all six illustrative interface kinds and marks selected capabilities as DGP-native, handoff, or not exposed. Its `.invalid` URLs are intentionally not live services. See `../../examples/profiles` and `../../bindings`.

## References

[R1] **DGP 0.1 Specification**, supplied in this conversation, especially §§1.2, 5.2, 7.4, 9, 12–14, and 17. Bundle file: `../../SPECIFICATION.md`.

[R2] TypeSafe AI, **Primitives (Questions)**, https://docs.typesafe.ai/primitives — Choice/Score/Noul, independent/dependent questions, and batching. Accessed 19 September 2026.

[R3] System Advisor Model, **Battery Storage**, https://sam.nlr.gov/battery-storage.html — battery dispatch, time-varying prices, time-series instructions, and degradation. Accessed 19 September 2026.

[R4] System Advisor Model, **Welcome**, https://sam.nlr.gov/ — performance and financial modelling scope. Accessed 19 September 2026.

[R5] Model Context Protocol, **Tasks**, version 2025-11-25, https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/tasks — task admission, polling, results, resource management, and experimental status. Accessed 19 September 2026. This reference does not claim that 2025-11-25 is the latest MCP version.

[R6] JSON Schema, **Draft 2020-12**, https://json-schema.org/draft/2020-12 — the schema dialect used by the existing DGP 0.1 core. Included here through the original specification's schema choice.
