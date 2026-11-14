# RPSL objects: attributes, status values, examples

Read the section for the object type you are creating or debugging. `mandatory` means the attribute must be present; `generated` means the software sets it and you should leave it out; `conditional` means a business rule decides.

## Contents

- [mntner](#mntner)
- [person and role](#person-and-role)
- [organisation](#organisation)
- [inetnum](#inetnum)
- [inet6num](#inet6num)
- [route and route6](#route-and-route6)
- [aut-num](#aut-num)
- [domain (reverse DNS)](#domain-reverse-dns)
- [Set objects](#set-objects)
- [irt, key-cert, as-block](#irt-key-cert-as-block)
- [Hierarchy and authorisation attributes](#hierarchy-and-authorisation-attributes)

## mntner

```
mntner:         EXAMPLE-MNT          mandatory, primary key
descr:          Example maintainer  optional, multiple
org:            ORG-EX1-RIPE        optional, inverse
admin-c:        EX1-RIPE            mandatory
tech-c:         EX1-RIPE            optional
upd-to:         hostmaster@example.net   mandatory  (failed-auth notifications)
mnt-nfy:        changes@example.net      optional   (successful-update notifications)
auth:           SSO user@example.net     mandatory, multiple
mnt-by:         EXAMPLE-MNT              mandatory  (normally itself)
mnt-ref:        EXAMPLE-MNT              optional
created / last-modified / source         generated / mandatory
```

`auth:` values: `SSO <email>`, `PGPKEY-<keyid>`, `X509-<n>`, `MD5-PW` (deprecated and unusable). Multiple `auth:` values are OR-ed. There is no referential integrity check on `auth:`, so a typo or a deleted `key-cert` locks the maintainer.

Locked out? The reset form at `https://apps.db.ripe.net/db-web-ui/webupdates/` ("reset maintainer") or `ripe-dbm@ripe.net`.

## person and role

```
person:         Jane Example          mandatory, lookup key (not the primary key)
address:        1 Example Street      optional, multiple
phone:          +31 20 000 0000       optional
e-mail:         jane@example.net      mandatory, lookup key
nic-hdl:        AUTO-1                mandatory, primary key
mnt-by:         EXAMPLE-MNT           mandatory
```

```
role:           Example NOC           mandatory
address:        ...
e-mail:         noc@example.net       mandatory
nic-hdl:        AUTO-1
abuse-mailbox:  abuse@example.net     conditional (only on role; disables rate limiting)
mnt-by:         EXAMPLE-MNT
```

- `nic-hdl: AUTO-1` (or `AUTO-1JE`, or `AUTO-1 JE`) lets the server pick the handle; `AUTO` IDs get a `-RIPE` suffix. Reference it as `AUTO-1` within the same update message.
- A chosen handle may use `-RIPE`, a two-letter country code, or no suffix. Deleted handles are never reusable.
- `person` is the only object type that should carry personal data; `role` should be business data only. Prefer role objects as `admin-c`/`tech-c` so staff changes touch one object.

## organisation

```
organisation:   AUTO-1TTR            mandatory, must be AUTO-1 (initials optional)
org-name:       Example Networks BV  mandatory
org-type:       OTHER                mandatory; users may only create OTHER
address:        ...                  mandatory, multiple
country:        NL                   optional, single
e-mail:         info@example.net     mandatory
phone / fax-no                       conditional (business contact)
abuse-c:        EXAMPLE-ABUSE-RIPE   conditional (role with abuse-mailbox)
mnt-ref:        EXAMPLE-MNT          mandatory (who may reference this org)
mnt-by:         EXAMPLE-MNT          mandatory
```

`org-type` values: `IANA`, `RIR`, `NIR`, `LIR`, `WHITEPAGES`, `DIRECT_ASSIGNMENT`, `OTHER`. Only the RIPE NCC sets anything other than `OTHER`. For LIR organisations the object is jointly maintained and most fields are editable only in the LIR Portal.

## inetnum

```
inetnum:        192.0.2.0 - 192.0.2.255   mandatory, primary key (prefix input is converted)
netname:        EXAMPLE-NET               mandatory, lookup key
descr:          Example customer          optional, multiple
country:        NL                        mandatory
org:            ORG-EX1-RIPE              conditional (mandatory for RIPE NCC allocations/assignments)
admin-c:        EX1-RIPE                  mandatory
tech-c:         EX1-RIPE                  mandatory
abuse-c:        EXAMPLE-ABUSE-RIPE        optional (overrides org's abuse contact)
status:         ASSIGNED PA               mandatory
assignment-size: 29                       optional (AGGREGATED-BY-LIR)
geofeed / geoloc / language / prefixlen    optional
mnt-by:         EXAMPLE-MNT               mandatory
mnt-lower:      EXAMPLE-MNT               conditional (authorises child objects)
mnt-routes:     EXAMPLE-MNT               optional (authorises route objects)
mnt-domains:    EXAMPLE-MNT               optional (authorises reverse DNS)
```

Status values for `inetnum`:

| status | meaning |
| --- | --- |
| `ALLOCATED UNSPECIFIED` | RIPE NCC administrative blocks, and some historical member allocations |
| `ALLOCATED PA` | allocation to a member (LIR) |
| `ALLOCATED-ASSIGNED PA` | allocation that is also a single assignment of the same size |
| `SUB-ALLOCATED PA` | part of an allocation handed to another organisation |
| `LIR-PARTITIONED PA` | internal partitioning by a member |
| `ASSIGNED PA` | assignment from an allocation to an end user |
| `ASSIGNED PI` | provider-independent assignment made by the RIPE NCC |
| `ASSIGNED ANYCAST` | anycast assignment (TLD infrastructure) |
| `AGGREGATED-BY-LIR` | one object standing in for many uniform assignments |
| `LEGACY` | pre-RIR space |

The status must fit the parent: `ASSIGNED PA` only under `ALLOCATED PA`, `SUB-ALLOCATED PA` under `ALLOCATED PA`, and so on. Assignments are leaves; allocations may have children.

## inet6num

Same shape as `inetnum` but keyed by prefix (`2001:db8::/32`) and with `assignment-size:` mandatory for `AGGREGATED-BY-LIR` (max 128).

Status values: `ALLOCATED-BY-RIR` (the IPv6 equivalent of the administrative block and member allocation), `ALLOCATED-BY-LIR` (sub-allocation), `AGGREGATED-BY-LIR`, `ASSIGNED`, `ASSIGNED PI`, `ASSIGNED ANYCAST`.

## route and route6

```
route:          192.0.2.0/24         mandatory, primary key (with origin)
descr:          Example customer     optional
origin:         AS64500              mandatory, primary key
pingable:       192.0.2.1            optional (must be inside the prefix)
ping-hdl:       EX1-RIPE             optional
holes:          192.0.2.128/25       optional (not reachable via the aggregate)
mnt-by:         EXAMPLE-MNT          mandatory
mnt-routes:     EXAMPLE-MNT { 192.0.2.0/24^+ }   optional
```

Authorisation for a `route` object comes from **both** sides:

- the address space: `mnt-routes:` on the covering `inet(6)num`, else `mnt-lower:`, else `mnt-by:`;
- the ASN: `mnt-routes:` on the `aut-num`, else its `mnt-by:`.

The RIPE NCC's own maintainer on an allocation does not help you here; you need a credential on a maintainer listed in one of those attributes. `mnt-routes:` values may be narrowed with a prefix list (`{ 192.0.2.0/24^+ }`) or `ANY`; you cannot set `ANY` on every `mnt-routes:` in the same object.

## aut-num

```
aut-num:        AS64500              mandatory, primary key
as-name:        EXAMPLE-AS           mandatory, single word
descr:          Example Networks     optional
org:            ORG-EX1-RIPE         conditional (mandatory when status is ASSIGNED)
admin-c:        EX1-RIPE             mandatory
tech-c:         EX1-RIPE             mandatory
abuse-c:        EXAMPLE-ABUSE-RIPE   optional
mnt-by:         EXAMPLE-MNT          mandatory
import / export / mp-import / mp-export / default    optional (routing policy)
status:         ASSIGNED             generated (ASSIGNED, LEGACY, OTHER)
```

`status` is generated: never set it. `import:`/`export:` references to other ASNs are not counted as references for deletion purposes, so an `aut-num` can be deleted while policy attributes still mention it (maintainers are emailed).

## domain (reverse DNS)

```
domain:         2.0.192.in-addr.arpa        mandatory, primary key
descr:          Example reverse zone
admin-c:        EX1-RIPE                    mandatory
tech-c:         EX1-RIPE                    mandatory
zone-c:         EX1-RIPE                    mandatory
nserver:        ns1.example.net             mandatory, multiple
nserver:        ns2.example.net 192.0.2.53  optional glue
ds-rdata:       64431 5 1 278BF194...       optional (DNSSEC)
mnt-by:         EXAMPLE-MNT                 mandatory
```

- Only reverse zones (`in-addr.arpa`, `ip6.arpa`) and ENUM (`e164.arpa`) live here; forward zones are not in the RIPE Database.
- Non-octet-boundary IPv4 delegations use a dash in the fourth label: `6-25.1.2.10.in-addr.arpa` for `10.2.1.6 - 10.2.1.25` (RFC 2317). `0-255` is not allowed.
- No child or parent `domain` object may already exist for the same reverse space.
- Authorisation comes from `mnt-domains:` on the covering `inet(6)num`, else `mnt-lower:`, else `mnt-by:`.
- Trailing dots in `domain:`/`nserver:` are stripped on storage.

## Set objects

| type | prefix | membership |
| --- | --- | --- |
| `as-set` | `as-` | `members:` ASNs and other sets; `mbrs-by-ref:` for self-registration |
| `route-set` | `rs-` | prefixes, ranges, other sets, ASNs (`AS64500` = routes it originates) |
| `rtr-set` | `rtrs-` | router names, addresses |
| `peering-set` | `prng-` | `peering:` or `mp-peering:` (one of the two, not both) |
| `filter-set` | `fltr-` | `filter:` or `mp-filter:` (one of the two, not both) |

Hierarchical names are colon-separated (`AS64500:AS-EXAMPLE`). Creating an `as-set`, `filter-set` or `peering-set` requires that a parent object exists and that you authenticate against its maintainer. Indirect membership works through `member-of:` on the member object plus a matching `mbrs-by-ref:` maintainer on the set.

## irt, key-cert, as-block

- `irt` (`IRT-NAME`): CSIRT contact, referenced from `inet(6)num` by `mnt-irt:` and inherited down the hierarchy. Needs `auth:`, `address:`, `e-mail:`, `admin-c:`, `tech-c:`. Business data only.
- `key-cert` (`PGP-<hex>` or `X509-<n>`): holds `certif:`; `method:`, `owner:`, `fingerpr:` are generated. For X.509 the key must be `AUTO-1`. Elliptic-curve PGP keys are not supported.
- `as-block`: RIPE NCC only; delegates ASN ranges and gates `aut-num` creation.

## Hierarchy and authorisation attributes

| attribute | on | authorises |
| --- | --- | --- |
| `mnt-by` | everything | create/modify/delete of this object |
| `mnt-lower` | inet(6)num, route(6), sets | creating one-level-more-specific children |
| `mnt-routes` | inet(6)num, aut-num, route(6) | creating `route(6)` objects for that space/ASN |
| `mnt-domains` | inet(6)num | creating reverse `domain` objects for that space |
| `mnt-ref` | mntner, organisation, person, role, irt | adding a reference to this object from another object |
| `mbrs-by-ref` | sets | which maintainers' objects may join via `member-of` |

Resolution order for a child object: the nearest ancestor with the specific attribute wins; if no ancestor has it, `mnt-by` of the parent applies. Values within one object are OR-ed.

Deleting a reference never needs authorisation; adding one does. That asymmetry is why `mnt-ref` matters for organisations.

## Notifications worth setting

- `upd-to:` on the mntner: someone tried to update your objects and failed authorisation.
- `mnt-nfy:` on the mntner: every successful update to anything it protects. Point both at a mailbox you archive; this is the practical audit trail, because REST updates send no acknowledgement email.
- `notify:` on an object: changes to that object specifically.
- `ref-nfy:` on an organisation: references added or removed.
