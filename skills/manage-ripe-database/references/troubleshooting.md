# Troubleshooting the RIPE Database

Read the error literally: RIPE names the object, the attribute and the maintainer it used. Most refusals are one of the cases below.

## Contents

- [whois error codes](#whois-error-codes)
- [Authorisation failures](#authorisation-failures)
- [Reference and integrity errors](#reference-and-integrity-errors)
- [Syntax and business-rule errors](#syntax-and-business-rule-errors)
- [Hierarchy and status errors](#hierarchy-and-status-errors)
- [REST/HTTP errors](#resthttp-errors)
- [When the maintainer is locked](#when-the-maintainer-is-locked)

## whois error codes

| Message | Meaning |
| --- | --- |
| `%ERROR:101: no entries found` | Nothing matched. Try a broader key, `-L`, or check the source |
| `%ERROR:102: unknown object type` | Typo in `-T` or the key form |
| `%ERROR:103: unknown source` | Source not `RIPE`/`TEST` |
| `%ERROR:106: no search key specified` | Empty query |
| `%ERROR:201: access denied` | Rate limit or personal-data quota exceeded; see Access to Personal Data |
| `%ERROR:202: access control limit reached` | Too many person/role objects returned today |
| `%ERROR:203: address passing not allowed` | `-V` proxy flag used without approval |

## Authorisation failures

> `Authorisation for [inetnum] 192.0.2.0 - 192.0.2.255 failed using "mnt-by:" not authenticated by: EXAMPLE-MNT`

1. Identify every `mnt-by:` on the object and every `auth:` inside each of those maintainers.
2. Check the **method/credential combination**: SSO works only on Webupdates and the Syncupdates web form; API keys work on the REST API and scripted Syncupdates; PGP works on email and Syncupdates; X.509 works on email, Syncupdates, and REST only over the `rest-cert` endpoints.
3. A key that works for reads still needs the maintainer to list your SSO email in `auth:`.
4. For `route`/`route6`, the failing attribute is often `mnt-routes:` on the covering `inetnum` or on the `aut-num`, not the route's own `mnt-by:`.

> `not authenticated by: UNFOUND`

The `auth:` value points at a `key-cert` or SSO account that does not resolve. For PGP, the `key-cert` object is missing or was deleted.

## Reference and integrity errors

> `Unknown object referenced: ORG-EX1-RIPE`

The referenced `mntner`, `person`, `role`, `organisation`, `irt` or `key-cert` does not exist in that source. Create objects bottom-up: organisation → role/person → mntner → resources.

> `Object [person] EX1-RIPE is referenced from other objects`

Deletion blocked. Find the references before deleting:

```bash
whois -h whois.ripe.net -i admin-c EX1-RIPE
whois -h whois.ripe.net -i tech-c  EX1-RIPE
whois -h whois.ripe.net -i zone-c  EX1-RIPE
whois -h whois.ripe.net -i mnt-by  EXAMPLE-MNT
whois -h whois.ripe.net -i abuse-c EX1-RIPE
```

Note `-i mnt-by` finds objects the maintainer protects; you must remove or repoint those `mnt-by:` values before the maintainer can be deleted.

> `Object [mntner] EXAMPLE-MNT is referenced from other objects`

Same for maintainers: any object with `mnt-by: EXAMPLE-MNT` blocks deletion. `mnt-lower:`, `mnt-routes:`, `mnt-domains:` and `mnt-ref:` references also count.

> Adding a reference is refused

Adding a reference to an `organisation`, `person`, `role`, `mntner` or `irt` requires authorisation through that object's `mnt-ref:`. Removing a reference never does. If you cannot add `org:` to your object, the organisation owner must add your maintainer to `mnt-ref:` first.

## Syntax and business-rule errors

> `Syntax error in inetnum` / `Invalid address format`

`inetnum` takes `start - end` in dotted quad or a prefix (converted for you). `inet6num`, `route6` take prefixes only. `route` takes an IPv4 prefix only. Check for a stray space, a trailing dot on a prefix, or IPv6 in an IPv4 field.

> `Attribute not allowed: xyz` / `Mandatory attribute missing: country`

Your object type does not accept that attribute, or a mandatory one is absent. Run `python scripts/rpsl.py check obj.txt` and compare with `python scripts/rpsl.py template <type>`.

> `Duplicate attribute: source` / a single-valued attribute repeated

`source`, `netname`, `status`, `org` (on inetnum/aut-num), `nic-hdl`, `as-name` and similar are single-valued. Repeated `descr:`, `remarks:`, `admin-c:`, `mnt-by:`, `auth:` are fine.

> `Status ... not allowed for this object` / `status not valid for parent`

The status must fit the parent object: `ASSIGNED PA` only under `ALLOCATED PA`, `SUB-ALLOCATED PA` under `ALLOCATED PA`, `ASSIGNED` under `ALLOCATED-BY-RIR`/`ALLOCATED-BY-LIR`. `LEGACY` only for legacy space. Check the covering object with `whois -h whois.ripe.net -L <address>`.

> `inetnum object ... overlaps with ...` / `cannot have parent or child`

`inetnum`/`inet6num` objects may not overlap with the same status, and an assignment cannot have children. Find the conflicting object with `-x` (exact) and `-m`/`-M` (more specific).

> `"AUTO-1" is not valid for this object type`

Only `person`, `role`, `organisation` and X.509 `key-cert` accept `AUTO-n`. Everything else needs a literal key.

> `Only the RIPE NCC can ...`

`org:`, `sponsoring-org:`, `country:` on some objects, `org-type` other than `OTHER`, `as-block`, and any RIPE NCC maintainer are outside your control. Do not try to work around it; the object is jointly maintained.

## REST/HTTP errors

| Status | Usual cause |
| --- | --- |
| 400 | Bad key or object type; business-rule violation; also returned when deleting a referenced object |
| 401 | No or wrong credential; also an SSO-only maintainer used over REST |
| 403/429 | Query limit exceeded; back off and add `-r`/`no-referenced` |
| 404 | Lookup is exact — the range does not exist even if a covering object does |
| 409 | POST for an object that already exists (use PUT), or a key conflict |
| 415 | Missing `Content-Type`/`Accept`; REST writes need `application/json` or `application/xml` |

A `200` from `/search` can still contain `errormessages`: results are streamed, so a mid-stream error does not change the status code.

`?dry-run` on POST/PUT/DELETE validates the whole request, including authorisation, without writing. Use it before every real change.

## When the maintainer is locked

Symptoms: every update fails authorisation; `auth:` references a key-cert that no longer exists; the only `auth:` value was your own credential and you removed it.

- Self-lock via a bad `auth:` is unrecoverable by API by design. Contact `ripe-dbm@ripe.net` with the maintainer name and proof of control.
- If a colleague holds a credential on the same maintainer, they can restore yours.
- Prevention: keep at least two `auth:` values from different methods, and never edit `auth:` and `mnt-by:` in the same PUT.

## Waiting for changes to appear

Updates take up to 10 seconds to show in queries (3–5 s typical for hierarchical objects, under 1 s for person/role/organisation). Trust the write response body, which is the stored object, rather than an immediate re-query.

## Query blocks

Hitting the personal-data quota blocks *all* queries from your IP until midnight UTC, not just contact lookups. Repeated blocks become permanent and are only lifted by request to `ripe-dbm@ripe.net`. In scripts, always pass `-r` (whois) or `flags=no-referenced` (REST search), and cache results instead of re-querying in a loop.
