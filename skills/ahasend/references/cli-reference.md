# AhaSend CLI command reference

Generated from `ahasend <command> --help` on **v0.5.0** (build 2026-11-11, commit b5b3145). Every usage line and every command-specific flag is listed; global flags are omitted because they apply to all commands:

| Global flag | Effect |
| --- | --- |
| `--profile <name>` | Use a saved profile instead of the default. |
| `--api-key <key>` + `--account-id <uuid>` | Use a key instead of a profile. **Always the production API**; cannot combine with `--profile`. Refused by `auth status/switch/logout`. |
| `--output json\|table\|plain\|csv` | Output format (default `plain`). |
| `--verbose` / `--debug` | Request logs / full request+response dumps on stderr, secrets redacted. |
| `--no-color` | Disable colour. |
| `-v, --version` / `-h, --help` | Version / help. |

Exit codes: `0` ok · `1` other API error or a failed item · `2` auth (401 or no credentials) · `3` config/profile problem · `4` validation or declined prompt · `5` not found · `6` permission (403) · `7` network · `8` rate limit (429) · `130` interrupted.

Commands that prompt before acting (need `-f/--force` in scripts): every `delete`, `auth logout --all`, `campaigns send`, `lists members remove`, `messages cancel`, `subaccounts suspend`, `suppressions wipe`, `templates draft discard`, `templates versions restore`.

---

## `apikeys`
Manage API keys for authentication and access control.
```
ahasend apikeys [flags]
```

### `apikeys create`
Create an API key with the specified scopes and label.
```
ahasend apikeys create --label <label> --scope <scope> [flags]
```
```
      --idempotency-key string   Idempotency key for safe retries (generated when omitted)
      --ip-allow-list strings    CIDR block or IP address allowed to use the key (can be used multiple times)
      --label string             Label for the API key (required)
      --scope strings            Scope to grant (required; can be used multiple times)
```

### `apikeys delete`
Delete an API key permanently.
```
ahasend apikeys delete <key-id> [flags]
```
```
  -f, --force   Skip confirmation prompt
```

### `apikeys get`
Get detailed information about a specific API key by its ID.
```
ahasend apikeys get <key-id> [flags]
```

### `apikeys list`
List all API keys for your account with pagination support.
```
ahasend apikeys list [flags]
```
```
      --after string    Return the page after this cursor
      --before string   Return the page before this cursor
      --limit int32     Maximum number of items to return (0-100; 0 uses the API default)
```

### `apikeys update`
Update an existing API key's label, scopes and IP allow list.
```
ahasend apikeys update <key-id> [flags]
```
```
      --clear-ip-allow-list     Remove the IP allow list so the key works from any IP
      --ip-allow-list strings   New CIDR block or IP address allowed to use the key, replacing the list (can be used multiple times)
      --label string            New label for the API key
      --scope strings           New scope to grant, replacing all scopes (can be used multiple times)
```

## `auth`
Authenticate with AhaSend and manage multiple authentication profiles.
```
ahasend auth [flags]
```

### `auth login`
Authenticate with AhaSend by providing your API key and account ID.
```
ahasend auth login [flags]
```
```
      --api-url string      AhaSend API URL (default "https://api.ahasend.com")
```

### `auth logout`
Remove stored API credentials for the current profile or a specific profile.
```
ahasend auth logout [profile] [flags]
```
```
      --all     Logout from all profiles
  -f, --force   Skip confirmation prompt
```

### `auth status`
Display information about the current authentication status, including:
```
ahasend auth status [flags]
```
```
      --all              List the names of all profiles
```

### `auth switch`
Switch the active authentication profile to use different AhaSend
```
ahasend auth switch <profile> [flags]
```

## `campaigns`
Draft, test, send, schedule and report on marketing campaigns, which send to
```
ahasend campaigns [flags]
```

### `campaigns create`
Create a draft campaign. Every field but the name can be set later with
```
ahasend campaigns create --name <name> [flags]
```
```
      --campaign-template-id string   ID of a campaign template whose design the campaign copies
      --editor string                 Editor of the design: advanced, simple or html
      --exclude-list-id strings       ID of a list whose contacts get no message (can be used multiple times)
      --exclude-segment-id strings    ID of a segment whose members get no message (can be used multiple times)
      --from string                   Sender email address
      --from-name string              Sender display name (needs --from)
      --html-file string              Path to the HTML
      --idempotency-key string        Idempotency key for safe retries (generated when omitted)
      --list-id strings               ID of a list to send to (can be used multiple times)
      --markup-file string            Path to the AhaML of a Simple Editor design
      --mjml-file string              Path to the MJML source
      --name string                   Campaign name, shown in the dashboard only (required)
      --preheader string              Preview text
      --reply-to string               Reply-to email address
      --segment-id strings            ID of a segment to send to (can be used multiple times)
      --subject string                Subject
      --text-file string              Path to the plain text version
```

### `campaigns delete`
Delete a draft campaign with its design and its audience. The API refuses
```
ahasend campaigns delete <campaign-id> [flags]
```
```
  -f, --force   Skip confirmation prompt
```

### `campaigns duplicate`
Make a new draft from a campaign in any status. The copy gets the campaign's
```
ahasend campaigns duplicate <campaign-id> [flags]
```
```
      --idempotency-key string   Idempotency key for safe retries (generated when omitted)
      --name string              Name of the copy
```

### `campaigns get`
Get one campaign with its audience and content. For a draft it also shows
```
ahasend campaigns get <campaign-id> [flags]
```
```
      --markup   Write only the design's AhaML to stdout, as --markup-file reads it
```

### `campaigns list`
List the account's campaigns, newest first, with cursor pagination. --status
```
ahasend campaigns list [flags]
```
```
      --after string    Return the page after this cursor
      --before string   Return the page before this cursor
      --limit int32     Maximum number of items to return (0-100; 0 uses the API default)
      --status string   Filter by campaign status: draft, validating, waiting_for_review, scheduled, sending, paused, sent, canceled or failed
```

