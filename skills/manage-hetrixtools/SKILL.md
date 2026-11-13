---
name: manage-hetrixtools
description: "Investigate uptime, blacklist, maintenance, and fleet."
version: 1.0.0
author: Nghia, Hermes Agent
license: WTFPL
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [hetrixtools, monitoring, uptime, blacklist, maintenance, infrastructure]
    related_skills: []
---

# HetrixTools Operations

Use the HetrixTools tools exposed by the Aperture MCP server (`mcp__aperture__hetrixtools_*`) to investigate monitoring data and, only after explicit approval, change monitoring state. This skill is for HetrixTools data; do not use it as a substitute for general server debugging.

## When to Use

- A HetrixTools uptime alert or downtime needs explanation.
- An IP or domain is listed on RBLs.
- A provider maintenance notice needs matching to monitors.
- The user asks for monitor, agent, fleet, account, or team-activity health.

## Rules

- Use Asia/Ho_Chi_Minh (UTC+7) for all displayed times. Convert Unix timestamps with `scripts/timeline.py`; never calculate dates mentally.
- Read operations are safe to perform immediately. Writes require explicit approval immediately before the write: creating, editing, deleting, checking blacklists on demand, changing maintenance mode, scheduling maintenance, changing status pages, or changing notes/policies.
- Trace every claim to returned fields. If evidence supports multiple causes, state both and what would distinguish them.
- Treat monitor, downtime, status-page, and contact-list IDs as opaque. Never invent, shorten, or mix IDs from different monitors.
- Verify every external write by reading the exact object back.

## Investigation Procedure

1. Anchor the monitor/target and time window. If no window is given, use the last 7 days and say so. If multiple monitors match, list them and ask which one.
2. For downtime: list downtime periods, exclude `maintenance: true`, read the location fail log, then fetch network diagnostics using the matching monitor and downtime IDs. If an agent exists, inspect metrics across the outage window. Use a web snapshot for website-monitor questions about returned status or page appearance.
3. Classify from evidence: breadth across regions, probe-node results, last clean MTR hop/AS, and continuity or gaps in agent metrics. Report regions separately from probe nodes: four regions may produce eight probe-node entries.
4. For blacklists: confirm the target is an existing blacklist monitor, read the current report, then read history and `meta.retention_days`. A clean existing monitor is different from a missing monitor/error. On-demand checks consume credits and are writes; ask first.
5. For maintenance: convert the provider's original time to UTC+7, match only affected monitors, and choose immediate maintenance for an already-running window or scheduled maintenance for a future window. Do not assume every monitor in a provider scope is owned by the user.
6. For fleet review: use full monitor details, agent metrics, process lists, warning policies, and activity logs with browsing events excluded as appropriate.

## Answer Format

Lead with a one- or two-sentence verdict containing the time and concrete numbers. Then include only evidence that was actually read, a confidence statement when cause is inferred, and actionable next steps. Keep chat answers under about one screen unless a report is requested. Always label displayed times `(+07)` or `(UTC+7)`.

For reports, write Markdown under the active workspace's `outputs/` directory and include timeline, evidence, ruled-out causes, and recommended action. Do not write to a machine-specific absolute path.

## Write Gate

Before any write, read API scope, account limits when creating, and the current object being changed. State the exact operation, alerting effect, and unchanged behavior; wait for an explicit yes. Read `references/write-recipes.md` for field-preservation traps. Afterward, read back the target and confirm the changed field.

## Pitfalls

- `get_location_fail_log.minutes` means failure minutes per page, not a time range; filter returned entries against the incident window.
- Fail logs and diagnostics return probe nodes, while monitor `locations` are regions.
- MTR loss on an intermediate hop with clean downstream hops is usually ICMP deprioritisation, not proof of a fault.
- Agent history gaps inside the incident window are evidence; do not smooth them away.
- Blacklist history retention is plan-dependent; never claim an old period is clean when it is outside retention.
- Heartbeat edits must resend timeout, grace, and public-stat flags. Website monitors with a keyword must resend the current keyword. Blacklist edits must resend the current label.
- Deleting blacklist monitors, especially ranges, is immediate and irreversible; require explicit confirmation.

## Verification

- For reads: identify the returned monitor/target and the fields supporting the verdict.
- For writes: read back the exact object or scheduled window and report the returned ID/state.
- Before finalizing: check every timestamp has UTC+7, maintenance is excluded from incident totals, counts distinguish regions/probes, and no inferred cause is presented as fact.

## References

- `references/tool-map.md` — tool grouping and parameter traps.
- `references/write-recipes.md` — exact write preflight, payload, and read-back rules.
- `references/output-formats.md` — concise incident, blacklist, fleet, maintenance, and report formats.
- `scripts/timeline.py` — timezone conversion and duration helper.
