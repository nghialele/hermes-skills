# HetrixTools write recipes

1. Read `get_api_scope`; confirm the key can affect the target.
2. For creation, read `get_account_limits`.
3. Read the current target with full details or the relevant GET policy/object.
4. State exact operation, target ID, time zone, alert effect, and unchanged behavior. Wait for explicit approval.
5. Invoke the write once. Do not blindly retry credit-consuming or append operations.
6. Read back the exact target and report the returned state/ID.

## Maintenance

Future window: `create_scheduled_maintenance` with future `start`/`end`, `timezone: "Asia/Ho_Chi_Minh"`, and `with_notifications: false` unless the user explicitly wants alerts. Confirm with `list_scheduled_maintenance`.

Already running: `set_maintenance_mode` with the intended notification behavior; this is a state, not a timer. Use `end_maintenance` to resume.

## Field traps

- Heartbeat edits: resend `timeout`, `grace`, and all `public_*_stats` flags.
- Website monitor with a keyword: resend current `keyword`, or `""` to clear it.
- Blacklist monitor edits: resend current `label`, or the API clears it.
- Monitor type cannot be changed; deletion/recreation is required and is destructive.
- Blacklist range creation expands to one monitor per IP; confirm the count first.
- Blacklist monitor deletion is immediate and irreversible.
- Status-page announcements replace the whole announcement and affected-monitor list; read current state first.
- Private-note set replaces the complete note; append can duplicate on retry.
