#!/usr/bin/env python3
"""RIPE Database REST client: read objects, search, and (with --apply) write.

Reads are safe and default to the real database. Writes default to TEST and
refuse to run without --apply, so an accidental invocation cannot change
production data.

  ripe.py get TYPE KEY [--unfiltered] [--source ripe|test]
  ripe.py search QUERY [--type T ...] [--inverse ATTR] [--no-referenced]
  ripe.py abuse RESOURCE
  ripe.py versions TYPE KEY [--source ...]
  ripe.py create TYPE --file OBJ [--source test] [--dry-run|--apply]
  ripe.py update TYPE KEY --file OBJ [--source test] [--dry-run|--apply]
  ripe.py delete TYPE KEY [--reason TEXT] [--source test] [--dry-run|--apply]

Any command accepts --print-request to show the equivalent curl instead of
sending it. Credentials come from RIPE_APIKEY ("keyid:secret") for writes and
authenticated reads.

Exit codes: 0 ok, 1 request failed, 2 usage error, 3 network unreachable.
"""

import argparse
import base64
import json
import os
import re
import shlex
import sys
import urllib.error
import urllib.parse
import urllib.request

HOSTS = {
    "ripe": "https://rest.db.ripe.net",
    "test": "https://rest-test.db.ripe.net",
}

# RIPE_REST_BASE overrides both hosts; useful for a local mock or a mirror
if os.environ.get("RIPE_REST_BASE"):
    HOSTS = {k: os.environ["RIPE_REST_BASE"] for k in HOSTS}


def die(msg, code=2):
    print(msg, file=sys.stderr)
    sys.exit(code)


def auth_header():
    key = os.environ.get("RIPE_APIKEY", "").strip()
    if not key:
        return None
    token = base64.b64encode(key.encode()).decode()
    return f"Basic {token}"


def parse_rpsl(text):
    """Return [(name, value)] for a single RPSL object in text."""
    attrs, last = [], None
    for raw in text.splitlines():
        if not raw.strip():
            continue
        if raw[0] in " \t+":
            if last is not None:
                extra = raw[1:].strip() if raw[0] in " \t" else raw.lstrip("+").strip()
                attrs[last] = (attrs[last][0], (attrs[last][1] + " " + extra).strip())
            continue
        if raw.startswith("%") or raw.startswith("#"):
            continue
        if ":" not in raw:
            continue
        name, _, value = raw.partition(":")
        attrs.append((name.strip().lower(), value.strip()))
        last = len(attrs) - 1
    return attrs


def attrs_to_rpsl(attrs):
    if not attrs:
        return ""
    width = max(len(a) for a, _ in attrs) + 1
    return "\n".join(f"{a + ':':<{width}} {v}".rstrip() for a, v in attrs)


def obj_to_json(attrs, otype, source):
    return {
        "objects": {
            "object": [{
                "type": otype,
                "source": {"id": source},
                "attributes": {"attribute": [{"name": a, "value": v} for a, v in attrs]},
            }]
        }
    }


def extract_objects(payload):
    """Pull RPSL text out of a JSON whois-resources response."""
    out = []
    for obj in payload.get("objects", {}).get("object", []) or []:
        attrs = [(a.get("name", ""), a.get("value", ""))
                 for a in obj.get("attributes", {}).get("attribute", []) or []]
        if attrs:
            out.append((obj.get("type", "?"), attrs))
    return out


def extract_errors(payload):
    msgs = []
    for m in payload.get("errormessages", {}).get("errormessage", []) or []:
        args = [a.get("value", "") for a in m.get("args", []) or []]
        text = m.get("text", "")
        for a in args:
            text = text.replace("%s", a, 1)
        msgs.append(f"{m.get('severity', 'Error')}: {text}")
    return msgs


def request(method, url, body=None, accept="application/json", authenticated=False, show=False):
    headers = {"Accept": accept}
    if body is not None:
        headers["Content-Type"] = "application/json"
    auth = auth_header() if (authenticated or method != "GET") else None
    if auth:
        headers["Authorization"] = auth

    if show:
        parts = ["curl", "-s", "-X", method]
        for k, v in headers.items():
            shown = "$RIPE_APIKEY" if k == "Authorization" else v
            if k == "Authorization":
                parts += ["-u", '"$RIPE_APIKEY"']
            else:
                parts += ["-H", shlex.quote(f"{k}: {shown}")]
        if body is not None:
            parts += ["--data", shlex.quote(json.dumps(body))]
        parts.append(shlex.quote(url))
        print(" ".join(parts))
        return 0, {"printed": True}, None  # 0 means "printed, nothing sent"

    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode("utf-8", "replace")
            status = r.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        status = e.code
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"network error talking to {urllib.parse.urlsplit(url).netloc}: {e}", file=sys.stderr)
        print("This environment may have no route to the RIPE endpoints. "
              "Re-run with --print-request and execute the curl on a host with internet access.",
              file=sys.stderr)
        return 3, None, None

    try:
        payload = json.loads(raw) if raw.strip().startswith("{") else None
    except json.JSONDecodeError:
        payload = None
    if payload is None:
        print(raw)
    return status, payload, raw


