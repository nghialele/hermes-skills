# hermes-skills

My agent's skill shelf: markdown files that teach an AI agent the things I got
tired of re-explaining — how to drive AhaSend, how to announce an IPv6 prefix
without breaking the internet, how to read a HetrixTools incident.

![license: WTFPL](https://img.shields.io/badge/license-WTFPL-brightgreen)
![made for: Hermes Agent](https://img.shields.io/badge/made%20for-Hermes%20Agent-blueviolet)

A skill is a folder with a `SKILL.md` in it: a description of *when* to use it,
then the actual instructions. No SDK, no build step, no runtime. The agent reads
it when the task matches and follows it like a competent colleague who has done
this before.

## Grab one

**Subscribe to the shelf** (Hermes Agent lists it as a skill source):

```bash
hermes skills tap add nghialele/hermes-skills
hermes skills search bgp        # once skills.sh has indexed the repo
```

**Just one skill** — the three-part identifier always works, tap or not:

```bash
hermes skills install nghialele/hermes-skills/bgp-anycast-dns
```

**Or copy it, it's a folder:**

```bash
git clone https://github.com/nghialele/hermes-skills
cp -r hermes-skills/skills/bgp-anycast-dns ~/.hermes/skills/bgp-anycast-dns
# Claude Code, Codex, and anything else on the ~/.agents/skills convention:
cp -r hermes-skills/skills/bgp-anycast-dns ~/.agents/skills/bgp-anycast-dns
```

Nothing here is Hermes-only except the `metadata.hermes` block, which other
agents ignore without complaining.

## The shelf

Click any name — every folder has its own README with the install line, the file
map, and the one-line version of what the agent will do with it. Those pages are
generated from `SKILL.md`, not hand-written, so they can't quietly disagree with
the skill they describe.

<!-- SKILLS:START -->
| Skill | What it does | v |
| --- | --- | --- |
| [`ahasend`](skills/ahasend/) | Manage AhaSend email: send, domains, webhooks, campaigns. | 1.0.0 |
| [`api-integration-design`](skills/api-integration-design/) | Use when designing a product on a third-party SaaS API. | 1.0.0 |
| [`bgp-anycast-dns`](skills/bgp-anycast-dns/) | Use when announcing IPv6 prefixes or anycasting DNS. | 1.0.0 |
| [`content-repurposer`](skills/content-repurposer/) | Repurpose long-form content (blog posts, articles, YouTube transcripts) into multiple formats automatically … | 1.0.0 |
| [`manage-hetrixtools`](skills/manage-hetrixtools/) | Investigate uptime, blacklist, maintenance, and fleet. | 1.0.0 |
| [`manage-ripe-database`](skills/manage-ripe-database/) | Use when reading or changing RIPE Database objects: whois, RPSL, REST API, route6, mntner, reverse DNS, RPKI ROAs. | 1.0.0 |

*6 skills, indexed by `scripts/build_index.py`. Every skill folder has its own README; CI fails if any of them drifts from `skills/`.*
<!-- SKILLS:END -->

## Living elsewhere

Bigger ones outgrew this shelf and got their own repo:

| Skill | Repo | What it does |
| --- | --- | --- |
| `jcode` | [hermes-jcode](https://github.com/nghialele/hermes-jcode) | Drive the jcode coding agent: one-shot runs, provider/model selection, install and auth status. Ships a plugin with tools, not just instructions. |
| `flowplan-mcp` | [hermes-flowplan](https://github.com/nghialele/hermes-flowplan) | Read and change Flowplan through MCP — pages, databases, records, tasks. |

## How these are written

Same house style in every file, because it's what survives contact with a real
model:

- **The description is the trigger**, not a summary — `Use when …`, with the
  words someone would actually type.
- **Answer first, mechanism second.** The command, then why it works.
- **Pitfalls come from things that actually bit me.** The `-C` vs
  `--remote-working-dir` mixup, the MCP server that silently never loads, the
  flag that was removed two versions ago.
- **Verify, don't vibe.** Every skill ends with how the agent proves it worked.

## Adding one

```bash
mkdir -p skills/my-new-skill
$EDITOR skills/my-new-skill/SKILL.md     # frontmatter: name, description, version, license
python scripts/build_index.py            # refreshes the table above + skills.json
python scripts/build_index.py --lint     # name matches the folder, description present
```

CI runs both, so the table can't quietly go stale. That is the entire
maintenance burden: a script that yells at you.

## License

WTFPL. Do what the fuck you want with these — fork, remix, sell, feed them to
your own agent, print them out and frame them. I genuinely do not care. See
[LICENSE](LICENSE).

**One bit of fine print I do care about:** a skill is a set of instructions for
something with a terminal. Read what you install before you install it, mine
included. The WTFPL covers my code, not your blast radius.
