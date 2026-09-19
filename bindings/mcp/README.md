# MCP mapping — no server included

See SPECIFICATION.md §13. Use ordinary MCP tools whose structured results contain canonical DGP records. Suggested tool names are application-defined, not new MCP standard methods.

| Tool | Semantic operation |
|---|---|
| `dgp_discover` | Core manifest; optional interface catalogue locator. |
| `dgp_frame_read` | Current or immutable historical frame. |
| `dgp_view_read` | Optional named frame projection. |
| `dgp_assessment_record` | Record an assessment without executing its selected action. |
| `dgp_commit` | The normal guarded commit; include a logical idempotency key. |
| `dgp_job_read` | Optional evaluation job snapshot. |
| `dgp_events_read` | Optional resumable event page. |
| `dgp_receipt_read` | Reconcile a known operation outcome. |

An app may also expose native tools such as load-profile import. Native tools are not DGP wrappers and do not have to mimic DGP's interaction sequence. They still share authoritative domain rules, permissions, revisions, and budgets.

The actual MCP lifecycle, transport, tool-result representation, authorization, and task/stream support must be implemented for an explicitly selected MCP version. The package does not implement that server. The dated 2025-11-25 Tasks reference is precedent, not a compatibility promise with another MCP version.
