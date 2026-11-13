---
name: api-integration-design
description: "Use when designing a product on a third-party SaaS API."
version: 1.0.0
author: lelebot
license: WTFPL
metadata:
  hermes:
    tags: [api, integration, product-design, bot, planning]
    related_skills: [superpowers:brainstorming, superpowers:writing-plans, spike]
---

# Designing a product on a third-party SaaS API

For bots, dashboards, CLIs and companions that wrap somebody else's HTTP API. The design
fails on missing facts, not on bad taste: enumerate the real API surface before drawing
anything, then build one capability layer that every surface shares.

## When to Use

- The user wants a bot, dashboard, CLI, MCP server or "companion" on top of somebody else's
  hosted API (a hosting panel, a SaaS, a managed platform).
- The user asks for an integration that must work both with and without an LLM.
- A design depends on credentials, scopes, or "does the API even do this?".
- You are about to hand such a design to a coding agent and want the constraints settled first.

Skip it for a single read-only API call or a script that lives and dies in one session.

## Step 1 — Enumerate the live route index, not the docs site

Marketing pages and doc indexes describe what the vendor *wants* to sell. The route index
describes what exists. Get the index first.

1. Look for a public route index / OpenAPI doc: `/api/v1/docs`, `/api-docs`,
   `/openapi.json`, `/swagger.json`, `/.well-known/openapi`. Many panels serve it with no
   auth and it returns the whole route list as JSON.
2. If a guessed path 404s, do not give up and do not trust the docs index alone — crawl the
   *marketing* page's anchors and follow the ones that name it. The link is usually there
   and usually absent from the docs navigation:
   ```python
   new_tab("https://vendor.com/features/<the-api-feature-page>"); wait_for_load()
   js("""(() => Array.from(document.querySelectorAll('a'))
        .map(a => a.textContent.trim().slice(0,60) + ' -> ' + a.href)
        .filter(s => /api|route|doc|reference|openapi/i.test(s)))()""")
   ```
3. Confirm the base URL and that auth is real with one unauthenticated request. A `401` is a
   good answer: it proves the host resolves and the route exists.
4. Read the index's own `auth` field — it names the exact schemes. Design from that, never
   from the user's paraphrase of it.

## Step 2 — Build the three-column map before designing

| the API covers | the panel covers, the API does not | needs money or secrets |
|---|---|---|
| automatable | explain-and-link only | gate hard or exclude |

Column two is the one that wrecks designs. Panel features with no route cannot be
implemented, only narrated — the product must say "do this in the panel" and deep-link,
never silently fail. Say this out loud to the user early; it usually shrinks the scope in a
way they are happy about.

Also record, per route: whether the mutation is async (poll for state, never blind-retry a
create/delete/pay), whether lists paginate, and whether rate limits are documented at all.
Undocumented limits mean the product enforces its own per-customer budget rather than
discovering the ceiling in production.

## Step 3 — Verify the auth model before accepting it

The user will say "OAuth" when they mean "the customer logs in". Check what the vendor
actually offers.

- **Consumer subscription logins are not available to third parties.** ChatGPT Plus, Claude
  Pro and similar flows use first-party client IDs; a third-party app cannot legitimately
  reuse them and they break without notice. If the design depends on them, say so in one
  line and offer the real path (bring-your-own API key, or the provider's published app
  registration).
- **A scoped API key is the common answer** and it changes the product: keys are per-account,
  shown once, hashed server-side, unrecoverable, and often narrower than the account. Every
  capability must degrade cleanly on a missing scope ("your key lacks `x:write`, here is the
  checkbox") instead of erroring.
- **Never accept a secret pasted into a chat channel or a chat modal.** Link through a
  one-time URL on your own domain, over DM, and burn the token on use.

## Step 4 — Play back what the thing does, not the label the user gave it

"Support bot", "companion", "assistant" are provisional words. Two products wear them and
they have opposite permission models:

- **provider-side agent** — speaks for the vendor, reads many accounts, low write authority
- **customer-side remote** — speaks for one account owner, full authority over their own
  resources, no support obligations

Ask who holds the authority and what the thing does in the user's day, then play it back in
one paragraph. Guessing wrong costs a whole design cycle, and the correction arrives blunt.

When a direct question goes unanswered twice because the user is busy refining scope, take
the obvious default, state it as *your* call in one line ("taking A unless you stop me"), and
keep moving. Do not re-ask a third time.

## Step 5 — One capability layer, every surface

Never write the feature twice because the product has two modes or two chat platforms. One
typed capability per API action, shared by the LLM tool schema, the deterministic UI and any
MCP export. This is what makes "works with and without a model" true by construction instead
of by duplicated effort.

See `references/capability-registry.md` for the shape, the risk classes and the write rule.

## Step 6 — Custody before convenience

If the hosted product stores other people's API keys, the security section is not an
appendix — it is the reason the product is risky. See `references/credential-custody.md`.

## Step 7 — Write the design, then have a builder read it

The design doc and its approval gate belong to `superpowers:brainstorming`; the plan belongs
to `superpowers:writing-plans`. What this skill adds to the handover: a builder check that
reads the doc cold, and a non-negotiable list the implementer cannot trade away —

- no capability bypasses the policy layer, and adapters never call the API directly
- no write executes without a confirmation bound to identity + arguments
- no secret in any log line, error, audit row, model context or channel message
- every capability has a test for the missing-scope path and the confirm-required path
- a fixture-driven fake API server, so the suite runs offline and never touches production

## Pitfalls

- **A docs index is a table of contents, not a capability list.** It will omit the route
  index, the scope names, and every endpoint that matters.
- **Do not assume a UI button has an endpoint.** Vendors ship panel features with no public
  route, and the docs often admit this only in passing.
- **Do not design the write path around the model's judgement.** Make writes structurally
  unexecutable without a human click; then prompt injection in logs, env values or
  documentation can only produce a suggestion.
- **Do not let one mode become a second-class citizen.** If click mode is a fallback, it will
  rot. It is the contract; the model is the convenience layer.
- **Do not put money in chat.** Return a checkout link. Payment and top-up routes are the
  fastest way to turn a bug into a liability.
