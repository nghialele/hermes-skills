# AhaSend REST API v2 — raw reference

Use this only for what the CLI does not expose. Base URL `https://api.ahasend.com`, auth header `Authorization: Bearer <api key>`, account ID in the path.

```bash
curl -sS -X POST "https://api.ahasend.com/v2/accounts/$AHASEND_ACCOUNT_ID/messages" \
  -H "Authorization: Bearer $AHASEND_API_KEY" \
  -H 'Content-Type: application/json' \
  -H "Idempotency-Key: order-1234" \
  -d @message.json
```

## Endpoint map

| Resource | Path (after `/v2`) |
| --- | --- |
| Ping | `/ping` |
| Send message | `POST /accounts/{account_id}/messages` |
| Send template message | `POST /accounts/{account_id}/messages/template` |
| Send with CC/BCC (conversation) | `POST /accounts/{account_id}/messages/conversation` |
| List / get message, cancel scheduled | `GET /accounts/{account_id}/messages`, `GET …/messages/{id}`, `DELETE …/messages/{id}` |
| Domains | `/accounts/{account_id}/domains`, `…/domains/{domain}` (+ `/verify`, `/check-dns`) |
| Webhooks | `/accounts/{account_id}/webhooks`, `…/webhooks/{id}` (+ `/trigger`) |
| Routes (inbound) | `/accounts/{account_id}/routes`, `…/routes/{id}` (+ `/trigger`) |
| Suppressions | `/accounts/{account_id}/suppressions`, `…/suppressions/{email}` |
| SMTP credentials | `/accounts/{account_id}/smtp-credentials` |
| API keys | `/accounts/{account_id}/api-keys` |
| Transactional templates | `/accounts/{account_id}/templates`, `…/{id}`, `…/{id}/versions`, `…/{id}/publish` |
| Campaigns | `/accounts/{account_id}/campaigns`, `…/{id}` (+ `/test`, `/send`, `/unschedule`, `/stats`, `/recipients`, `/duplicate`) |
| Campaign templates | `/accounts/{account_id}/campaign-templates` |
| Contacts | `/accounts/{account_id}/contacts`, `…/contacts/{id_or_email}`, `…/contacts/batch` |
| Lists | `/accounts/{account_id}/lists`, `…/lists/{id}`, `…/lists/{id}/members` |
| Segments | `/accounts/{account_id}/segments`, `…/{id}` (+ `/preview`, `/members`) |
| Statistics | `/accounts/{account_id}/statistics/emails`, `…/statistics/transactional/{deliverability,bounce,delivery-time}` |
| Sub-accounts | `/accounts/{account_id}/sub-accounts`, `…/{id}` (+ `/usage`, `/suspend`, `/api-keys`) |

## Create message payload

```json
{
  "sandbox": true,
  "sandbox_result": "deliver",
  "from": { "email": "hello@yourdomain.com", "name": "Your Company" },
  "recipients": [
    { "email": "a@example.com", "name": "Alice", "substitutions": { "first_name": "Alice" } },
    { "email": "b@example.com", "name": "Bob" }
  ],
  "subject": "Welcome {{first_name}}!",
  "html_content": "<h1>Hi {{first_name}}</h1>",
  "text_content": "Hi {{first_name}}",
  "amp_content": "…",
  "substitutions": { "first_name": "there", "month": "December" },
  "reply_to": { "email": "support@yourdomain.com" },
  "attachments": [{ "filename": "invoice.pdf", "content": "<base64>", "content_type": "application/pdf" }],
  "headers": { "X-Campaign": "spring" },
  "tags": ["welcome", "onboarding"],
  "track_opens": true,
  "track_clicks": true,
  "schedule": { "first_attempt": "2026-11-20T02:00:00Z", "expires": "2026-11-21T02:00:00Z" },
  "retention": { "metadata": 30, "data": 7 }
}
```

