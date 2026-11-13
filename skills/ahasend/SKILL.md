---
name: ahasend
category: email
description: "Manage AhaSend email: send, domains, webhooks, campaigns."
version: 1.0.0
author: Nghia, Hermes Agent
license: WTFPL
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [ahasend, email, smtp, transactional, campaigns, webhooks, dns, deliverability]
    related_skills: [himalaya, email-inbox-triage]
---

# AhaSend Operations

Drive the AhaSend account through the `ahasend` CLI (v0.5.0). The CLI is the default surface: it wraps API v2, handles retries, idempotency, pagination and output formats. Drop to raw `curl` against `https://api.ahasend.com/v2` only when you need a field the CLI does not expose — see `references/api-v2.md`.

## When to Use

- Sending transactional email or a personalized batch.
- Adding, verifying or debugging a sending domain (SPF/DKIM/DMARC/return-path).
- Creating, listing, testing or streaming webhooks and inbound routes.
- Managing suppressions, transactional templates, contacts, lists, segments, campaigns, API keys, SMTP credentials, sub-accounts.
- Reading delivery, bounce, deliverability or delivery-time statistics.

## Setup (once per machine)

```bash
npm install -g @ahasend/cli      # or: brew install ahasend/tap/ahasend / irm https://ahasend.com/install.ps1 | iex
ahasend --version
ahasend auth login                # prompts for API key + account ID on stderr
ahasend ping && ahasend auth status
```

- Profiles live in `~/.ahasend/config.yaml` (`%USERPROFILE%\.ahasend\config.yaml`), **plain-text keys**. The `0600` chmod is real on Linux/macOS but a **no-op on Windows** (inherited ACLs stay: SYSTEM + Administrators). Read `references/secrets.md` before storing a key.
- **On this machine use the patched build** `C:\Users\Administrator\bin\ahasend.exe` (v0.5.0-keyring): it also reads `AHASEND_API_KEY` + `AHASEND_ACCOUNT_ID` (+ optional `AHASEND_API_URL`) and the OS credential store, so `ahasend auth login --keyring` keeps the key out of every file. The stock npm CLI has neither.
- **Never accept an API key or SMTP password in chat.** The operator runs `ahasend auth login --keyring` (patched) or `~/.ahasend-secret/store.ps1` (stock) themselves.
- Account ID is a UUID; the CLI rejects a non-UUID before any request (exit 3).
- `ahasend auth status` shows profile, account, and whether the key verifies. It exits nonzero when the key fails.

## Golden Rules

1. **Sandbox first.** `--sandbox` (optionally `--sandbox-result bounce|defer|fail|suppress`) validates and records the message without delivering and without burning monthly credits. Every new content path gets a sandbox send before a live one.
2. **`--output json` for anything you parse**, `table` for humans, `csv` for spreadsheets. JSON is the API body unchanged, so `references/api-v2.md` field names apply.
3. **`-f/--force` in scripts.** Deletes, `campaigns send`, `lists members remove`, `messages cancel`, `suppressions wipe`, `subaccounts suspend`, `templates draft discard`, `templates versions restore` all prompt otherwise, and a declined/absent prompt exits 4.
4. **Branch on exit codes, not on message text.** 0 ok, 1 partial/other, 2 auth, 3 config, 4 validation, 5 not found, 6 permission, 7 network, 8 rate limit, 130 interrupted.
5. **Read back after every write.** `domains get`, `webhooks get`, `campaigns get`, `suppressions check` — confirm the changed field, then report the returned ID.
6. **Confirm before anything irreversible or reputation-affecting:** domain delete, suppression wipe, campaign send to a real list, `subaccounts suspend`, sending live mail to more than a handful of recipients.
7. Times: `--from-time` / `--to-time` / `--schedule` accept RFC3339 or relative (`24h`, `7d`). Display times to Nghia in **Asia/Ho_Chi_Minh (UTC+7)**.
8. **A doc claim is not a fact until a probe agrees.** AhaSend's Mintlify "Agent Instructions" header is auto-injected and drifts from the pages it describes. When a header, a page and a troubleshooting entry disagree, probe live (`ahasend smtp send --test --server …` needs no credentials) and trust the probe. Never encode a doc claim as a hard constraint the operator has to argue with later.

