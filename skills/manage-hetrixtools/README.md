# HetrixTools Operations

> Investigate uptime, blacklist, maintenance, and fleet.

Use the HetrixTools tools exposed by the Aperture MCP server (`mcp__aperture__hetrixtools_*`) to investigate monitoring data and, only after explicit approval, change monitoring state. This skill is for HetrixTools data; do not use it as a substitute for general server debugging.

`1.0.0` · WTFPL · Nghia, Hermes Agent

**You read this. The agent reads [`SKILL.md`](SKILL.md).** That file is the
actual skill — the trigger, the commands, the pitfalls. This page is the front
door: what it is, how to install it, and what else is in the folder.

## Install

```bash
hermes skills install nghialele/hermes-skills/manage-hetrixtools
```

Or just copy the folder:

```bash
cp -r skills/manage-hetrixtools ~/.hermes/skills/manage-hetrixtools
```

## What's inside

| File | Size | Role |
| --- | --- | --- |
| [`SKILL.md`](SKILL.md) | 5.4 KB | the skill itself — the agent reads this |
| [`references/output-formats.md`](references/output-formats.md) | 1.0 KB | reference notes the agent loads when it needs the detail |
| [`references/tool-map.md`](references/tool-map.md) | 1.6 KB | reference notes the agent loads when it needs the detail |
| [`references/write-recipes.md`](references/write-recipes.md) | 1.5 KB | reference notes the agent loads when it needs the detail |
| [`scripts/timeline.py`](scripts/timeline.py) | 1017 B | helper scripts the skill runs |

## Part of

[hermes-skills](https://github.com/nghialele/hermes-skills) — my agent's skill shelf. WTFPL, do what you want;
read it before you run it, because these are instructions for something with a
terminal.
