#!/usr/bin/env python3
"""Offline RPSL helper: templates, linting, REST URL/body construction.

No network access. Commands:
  template TYPE              print a skeleton object with mandatory attributes
  check FILE                 lint one object (exit 1 on errors)
  url FILE [--exists]        print the REST method and URL for the object
  json FILE                  print the JSON request body for POST/PUT
"""

import argparse
import json
import re
import sys
from urllib.parse import quote

ATTR_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9_-]*):(?:\s*(.*))?$")

# mandatory / single-valued / optional / primary-key attributes per type
TEMPLATES = {
    "mntner": {
        "mandatory": ["mntner", "admin-c", "upd-to", "auth", "mnt-by", "source"],
        "single": ["mntner", "source"],
        "optional": ["descr", "org", "tech-c", "mnt-nfy", "remarks", "notify", "mnt-ref"],
        "key": ["mntner"],
        "notes": {
            "mntner": "must be unique; ends in -mnt by convention",
            "admin-c": "NIC handle of a person or role object",
            "upd-to": "email notified when an update fails authorisation",
            "auth": "SSO <email> | PGPKEY-<id> | X509-<n>",
            "mnt-by": "normally this same mntner",
        },
    },
    "person": {
        "mandatory": ["person", "e-mail", "nic-hdl", "mnt-by", "source"],
        "single": ["nic-hdl", "source"],
        "optional": ["address", "phone", "fax-no", "contact", "org", "remarks", "notify", "mnt-ref"],
        "key": ["nic-hdl"],
        "notes": {
            "person": "full name, at least two words",
            "nic-hdl": "AUTO-1 lets the server assign one",
            "mnt-by": "an existing maintainer you can authenticate against",
        },
    },
    "role": {
        "mandatory": ["role", "e-mail", "nic-hdl", "mnt-by", "source"],
        "single": ["nic-hdl", "source"],
        "optional": ["address", "phone", "fax-no", "contact", "org", "admin-c", "tech-c",
                     "remarks", "notify", "abuse-mailbox", "mnt-ref"],
        "key": ["nic-hdl"],
        "notes": {
            "role": "business function, not a person's name",
            "abuse-mailbox": "only meaningful on role objects; disables query rate limiting",
        },
    },
    "organisation": {
        "mandatory": ["organisation", "org-name", "org-type", "address", "e-mail", "mnt-ref",
                      "mnt-by", "source"],
        "single": ["organisation", "org-name", "org-type", "country", "source"],
        "optional": ["descr", "remarks", "phone", "fax-no", "contact", "geoloc", "language",
                     "reg-nr", "org", "admin-c", "tech-c", "abuse-c", "ref-nfy", "notify"],
        "key": ["organisation"],
        "notes": {
            "organisation": "must be AUTO-1 on create; the server assigns the ID",
            "org-type": "users may only create OTHER",
            "mnt-ref": "who may reference this organisation from other objects",
        },
    },
    "inetnum": {
        "mandatory": ["inetnum", "netname", "country", "admin-c", "tech-c", "status", "mnt-by", "source"],
        "single": ["inetnum", "netname", "org", "status", "assignment-size", "geofeed",
                   "geoloc", "prefixlen", "sponsoring-org", "source"],
        "optional": ["descr", "abuse-c", "remarks", "notify", "mnt-lower", "mnt-routes",
                     "mnt-domains", "mnt-irt", "language"],
        "key": ["inetnum"],
        "notes": {
            "inetnum": "start - end in dotted quad, or a prefix (converted for you)",
            "netname": "letters, digits, underscore, hyphen; starts with a letter",
            "status": "ASSIGNED PA | ALLOCATED PA | SUB-ALLOCATED PA | LIR-PARTITIONED PA | "
                      "ASSIGNED PI | ASSIGNED ANYCAST | AGGREGATED-BY-LIR | LEGACY | "
                      "ALLOCATED UNSPECIFIED | ALLOCATED-ASSIGNED PA",
        },
    },
    "inet6num": {
        "mandatory": ["inet6num", "netname", "country", "admin-c", "tech-c", "status", "mnt-by", "source"],
        "single": ["inet6num", "netname", "org", "status", "assignment-size", "geofeed",
                   "geoloc", "prefixlen", "sponsoring-org", "source"],
        "optional": ["descr", "abuse-c", "remarks", "notify", "mnt-lower", "mnt-routes",
                     "mnt-domains", "mnt-irt", "language"],
        "key": ["inet6num"],
        "notes": {
            "inet6num": "prefix notation only, e.g. 2001:db8:1234::/48",
            "status": "ASSIGNED | ALLOCATED-BY-RIR | ALLOCATED-BY-LIR | AGGREGATED-BY-LIR | "
                      "ASSIGNED PI | ASSIGNED ANYCAST",
            "assignment-size": "required for AGGREGATED-BY-LIR",
        },
    },
    "route": {
        "mandatory": ["route", "origin", "mnt-by", "source"],
        "single": ["route", "origin", "aggr-mtd", "aggr-bndry", "export-comps", "components", "source"],
        "optional": ["descr", "pingable", "ping-hdl", "holes", "org", "member-of", "inject",
                     "remarks", "notify", "mnt-lower", "mnt-routes"],
        "key": ["route", "origin"],
        "notes": {
            "route": "IPv4 prefix only, e.g. 192.0.2.0/24",
            "origin": "ASn that originates the route",
            "mnt-by": "needs a maintainer that also authorises routes for the address space",
        },
    },
    "route6": {
        "mandatory": ["route6", "origin", "mnt-by", "source"],
        "single": ["route6", "origin", "aggr-mtd", "aggr-bndry", "export-comps", "components", "source"],
        "optional": ["descr", "pingable", "ping-hdl", "holes", "org", "member-of", "inject",
                     "remarks", "notify", "mnt-lower", "mnt-routes"],
        "key": ["route6", "origin"],
        "notes": {"route6": "IPv6 prefix only, e.g. 2001:db8::/32"},
    },
    "aut-num": {
        "mandatory": ["aut-num", "as-name", "admin-c", "tech-c", "mnt-by", "source"],
        "single": ["aut-num", "as-name", "org", "abuse-c", "status", "source"],
        "optional": ["descr", "member-of", "import-via", "import", "mp-import", "export-via",
                     "export", "mp-export", "default", "mp-default", "remarks", "notify"],
        "key": ["aut-num"],
        "notes": {
            "aut-num": "ASn, no leading zeroes",
            "as-name": "single word of letters, digits, - and _",
            "status": "generated by the server; do not set it",
        },
    },
    "domain": {
        "mandatory": ["domain", "admin-c", "tech-c", "zone-c", "nserver", "mnt-by", "source"],
        "single": ["domain", "source"],
        "optional": ["descr", "org", "ds-rdata", "remarks", "notify"],
        "key": ["domain"],
        "notes": {
            "domain": "reverse zone: x.in-addr.arpa, x.ip6.arpa, or e164.arpa",
            "nserver": "nameserver name, optional glue address after it",
            "ds-rdata": "key tag, algorithm, digest type, digest",
        },
    },
    "as-set": {
        "mandatory": ["as-set", "tech-c", "admin-c", "mnt-by", "source"],
        "single": ["as-set", "source"],
        "optional": ["descr", "members", "mbrs-by-ref", "remarks", "org", "notify", "mnt-lower"],
        "key": ["as-set"],
        "notes": {"as-set": "starts with as-; hierarchical with colons"},
    },
    "route-set": {
        "mandatory": ["route-set", "tech-c", "admin-c", "mnt-by", "source"],
        "single": ["route-set", "source"],
        "optional": ["descr", "members", "mp-members", "mbrs-by-ref", "remarks", "org",
                     "notify", "mnt-lower"],
        "key": ["route-set"],
        "notes": {"route-set": "starts with rs-"},
    },
    "rtr-set": {
        "mandatory": ["rtr-set", "tech-c", "admin-c", "mnt-by", "source"],
        "single": ["rtr-set", "source"],
        "optional": ["descr", "members", "mp-members", "mbrs-by-ref", "remarks", "org",
                     "notify", "mnt-lower"],
        "key": ["rtr-set"],
        "notes": {"rtr-set": "starts with rtrs-"},
    },
    "peering-set": {
        "mandatory": ["peering-set", "tech-c", "admin-c", "mnt-by", "source"],
        "single": ["peering-set", "source"],
        "optional": ["descr", "peering", "mp-peering", "remarks", "org", "notify", "mnt-lower"],
        "key": ["peering-set"],
        "notes": {"peering-set": "starts with prng-; needs peering: or mp-peering:, not both"},
    },
    "filter-set": {
        "mandatory": ["filter-set", "tech-c", "admin-c", "mnt-by", "source"],
        "single": ["filter-set", "source"],
        "optional": ["descr", "filter", "mp-filter", "remarks", "org", "notify", "mnt-lower"],
        "key": ["filter-set"],
        "notes": {"filter-set": "starts with fltr-; needs filter: or mp-filter:, not both"},
    },
    "irt": {
        "mandatory": ["irt", "address", "e-mail", "admin-c", "tech-c", "auth", "mnt-by", "source"],
        "single": ["irt", "source"],
        "optional": ["phone", "fax-no", "contact", "signature", "encryption", "org", "remarks",
                     "irt-nfy", "notify", "mnt-ref"],
        "key": ["irt"],
        "notes": {"irt": "starts with IRT-; business contact data only"},
    },
    "key-cert": {
        "mandatory": ["key-cert", "certif", "mnt-by", "source"],
        "single": ["key-cert", "method", "fingerpr", "source"],
        "optional": ["owner", "org", "remarks", "notify", "admin-c", "tech-c"],
        "key": ["key-cert"],
        "notes": {"key-cert": "PGP-<hex> or AUTO-1 for X.509", "certif": "ASCII-armoured key"},
    },
}

