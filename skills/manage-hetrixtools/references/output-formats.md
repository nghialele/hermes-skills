# HetrixTools output formats

## Incident

**Verdict:** `<monitor>` was `<state>` for `<duration>` from `<start> (+07)`. `<cause or live candidates>`.

**Timeline (Asia/Ho_Chi_Minh, UTC+7)**
- `<start> → <end>` — `<duration>`, `<regions/probes>`, `<observed failure>`

**Evidence**
- Breadth: `<regions / probe nodes>`
- Agent: `<continuity or gap>`
- Diagnostics: `<first loss hop/AS and downstream behavior>`

**Confidence:** `<level>` — `<why>`.

**Next steps**
1. `<user action>`
2. `<safe monitoring improvement>`

## Blacklist

**Verdict:** `<target>` is listed on `<n>/<total>` RBLs as of `<time> (+07)`. `<history pattern or retention limit>`.

List RBL, listed time, and delist URL. Distinguish a clean existing monitor from a missing monitor/error.

## Fleet

Lead with monitor count, up/down count, lowest uptime, and the two items worth attention. Sort by attention, not alphabetically.

## Maintenance

Show original provider time and converted `(+07)` time, exact monitor, start/end, alert behavior, unchanged behavior, and returned window ID.