def is_bare_ip(value):
    v = value.strip()
    if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", v):
        return True
    return bool(re.fullmatch(r"[0-9A-Fa-f:]{2,}", v)) and v.count(":") >= 2


def key_path(otype, key):
    return f"/{otype}/{urllib.parse.quote(key, safe='/:.-_~ ')}".replace(" ", "%20")


def cmd_get(args):
    url = f"{HOSTS[args.source]}/{args.source}{key_path(args.type, args.key)}"
    if args.unfiltered:
        url += "?unfiltered"
    status, payload, _ = request("GET", url, authenticated=args.unfiltered, show=args.print_request)
    if status == 0:
        return 0
    if status == 3:
        return 3
    if status == 404:
        print(f"not found: {args.type} {args.key} in source {args.source}", file=sys.stderr)
        if is_bare_ip(args.key) and args.type in ("inetnum", "inet6num"):
            print("lookup is exact and does not walk up the hierarchy. For a single address use "
                  f"`search {args.key}` or `whois -h whois.ripe.net -L {args.key}`.",
                  file=sys.stderr)
        return 1
    if payload is None:
        return 0 if status == 200 else 1
    for e in extract_errors(payload):
        print(e, file=sys.stderr)
    objs = extract_objects(payload)
    if not objs:
        print("no objects returned", file=sys.stderr)
        return 1
    for i, (otype, attrs) in enumerate(objs):
        if i:
            print()
        print(attrs_to_rpsl(attrs))
    return 0 if status == 200 else 1


def cmd_search(args):
    params = [("source", args.source), ("query-string", args.query)]
    for t in args.type or []:
        params.append(("type-filter", t))
    if args.inverse:
        params.append(("inverse-attribute", args.inverse))
    if args.no_referenced:
        params.append(("flags", "no-referenced"))
    if args.unfiltered:
        params.append(("flags", "no-filtering"))
    if args.limit:
        params.append(("limit", str(args.limit)))
    url = f"{HOSTS[args.source]}/search?" + urllib.parse.urlencode(params)
    status, payload, _ = request("GET", url, show=args.print_request)
    if status == 0:
        return 0
    if status == 3:
        return 3
    if payload is None:
        return 0 if status == 200 else 1
    for e in extract_errors(payload):
        print(e, file=sys.stderr)
    objs = extract_objects(payload)
    if not objs:
        print("no objects matched", file=sys.stderr)
        return 1
    for i, (otype, attrs) in enumerate(objs):
        if i:
            print()
        print(attrs_to_rpsl(attrs))
    print(f"\n% {len(objs)} object(s)", file=sys.stderr)
    return 0


def cmd_abuse(args):
    url = f"{HOSTS[args.source]}/abuse-contact/{urllib.parse.quote(args.resource, safe='/:. -_~')}"
    status, payload, _ = request("GET", url, show=args.print_request)
    if status == 0:
        return 0
    if status == 3:
        return 3
    if payload is None:
        return 0 if status == 200 else 1
    found = False
    for res in payload.get("abuse-resources", {}).get("abuse-resource", []) or []:
        for a in res.get("abuse-contacts", {}).get("abuse-contact", []) or []:
            print(f"{res.get('resource', args.resource)}\t{a.get('value', a)}")
            found = True
    if not found:
        print(json.dumps(payload, indent=2))
    return 0


def cmd_versions(args):
    url = f"{HOSTS[args.source]}/{args.source}{key_path(args.type, args.key)}/versions"
    status, payload, _ = request("GET", url, show=args.print_request)
    if status == 0:
        return 0
    if status == 3:
        return 3
    if payload is None:
        return 0 if status == 200 else 1
    for v in payload.get("versions", {}).get("version", []) or []:
        print(f"{v.get('revision')}\t{v.get('date')}\t{v.get('operation')}")
    return 0