### `campaigns recipients`
List a campaign's recipients, with cursor pagination. Give exactly one of
```
ahasend campaigns recipients <campaign-id> [flags]
```
```
      --after string                   Return the page after this cursor
      --before string                  Return the page before this cursor
      --bounce-classification string   Bounce classification to list
      --limit int32                    Maximum number of items to return (0-100; 0 uses the API default)
      --status string                  Recipient status to list: Processing, Queued, Deferred, Delivered, Bounced, Failed, Administratively Bounced, Suppressed, Rejected, Complained or Unsubscribed
```

### `campaigns send`
Send a draft campaign to its lists and segments now, or at the time given
```
ahasend campaigns send <campaign-id> [flags]
```
```
  -f, --force                    Skip confirmation prompt
      --idempotency-key string   Idempotency key for safe retries (generated when omitted)
      --schedule string          Schedule the send for an RFC3339 or relative time like '2h' (the API takes one more than a minute ahead); sends now when omitted
```

### `campaigns stats`
Show a campaign's live counters, its rates and its stored report, with the
```
ahasend campaigns stats <campaign-id> [flags]
```

### `campaigns templates`
Manage campaign templates, the designs a campaign can copy with
```
ahasend campaigns templates [flags]
```

### `campaigns templates create`
Create a campaign template. Content comes from files: --markup-file for the
```
ahasend campaigns templates create --name <name> [flags]
```
```
      --editor string            Editor of the design: advanced, simple or html
      --html-file string         Path to the HTML
      --idempotency-key string   Idempotency key for safe retries (generated when omitted)
      --markup-file string       Path to the AhaML of a Simple Editor design
      --mjml-file string         Path to the MJML source
      --name string              Campaign template name (required)
      --text-file string         Path to the plain text version
```

### `campaigns templates delete`
Delete a campaign template. Campaigns made from it keep their own copies.
```
ahasend campaigns templates delete <campaign-template-id> [flags]
```
```
  -f, --force   Skip confirmation prompt
```

### `campaigns templates get`
Get one campaign template with its content.
```
ahasend campaigns templates get <campaign-template-id> [flags]
```
```
      --markup   Write only the design's AhaML to stdout, as --markup-file reads it
```

### `campaigns templates list`
List the account's campaign templates, without their content, with cursor
```
ahasend campaigns templates list [flags]
```
```
      --after string    Return the page after this cursor
      --before string   Return the page before this cursor
      --limit int32     Maximum number of items to return (0-100; 0 uses the API default)
```

### `campaigns templates update`
Partially update a campaign template. Only the flags you set are sent, and the
```
ahasend campaigns templates update <campaign-template-id> [flags]
```
```
      --html-file string         Path to the HTML
      --idempotency-key string   Idempotency key for safe retries (generated when omitted)
      --markup-file string       Path to the AhaML of a Simple Editor design
      --mjml-file string         Path to the MJML source
      --name string              New campaign template name
      --regenerate-text          Make the text version again from the HTML
      --text-file string         Path to the plain text version
```

### `campaigns test`
Send a test of a draft campaign to up to 5 addresses, with placeholders for
```
ahasend campaigns test <campaign-id> --to <address> [flags]
```
```
      --idempotency-key string   Idempotency key for safe retries (generated when omitted)
      --to strings               Address to send the test to (required; can be used multiple times)
```

### `campaigns unschedule`
Return a validating or scheduled campaign to draft, cancelling its audience
```
ahasend campaigns unschedule <campaign-id> [flags]
```
```
      --idempotency-key string   Idempotency key for safe retries (generated when omitted)
```

### `campaigns update`
Partially update a draft campaign. Only the flags you set are sent.
```
ahasend campaigns update <campaign-id> [flags]
```
```
      --clear-exclude-lists          Exclude no list
      --clear-exclude-segments       Exclude no segment
      --clear-from                   Remove the sender
      --clear-lists                  Remove every list the campaign sends to
      --clear-reply-to               Remove the reply-to
      --clear-segments               Remove every segment the campaign sends to
      --exclude-list-id strings      New list whose contacts get no message, replacing the excluded lists (can be used multiple times)
      --exclude-segment-id strings   New segment whose members get no message, replacing the excluded segments (can be used multiple times)
      --from string                  Sender email address
      --from-name string             Sender display name (needs --from)
      --html-file string             Path to the HTML
      --idempotency-key string       Idempotency key for safe retries (generated when omitted)
      --list-id strings              New list to send to, replacing the lists (can be used multiple times)
      --markup-file string           Path to the AhaML of a Simple Editor design
      --mjml-file string             Path to the MJML source
      --name string                  New campaign name
      --preheader string             New preview text (empty clears it)
      --regenerate-text              Make the text version again from the HTML
      --reply-to string              New reply-to email address
      --segment-id strings           New segment to send to, replacing the segments (can be used multiple times)
      --subject string               New subject (empty clears it)
      --text-file string             Path to the plain text version
```

## `contacts`
Manage account-global contacts used for transactional and marketing email.
```
ahasend contacts [flags]
```

### `contacts batch`
Synchronously create or update up to 1,000 contacts from a JSON file whose
```
ahasend contacts batch --file <path> [flags]
```
```
      --file string              JSON file containing {"data":[...]} (required)
      --idempotency-key string   Idempotency key for safe retries (generated when omitted)
```

### `contacts create`
Create one account-global contact. Attribute keys must already exist in the
```
ahasend contacts create <email> [flags]
```
```
      --attributes string        Contact attributes as a JSON object
      --first-name string        Contact first name
      --idempotency-key string   Idempotency key for safe retries (generated when omitted)
      --last-name string         Contact last name
      --status string            Contact status: enabled, disabled or blocked
      --status-reason string     Reason for the contact status
      --unsubscribed             Whether the contact is globally unsubscribed
```