- Each entry in `recipients` becomes its own email (no shared To/CC), and per-recipient `substitutions` override the global ones.
- `sandbox: true` forces sandbox even with a production key; `sandbox_result` is `deliver|bounce|defer|fail|suppress` and drives the matching webhook events.
- Substitution values are HTML-escaped inside `html_content`/`amp_content`; `{{ value|safe }}` inserts raw HTML (escape user input yourself). Subject, text and headers get values verbatim.
- Limits: 100 recipients/request · 30 MB body · 20 MiB final message · first attempt within 7 days, expiry within 8 days.

Response `202`:

```json
{ "object": "list", "data": [ { "object": "message", "id": "uuid", "message_id_header": "<uuid@yourdomain.com>",
  "recipient": { "email": "a@example.com" }, "status": "queued", "error": null } ] }
```

`status` is `queued`, `scheduled` or `error`; on `error` the `id` and `message_id_header` are `null`. Use the returned `id` for `GET`/`DELETE`.

## Pagination, idempotency, errors

- Cursor pagination: `?limit=` (≤100) plus `?after=` / `?before=`; read `pagination.next_cursor`.
- `Idempotency-Key` on supported writes: a repeated identical request replays the stored result for 24 h; a changed payload answers `422`.
- Error body: `{"message": "..."}` with `request_id`. Statuses: 400/422 validation · 401 auth · 403 permission/scope · 404 missing · 409 conflict or in-progress · 413 too large · 429 rate limit (`Retry-After`) · 5xx server.
- Rate limits are per account: 100 rps (burst 200) for normal endpoints, **1 rps** for transactional statistics and the stream/trigger endpoints.

## Scopes (API key permissions)

`accounts:read|write|billing` · `accounts:members:read|add|update|remove` · `domains:read|write|delete:all|delete:{domain}` · `messages:send|cancel|read` × (`:all` or `:{domain}`) · `webhooks:read|write|delete` × (`:all` or `:{domain}`) · `routes:read|write|delete` × (`:all` or `:{domain}`) · `smtp-credentials:read|write|delete` × (`:all` or `:{domain}`) · `suppressions:read|write|delete|wipe` · `templates:read|write|delete` · `campaigns:read|write|delete|send` · `contacts:read|write|delete` · `lists:read|write|delete` · `segments:read|write|delete` · `api-keys:read|write|delete` · `statistics:read:all|read:{domain}` · `sub-accounts:read|write|delete|suspend|usage` · `sub-account-api-keys:read|write|delete` · `*` (everything, dev only).

Rules that bite:

- Domain scopes keep the braces: `messages:send:{example.com}`.
- `:all` supersedes the domain form; duplicates are rejected and redundant domain scopes are dropped.
- Webhook writes with contact events also need `contacts:read` (+ `lists:read` for list events).
- Deleting a domain needs `domains:delete:all` or the matching `domains:delete:{domain}`.
- Sending a stored template needs the **send** scope of the sender domain, not `templates:*`.
- Campaign send/test/unschedule need only `campaigns:send`.
- `lists:write` (not `lists:delete`) removes a list member; `include_contacts=true` also needs `contacts:read`.
- Segment preview/members and "segments of a contact" also need `contacts:read`.
- Sub-account nested keys are manageable only with the parent's `sub-account-api-keys:*` scopes.

For send-only integrations create an API Key v2 in Credentials → Add, mode Production or Sandbox, scoped to `messages:send:{your-domain}` (optionally plus `statistics:read:{your-domain}`).

## Webhook payload and signatures

Standard Webhooks format:

```json
{ "type": "message.delivered", "webhook_id": "uuid", "timestamp": "2026-05-06T09:49:16.687031577Z", "data": { } }
```

Headers: `webhook-id` (dedupe key per delivery), `webhook-timestamp` (unix seconds), `webhook-signature` (`v1,<base64 HMAC-SHA256 of "{id}.{timestamp}.{raw body}">`). `webhook_id` identifies the configured endpoint, **not** the delivery — never dedupe on it. Verify against the raw body with a `standardwebhooks` library before parsing. 6 attempts over ~16 min, 5 s timeout, 2xx only; auto-disabled after >100 consecutive failures.

