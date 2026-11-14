# REST API reference

Base URLs: `https://rest.db.ripe.net` (source `ripe`) and `https://rest-test.db.ripe.net` (source `test`). Client-certificate variants: `https://rest-cert.db.ripe.net`, `https://rest-cert-test.db.ripe.net`. HTTPS is mandatory for writes.

Format: default XML. Send `Accept: application/json` or append `.json`/`.xml`/`.txt` to the path. For writes, `Content-Type` must be `application/xml` or `application/json` — there is no RPSL-body shortcut, so a plain RPSL file has to be wrapped. `scripts/ripe.py` and `scripts/rpsl.py` do the wrapping.

## Contents

- [URI scheme](#uri-scheme)
- [Lookup](#lookup)
- [Search](#search)
- [Write operations](#write-operations)
- [JSON body shape](#json-body-shape)
- [Other endpoints](#other-endpoints)
- [Status codes](#status-codes)
- [Query parameters and flags](#query-parameters-and-flags)

## URI scheme

`/{source}/{objectType}/{key}`

| object type | key form |
| --- | --- |
| `person`, `role` | `nic-hdl`, e.g. `EX1-RIPE` |
| `inetnum` | `start - end`, URL-encoded (`%20-%20`); a prefix works too |
| `inet6num`, `route`, `route6` | prefix (`192.0.2.0/24`); for routes append the origin with no separator (`192.0.2.0/24AS64500`) |
| `aut-num` | `AS64500` |
| everything else | the primary key value |

Keys are case-insensitive. Lookup returns exactly one object and never walks up the hierarchy, so `inetnum/192.0.2.5` finds nothing while `inetnum/192.0.2.0 - 192.0.2.255` works. Use `search` or whois when you do not know the exact range.

## Lookup

```bash
curl -s 'https://rest.db.ripe.net/ripe/mntner/EXAMPLE-MNT?unfiltered'
curl -s -H 'Accept: application/json' 'https://rest.db.ripe.net/ripe/inetnum/192.0.2.0%20-%20192.0.2.255'
curl -s -H 'Accept: text/plain' 'https://rest-test.db.ripe.net/test/person/EX1-TEST?unfiltered'
```

Parameters: `unfiltered` (keep `e-mail:`/`notify:`), `unformatted` (keep original spacing). Both are presence flags.

## Search

`/search?source=ripe&query-string=...` — the whois search over HTTP, returning many objects.

| parameter | meaning |
| --- | --- |
| `query-string` | mandatory search term |
| `source` | repeatable; `ripe`, `test`, or GRS mirrors (`apnic-grs`, `arin-grs`, `afrinic-grs`, `lacnic-grs`, `jpirr-grs`, `radb-grs`) |
| `inverse-attribute` | turns the search into an inverse lookup (`mnt-by`, `org`, `tech-c`, ...) |
| `type-filter` | repeatable object-type restriction |
| `flags` | repeatable query flags, e.g. `no-referenced`, `no-filtering`, `no-irt` |
| `include-tag` / `exclude-tag` | filter on object tags |
| `limit` / `offset` | paging |
| `abuse-contact` | add the abuse contact address to results |
| `resource-holder` | add the holding organisation |
| `roa-check` | validate route objects against RPKI ROAs |

```bash
curl -s 'https://rest.db.ripe.net/search?source=ripe&query-string=EXAMPLE-MNT&type-filter=inetnum&flags=no-referenced'
curl -s 'https://rest.db.ripe.net/search?inverse-attribute=org&type-filter=inetnum&source=ripe&query-string=ORG-EX1-RIPE'
```

Search streams results, so a mid-stream failure still returns 200 with `errormessages` in the body — always check the body, not just the status.

## Write operations

| method | path | effect |
| --- | --- | --- |
| POST | `/{source}/{objectType}` | create; fails 409 if the object exists |
| PUT | `/{source}/{objectType}/{key}` | modify; fails if it does not exist |
| DELETE | `/{source}/{objectType}/{key}?reason=...` | delete |

All accept `?dry-run` (validate, change nothing). POST/PUT accept `?unformatted`.

```bash
curl -s -X POST -u "$RIPE_APIKEY" \
  -H 'Content-Type: application/json' -H 'Accept: application/json' \
  --data @obj.json 'https://rest-test.db.ripe.net/test/inetnum?dry-run'
```

A `PUT` must contain the complete object, not a patch. To modify: fetch unfiltered, edit, PUT the whole thing. `DELETE` needs no body but the stored object must be unreferenced; a referenced object returns 400 with `Object [person] X is referenced from other objects`.

`NO OPERATION`: submitting a PUT whose content equals the stored object (ignoring whitespace) succeeds without a change.

## JSON body shape

```json
{
  "objects": {
    "object": [
      {
        "type": "inetnum",
        "source": {"id": "test"},
        "attributes": {
          "attribute": [
            {"name": "inetnum", "value": "192.0.2.0 - 192.0.2.255"},
            {"name": "netname", "value": "EXAMPLE-NET"},
            {"name": "source", "value": "TEST"}
          ]
        }
      }
    ]
  }
}
```

Repeated attributes appear as multiple entries with the same `name`. Order is preserved as given. Responses add `link`, `primary-key`, `referenced-type` on reference attributes, and `errormessages` with `severity` (`Error`/`Warning`/`Info`) and `args`.

XML is the same tree with `<whois-resources><objects><object type="...">`.

## Other endpoints

| endpoint | use |
| --- | --- |
| `/metadata/sources` | list sources |
| `/metadata/templates/{type}` | authoritative attribute template for an object type |
| `/abuse-contact/{resource}` | abuse address for an IP, range, prefix or ASN |
| `/geolocation?ipkey={ip}` | `geoloc`/`language` data |
| `/{source}/{type}/{key}/versions` | version list |
| `/{source}/{type}/{key}/versions/{n}` | one historical version |

Historical data starts at the object's most recent creation, is unavailable for deleted objects, and cannot be queried for `person`/`role`. Email attributes are always stripped from historical output.

## Status codes

| code | meaning in practice |
| --- | --- |
| 200 | success (check `errormessages` on searches) |
| 400 | bad object type/key, syntax error, business-rule violation, referenced object on delete |
| 401 | missing or wrong credential |
| 403 / 429 | query limit exceeded |
| 404 | no such object |
| 409 | create when it already exists |
| 415 | missing/unsupported `Content-Type` or `Accept` |
| 500 | server error |

## Query parameters and flags

whois flags that matter most, usable with `-h whois.ripe.net` or as `flags=` values:

| flag | effect |
| --- | --- |
| `-r` / `no-referenced` | do not pull in referenced contact objects (use in scripts) |
| `-B` / `no-filtering` | do not filter `e-mail:`/`notify:` |
| `-T type,...` | restrict object types |
| `-i ATTR value` | inverse lookup |
| `-x` | exact match only |
| `-m` / `-M` | one level / all levels more specific |
| `-l` / `-L` | one level / all levels less specific |
| `-b` | abuse contact summary |
| `-c` | irt object for the range |
| `-K` | primary keys only |
| `-s source` | choose sources |

Character set: objects are stored as latin-1. Non-latin-1 characters in a request become `?`, so keep names and addresses ASCII or accept the substitution and re-query to confirm what was stored.
