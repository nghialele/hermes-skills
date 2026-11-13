# BGP Anycast & BYOIP

> Use when announcing IPv6 prefixes or anycasting DNS.

Announce prefixes you own, run anycast authoritative nameservers, and reason about which layer should pick "the nearest server". Covers the decision, the announcement chain, node config, and verification.

`1.0.0` · WTFPL · Hermes Agent

**You read this. The agent reads [`SKILL.md`](SKILL.md).** That file is the
actual skill — the trigger, the commands, the pitfalls. This page is the front
door: what it is, how to install it, and what else is in the folder.

## Install

```bash
hermes skills install nghialele/hermes-skills/bgp-anycast-dns
```

Or just copy the folder:

```bash
cp -r skills/bgp-anycast-dns ~/.hermes/skills/bgp-anycast-dns
```

## What's inside

| File | Size | Role |
| --- | --- | --- |
| [`SKILL.md`](SKILL.md) | 12.7 KB | the skill itself — the agent reads this |
| [`references/announcement-chain.md`](references/announcement-chain.md) | 5.6 KB | reference notes the agent loads when it needs the detail |
| [`scripts/verify-prefix.sh`](scripts/verify-prefix.sh) | 2.6 KB | helper scripts the skill runs |
| [`templates/bird2-anycast.conf`](templates/bird2-anycast.conf) | 3.0 KB | templates it fills in |

## Part of

[hermes-skills](https://github.com/nghialele/hermes-skills) — my agent's skill shelf. WTFPL, do what you want;
read it before you run it, because these are instructions for something with a
terminal.
