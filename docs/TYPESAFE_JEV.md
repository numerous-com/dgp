# TypeSafe AI, Jev, and Decision Graph Protocol

DGP is a Numerous ApS application protocol. Jev is TypeSafe AI's decision model.
DGP describes evidence, decisions, permissions, and effects; Jev can assess
the evidence and return a judgment used by a DGP client.

TypeSafe documents three typed question primitives: **Choice**, **Noul**, and
**Score**. Multiple questions can share one state in a request. See the official
[TypeSafe introduction](https://docs.typesafe.ai/introduction) and
[API quick start](https://docs.typesafe.ai/introduction/quickstart)
(checked 20 September 2026).

## Mapping Jev to DGP

| Layer | Responsibility |
|---|---|
| DGP application | Publish current evidence and offered decisions; enforce permissions and commits. |
| Jev assessor | Evaluate bounded questions against supplied state. |
| Deterministic controller | Validate identifiers, bind results to frames, enforce budgets and select the next step. |
| Optional LLM service | Produce a requested draft, analysis, or missing structured input. |

The reference adapter is [JevResolver](../dgp_demo/providers.py). It uses
`POST https://api.typesafe.ai/v1/systemone`, reads `TYPESAFE_API_KEY` from the
environment, and supports an explicit `JEV_MODEL` setting. Follow
[the README](../README.md#use-real-jev-and-optional-llm-assistance) for opt-in usage.
Provider contracts are fixture-tested; this repository does not claim a live
provider certification or that a particular model ID is available to every account.

## Parallel assessments and speculative decisions

The [assessment-batching profile](../profiles/jev-harness/PROFILE.md) defines
registration of separate assessments sharing one immutable frame. Its optional
usage provenance counts a shared provider call once. It is not an implemented
batch inference endpoint.

Independent, fully specified questions can share evidence. A question needing
another answer or newly retrieved evidence needs a later step or explicitly
constructed conditional alternatives. A future graph template is not a currently
offered decision. Speculative assessments cannot authorize effects; using cached
computation requires equivalence checks and a fresh live assessment.

## Interoperability

DGP's core is assessor-neutral. A deterministic resolver, another model, or an
authorized human can produce assessments. The host retains authority regardless
of the assessor. MCP and GraphQL mappings are documented separately; their
presence does not imply an implemented transport server.

TypeSafe and Jev are referenced for interoperability. Numerous ApS maintains DGP
independently; this repository is not an official TypeSafe product or standard.