def load_attrs(path):
    text = open(path, encoding="utf-8").read()
    attrs = parse_rpsl(text)
    if not attrs:
        die(f"no RPSL attributes found in {path}")
    return attrs


def write_guard(args):
    if not args.apply and not args.dry_run and not args.print_request:
        print("refusing to write: pass --dry-run to validate, --apply to send, "
              "or --print-request to inspect", file=sys.stderr)
        return False
    if args.source == "ripe" and args.apply and not args.i_know:
        print("refusing to write to the live RIPE database: add --i-know, or use --source test",
              file=sys.stderr)
        return False
    return True


def cmd_write(args):
    if not write_guard(args):
        return 2
    base = HOSTS[args.source]
    if args.cmd == "create":
        method, url = "POST", f"{base}/{args.source}/{args.type}"
    elif args.cmd == "update":
        method, url = "PUT", f"{base}/{args.source}{key_path(args.type, args.key)}"
    else:
        method, url = "DELETE", f"{base}/{args.source}{key_path(args.type, args.key)}"

    body = None
    if method != "DELETE":
        body = obj_to_json(load_attrs(args.file), args.type, args.source)

    query = []
    if args.dry_run:
        query.append("dry-run")
    if args.cmd == "delete" and args.reason:
        query.append("reason=" + urllib.parse.quote(args.reason))
    if query:
        url += "?" + "&".join(query)

    print(f"{method} {url}", file=sys.stderr)
    status, payload, _ = request(method, url,
                                 body=None if method == "DELETE" else body,
                                 show=args.print_request)
    if status == 0:
        return 0
    if status == 3:
        return 3
    if payload is None:
        return 0 if status == 200 else 1
    for e in extract_errors(payload):
        print(e, file=sys.stderr)
    objs = extract_objects(payload)
    for otype, oattrs in objs:
        print(attrs_to_rpsl(oattrs))
    if status == 200:
        if args.dry_run:
            print("\n% dry-run passed; nothing was written", file=sys.stderr)
        else:
            print(f"\n% {args.cmd} succeeded", file=sys.stderr)
        return 0
    print(f"\n% {args.cmd} failed with HTTP {status}", file=sys.stderr)
    return 1


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--print-request", action="store_true", help="print the curl, send nothing")
    sub = p.add_subparsers(dest="cmd", required=True)

    # also accepted after the subcommand; SUPPRESS keeps it from overwriting a
    # value given before the subcommand
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--print-request", action="store_true",
                        default=argparse.SUPPRESS, help="print the curl, send nothing")

    def add_source(sp, default="ripe"):
        sp.add_argument("--source", choices=sorted(HOSTS), default=default)

    g = sub.add_parser("get", parents=[common], help="look up one object by key")
    g.add_argument("type")
    g.add_argument("key")
    g.add_argument("--unfiltered", action="store_true")
    add_source(g)
    g.set_defaults(func=cmd_get)

    s = sub.add_parser("search", parents=[common], help="whois-style search")
    s.add_argument("query")
    s.add_argument("--type", action="append", help="object type filter, repeatable")
    s.add_argument("--inverse", metavar="ATTR", help="inverse lookup on this attribute")
    s.add_argument("--no-referenced", action="store_true", help="do not pull in contacts")
    s.add_argument("--unfiltered", action="store_true")
    s.add_argument("--limit", type=int)
    add_source(s)
    s.set_defaults(func=cmd_search)

    a = sub.add_parser("abuse", parents=[common], help="abuse contact for a resource")
    a.add_argument("resource")
    add_source(a)
    a.set_defaults(func=cmd_abuse)

    v = sub.add_parser("versions", parents=[common], help="version history of an object")
    v.add_argument("type")
    v.add_argument("key")
    add_source(v)
    v.set_defaults(func=cmd_versions)

    for name, helptext in (("create", "create an object (POST)"),
                           ("update", "modify an object (PUT)"),
                           ("delete", "delete an object (DELETE)")):
        w = sub.add_parser(name, parents=[common], help=helptext)
        w.add_argument("type")
        if name != "create":
            w.add_argument("key")
        if name != "delete":
            w.add_argument("--file", required=True, help="RPSL file with the object")
        w.add_argument("--reason", help="delete reason")
        add_source(w, default="test")
        w.add_argument("--dry-run", action="store_true")
        w.add_argument("--apply", action="store_true")
        w.add_argument("--i-know", action="store_true", help="allow writing to the live database")
        w.set_defaults(func=cmd_write)

    args = p.parse_args()
    sys.exit(args.func(args) or 0)


if __name__ == "__main__":
    main()