TYPE_OF_FIRST_ATTR = {
    "mntner": "mntner", "person": "person", "role": "role", "organisation": "organisation",
    "inetnum": "inetnum", "inet6num": "inet6num", "route": "route", "route6": "route6",
    "aut-num": "aut-num", "domain": "domain", "as-set": "as-set", "route-set": "route-set",
    "rtr-set": "rtr-set", "peering-set": "peering-set", "filter-set": "filter-set",
    "irt": "irt", "key-cert": "key-cert", "as-block": "as-block", "inet-rtr": "inet-rtr",
}

# attributes the server generates; presence in an update is at best ignored
GENERATED = {"created", "last-modified"}
GENERATED_BY_TYPE = {"aut-num": {"status"}}
GENERATED_SOFT = {"method", "owner", "fingerpr"}

STATUS_VALUES = {
    "inetnum": {
        "ALLOCATED UNSPECIFIED", "ALLOCATED PA", "ALLOCATED-ASSIGNED PA", "SUB-ALLOCATED PA",
        "LIR-PARTITIONED PA", "ASSIGNED PA", "ASSIGNED PI", "ASSIGNED ANYCAST",
        "AGGREGATED-BY-LIR", "LEGACY",
    },
    "inet6num": {
        "ALLOCATED-BY-RIR", "ALLOCATED-BY-LIR", "AGGREGATED-BY-LIR", "ASSIGNED",
        "ASSIGNED PI", "ASSIGNED ANYCAST",
    },
    "aut-num": {"ASSIGNED", "LEGACY", "OTHER"},
}


