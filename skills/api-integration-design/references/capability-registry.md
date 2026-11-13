# The capability registry

The pattern that makes "works with an LLM" and "works without an LLM" the same product.

## Shape

One typed function per API action. Nothing else may touch the API.

```ts
type Capability = {
  id: string;                       // "app.restart"
  title: string;                    // "Restart an app"
  scope: string;                    // "apps:power"
  risk: 'read' | 'reversible' | 'config' | 'destructive' | 'money';
  params: ZodSchema;                // validated before any network call
  summarise(args): string;          // one line for the confirmation card
  secret?: boolean;                 // arguments never logged or stored
  run(ctx, args): Promise<Result>;
};
```

One definition, three renderings:

1. **MCP / LLM tool schema** — generated from `params` and `title`.
2. **Chat UI** — slash commands, buttons, selects, numbered menus.
3. **Audit and help text** — the same ids and summaries.

A capability added once appears everywhere. A capability that exists only in the LLM path is
a bug, not a feature.

## Risk classes and what each demands

| class | examples | gate |
|---|---|---|
| `read` | list, get, logs, stats, balance | none beyond scope |
| `reversible` | start, stop, restart, snapshot | one click |
| `config` | env patch, domain, subdomain, resize | card showing a diff |
| `destructive` | delete, restore, cancel | card + typed resource name |
| `money` | pay, top-up, upgrade | not in chat at all; deep link |

Anything the API cannot express (no route) stays out of the registry and appears in help as
"do this in the panel" with a link. Silence reads as a bug.

## The write rule

> The model may read anything and may **propose** a write. It may never execute one.

A propose call returns a nonce, not an action. The nonce binds:

- capability id + a hash of the exact arguments
- the identity that is allowed to confirm
- a 120-second expiry, single use

The human clicks. Click mode produces the identical card, minus the model. Consequences worth
stating in the design:

- prompt injection from a log line, env value or doc article can at worst produce a bad
  suggestion the user declines
- the audit log records who clicked, not who generated the text
- there is no "auto-approve writes" switch in v1; if one is ever added it is per-capability
  and defaults off

## Degradation

Missing scope is a first-class outcome, not an exception. Resolve it into: which scope is
missing, which capability needs it, and the exact place to tick it. Fetch the vendor's scope
list at startup (many expose a scopes endpoint) and treat an unknown scope as unknown rather
than guessing.

## Testing the contract

For every capability: the happy path, the missing-scope path, and the confirm-required path.
Run them against a fixture-driven fake of the vendor API so the suite is offline and
production is never the test environment.