### `contacts delete`
Permanently delete one contact by ID or raw email. Delete asks for
```
ahasend contacts delete <id-or-email> [flags]
```
```
  -f, --force   Skip confirmation prompt
```

### `contacts get`
Get one contact by ID or raw email address. Pass email addresses exactly as
```
ahasend contacts get <id-or-email> [flags]
```

### `contacts list`
List the account's contacts, newest first, with cursor pagination. Filter by
```
ahasend contacts list [flags]
```
```
      --after string       Return the page after this cursor
      --before string      Return the page before this cursor
      --email string       Filter by normalized exact email address
      --from-time string   Filter contacts created after this time (RFC3339 or relative like '24h', '7d')
      --limit int32        Maximum number of items to return (0-100; 0 uses the API default)
      --status string      Filter by status: enabled, disabled or blocked
      --subscribed         Filter by global subscription state
      --to-time string     Filter contacts created before this time (RFC3339 or relative)
```

### `contacts memberships`
List one contact's list memberships by contact ID or raw email, each with
```
ahasend contacts memberships <id-or-email> [flags]
```
```
      --after string                 Return the page after this cursor
      --before string                Return the page before this cursor
      --limit int32                  Maximum number of items to return (0-100; 0 uses the API default)
      --subscription-status string   Filter by membership status: unconfirmed, confirmed, unsubscribed or complained
```

### `contacts segments`
List the segments one contact is a member of, by contact ID or raw email,
```
ahasend contacts segments <id-or-email> [flags]
```
```
      --after string    Return the page after this cursor
      --before string   Return the page before this cursor
      --limit int32     Maximum number of items to return (0-100; 0 uses the API default)
```

### `contacts update`
Partially update one contact by ID or raw email. Only explicitly supplied
```
ahasend contacts update <id-or-email> [flags]
```
```
      --attributes string      Attributes to change as a JSON object (a null value removes that attribute)
      --email string           New email address
      --first-name string      New first name (empty clears it)
      --last-name string       New last name (empty clears it)
      --status string          New status: enabled, disabled or blocked
      --status-reason string   New reason for the status (empty clears it)
      --unsubscribed           Whether the contact is globally unsubscribed (false resubscribes it)
```

## `domains`
Manage your email sending domains including DNS verification, monitoring,
```
ahasend domains [flags]
```

### `domains check-dns`
Trigger a fresh DNS validation check for a domain. If the domain was checked
```
ahasend domains check-dns <domain> [flags]
```
```
      --show-records   Print the DNS setup instructions even when the DNS is valid
```

### `domains create`
Create a domain in your AhaSend account for email sending. After creating
```
ahasend domains create [domain] [flags]
```
```
      --dkim-private-key-file string    File with the domain's DKIM private key, an RSA key in PEM form of at least 1024 bits (Platform Partner accounts only)
      --dkim-rotation-interval int      DKIM rotation interval in days (managed DNS domains on eligible plans only)
      --dkim-selector string            Custom DKIM selector (Platform Partner accounts only)
      --format string                   DNS record format: bind, cloudflare or terraform (terraform for Cloudflare provider v5); not with --no-dns-help or --output json
      --idempotency-key string          Idempotency key for safe retries (generated when omitted)
      --media-subdomain string          Custom media subdomain
      --no-dns-help                     Skip DNS configuration instructions
      --non-interactive                 Never prompt; fail when a required flag is missing
      --return-path-subdomain string    Custom return-path subdomain
      --sending-type string             Sending type: transactional or marketing (default transactional)
      --subscription-subdomain string   Custom subscription management subdomain
      --tracking-subdomain string       Custom tracking subdomain
```

### `domains delete`
Delete a domain from your AhaSend account. This action cannot be undone.
```
ahasend domains delete <domain> [flags]
```
```
  -f, --force   Skip confirmation prompt
```

### `domains get`
Get detailed information about a specific domain including DNS records,
```
ahasend domains get <domain> [flags]
```

### `domains list`
List all domains in your AhaSend account with their verification status,
```
ahasend domains list [flags]
```
```
      --after string          Return the page after this cursor
      --before string         Return the page before this cursor
      --limit int32           Maximum number of items to return (0-100; 0 uses the API default)
      --sending-type string   Filter by sending type: transactional or marketing
      --status string         Filter by DNS status: verified, pending or failed
```

### `domains update`
Update domain settings such as custom subdomains, DKIM rotation interval,
```
ahasend domains update <domain> [flags]
```
```
      --dkim-rotation-interval int      DKIM rotation interval in days (managed DNS domains on eligible plans only)
      --dkim-selector string            Custom DKIM selector; an empty value clears it (Platform Partner accounts only)
      --media-subdomain string          Custom media subdomain
      --return-path-subdomain string    Custom return-path subdomain
      --sending-type string             Sending type: transactional or marketing
      --subscription-subdomain string   Custom subscription management subdomain
      --tracking-subdomain string       Custom tracking subdomain
```

### `domains verify`
Show the DNS status of a domain as of its last DNS check, with
```
ahasend domains verify <domain> [flags]
```
```
      --show-records   Print the DNS setup instructions even when the DNS is valid
```

## `lists`
Manage contact lists, the static lists of contacts that campaigns target,
```
ahasend lists [flags]
```

### `lists create`
Create a contact list with no members. --tag can be used multiple times and
```
ahasend lists create --name <name> [flags]
```
```
      --description string       List description
      --idempotency-key string   Idempotency key for safe retries (generated when omitted)
      --name string              List name (required)
      --tag strings              Tag for the list (can be used multiple times)
```

### `lists delete`
Delete a contact list. The API refuses while a campaign that still needs the
```
ahasend lists delete <list-id> [flags]
```
```
  -f, --force   Skip confirmation prompt
```