def parse_objects(text):
    """Split RPSL text into objects: list of (type, [(attr, value), ...])."""
    objects, current, last_attr = [], [], None
    for raw in text.splitlines():
        if not raw.strip():
            if current:
                objects.append(current)
            current, last_attr = [], None
            continue
        if raw[0] in " \t+" or (raw[0] == "#" and not ATTR_RE.match(raw)):
            # continuation line: append to the previous attribute's value
            if current:
                name, value = current[-1]
                extra = raw[1:].strip() if raw[0] in " \t" else raw.lstrip("+").strip()
                current[-1] = (name, (value + " " + extra).strip())
            continue
        if raw.lstrip().startswith("%") or raw.lstrip().startswith("#"):
            continue
        m = ATTR_RE.match(raw)
        if not m:
            continue
        name, value = m.group(1).lower(), (m.group(2) or "").strip()
        current.append((name, value))
        last_attr = name
    if current:
        objects.append(current)
    return objects


def type_of(obj):
    if not obj:
        return None
    return TYPE_OF_FIRST_ATTR.get(obj[0][0])


def values(obj, name):
    return [v for a, v in obj if a == name]


def render(obj):
    """Align to RIPE's convention: the value starts in column 17."""
    return "\n".join(f"{a + ':':<16}{v}".rstrip() for a, v in obj)


def cmd_template(args):
    tpl = TEMPLATES.get(args.type)
    if not tpl:
        sys.exit(f"unknown object type {args.type!r}; known: {', '.join(sorted(TEMPLATES))}")
    obj = [(a, f"<{a}>") for a in tpl["mandatory"] if a != "source"]
    obj.append(("source", args.source))
    print(render(obj))
    print()
    print("optional attributes: " + ", ".join(tpl["optional"]), file=sys.stderr)
    for a, hint in (tpl.get("notes") or {}).items():
        print(f"  {a}: {hint}", file=sys.stderr)


