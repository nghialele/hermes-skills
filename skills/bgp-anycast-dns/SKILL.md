---
name: bgp-anycast-dns
description: "Use when announcing IPv6 prefixes or anycasting DNS."
version: 1.0.0
author: Hermes Agent
license: WTFPL
platforms: [linux, windows, macos]
metadata:
  hermes:
    tags: [bgp, anycast, ipv6, byoip, dns, rpki, bird2, routing, authoritative-dns]
    category: devops
    related_skills: [manage-hetrixtools]
---

# BGP Anycast & BYOIP

Announce prefixes you own, run anycast authoritative nameservers, and reason about which layer should pick "the nearest server". Covers the decision, the announcement chain, node config, and verification.

## When to Use

- Announcing an IPv6 prefix you own (BYOIP) through a VPS provider.
- Building or extending anycast authoritative nameservers.
- Choosing between GeoDNS, an HTTP redirect, and anycast for "nearest server".
- Reviewing a prefix plan, ROA/RPKI state, or an ASN decision.
- Explaining how announcements work to a learner — see **Teaching this user**.

## Core rules

**1. Ownership is not reachability.** A prefix in the RIR is an allocation, a registry promise. The global routing table contains nothing about it. Five gates must all be open: (a) `inet6num` registration, (b) authorization to originate — a `route6` object naming your ASN *and* an RPKI ROA binding prefix→ASN, (c) a BGP session to the provider, (d) the provider's import policy accepting it, (e) everyone else's filters accepting what the provider re-announces. Gates b and d are where plans die; a, c, e are mechanical.

**2. `/48` is the IPv6 announcement unit.** Global filters drop prefixes longer than /48 — the direct analogue of IPv4's /24 floor. A /44 = 16 × /48. Announce either the /44 or its /48s, never both: the more-specific wins traffic and the pair looks like accidental deaggregation.

**3. Your own ASN is the anycast mechanism, not paperwork.** Anycast works because the *same prefix* appears from *multiple locations* under the *same origin AS* — the internet then sees one route with several paths and each network picks its nearest exit. Different origin ASN per site produces different routes and no anycast semantics. A borrowed/provider ASN is fine for a single-node first announcement and dies at the second site.

**4. One prefix per anycast address.** Give `ns1` and `ns2` different /48s, each announced from every site. One /48 behind both names collapses the redundancy the NS set exists for.

**5. Health-checked withdrawal is static-route presence.** The daemon exports what its RIB says is reachable, and a `static` route is always reachable. So the watchdog's whole job is enabling/disabling that static protocol. This is the difference between anycast that fails over and anycast that hides breakage.

**6. Anycast is data-plane only.** Primary/secondary roles, TSIG AXFR, NOTIFY, and serial discipline are unchanged. Do not redesign the control plane because you changed how resolvers reach the edges.

**7. Buy the ASN before buying more address space.** Size the need first: two anycast /48s plus one /48 per BGP node is ~4–6 /48s, which a single /44 already covers. A larger prefix adds hijack surface and registry scrutiny without adding capability. If independence from the current LIR is the real motive, a second prefix *from a different LIR* beats a bigger one from the same.

