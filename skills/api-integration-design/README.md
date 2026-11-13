# Designing a product on a third-party SaaS API

> Use when designing a product on a third-party SaaS API.

For bots, dashboards, CLIs and companions that wrap somebody else's HTTP API. The design fails on missing facts, not on bad taste: enumerate the real API surface before drawing anything, then build one capability layer that every surface shares.

`1.0.0` · WTFPL · lelebot

**You read this. The agent reads [`SKILL.md`](SKILL.md).** That file is the
actual skill — the trigger, the commands, the pitfalls. This page is the front
door: what it is, how to install it, and what else is in the folder.

## Install

```bash
hermes skills install nghialele/hermes-skills/api-integration-design
```

Or just copy the folder:

```bash
cp -r skills/api-integration-design ~/.hermes/skills/api-integration-design
```

## What's inside

| File | Size | Role |
| --- | --- | --- |
| [`SKILL.md`](SKILL.md) | 7.1 KB | the skill itself — the agent reads this |
| [`references/capability-registry.md`](references/capability-registry.md) | 2.9 KB | reference notes the agent loads when it needs the detail |
| [`references/credential-custody.md`](references/credential-custody.md) | 2.4 KB | reference notes the agent loads when it needs the detail |

## Part of

[hermes-skills](https://github.com/nghialele/hermes-skills) — my agent's skill shelf. WTFPL, do what you want;
read it before you run it, because these are instructions for something with a
terminal.
