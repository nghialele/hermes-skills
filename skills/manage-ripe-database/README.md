# RIPE Database

> Use when reading or changing RIPE Database objects: whois, RPSL, REST API, route6, mntner, reverse DNS, RPKI ROAs.

The RIPE Database is two registries in one public database: the **Internet Number Registry** (who holds which address space and ASNs: `inetnum`, `inet6num`, `aut-num`, `organisation`) and an **Internet Routing Registry** (`route`, `route6`, `as-set`, and policy attributes). Records are written in RPSL, a plain-text attribute format.

`1.0.0` · WTFPL · Hermes Agent

**You read this. The agent reads [`SKILL.md`](SKILL.md).** That file is the
actual skill — the trigger, the commands, the pitfalls. This page is the front
door: what it is, how to install it, and what else is in the folder.

## Install

```bash
hermes skills install nghialele/hermes-skills/manage-ripe-database
```

Or just copy the folder:

```bash
cp -r skills/manage-ripe-database ~/.hermes/skills/manage-ripe-database
```

## What's inside

| File | Size | Role |
| --- | --- | --- |
| [`SKILL.md`](SKILL.md) | 10.6 KB | the skill itself — the agent reads this |
| [`references/objects.md`](references/objects.md) | 11.5 KB | reference notes the agent loads when it needs the detail |
| [`references/rest-api.md`](references/rest-api.md) | 6.6 KB | reference notes the agent loads when it needs the detail |
| [`references/troubleshooting.md`](references/troubleshooting.md) | 7.2 KB | reference notes the agent loads when it needs the detail |
| [`scripts/ripe.py`](scripts/ripe.py) | 14.1 KB | helper scripts the skill runs |
| [`scripts/rpsl.py`](scripts/rpsl.py) | 21.5 KB | helper scripts the skill runs |

## Part of

[hermes-skills](https://github.com/nghialele/hermes-skills) — my agent's skill shelf. WTFPL, do what you want;
read it before you run it, because these are instructions for something with a
terminal.