Event types: `message.reception`, `message.delivered`, `message.transient_error` (deferral), `message.failed`, `message.bounced`, `message.suppressed`, `message.opened`, `message.clicked`, `message.unsubscribed`, `message.complained`, `suppression.created`, `suppression.deleted`, `domain.dns_error`, `domain.sending_type_changed`, `contact.created`, `contact.updated`, `contact.deleted`, `contact.added_to_list`, `contact.removed_from_list`, `contact.subscribed`, `contact.unsubscribed`, `contact.complained`. Inbound routing uses the separate `message.routing` event.

Lifecycle: `reception → delivered → [opened] → [clicked]`; hard bounce `→ bounced` (address suppressed); soft bounce `→ deferred … → delivered|failed` (retry-exhaustion terminal events carry no `delivery_attempt`); already-suppressed recipients go `→ suppressed` with no delivery attempt.

## Segment definition JSON (`segments create --definition-file`)

```json
{
  "schema_version": 1,
  "match": "all",
  "conditions": [
    { "field": "attributes.country", "op": "equal", "value": "DE" },
    { "field": "created_at", "op": "after", "value": "30 days ago" },
    { "field": "list", "op": "in", "value": "<list-uuid>" },
    { "match": "any", "conditions": [
      { "field": "campaign", "op": "opened", "value": "<campaign-uuid>" },
      { "field": "campaign_count", "op": "opened_at_least", "value": { "count": 3, "since": "90 days ago" } }
    ]}
  ]
}
```

- `match` is `all`/`any`; groups nest one level only; ≤50 conditions total, ≤5 campaign conditions; ≤100 segments per account.
- Text ops: `equal, not_equal, contains, not_contains, begins_with, not_begins_with, ends_with, not_ends_with, is_empty, is_not_empty`.
- Number ops: `equal, not_equal, less, less_or_equal, greater, greater_or_equal`.
- Date ops: `equal, not_equal, before, before_or_on, after, after_or_on` (dates or relatives like `today`, `30 days ago`, `2 hours from now`); date fields also take `month_is`, `anniversary_within`.
- Boolean ops: `is_true`, `is_false`. List: `in`, `not_in`. Campaign: `received, not_received, opened, not_opened, clicked, not_clicked`. Any campaign: same minus `not_received`, value is a relative time. Count: `received_at_least`, `opened_at_least`, … with `{count, since}`.
- A new or edited segment is `building` until members are found; campaigns cannot send or schedule while it is `building` or `failed`.
- Reachable ≠ member: a campaign reaches only enabled, non-unsubscribed, valid, and confirmed-on-a-list (or list-less) contacts.

## SMTP

`send.ahasend.com` · **587, 25, 2525** with STARTTLS (`AUTH PLAIN` after STARTTLS) · **465** with implicit TLS (`AUTH PLAIN` or `AUTH LOGIN`). Port 465 is supported and works: `ahasend smtp send --server send.ahasend.com:465` starts TLS at once (verified live). It fails only when the client waits for a greeting first, or when the host blocks outbound 465. The docs' "Port 465 is not supported" agent line is stale boilerplate. Up to 50 recipients per message, 20 MiB total including base64 attachments, 10,000 messages per connection. Sandbox via SMTP: header `AhaSend-Sandbox: true` and `AhaSend-Sandbox-Result: deliver|bounce|defer|fail|suppress`. Tracking headers: `AhaSend-Track-Opens`, `AhaSend-Track-Clicks`.

## Plans and limits (Nov 2026)

Free 1,000 emails/month (3 domains) · Pro 25,000 (unlimited domains) · Max 100,000. Monthly volume is shared by transactional and campaigns. Metadata retention 1–7/14/30 days, message data 1–7 (Free) / 0–14 (Pro) / 0–30 (Max); new accounts default to 7 days, zero retention needs approval. Hourly sending limits start low and grow with age, plan and reputation. Campaign test sends: 5 addresses via API, 50/day/account (UTC). Campaign audience: up to 50 lists per campaign via API. Contact batch upsert: 1,000/request. Template content ≤200 KB per format. Marketing mail needs a marketing-type domain and is subject to a separate daily limit.
