---
name: manage-ripe-database
description: "Use when reading or changing RIPE Database objects: whois, RPSL, REST API, route6, mntner, reverse DNS, RPKI ROAs."
version: 1.0.0
author: Hermes Agent
license: WTFPL
platforms: [linux, windows, macos]
metadata:
  hermes:
    tags: [ripe, rpsl, whois, rpki, route6, inet6num, maintainer, irr, reverse-dns]
    category: devops
    related_skills: [bgp-anycast-dns]
---

# RIPE Database

The RIPE Database is two registries in one public database: the **Internet Number Registry** (who holds which address space and ASNs: `inetnum`, `inet6num`, `aut-num`, `organisation`) and an **Internet Routing Registry** (`route`, `route6`, `as-set`, and policy attributes). Records are written in RPSL, a plain-text attribute format.

Three things drive almost every task:

1. **Every object is protected by a maintainer.** An object lists `mnt-by: <mntner>`; that `mntner` object holds `auth:` credentials. An update succeeds only if the credential you present matches one `auth:` value of one referenced `mntner` (multiple `mnt-by:` values are a logical OR).
2. **Address space is a hierarchy.** `inetnum`/`inet6num` objects nest from `0/0` and `::/0` down to assignments. `status:` says where an object sits in that hierarchy, and the status must fit its parent. `mnt-lower:`, `mnt-routes:` and `mnt-domains:` hand out authority for children, routes and reverse DNS separately.
3. **Reads are filtered, writes are exact.** Query responses drop `e-mail:`/`notify:` values and mark the object `source: RIPE # Filtered`. Filtered text can never be used to update or delete. Always fetch with `?unfiltered` before editing.

## Ground rules

- **Practise in TEST first.** `rest-test.db.ripe.net` (source `test`) and `whois-test.ripe.net` run the same software, reset nightly, and let you authenticate as any maintainer. Nothing there touches the real database.
- **Fetch unfiltered, then edit.** `?unfiltered` on lookup, `-B` on whois. An update built from filtered output fails on missing attributes or an unrecognised `source:`.
- **Deleting needs an unreferenced object.** Any live reference from another object blocks the delete, and the submitted object must match the stored one (whitespace-insensitive). Check references first with `-i` inverse queries.
- **Never guess at a maintainer you cannot authenticate against.** A wrong `auth:` value locks the `mntner` for everyone; recovering it needs RIPE NCC staff. Changing `mnt-by:` on a `mntner` that only lists itself can lock it out the same way.
- **Do not bulk-harvest person and role objects.** Each returned contact counts against a per-IP daily limit under the Acceptable Use Policy; exceeding it blocks all your queries until midnight UTC, and repeat blocks become permanent. Add `-r` so queries stop pulling in referenced contacts you did not ask for.
- **Wait for propagation.** Updates take up to 10 seconds to appear in queries. The write response body is authoritative; do not immediately re-query and conclude failure.

## Step 1: classify the request

| The user wants | Go to |
| --- | --- |
| "Who owns this IP / ASN / what is this object" | Query recipes |
| "Why is this route not in the IRR / who can create routes" | `references/objects.md`, authorisation section |
| "Set up reverse DNS / add a DS record" | `references/objects.md` (`domain`) |
| "Create or fix objects, script updates" | Change workflow |
| "It failed with ..." | `references/troubleshooting.md` |
| Exact attribute lists, status values, examples | `references/objects.md` |
| Endpoint and parameter detail, JSON shape, error codes | `references/rest-api.md` |

## Query recipes

whois on port 43 (`whois.ripe.net`) is the fastest read path and supports hierarchy and inverse queries the REST search does not. If the `whois` client is missing (`apt-get install -y whois`) or port 43 is blocked, use the REST calls below instead — they answer the same questions. Note that whois flags and the query argument go to the server, so keep `-h whois.ripe.net` before them and quote any query containing spaces.

```bash
whois -h whois.ripe.net 193.0.7.35          # smallest inetnum covering the address
whois -h whois.ripe.net AS3333              # aut-num, plus its as-block
whois -h whois.ripe.net -T route,route6 -i origin AS3333   # routes originated
whois -h whois.ripe.net -m 193.0.0.0/21     # one level more specific
whois -h whois.ripe.net -L 193.0.7.35       # all less specific, including exact
whois -h whois.ripe.net -i mnt-by EXAMPLE-MNT              # everything a maintainer controls
whois -h whois.ripe.net -b 193.0.7.35       # abuse contact for the range
whois -h whois.ripe.net --list-versions 193.0.0.0 - 193.0.7.255
whois -h whois.ripe.net --diff-versions 10:11 193.0.0.0 - 193.0.7.255
```

REST equivalents, better when you need JSON or a script:

```bash
curl -s 'https://rest.db.ripe.net/ripe/inetnum/193.0.0.0%20-%20193.0.7.255?unfiltered'
curl -s -H 'Accept: application/json' 'https://rest.db.ripe.net/ripe/aut-num/AS3333'
curl -s 'https://rest.db.ripe.net/search?source=ripe&query-string=EXAMPLE-MNT&type-filter=inetnum&flags=no-referenced'
curl -s 'https://rest.db.ripe.net/abuse-contact/AS3333'
curl -s 'https://rest.db.ripe.net/ripe/aut-num/AS3333/versions'
```