### `lists get`
Get one contact list, including its contact count.
```
ahasend lists get <list-id> [flags]
```

### `lists list`
List the account's contact lists, newest first, with cursor pagination.
```
ahasend lists list [flags]
```
```
      --after string    Return the page after this cursor
      --before string   Return the page before this cursor
      --limit int32     Maximum number of items to return (0-100; 0 uses the API default)
      --name string     Filter by list name: lists whose name contains it, in any case
```

### `lists members`
Manage the contacts that belong to a contact list. A member is one contact's
```
ahasend lists members [flags]
```

### `lists members add`
Add up to 1,000 existing contacts to a list in one request.
```
ahasend lists members add <list-id> [flags]
```
```
      --contact-id strings       ID of a contact to add (can be used multiple times)
      --email strings            Email address of a contact to add (can be used multiple times)
      --file string              JSON file containing {"data":[...]}
      --idempotency-key string   Idempotency key for safe retries (generated when omitted)
```

### `lists members list`
List a contact list's members, newest first, with cursor pagination.
```
ahasend lists members list <list-id> [flags]
```
```
      --after string                 Return the page after this cursor
      --before string                Return the page before this cursor
      --email string                 Filter by normalized exact email address
      --include-contacts             Embed each member's contact
      --limit int32                  Maximum number of items to return (0-100; 0 uses the API default)
      --subscription-status string   Filter by membership status: unconfirmed, confirmed, unsubscribed or complained
```

### `lists members remove`
Remove one contact from a list by contact ID or raw email. This deletes the
```
ahasend lists members remove <list-id> <id-or-email> [flags]
```
```
  -f, --force   Skip confirmation prompt
```

### `lists members set`
Add one existing contact to a list, or change its membership, by contact ID
```
ahasend lists members set <list-id> <id-or-email> [flags]
```
```
      --subscription-status string   Membership status to write: confirmed, unconfirmed or unsubscribed
```

### `lists update`
Partially update a contact list. Only the flags you set are sent.
```
ahasend lists update <list-id> [flags]
```
```
      --clear-tags           Remove every tag from the list
      --description string   New list description (empty clears it)
      --name string          New list name
      --tag strings          New tag for the list, replacing all tags (can be used multiple times)
```

## `messages`
Send email messages and manage message operations using AhaSend: send
```
ahasend messages [flags]
```

### `messages cancel`
Cancel a scheduled message that has not been sent yet.
```
ahasend messages cancel <message-id>... [flags]
```
```
  -f, --force   Skip confirmation prompt
```

### `messages get`
Get detailed information about a specific message including its content,
```
ahasend messages get <message-id> [flags]
```

### `messages list`
List messages, with cursor pagination. Filter by sender, recipient,
```
ahasend messages list [flags]
```
```
      --after string        Return the page after this cursor
      --before string       Return the page before this cursor
      --from-time string    Filter messages created after this time (RFC3339 or relative like '24h', '7d')
      --limit int32         Maximum number of items to return (0-100; 0 uses the API default)
      --message-id string   Filter by the Message-ID header, with its angle brackets
      --recipient string    Filter by recipient: addresses that contain the value, such as @example.com
      --sender string       Filter by sender email address (must be from your domain)
      --show-details        Show detailed message information
      --status strings      Filter by message status: received, delivered, opened, clicked, deferred, bounced, failed, suppressed, sandbox delivered, sandbox deferred, sandbox failed, sandbox bounced or sandbox suppressed (can be used multiple times)
      --subject string      Filter by subject text (matches subjects that contain it)
      --tag strings         Filter by tag, at most 20, none with a comma (can be used multiple times)
      --to-time string      Filter messages created before this time (RFC3339 or relative)
```

### `messages send`
Send an email message using the AhaSend API. You can send plain text, HTML,
```
ahasend messages send [flags]
```
```
      --amp string                    AMP HTML content
      --amp-file string               File with the AMP HTML content
      --attach strings                File to attach, at most 10,485,760 bytes (10 MiB) (can be used multiple times)
      --from string                   Sender email address (required unless --template-id is set)
      --from-name string              Sender display name (needs --from)
      --global-substitutions string   JSON file with global template variables
      --header strings                Custom header in 'Name: value' format, each name once in any case, in double quotes when the value holds a comma: '"Name: a, b"'; not From, Sender, To, Cc, Bcc, Subject, Message-ID or a header AhaSend sets, such as AhaSend-Sandbox (can be used multiple times)
      --html string                   HTML content
      --html-file string              File with the HTML content
      --idempotency-key string        Idempotency key for safe retries (generated when omitted)
      --max-concurrency int           Maximum concurrent sends for batch operations (1-10) (default 1)
      --max-retries int               Times to send a failed request again (0 or more) (default 3)
      --non-interactive               Never prompt; fail when a required flag is missing
      --progress                      Show progress bar for batch operations (disabled in debug mode)
      --recipients string             Recipients file (JSON or CSV format) with per-recipient substitutions
      --reply-to string               Reply-to email address
      --sandbox                       Send in sandbox mode, which delivers nothing
      --sandbox-result string         Sandbox result simulation: deliver, bounce, defer, fail or suppress (needs --sandbox) (default "deliver")
      --schedule string               Schedule delivery for a time in RFC3339 format or relative like '30m', '2h' (the API takes a future time within 7 days)
      --show-metrics                  Show performance metrics on stderr after the send
      --subject string                Email subject (required unless --template-id is set)
      --tag strings                   Message tag (can be used multiple times)
      --template-id string            Send this transactional template; it supplies the content
      --text string                   Plain text content
      --text-file string              File with the plain text content
      --to strings                    Recipient email address (can be used multiple times)
      --track-clicks                  Track clicks (--track-clicks=false turns it off); the account's setting applies when omitted
      --track-opens                   Track opens (--track-opens=false turns it off); the account's setting applies when omitted
```