def cmd_check(args):
    text = open(args.file, encoding="utf-8").read()
    objects = parse_objects(text)
    if not objects:
        sys.exit("no RPSL object found (an object starts with its type attribute, e.g. 'inetnum:')")
    if len(objects) > 1:
        print(f"note: found {len(objects)} objects; checking only the first. A blank line ends an "
              f"object, so a blank line inside one splits it in two — if that was not intended, "
              f"remove it (use 'remarks:' with no value for visual spacing).", file=sys.stderr)
    obj = objects[0]
    errors, warnings = [], []

    otype = type_of(obj)
    if not otype:
        errors.append(f"unrecognised first attribute {obj[0][0]!r}; cannot tell the object type")
        report(errors, warnings)
        return
    tpl = TEMPLATES.get(otype)
    if not tpl:
        errors.append(f"object type {otype!r} is not one this linter knows; "
                      f"check the template with: whois -h whois.ripe.net -t {otype}")
        report(errors, warnings)
        return

    present = {a for a, _ in obj}
    for a in tpl["mandatory"]:
        if a not in present:
            hint = tpl.get("notes", {}).get(a)
            errors.append(f"missing mandatory attribute {a}:" + (f" ({hint})" if hint else ""))
    for a in tpl["single"]:
        if len(values(obj, a)) > 1:
            errors.append(f"{a}: may appear only once, found {len(values(obj, a))}")
    for a in tpl["key"]:
        if not values(obj, a) or not values(obj, a)[0]:
            errors.append(f"{a}: primary key is empty")

    for a in present:
        if a in GENERATED or a in GENERATED_BY_TYPE.get(otype, ()) or a in GENERATED_SOFT:
            warnings.append(f"{a}: is generated by the server; remove it from an update "
                            f"(it is ignored or corrected)")
    if "source" in present and values(obj, "source")[0].upper() not in ("RIPE", "TEST"):
        warnings.append(f"source: {values(obj, 'source')[0]} is neither RIPE nor TEST")

    unfilled = [a for a, v in obj if is_placeholder(v)]
    if unfilled:
        errors.append(f"unfilled placeholder value(s): {', '.join(sorted(set(unfilled)))} — "
                      f"replace every <attribute> with a real value")
        report(errors, warnings, otype)
        return

    for a, v in obj:
        try:
            v.encode("latin-1")
        except UnicodeEncodeError:
            warnings.append(f"{a}: contains non-latin-1 characters; they will be stored as '?'")

    if otype in STATUS_VALUES:
        for v in values(obj, "status"):
            if v and v.upper() not in STATUS_VALUES[otype]:
                errors.append(f"status: {v!r} is not valid for {otype}; expected one of "
                              f"{', '.join(sorted(STATUS_VALUES[otype]))}")
    if otype == "inet6num" and "AGGREGATED-BY-LIR" in [v.upper() for v in values(obj, "status")]:
        if not values(obj, "assignment-size"):
            errors.append("status AGGREGATED-BY-LIR requires assignment-size:")

    for v in values(obj, "nic-hdl"):
        if v and v.upper().startswith("AUTO") and not re.fullmatch(r"AUTO-\d+[A-Za-z]{0,4}", v.upper()):
            errors.append(f"nic-hdl: {v!r} is not a valid AUTO form (AUTO-1, AUTO-1JE)")
    for v in values(obj, "organisation"):
        if v and not v.upper().startswith("AUTO-") and not re.fullmatch(r"ORG-[A-Za-z0-9]{2,4}-[A-Za-z0-9-]+", v):
            warnings.append(f"organisation: {v!r} is not an ORG-...-<source> ID; "
                            f"on create it must be AUTO-1")

    if otype in ("inetnum",):
        for v in values(obj, "inetnum"):
            if " - " in v:
                start, end = [x.strip() for x in v.split(" - ", 1)]
                if not (is_ipv4(start) and is_ipv4(end)):
                    errors.append(f"inetnum: cannot parse range {v!r}")
                elif ip_to_int(start) > ip_to_int(end):
                    errors.append(f"inetnum: start {start} is after end {end}")
    if otype in ("inet6num", "route6"):
        for v in values(obj, otype):
            if v and not re.fullmatch(r"[0-9A-Fa-f:]+/\d{1,3}", v):
                errors.append(f"{otype}: {v!r} is not an IPv6 prefix")
    if otype == "route":
        for v in values(obj, "route"):
            if v and not re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}/\d{1,2}", v):
                errors.append(f"route: {v!r} is not an IPv4 prefix")
    if otype in ("route", "route6"):
        for v in values(obj, "origin"):
            if v and not re.fullmatch(r"AS\d+", v.upper()):
                errors.append(f"origin: {v!r} is not an AS number")
            elif v and v.upper() != v:
                warnings.append(f"origin: {v!r} should be upper case")
        ping = values(obj, "pingable")
        if ping and otype == "route":
            prefix = values(obj, "route")[0]
            if is_ipv4(ping[0]) and "/" in prefix:
                if not in_prefix(ping[0], prefix):
                    errors.append(f"pingable: {ping[0]} is outside {prefix}")

    if otype == "domain":
        for v in values(obj, "domain"):
            if v and not (v.rstrip(".").endswith(("in-addr.arpa", "ip6.arpa", "e164.arpa"))):
                warnings.append(f"domain: {v!r} is not a reverse zone; forward zones do not "
                                f"belong in the RIPE Database")
    if otype in ("person", "role", "organisation"):
        for v in values(obj, "phone"):
            if v and not v.startswith("+"):
                warnings.append(f"phone: {v!r} should be in international format starting with +")
    if otype == "person":
        for v in values(obj, "person"):
            if v and len(v.split()) < 2:
                errors.append("person: needs at least two words")
    for v in values(obj, "mnt-by"):
        if v and not v.lower().endswith("-mnt") and otype != "mntner":
            warnings.append(f"mnt-by: {v!r} does not end in -mnt (allowed, but unusual)")

    report(errors, warnings, otype)