## Core Recipes

### Send one email

```bash
ahasend messages send --sandbox \
  --from 'noreply@example.com' --from-name 'Example' \
  --to user@example.com \
  --subject 'Hello' --text 'Body' --html-file mail.html \
  --output json
```

Text or HTML is required; `--amp`/`--amp-file` is an extra part. Inline (`--text`, `--html`) and file (`--text-file`, `--html-file`) variants cannot be combined. `--attach` caps at 10 MiB per file. `--schedule 2h` or RFC3339, first attempt within 7 days.

### Send a batch (CSV/JSON recipients)

```bash
ahasend messages send --from 'noreply@example.com' \
  --recipients recipients.csv --subject 'Hi {{ first_name }}' \
  --html-file mail.html --global-substitutions global.json \
  --max-concurrency 5 --progress --show-metrics --output json > results.json
```

- CSV needs an `email` column; `name` sets the display name; every other column becomes a substitution.
- JSON is `[{"email":...,"name":...,"substitution_data":{...}}]` and allows lists/objects (needed for `{% for %}` loops).
- The whole file is validated first — one bad address sends nothing (exit 4).
- 100 recipients per request. Failed recipients are written to `~/.ahasend/failed-*.json`, unknown-outcome ones to `unknown-*.json`; both are reusable as `--recipients`. Delete them when done (personal data).
- Templates: MiniJinja/Jinja2 — `{{ var }}`, `{{ var|default("there") }}`, `{% if %}`, `{% for %}`. Values are HTML-escaped in HTML/AMP; use `|safe` only for HTML you built yourself.

### Domains

```bash
ahasend domains create example.com --sending-type transactional --format cloudflare
ahasend domains check-dns example.com        # prints required records
ahasend domains verify example.com
ahasend domains list --status pending --output table
```

`--format bind|cloudflare|terraform` for paste-ready records (not with `--output json`). Custom `--tracking-subdomain`, `--return-path-subdomain`, `--media-subdomain`, `--subscription-subdomain`. `--sending-type marketing` is a **separate infrastructure and daily limit** — required for marketing mail sent through the API/SMTP. Verification is DNS-dependent; re-check after the TTL, do not assume failure.

### Webhooks

```bash
ahasend webhooks create --name 'app' --url https://app.example.com/hooks/ahasend \
  --events message.delivered --events message.bounced --events message.complained
ahasend webhooks list --output table
ahasend webhooks trigger <webhook-id> --events message.delivered   # sample event
ahasend webhooks listen --events message.bounced --forward-to http://localhost:3000/hook
```

- Events: `message.reception`, `message.delivered`, `message.transient_error`, `message.failed`, `message.bounced`, `message.suppressed`, `message.opened`, `message.clicked`, `message.unsubscribed`, `message.complained`, `suppression.created`, `suppression.deleted`, `domain.dns_error`, `domain.sending_type_changed`, `contact.created|updated|deleted|added_to_list|removed_from_list|subscribed|unsubscribed|complained`. Short names (`delivered`) work too.
- `--all-events` covers everything except contact events; `--all-contact-events` covers those.
- Signature = Standard Webhooks: `webhook-id`, `webhook-timestamp`, `webhook-signature` (`v1,<base64 hmac-sha256 of id.timestamp.body>`). Verify with a `standardwebhooks` library; the CLI's `listen`/`trigger` skips verification.
- 6 delivery attempts over ~16 min; endpoint must answer 2xx within 5 s. A webhook is auto-disabled after >100 consecutive failures.

### Suppressions

```bash
ahasend suppressions check user@example.com
ahasend suppressions list --domain example.com --output table
ahasend suppressions create user@example.com --expires 30d --reason 'hard bounce'
ahasend suppressions delete user@example.com          # -f in scripts
```

### Stats

```bash
ahasend stats emails --from-time 7d --group-by day --output json
ahasend stats deliverability --from-time 30d --sender-domain example.com
ahasend stats bounces --from-time 7d
ahasend stats delivery-time --from-time 7d
```