## `ping`
Test the connection to the AhaSend API and that the API accepts your API key.
```
ahasend ping [flags]
```

## `routes`
Manage inbound email routes for processing incoming messages through webhooks.
```
ahasend routes [flags]
```

### `routes create`
Create an inbound email route that posts incoming emails to a webhook.
```
ahasend routes create --name <name> --url <url> --recipient <pattern> [flags]
```
```
      --enabled                  Enable the route (the API enables it when omitted) (default true)
      --group-by-message-id      Group related emails by message ID (conversation threading)
      --idempotency-key string   Idempotency key for safe retries (generated when omitted)
      --include-attachments      Include email attachments in webhook payload
      --include-headers          Include email headers in webhook payload
      --name string              Route name (required)
      --non-interactive          Never prompt; fail when a required flag is missing
      --recipient string         Recipient filter, local@domain, such as 'support@example.com' or '*@example.com' (required)
      --strip-replies            Strip reply content from emails
      --url string               Webhook URL for processing emails (required)
```

### `routes delete`
Delete an inbound email route permanently from your account.
```
ahasend routes delete <route-id> [flags]
```
```
  -f, --force   Skip confirmation prompt
```

### `routes get`
Get detailed information about a specific route including its
```
ahasend routes get <route-id> [flags]
```

### `routes list`
List the inbound email routes configured for your account.
```
ahasend routes list [flags]
```
```
      --after string    Return the page after this cursor
      --before string   Return the page before this cursor
      --domain string   Filter by recipient domain (required with a domain-scoped API key)
      --enabled         Show only enabled (--enabled) or disabled (--enabled=false) routes of the page (not with --output json)
      --limit int32     Maximum number of items to return (0-100; 0 uses the API default)
```

### `routes listen`
Listen for inbound email routing events in real-time over a WebSocket
```
ahasend routes listen [flags]
```
```
      --forward-to string   Local endpoint to forward events to
      --recipient string    Recipient pattern for temporary route (e.g., *@domain.com)
      --route-id string     Use existing route instead of creating temporary one
      --skip-verify         Skip SSL certificate verification for local endpoints when forwarding events (needs --forward-to)
      --slim-output         Slim down the payload for printing to the console
```

### `routes trigger`
Trigger route events for development and testing purposes.
```
ahasend routes trigger <route-id> [flags]
```

### `routes update`
Partially update an inbound email route. Only the flags you set are sent;
```
ahasend routes update <route-id> [flags]
```
```
      --enabled               Enable (--enabled) or disable (--enabled=false) the route
      --group-by-message-id   Group related emails by message ID (=false to stop)
      --include-attachments   Include attachments in the webhook payload (=false to stop)
      --include-headers       Include headers in the webhook payload (=false to stop)
      --name string           New route name
      --recipient string      New recipient filter, local@domain, such as '*@example.com'
      --strip-replies         Strip reply content from emails (=false to stop)
      --url string            New webhook URL
```

## `segments`
Manage segments: saved rules over the account's contacts, whose members
```
ahasend segments [flags]
```

### `segments create`
Create a segment from a definition file. A new segment is building until
```
ahasend segments create --name <name> --definition-file <path> [flags]
```
```
      --definition-file string   JSON file holding the segment definition (required)
      --description string       Segment description
      --idempotency-key string   Idempotency key for safe retries (generated when omitted)
      --name string              Segment name (required)
      --timezone string          IANA time zone that relative times and days are read in, such as Europe/Berlin (UTC when omitted)
```

### `segments delete`
Delete a segment; its members are removed shortly after. The API refuses
```
ahasend segments delete <segment-id> [flags]
```
```
  -f, --force   Skip confirmation prompt
```

### `segments get`
Get one segment, with its state and its definition. A failed segment shows
```
ahasend segments get <segment-id> [flags]
```

### `segments list`
List the account's segments, newest first, with cursor pagination.
```
ahasend segments list [flags]
```
```
      --after string    Return the page after this cursor
      --before string   Return the page before this cursor
      --limit int32     Maximum number of items to return (0-100; 0 uses the API default)
```

### `segments members`
List a segment's members by contact ID, from the lowest, with cursor
```
ahasend segments members <segment-id> [flags]
```
```
      --after string    Return the page after this cursor
      --before string   Return the page before this cursor
      --limit int32     Maximum number of items to return (0-100; 0 uses the API default)
```

### `segments preview`
Try a definition file without saving anything: the output is how many
```
ahasend segments preview --definition-file <path> [flags]
```
```
      --definition-file string   JSON file holding the segment definition to try (required)
      --timezone string          IANA time zone that relative times and days are read in, such as Europe/Berlin (UTC when omitted)
```

### `segments update`
Partially update a segment. Only the flags you set are sent, and at least
```
ahasend segments update <segment-id> [flags]
```
```
      --definition-file string   JSON file holding the new segment definition, which replaces the rules
      --description string       New segment description (empty clears it)
      --name string              New segment name
      --timezone string          New IANA time zone that relative times and days are read in (empty sets UTC)
```

## `smtp`
Manage SMTP credentials for sending emails through AhaSend's SMTP service.
```
ahasend smtp [flags]
```

### `smtp create`
Create an SMTP credential for sending emails via SMTP protocol.
```
ahasend smtp create --name <name> [flags]
```
```
      --domains strings          Allowed domain for a scoped credential (can be used multiple times)
      --idempotency-key string   Idempotency key for safe retries (generated when omitted)
      --name string              Credential name (required)
      --non-interactive          Never prompt; fail when a required flag is missing
      --sandbox                  Create as sandbox credential for testing
      --scope string             Credential scope: global or scoped (default "global")
```

### `smtp delete`
Delete an SMTP credential permanently.
```
ahasend smtp delete <credential-id> [flags]
```
```
  -f, --force   Skip confirmation prompt
```

### `smtp get`
Get detailed information about a specific SMTP credential.
```
ahasend smtp get <credential-id> [flags]
```

