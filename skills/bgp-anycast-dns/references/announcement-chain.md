# The announcement chain

Why "I own the prefix" and "the internet can reach it" are unrelated facts, and what sits between them.

## The five gates

A prefix reaches the global routing table only if all five pass. Any one failure produces the same symptom — nothing is reachable — so diagnose in order rather than guessing.

| # | Gate | Artifact | Failure symptom |
|---|---|---|---|
| 1 | Registration | `inet6num` at the RIR | You cannot create the route object at all |
| 2 | Authorization to originate | `route6` object + RPKI ROA | Prefix appears but is marked **Invalid** and dropped by RPKI-validating networks (Cloudflare, most Tier-1s) |
| 3 | BGP session | TCP/179 to the provider, `Established` | No session state; nothing announced |
| 4 | Provider import policy | Their filters: prefix-length minimum, IRR lookup, RPKI validation, "customers only" | Session is `Established` and you export the route, but nothing appears publicly |
| 5 | Global filters | Everyone downstream of the provider | Provider sees it; the rest of the internet does not |

Gate 4 is the one that burns people: a healthy session proves nothing. The only proof of gates 4–5 is an external looking glass.

## ROA specifics

- `origin` = your ASN (the one you peer with, not the provider's).
- `maxLength` = the length you actually announce. A /48 announcement wants `maxLength = 48`. Setting `maxLength = 44` on a /48 announcement makes the /48 **Invalid**.
- A ROA authorizes an origin. It does **not** make the provider accept or re-announce the prefix — that is gate 4 and it is a commercial relationship, not a cryptographic one.
- `route6` is the paperwork version of the same authorization, used by IRR-based filters. Many automated providers create both from a panel form.

## Prefix arithmetic

| Prefix | /48s | Notes |
|---|---|---|
| /48 | 1 | Longest globally accepted IPv6 announcement |
| /44 | 16 | Comfortable for a personal anycast deployment |
| /40 | 256 | More than this class of work consumes |
| /36 | 4,096 | Registry/ISP territory |

Budget: two anycast addresses (`ns1`, `ns2`) need two /48s; per-node unicast /48s for a pre-anycast stage need one each. Four to six /48s total — a /44 covers it with room to spare.

Provider allocations on one fleet routinely differ (a /36, a /64 and a /112 side by side). Never derive a mask from a neighbour's value; read each node's own `ip -6 addr`.

## What to ask a provider before ordering

1. Do you accept a **/48** from a customer, or is there a minimum? (The deciding factor — a provider that only takes /44s changes the plan.)
2. Whose **ASN** originates — mine or yours? If yours, anycast across providers is impossible.
3. Which **neighbour address, ASN, and password** (if any) do I peer with? IPv6 neighbour, or IPv4-only with MP-BGP?
4. What **ROA `origin` and `maxLength`** do you expect, and do you create the `route6` for me?
5. Does the VPS have **working IPv6 egress** today? (Ask, then test. BYOIP does not create transit.)
6. **Reverse DNS** for the announced prefix — delegated to me, or set by you?
7. Any **fees** for the session or for each announcement?

## Verification that actually proves something

```bash
# External looking glass (bgp.tools, bgp.he.net) — the only proof of gates 4-5
#   prefix present?  origin AS correct?  RPKI status Valid?

# On the node — proves gates 2-3 and that nothing extra is leaking
birdc show protocols                    # Established
birdc show route export <session>       # exactly your prefix

# From outside — proves the anycast address answers
for ip in <anycast-a> <anycast-b>; do
  dig +short +norec SOA <zone> @$ip
  dig +noall +comments A <zone> @$ip | grep -E 'status|flags'   # want NOERROR + aa
done

# Anycast is real only if different regions land on different nodes
traceroute -6 <anycast-address>   # from several vantage points
```

A prefix that shows `NotFound` is an authorization problem (gates 1–2). A prefix that shows `Invalid` is a ROA/`maxLength` problem. A session that is `Established` while the prefix is absent everywhere is gate 4 — the provider is not accepting it.

## Withdrawal and failover

BGP withdraws a route when the session drops. It does **not** notice that your service stopped answering. So the announcement must be tied to a local health signal, or anycast will keep steering traffic into a broken node — worse than unicast, where a resolver times out and retries elsewhere.

The pattern is one line of state: a `static` route for the prefix exists in the RIB while healthy, and is removed when not. In BIRD that is `birdc disable <static-protocol>` / `birdc enable <static-protocol>`. A watchdog probing the local service (e.g. an authoritative SOA query against `127.0.0.1`) toggles it.

Consider BFD for link/session failure detection, but BFD does not replace the application-level check — it detects a dead path, not a dead daemon.

## Layer choice

| Layer | Mechanism | Who decides | Cost |
|---|---|---|---|
| DNS | GeoDNS / ECS | the recursive resolver | own authoritative NS |
| HTTP | redirect server | you, from the real client IP | extra round trip |
| App | instance redirects | you, per request | code changes |
| Network | anycast + BGP | the routers | prefix + ASN + peering |

Lower layer = more transparent, less controllable. The deciding layer is where client identity lives: DNS sees only the recursive resolver's address (the ECS problem), HTTP sees the real client, L3 needs neither. For an authoritative NS serving identical answers from every node, anycast's lack of control is irrelevant — which is why the layer that is wrong for geo-targeting is right for nameservers.