Stats endpoints are capped at **1 request/second** — never loop them.

### Templates

```bash
ahasend templates create --name order --subject 'Order {{ id }}' --html-file t.html --publish
ahasend templates get <id> --published        # what sends actually use
ahasend templates get <id> --markup > design.ahaml
ahasend templates update <id> --markup-file design.ahaml --publish
ahasend messages send --template-id <id> --to user@example.com
```

Edits land on the **draft**; sends use the published copy until `templates publish`. With `--template-id`, content flags are rejected and `--from`/`--subject` are optional.

### Campaigns (marketing)

```bash
ahasend campaigns create --name spring --from 'news@example.com' --subject 'Spring' \
  --list-id <list> --html-file c.html
ahasend campaigns get <id>                 # shows issues that block sending
ahasend campaigns test <id> --to you@example.com    # max 5 addresses, 50/day/account
ahasend campaigns send <id> --schedule 2026-11-20T09:00:00+07:00
ahasend campaigns stats <id> --output json
```

Only a `draft` with no issues can send; a campaign whose segment is `building`/`failed` cannot be scheduled. Daily marketing limit is separate from transactional.

## Pitfalls

- **`auth status|switch|logout` refuse `--api-key`/`--account-id`** (exit 4); only `auth login` takes them.
- `--api-key` **always** targets the production API and cannot combine with `--profile`.
- Scope braces are literal: `messages:send:{example.com}`, not `messages:send:example.com`. `:all` supersedes the domain form.
- Deleting a domain needs `domains:delete:all` or `domains:delete:{domain}` — plain `domains:write` is not enough.
- Sending a transactional template needs the **send** scope of the sender domain, not `templates:write`.
- Rate limits are **per account, not per key**: 100 rps (burst 200), stats/listen/trigger 1 rps. `429` carries `Retry-After`; the CLI retries 429/5xx/409 itself (`--max-retries`, default 3).
- SMTP: `send.ahasend.com`, ports **25/587/2525 with STARTTLS** and **465 with implicit TLS** (TLS from the first byte; AUTH PLAIN or LOGIN). Verified live from this host on both 465 and 587 with `ahasend smtp send --test --server send.ahasend.com:465`. The docs' boilerplate "Port 465 is not supported" agent line is stale and contradicts `/smtp`, `/troubleshooting` and `/smtp/errors`. Port 465 fails only when the client is set to STARTTLS (waits 30 s for a greeting) or the host blocks outbound 465. Up to 50 recipients/message, 20 MiB total.
- Free plan = 1,000 emails/month shared by transactional and campaigns; hourly sending limits start low on new accounts.
- All message data is stored in the EU; retention is plan-bounded (new accounts 7 days), so old message bodies may be gone — say so instead of guessing.
- `webhooks listen` / `routes listen` ignore `--output`; they always stream text. Use `--forward-to` to process events in code.
- `--limit` is 0–100 (0 = API default). Page with `--after`/`--before`, never both.
- Idempotency: reuse the same `--idempotency-key` only for a byte-identical request; changed content or a relative `--schedule` makes the API answer 422. Keys live 24 h.
- A campaign/list/campaign-field used by a segment cannot be deleted (409, names the segments).

## Verification

- Sends: report the returned message `id`s and per-recipient status from `--output json`; for batches state succeeded/failed counts and the failed-recipients file path.
- Domains: `domains get` must show the expected `sending_type` and DNS status.
- Webhooks: `webhooks get <id>` must show the intended `events` and `enabled`.
- Campaigns: `campaigns get` must show `draft` with no issues before a send is claimed as scheduled.
- Never present a sandbox send as a delivered email.

## References

- `references/cli-reference.md` — every command, usage line and flag from `ahasend <cmd> --help` (v0.5.0).
- `references/api-v2.md` — raw REST v2 payloads, endpoints, scopes, rate limits, webhook events and signature rules.
- `references/secrets.md` — where the CLI stores keys, why Windows `0600` does nothing, and the ranked options (DPAPI wrapper, fork with env/keyring, hardening).
