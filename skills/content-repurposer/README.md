# Content Repurposer — One Source → Multiple Platforms

> Repurpose long-form content (blog posts, articles, YouTube transcripts) into multiple formats automatically — Twitter/X threads, LinkedIn posts, email newsletters, Instagram captions, and short-form summaries. Use when converting blog posts to social media, creating multi-platform content from a single source, generating tweet threads from articles, writing newsletters from blog content, or building a content distribution pipeline.

Turn any long-form content into platform-optimized posts for Twitter/X, LinkedIn, email, and more.

`1.0.0` · WTFPL · Nghia

**You read this. The agent reads [`SKILL.md`](SKILL.md).** That file is the
actual skill — the trigger, the commands, the pitfalls. This page is the front
door: what it is, how to install it, and what else is in the folder.

## Install

```bash
hermes skills install nghialele/hermes-skills/content-repurposer
```

Or just copy the folder:

```bash
cp -r skills/content-repurposer ~/.hermes/skills/content-repurposer
```

## What's inside

| File | Size | Role |
| --- | --- | --- |
| [`SKILL.md`](SKILL.md) | 2.9 KB | the skill itself — the agent reads this |
| [`references/platform-guides.md`](references/platform-guides.md) | 1.6 KB | reference notes the agent loads when it needs the detail |
| [`scripts/config.json`](scripts/config.json) | 107 B | helper scripts the skill runs |
| [`scripts/repurpose.js`](scripts/repurpose.js) | 6.6 KB | helper scripts the skill runs |
| [`skill-card.md`](skill-card.md) | 2.1 KB | supporting file |

## Part of

[hermes-skills](https://github.com/nghialele/hermes-skills) — my agent's skill shelf. WTFPL, do what you want;
read it before you run it, because these are instructions for something with a
terminal.