### `smtp list`
List the SMTP credentials in your account, with cursor pagination.
```
ahasend smtp list [flags]
```
```
      --after string    Return the page after this cursor
      --before string   Return the page before this cursor
      --limit int32     Maximum number of items to return (0-100; 0 uses the API default)
```

### `smtp send`
Send an email using SMTP protocol with AhaSend's SMTP server.
```
ahasend smtp send [flags]
```
```
      --attach strings          File to attach (can be used multiple times)
      --bcc strings             BCC recipient (can be used multiple times)
      --cc strings              CC recipient (can be used multiple times)
      --from string             Sender email address (required)
      --header strings          Custom header in 'Name: value' format, each name once in any case, in double quotes when the value holds a comma: '"Name: a, b"'; not From, Sender, To, Cc, Bcc, Subject or the MIME headers (can be used multiple times)
      --html string             HTML content
      --html-file string        File with the HTML content
      --non-interactive         Never prompt; fail when a required flag is missing
      --password string         SMTP password (required, except by --test); other users of this machine can see it in the process list, so prefer --password-stdin
      --password-stdin          Read the SMTP password from the first line of stdin, in place of --password; the command then asks for nothing
      --sandbox                 Send in sandbox mode, which delivers nothing
      --sandbox-result string   Sandbox result simulation: deliver, bounce, defer, fail or suppress (needs --sandbox) (default "deliver")
      --server string           SMTP server address (default "send.ahasend.com:587")
      --subject string          Email subject (required)
      --tag strings             Message tag (can be used multiple times)
      --test                    Connect to --server, and log in when --username and --password are given, then quit without sending
      --text string             Plain text content
      --text-file string        File with the plain text content
      --to strings              Recipient email address (can be used multiple times)
      --track-clicks            Track clicks (--track-clicks=false turns it off); the account's setting applies when omitted
      --track-opens             Track opens (--track-opens=false turns it off); the account's setting applies when omitted
      --username string         SMTP username (required, except by --test)
```

## `stats`
View email statistics and reports including email counts of any period,
```
ahasend stats [flags]
```

### `stats bounces`
View email bounce statistics by classification for each time period.
```
ahasend stats bounces [flags]
```
```
      --from-time string           Start time (RFC3339, or relative like '7d' or '24h' for 7 days or 24 hours ago; empty leaves it to the API) (default "7d")
      --group-by string            Group results by: hour, day, week or month (default "day")
      --recipient-domain strings   Filter by recipient domain (can be used multiple times)
      --sender-domain strings      Filter by sender domain (can be used multiple times)
      --tag strings                Filter by message tag, none with a comma (can be used multiple times)
      --to-time string             End time (RFC3339, or relative like '1d' for 1 day ago; empty leaves it to the API, which uses now)
```

### `stats deliverability`
View email deliverability statistics. Each period shows how many messages
```
ahasend stats deliverability [flags]
```
```
      --from-time string           Start time (RFC3339, or relative like '7d' or '24h' for 7 days or 24 hours ago; empty leaves it to the API) (default "7d")
      --group-by string            Group results by: hour, day, week or month (default "day")
      --recipient-domain strings   Filter by recipient domain (can be used multiple times)
      --sender-domain strings      Filter by sender domain (can be used multiple times)
      --tag strings                Filter by message tag, none with a comma (can be used multiple times)
      --to-time string             End time (RFC3339, or relative like '1d' for 1 day ago; empty leaves it to the API, which uses now)
```

### `stats delivery-time`
View detailed email delivery time statistics and performance metrics.
```
ahasend stats delivery-time [flags]
```
```
      --from-time string           Start time (RFC3339, or relative like '7d' or '24h' for 7 days or 24 hours ago; empty leaves it to the API) (default "7d")
      --group-by string            Group results by: hour, day, week or month (default "day")
      --recipient-domain strings   Filter by recipient domain (can be used multiple times)
      --sender-domain strings      Filter by sender domain (can be used multiple times)
      --tag strings                Filter by message tag, none with a comma (can be used multiple times)
      --to-time string             End time (RFC3339, or relative like '1d' for 1 day ago; empty leaves it to the API, which uses now)
```

### `stats emails`
View email counts of any period in the account's history, for the whole
```
ahasend stats emails [flags]
```
```
      --breakdown string        Break the counts down by: domain
      --from-time string        Start time, included (RFC3339, or relative like '90d' for 90 days ago; without it, the API starts 30 days before the end)
      --group-by string         Group results by: hour, day, week or month (without it, the API groups by day)
      --sender-domain strings   Count only this domain of the account (can be used multiple times)
      --to-time string          End time, excluded (RFC3339, or relative like '1d' for 1 day ago; without it, the API ends the range now)
```

## `subaccounts`
Manage sub-accounts under your AhaSend parent account, including listing
```
ahasend subaccounts [flags]
```

### `subaccounts api-keys`
Manage API keys that belong to a specific sub-account.
```
ahasend subaccounts api-keys [flags]
```

### `subaccounts api-keys create`
Create an API key that belongs to a specific sub-account with the given
```
ahasend subaccounts api-keys create <sub-account-id> --label <label> --scope <scope> [flags]
```
```
      --idempotency-key string   Idempotency key for safe retries (generated when omitted)
      --ip-allow-list strings    CIDR block or IP address allowed to use the key (can be used multiple times)
      --label string             Label for the API key (required)
      --scope strings            Scope to grant (required; can be used multiple times)
```

### `subaccounts api-keys delete`
Delete an API key that belongs to a sub-account permanently.
```
ahasend subaccounts api-keys delete <sub-account-id> <key-id> [flags]
```
```
  -f, --force   Skip confirmation prompt
```

### `subaccounts api-keys get`
Get detailed information about a specific API key that belongs to a
```
ahasend subaccounts api-keys get <sub-account-id> <key-id> [flags]
```

