# HetrixTools tool map

All tools are exposed as `mcp__aperture__hetrixtools_<name>`.

## Discovery
- `ping`, `get_api_scope`, `get_account_limits`, `get_api_status`, `list_contact_lists`.

## Uptime
- `list_uptime_monitors`: entry point; use name/target filters and `full_details` only when configuration matters.
- `list_uptime_downtimes`: periods with `start`, `end`, `maintenance`; null end means ongoing.
- `get_location_fail_log`: raw probe failures; paginate backward with `meta.next_page_timestamp`.
- `get_network_diagnostics`: stored ping/MTR; requires matching monitor and downtime IDs.
- `get_web_snapshot`: stored website screenshot/status.
- `get_uptime_report`: trend and response times; pass `timezone: "+07:00"` and verify the echoed timezone.

## Agents
- `get_server_agent_metrics`, `list_server_agent_processes`.
- `get_server_agent_warning_policies`, `update_server_agent_warning_policies`.
- `get_server_agent`, `create_server_agent`, `delete_server_agent`.

## Blacklists
- `list_blacklist_monitors`, `get_blacklist_report`, `get_blacklist_history`, `get_blacklist_report_at_date`.
- `check_blacklist_ipv4` / `check_blacklist_domain`: credit-consuming writes; approval required.
- `list_blacklists`, `list_active_ipv4_rbls`, `list_active_domain_rbls`.

## Maintenance, status, activity
- `set_maintenance_mode`, `list_scheduled_maintenance`, `create_scheduled_maintenance`, `delete_scheduled_maintenance`.
- Status page list/membership/announcement tools.
- `get_account_activity_log`: prefer `exclude_browsing: true`.
- Uptime private-note get/append/set/delete tools; notes max 1024 UTF-8 bytes.
