# AhaSend Operations

> Manage AhaSend email: send, domains, webhooks, campaigns.

Drive the AhaSend account through the `ahasend` CLI (v0.5.0). The CLI is the default surface: it wraps API v2, handles retries, idempotency, pagination and output formats. Drop to raw `curl` against `https://api.ahasend.com/v2` only when you need a field the CLI does not expose — see `references/api-v2.md`.

`1.0.0` · WTFPL · Nghia, Hermes Agent

**You read this. The agent reads [`SKILL.md`](SKILL.md).** That file is the
actual skill — the trigger, the commands, the pitfalls. This page is the front
door: what it is, how to install it, and what else is in the folder.

## Install

```bash
hermes skills install nghialele/hermes-skills/ahasend
```

Or just copy the folder:

```bash
cp -r skills/ahasend ~/.hermes/skills/ahasend
```

## What's inside

| File | Size | Role |
| --- | --- | --- |
| [`SKILL.md`](SKILL.md) | 12.1 KB | the skill itself — the agent reads this |
| [`references/api-v2.md`](references/api-v2.md) | 10.9 KB | reference notes the agent loads when it needs the detail |
| [`references/cli-reference.md`](references/cli-reference.md) | 55.7 KB | reference notes the agent loads when it needs the detail |
| [`references/secrets.md`](references/secrets.md) | 5.3 KB | reference notes the agent loads when it needs the detail |

## Part of

[hermes-skills](https://github.com/nghialele/hermes-skills) — my agent's skill shelf. WTFPL, do what you want;
read it before you run it, because these are instructions for something with a
terminal.