### `subaccounts api-keys list`
List all API keys that belong to a specific sub-account with their ID,
```
ahasend subaccounts api-keys list <sub-account-id> [flags]
```
```
      --after string    Return the page after this cursor
      --before string   Return the page before this cursor
      --limit int32     Maximum number of items to return (0-100; 0 uses the API default)
```

### `subaccounts api-keys update`
Update the label, scopes and IP allow list of an API key that belongs to a
```
ahasend subaccounts api-keys update <sub-account-id> <key-id> [flags]
```
```
      --clear-ip-allow-list     Remove the IP allow list so the key works from any IP
      --ip-allow-list strings   New CIDR block or IP address allowed to use the key, replacing the list (can be used multiple times)
      --label string            New label for the API key
      --scope strings           New scope to grant, replacing all scopes (can be used multiple times)
```

### `subaccounts create`
Create a sub-account under your AhaSend parent account.
```
ahasend subaccounts create --name <name> --website <domain> [flags]
```
```
      --idempotency-key string   Idempotency key for safe retries (generated when omitted)
      --monthly-credit int       Monthly credit allocation (0-1000000000)
      --name string              Sub-account name (required)
      --website string           Sub-account website domain, e.g. example.com (required)
```

### `subaccounts delete`
Delete a sub-account under your AhaSend parent account.
```
ahasend subaccounts delete <sub-account-id> [flags]
```
```
  -f, --force   Skip confirmation prompt
```

### `subaccounts get`
Get detailed information about a specific sub-account including its status,
```
ahasend subaccounts get <sub-account-id> [flags]
```

### `subaccounts list`
List all sub-accounts under your AhaSend parent account with their status,
```
ahasend subaccounts list [flags]
```
```
      --after string    Return the page after this cursor
      --before string   Return the page before this cursor
      --limit int32     Maximum number of items to return (0-100; 0 uses the API default)
```

### `subaccounts suspend`
Suspend a sub-account under your AhaSend parent account.
```
ahasend subaccounts suspend <sub-account-id> [flags]
```
```
  -f, --force           Skip confirmation prompt
      --reason string   Reason for the suspension (required)
```

### `subaccounts unpause-domain`
Lift the pause on a domain of a sub-account, so that the domain can send again.
```
ahasend subaccounts unpause-domain <sub-account-id> <domain> [flags]
```

### `subaccounts unsuspend`
Unsuspend a previously suspended sub-account under your AhaSend parent
```
ahasend subaccounts unsuspend <sub-account-id> [flags]
```

### `subaccounts update`
Update a sub-account under your AhaSend parent account.
```
ahasend subaccounts update <sub-account-id> [flags]
```
```
      --monthly-credit int   New monthly credit allocation (0-1000000000)
      --name string          New sub-account name
      --website string       New sub-account website domain, e.g. example.com
```

### `subaccounts usage`
Show usage allocation for the current billing period across the parent
```
ahasend subaccounts usage [flags]
```

## `suppressions`
Manage email suppressions (bounces, complaints, unsubscribes).
```
ahasend suppressions [flags]
```

### `suppressions check`
Check if an email address is suppressed and cannot receive emails.
```
ahasend suppressions check <email> [flags]
```
```
      --domain string   Check suppression for specific domain only
```

### `suppressions create`
Create a suppression entry to prevent sending emails to an address.
```
ahasend suppressions create <email> --expires <time> [flags]
```
```
      --domain string            Suppress the address for this domain only (default: every current domain)
      --expires string           Expiration time (e.g., '30d', '2027-12-31T23:59:59Z') (required)
      --idempotency-key string   Idempotency key for safe retries (generated when omitted)
      --reason string            Suppression reason (up to 255 characters)
```

### `suppressions delete`
Delete the suppressions of an email address so it can receive emails again.
```
ahasend suppressions delete <email> [flags]
```
```
      --domain string   Delete only the suppression for this domain (default: every domain)
  -f, --force           Skip confirmation prompt
```

### `suppressions list`
List suppressed email addresses, with cursor pagination. Filter by email
```
ahasend suppressions list [flags]
```
```
      --after string       Return the page after this cursor
      --before string      Return the page before this cursor
      --domain string      Filter by specific domain
      --email string       Filter by email address
      --from-time string   Filter suppressions created after this time (RFC3339 or relative like '24h', '7d')
      --limit int32        Maximum number of items to return (0-100; 0 uses the API default)
      --to-time string     Filter suppressions created before this time (RFC3339 or relative)
```

### `suppressions wipe`
Delete all suppressions from your account, or from one domain with
```
ahasend suppressions wipe [flags]
```
```
      --domain string   Domain to wipe suppressions for
  -f, --force           Skip confirmation prompt
```

## `templates`
Manage transactional templates, the stored designs that
```
ahasend templates [flags]
```

### `templates create`
Create a transactional template. Its fields go to the template's draft, so
```
ahasend templates create --name <name> [flags]
```
```
      --editor string            Editor of the design: advanced, simple or html
      --from string              Sender email address
      --from-name string         Sender display name (needs --from)
      --html-file string         Path to the HTML
      --idempotency-key string   Idempotency key for safe retries (generated when omitted)
      --markup-file string       Path to the AhaML of a Simple Editor design
      --mjml-file string         Path to the MJML source
      --name string              Template name (required)
      --preheader string         Preview text
      --publish                  Publish the draft once it is written
      --reply-to string          Default reply-to email address (needs --from)
      --subject string           Subject
      --text-file string         Path to the plain text version
```

### `templates delete`
Delete a transactional template. Sends of it fail from then on. Delete asks
```
ahasend templates delete <template-id> [flags]
```
```
  -f, --force   Skip confirmation prompt
```

### `templates draft`
Discard a template's draft: the changes saved in the dashboard or through
```
ahasend templates draft [flags]
```