`scripts/ripe.py` wraps these and prints RPSL instead of XML. If the machine has no route to the RIPE endpoints, the script exits 3 and says so; in that case use `--print-request` to get the exact curl and hand it to the user, or fall back to quoting the query they should run themselves. Never present an unverified lookup as a result.

```bash
python scripts/ripe.py get inetnum "193.0.0.0 - 193.0.7.255" --unfiltered
python scripts/ripe.py search EXAMPLE-MNT --type inetnum --no-referenced
python scripts/ripe.py abuse AS3333
python scripts/ripe.py versions aut-num AS3333
```

`get` is an exact lookup: it never walks up the hierarchy, so `get inetnum 193.0.7.35` returns nothing even though the range exists. For a bare address, an ASN you are not sure about, or any "who owns this" question, use `search` (or whois) and let the server find the covering object.

## Change workflow

Follow this order every time; each step catches a class of failure that is expensive later.

1. **Confirm the object and its maintainer.** Look it up unfiltered and note every `mnt-by:`. If none of them carries an `auth:` you hold, stop and say so rather than attempting the update.
2. **Draft the object and lint it offline.**
   ```bash
   python scripts/rpsl.py template inetnum > obj.txt   # mandatory attributes, values as <placeholders>
   $EDITOR obj.txt                                    # replace every <...> with a real value
   python scripts/rpsl.py check obj.txt                # mandatory, single-value, status, keys
   python scripts/rpsl.py url obj.txt                  # the REST path and method to use
   ```
   `check` fails loudly while placeholders remain, so an unfilled template cannot be sent by accident.
3. **Dry-run against TEST.** `?dry-run` validates without writing, on either environment.
4. **Apply.** POST creates (fails if it exists), PUT modifies (fails if it does not), DELETE removes. Method and operation must agree.
5. **Verify from the response**, then re-query once after a few seconds.

```bash
# preview the exact request without sending it
python scripts/ripe.py create inetnum --file obj.txt --source test --print-request
# validate on TEST, then apply
python scripts/ripe.py create inetnum --file obj.txt --source test --dry-run
python scripts/ripe.py create inetnum --file obj.txt --source test --apply
```

`ripe.py` will not write without `--apply`, `--source` defaults to `test`, and a live write needs `--i-know` on top of `--apply`. If the machine has no route to the RIPE endpoints, use `--print-request` and hand the curl to the user rather than reporting a failure.

## Authentication

Choose the credential to match the update method; they are not interchangeable.

| Method | Works with |
| --- | --- |
| SSO (RIPE NCC Access email in `auth: SSO`) | Webupdates, Syncupdates web form |
| API key | REST API (and scripted Syncupdates) |
| PGP | Email, Syncupdates |
| X.509 / client certificate | Email, Syncupdates, REST over `rest-cert.db.ripe.net` |

For anything scripted, use an API key: create one under **API keys** in Webupdates while signed in to RIPE NCC Access, and make sure your Access email is already an `auth: SSO` value on the maintainer. The key is shown once; it is used as HTTP Basic auth as `base64(keyid:secret)`.

```bash
export RIPE_APIKEY='keyid:secret'      # ripe.py reads this
curl -s -u "$RIPE_APIKEY" 'https://rest.db.ripe.net/ripe/mntner/EXAMPLE-MNT?unfiltered'
```

An authenticated lookup is the only way to see a maintainer's full `auth:` list; unauthenticated queries filter it regardless of flags.

## Object cheat-sheet

| Type | Primary key | Notes |
| --- | --- | --- |
| `mntner` | name | Holds `auth:`; `upd-to:` mandatory; must end in `-mnt` by convention |
| `person` / `role` | `nic-hdl` | First attribute is not the key; `AUTO-1` asks the server to assign one; NIC handles are never reusable |
| `organisation` | `organisation` | Must be `AUTO-1` on create; users may only set `org-type: OTHER` |
| `inetnum` | `start - end` | Prefix input is converted to range notation; `status:` decides the hierarchy |
| `inet6num` | prefix | Canonicalised; `AGGREGATED-BY-LIR` needs `assignment-size:` |
| `route` / `route6` | prefix + `origin` | Needs authorisation from both the address space and the ASN |
| `aut-num` | `ASn` | `status:` is generated, never set by hand |
| `domain` | reverse zone | `in-addr.arpa`/`ip6.arpa`/`e164.arpa`; `nserver:` mandatory |

Full attribute tables, status values and worked examples: `references/objects.md`.

## Getting started from nothing

A `person`/`role` and its `mntner` cannot be created by the normal update methods, because each needs the other to exist for authorisation. New users create that first pair through the startup form at `https://apps.db.ripe.net/db-web-ui/webupdates/create/RIPE/role/self` (TEST: `.../create/TEST/role/self`). Everything after that goes through the normal workflow.

An individual without a contract with the RIPE NCC usually holds PI space or an ASN as a **direct assignment**; the RIPE NCC and a sponsoring LIR keep a `mnt-by:` on those objects, so some attributes (notably `org:` and `sponsoring-org:`) are outside your control. Say which attributes are yours before promising a change.

## When something is refused

Read the error text literally: RIPE returns one message per problem, naming the object, attribute and maintainer. The common ones, with the fix, are in `references/troubleshooting.md`. For anything unresolved, the RIPE Database team is `ripe-dbm@ripe.net` and the working group is `db-wg@ripe.net`.