PLACEHOLDER = re.compile(r"^<.*>$")


def is_placeholder(v):
    return bool(PLACEHOLDER.match(v.strip()))


def report(errors, warnings, otype=None):
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    if errors:
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
        sys.exit(1)
    head = f"{otype}: " if otype else ""
    print(f"\nOK    {head}{len(warnings)} warning(s). Lint is offline; the server enforces more "
          f"(references, hierarchy, authorisation). Try ?dry-run next.")


def is_ipv4(s):
    parts = s.split(".")
    return len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)


def ip_to_int(s):
    a, b, c, d = (int(p) for p in s.split("."))
    return (a << 24) | (b << 16) | (c << 8) | d


def in_prefix(ip, prefix):
    net, bits = prefix.split("/")
    bits = int(bits)
    mask = (0xFFFFFFFF << (32 - bits)) & 0xFFFFFFFF if bits else 0
    return ip_to_int(ip) & mask == ip_to_int(net) & mask


def object_key(obj, otype):
    tpl = TEMPLATES.get(otype, {})
    keys = tpl.get("key", [])
    parts = []
    for k in keys:
        v = values(obj, k)
        if not v:
            sys.exit(f"cannot build a key: {k}: is missing")
        parts.append(v[0])
    if otype in ("route", "route6"):
        return parts[0] + parts[1]          # prefixASn, no separator
    if otype == "inetnum":
        return parts[0].replace(" - ", " - ")
    return parts[0]


def cmd_url(args):
    obj = parse_objects(open(args.file, encoding="utf-8").read())[0]
    otype = type_of(obj)
    if not otype:
        sys.exit("cannot determine the object type from the first attribute")
    source = (values(obj, "source") or ["RIPE"])[0].lower()
    host = "rest-test.db.ripe.net" if source == "test" else "rest.db.ripe.net"
    key = object_key(obj, otype)
    if args.exists:
        method, path = "PUT", f"/{source}/{otype}/{quote(key, safe='/:.-_~')}"
    else:
        method, path = "POST", f"/{source}/{otype}"
    print(f"{method} https://{host}{path}")
    print("# add ?dry-run to validate without writing", file=sys.stderr)


def cmd_json(args):
    obj = parse_objects(open(args.file, encoding="utf-8").read())[0]
    otype = type_of(obj)
    source = (values(obj, "source") or ["RIPE"])[0]
    body = {
        "objects": {
            "object": [{
                "type": otype,
                "source": {"id": source},
                "attributes": {"attribute": [{"name": a, "value": v} for a, v in obj]},
            }]
        }
    }
    print(json.dumps(body, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("template", help="print a skeleton object")
    t.add_argument("type")
    t.add_argument("--source", default="RIPE")
    t.set_defaults(func=cmd_template)

    c = sub.add_parser("check", help="lint an RPSL file")
    c.add_argument("file")
    c.set_defaults(func=cmd_check)

    u = sub.add_parser("url", help="print the REST method and URL")
    u.add_argument("file")
    u.add_argument("--exists", action="store_true", help="the object already exists (PUT)")
    u.set_defaults(func=cmd_url)

    j = sub.add_parser("json", help="print the JSON request body")
    j.add_argument("file")
    j.set_defaults(func=cmd_json)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