### `templates draft discard`
Discard a template's unpublished draft and print the template. A template with
```
ahasend templates draft discard <template-id> [flags]
```
```
  -f, --force   Skip confirmation prompt
```

### `templates get`
Get one transactional template as its working copy: the draft while the
```
ahasend templates get <template-id> [flags]
```
```
      --markup      Write only the design's AhaML to stdout, as --markup-file reads it
      --published   Get the published copy, which sends use, instead of the working copy
```

### `templates list`
List the account's transactional templates, newest first, with cursor
```
ahasend templates list [flags]
```
```
      --after string    Return the page after this cursor
      --before string   Return the page before this cursor
      --limit int32     Maximum number of items to return (0-100; 0 uses the API default)
```

### `templates publish`
Publish a template's draft, including changes made in the dashboard, and keep
```
ahasend templates publish <template-id> [flags]
```
```
      --idempotency-key string   Idempotency key for safe retries (generated when omitted)
```

### `templates update`
Partially update a transactional template. Only the flags you set are sent.
```
ahasend templates update <template-id> [flags]
```
```
      --clear-from               Remove the sender and the reply-to
      --clear-reply-to           Remove the reply-to
      --from string              Sender email address
      --from-name string         Sender display name (needs --from)
      --html-file string         Path to the HTML
      --idempotency-key string   Idempotency key for safe retries (generated when omitted)
      --markup-file string       Path to the AhaML of a Simple Editor design
      --mjml-file string         Path to the MJML source
      --name string              New template name
      --preheader string         New preview text (empty clears it)
      --publish                  Publish the draft once it is written
      --regenerate-text          Make the text version again from the HTML
      --reply-to string          New default reply-to email address (the template must have a sender; not with --clear-from)
      --subject string           New subject (empty clears it)
      --text-file string         Path to the plain text version
```

### `templates versions`
List, inspect and restore a template's published versions. Every publish keeps
```
ahasend templates versions [flags]
```

### `templates versions get`
Get one published version of a template with its content.
```
ahasend templates versions get <template-id> <version-id> [flags]
```

### `templates versions list`
List a template's published versions, newest first, without their content.
```
ahasend templates versions list <template-id> [flags]
```

### `templates versions restore`
Restore a published version into the template's draft, replacing the draft.
```
ahasend templates versions restore <template-id> <version-id> [flags]
```
```
  -f, --force                    Skip confirmation prompt
      --idempotency-key string   Idempotency key for safe retries (generated when omitted)
      --publish                  Publish the draft once the version is restored
```

## `webhooks`
Manage your webhook endpoints for receiving real-time event notifications
```
ahasend webhooks [flags]
```

### `webhooks create`
Create a webhook endpoint to receive event notifications from AhaSend,
```
ahasend webhooks create --name <name> --url <url> [flags]
```
```
      --all-contact-events       Select every contact event
      --all-events               Select every event except the contact events
      --domains strings          Domain a scoped webhook is limited to (can be used multiple times)
      --enabled                  Enable the webhook (the API enables it when omitted) (default true)
      --events strings           Event type, such as delivered or message.delivered (can be used multiple times)
      --idempotency-key string   Idempotency key for safe retries (generated when omitted)
      --name string              Webhook name (required)
      --non-interactive          Never prompt; fail when a required flag is missing
      --origins strings          Origin whose contact and suppression events the webhook gets: recipient, api, dashboard or system; every origin when not set (can be used multiple times)
      --scope string             Webhook scope: global or scoped (default "global")
      --url string               Webhook URL (required)
```

### `webhooks delete`
Delete a webhook permanently.
```
ahasend webhooks delete <webhook-id> [flags]
```
```
  -f, --force   Skip confirmation prompt
```

### `webhooks get`
Get detailed information about a specific webhook including its
```
ahasend webhooks get <webhook-id> [flags]
```

### `webhooks list`
List the webhooks in your AhaSend account with their configuration,
```
ahasend webhooks list [flags]
```
```
      --after string     Return the page after this cursor
      --before string    Return the page before this cursor
      --enabled          Filter by enabled (--enabled) or disabled (--enabled=false) state
      --events strings   List only the webhooks with this event on, such as delivered or message.delivered (can be used multiple times)
      --limit int32      Maximum number of items to return (0-100; 0 uses the API default)
```

### `webhooks listen`
Listen for webhook events in real-time over a WebSocket connection.
```
ahasend webhooks listen [flags]
```
```
      --events strings      Show only this event type, such as message.opened or opened (can be used multiple times)
      --forward-to string   Local endpoint to forward events to
      --skip-verify         Skip SSL certificate verification for local endpoints when forwarding events (needs --forward-to)
      --slim-output         Slim down the payload for printing to the console
      --webhook-id string   Use existing webhook instead of creating temporary one
```

### `webhooks trigger`
Trigger webhook events for development and testing purposes.
```
ahasend webhooks trigger <webhook-id> [flags]
```
```
      --all-contact-events   Select every contact event
      --all-events           Select every event except the contact events
      --events strings       Event type to trigger, such as message.delivered or delivered (can be used multiple times)
```

### `webhooks update`
Partially update a webhook. Only the flags you set are sent; other
```
ahasend webhooks update <webhook-id> [flags]
```
```
      --all-contact-events   Select every contact event
      --all-events           Select every event except the contact events
      --all-origins          Get the contact and suppression events of every origin
      --clear-events         Remove every event type
      --domains strings      Domain restriction, replacing all domains (can be used multiple times)
      --enabled              Enable (--enabled) or disable (--enabled=false) the webhook
      --events strings       Event type, such as delivered or message.delivered, replacing all event types (can be used multiple times)
      --name string          New webhook name
      --origins strings      Origin whose contact and suppression events the webhook gets: recipient, api, dashboard or system, replacing all origins (can be used multiple times)
      --scope string         New webhook scope: global or scoped
      --url string           New webhook URL
```