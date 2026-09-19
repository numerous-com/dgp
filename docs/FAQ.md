# Decision Graph Protocol FAQ

## What is DGP?

Decision Graph Protocol is an MIT-licensed protocol by Numerous ApS for decision-based
AI agents. An application offers immutable evidence frames, typed decisions, and
guarded transitions. Assessments describe judgments; commits request effects.

## How does DGP relate to TypeSafe and Jev?

Jev is the intended first intelligent assessor. DGP remains assessor-neutral and
can also use deterministic, human, or other model judgments. See the
[TypeSafe/Jev integration guide](TYPESAFE_JEV.md).

## Does DGP replace an LLM agent or existing tools?

DGP supplies a decision/control contract around application capabilities.
Existing tools and native interfaces can share the same host guards. An LLM can
still prepare options, generate bounded text, or supply missing inputs.

## Is DGP a workflow engine or a complete decision tree?

No. A publisher may expose only the useful current decisions in part of an
application. Graph previews describe possibilities; they do not grant authority
to execute future actions.

## Does a high-confidence Jev answer authorize an action?

No. The application rechecks permissions, state, expiry, and domain guards.
Confidence is an assessment property, not an execution credential.

## Can DGP batch decisions or speculate?

The optional assessment-batching profile describes independent assessments with
shared evidence and per-item outcomes. Speculative assessments cannot be directly
committed. This profile has schemas and contract tests, not a production endpoint.

## What can I run today?

ThreadDesk's local HTTP demo, browser UI, controller CLI, deterministic mock
resolvers, and validation suite. Its Git/test/publication effects are simulated.
Farm Energy is a design profile. Read [implementation status](IMPLEMENTATION_STATUS.md).

## Is DGP an official TypeSafe, MCP, or GraphQL standard?

No. It is an independent experimental Numerous ApS protocol, with documented
interoperability references and optional mappings.

## What is the license?

The code and documentation are released under the [MIT License](../LICENSE),
Copyright (c) 2026 Numerous ApS. Dependencies retain their respective licenses.