**8. GeoDNS cannot select nameservers.** The delegation is one NS RRset published as glue at the TLD — it cannot vary per resolver. GeoDNS (Technitium's Split Horizon APP records / Geo Distance app, or ECS) only steers answers *inside* a zone, i.e. which service node a user reaches. Anycast is the only mechanism for the NS layer. These are different problems, not alternatives.

**9. RPKI answers "who may originate this" independently of whois.** An org with no `aut-num` can still have a ROA naming a third party's ASN — that means the space was set up as a borrowed-ASN announcement. The ROA's origin dictates the local-AS of every session; run a different one and the announcement is `Invalid` and silently dropped by validating networks. Query the ROA before answering any question about "what AS is this prefix"; reading the org's objects alone gives the wrong answer.

## Procedure

**Step 0 — Confirm inputs before designing.** Query four things, not one: the `inet6num` (who maintains it), the covering less-specific (who really holds the block — a note naming a reseller is often wrong), the RPKI ROA (`validating_roas[].origin` names the AS that may announce it), and RIPEstat `announced` (whether anyone announces it today). `scripts/verify-prefix.sh <prefix> [ASxxxxx]` does all four. Exact prefix strings, whether the ASN is yours or a third party's, and which providers actually offer BGP sessions all follow from that. Do not design against a guess; one sharp question is cheaper than a wrong plan.

**Step 1 — Inventory tooling.** Check the control host and every target node for: `dig`/`delv`, the routing daemon, `ip`, `ss`, `nft`/`ufw`, `jq`, `tailscale`, `python3`. Confirm `net.ipv6.conf.all.forwarding` and per-node IPv6 egress with a real ping to a public v6 address — provider allocations differ wildly in mask (a /36, a /64, a /112 on the same fleet is normal), so never assume uniform prefixes when scripting.

**Step 2 — ASN.** An RIR registration in your own name, not borrowed. This is the only long-lead item; start it first.

**Step 3 — Authorize the origin.** Create a ROA per announced prefix with `origin = your ASN` and `maxLength` equal to the prefix length, and the matching `route6` object. Confirm the panel reports it published before announcing anything.

**Step 4 — First announcement, one node.** Install the daemon, bind one address out of the /48 to `lo`, add the static route, bring up the session. See **templates/bird2-anycast.conf**.

**Step 5 — Verify from outside.** The announcement is only real if a third party sees it — see **Verification**. Do not accept `show protocols: Established` as proof of a working announcement.

**Step 6 — Second site, same prefix.** This is the moment anycast exists. Two sites is a failover pair, not real anycast — good enough to learn on, not enough to claim robustness. Real multi-site anycast wants three independent origins; count *networks*, not servers, because two nodes behind one upstream are one origin for failure purposes.

**Step 7 — Health-checked withdrawal.** Before anything production points at the anycast address: a watchdog that probes the local service and toggles the static protocol.

**Step 8 — Move the service onto the anycast address.** Point the zone/glue at the anycast IPs last, per node, so a broken node never enters the delegation.

**Step 9 — Third site** when a third BGP-capable provider exists in the right region.

## Verification

Run from a host outside the announced network, or from a node with working egress — never from the node itself.

```bash
# Prefix visible and authorized
# bgp.tools / bgp.he.net: prefix present, origin = your ASN, RPKI = Valid
# 'NotFound' or 'Invalid' means the ROA/route6 is wrong, not that the session is down.

# On the node: session and what is actually exported
birdc show protocols
birdc show route export upstream_v6     # exactly your /48, nothing else

# Reachability of the anycast address from outside
dig +short +norec SOA example.com @<anycast-address>
ping -6 -c3 <anycast-address>
```

Traceroute from several regions should land on different nodes. If every path lands on one node, you have a single origin, not anycast.

## Pitfalls

- **BGP withdraws on session death, not application death.** A node that is alive and peering but no longer answering keeps receiving traffic indefinitely. Anycast without health-checked withdrawal converts an outage into a silent black hole — the exact failure mode unicast exposes through resolver retry.
- **BYOIP does not create transit.** You can only announce a v6 prefix from a node with working v6 upstream; a host with a broken v6 path cannot originate it. Test egress per node rather than trusting the provider's claim. Escape hatch: IPv6 routes can be carried over an **IPv4** BGP session (MP-BGP), so a v4-only-transit node may still originate v6 — ask the provider instead of assuming it is blocked.
- **`blackhole` for the announced /48 is correct and safe.** A locally bound /128 is more specific, so traffic to the service address is still delivered while traffic to unbound addresses in the /48 is dropped locally instead of looping.
- **Do not trust a cited paper's protocol claims.** Widely-circulated material mixes up RFC 2526 "reserved subnet anycast addresses" (a different, essentially unused mechanism) with real anycast, which is an ordinary unicast prefix announced from several places. Verify against the RFC itself before repeating a claim.
- **Prefix-length minimums are per-family.** IPv4's /24 floor and IPv6's /48 floor are separate rules; an argument that a plan is infeasible because it needs a /24 says nothing about a /48 plan.
- **Glue at the registrar overrides the zone.** Removing AAAA records from a zone does nothing while the TLD still publishes AAAA glue — resolvers use the glue. Any v6 withdrawal must be done at the registrar.
- **Replacing a whole listener/ACL list.** Settings that set an endpoint or key list typically *replace* it; add the new entry to the full list or you silently drop the others. Back up the config file first.
- **The ROA belongs to the resource holder in RPKI, not the `inet6num` maintainer.** You may be able to edit the object and still be unable to create or re-point the ROA, because the LIR holds the resource. Confirm the prefix appears in the RIR's RPKI portal before promising a second ROA — this is the gate that stalls prefix plans for weeks.
- **Multiple ROAs for one prefix with different origins coexist.** Adding an own ASN never requires deleting the incumbent's ROA; only the origin you actually announce from validates. State that explicitly, or the owner assumes they must break the existing arrangement to proceed.
- **`ALLOCATED-BY-LIR` means a parent LIR holds the block.** Ask the parent holder to sponsor an ASN before buying one from a reseller — usually faster and cheaper, and when the block was never delegated to the end org, only the parent can touch the ROA.
- **`whois -i` inverse lookups need `-r`.** Without it the filtered output can return the object you queried instead of the inverse result, which reads as "no entries found" and hides a real object.

## Driving a fleet of nodes

Run multi-line inspection as a script piped over stdin, not as an inline quoted command. Inline `ssh host '...'` with nested quotes mangles field extraction and `$var` expansion, and can silently execute locally against the wrong host.

```bash
# write the script to a file, then:
ssh -o BatchMode=yes -o ConnectTimeout=8 root@<ip> 'bash -s' < /path/to/inspect.sh
```

On Windows/MSYS hosts, pass native forward-slash paths (`C:/Users/...`) to native binaries — an MSYS path like `/tmp/x` fails to open. Reach nodes by tailnet IP or MagicDNS name; short names usually have no `~/.ssh/config` entry. Keep `grep -E` patterns free of parentheses when the command is inlined over ssh — the nested quoting breaks and the shell either errors out or silently runs against the wrong host; put anything with `(` or a pipe into the piped script instead.

## State and known-fleet specifics

Node inventory, delegation state, and open risks change weekly — read them from the canonical notes rather than from this skill. The Flowplan pages hold the live report and the BGP/BYOIP plan; re-verify against the nodes before acting. Durable constraints worth re-checking, not assuming: a hidden primary must never enter the public NS set; a provider that does not offer BGP cannot be an anycast edge; count independent upstream networks when claiming site diversity.

## Teaching this user

- Treat cited material as **reference, not doctrine**. When a paper or vendor doc is wrong, say so plainly and name the correct mechanism — this is explicitly wanted.
- Explain the concept before the verdict. This user is learning BGP from scratch and asks for lectures; give the mechanism, then the recommendation, not the recommendation alone.
- Lead with the answer, then the reasoning. Numbered steps for procedures.
- Never present an assumption as a measured fact. Say which claims were run and which were inferred.
- Correct English usage plainly when it appears, without commentary.

## Support files

- **templates/bird2-anycast.conf** — known-good BIRD2 starting point: static /48 to trigger export, upstream session, health-check toggle.
- **references/announcement-chain.md** — the five gates in depth, prefix arithmetic, what to ask a provider before ordering, RPKI/ROA specifics.
- **scripts/verify-prefix.sh** — read-only probe for Step 0: registry objects, candidate parent prefixes, ASNs in the org, announcement state, RPKI origin, /48 breakdown.
