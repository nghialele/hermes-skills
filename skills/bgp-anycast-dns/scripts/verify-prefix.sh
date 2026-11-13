#!/usr/bin/env bash
# verify-prefix.sh — answer, from live registries: who holds this prefix, which AS
# may originate it, and is anyone announcing it today?
#
#   verify-prefix.sh 2a14:7583:ff60::/44            # everything except the RPKI test
#   verify-prefix.sh 2a14:7583:ff60::/44 AS206540   # also test RPKI validity as that origin
#
# Read-only: whois and RIPEstat GETs only, no writes.
#
# The RPKI check works even with the WRONG ASN: RIPEstat returns status
# invalid_asn but still lists validating_roas[].origin, which is how you discover
# the origin AS a prefix is actually authorized for. Any plausible ASN will do.
set -uo pipefail

PREFIX="${1:-}"
ASN="${2:-}"
if [ -z "$PREFIX" ]; then
  echo "usage: verify-prefix.sh <prefix> [ASxxxxx]" >&2
  exit 2
fi

W="whois -h whois.ripe.net -r"
RS="https://stat.ripe.net/data"
hr() { printf '\n=== %s ===\n' "$1"; }

hr "1. registry objects for $PREFIX"
$W "$PREFIX" 2>&1 | grep -E '^(inet6num|inetnum|route6|netname|status|org|country|mnt-by|created|origin)' || echo "  (no object found)"

hr "2. candidate parent prefixes (query the longest that exists to find the real LIR)"
python3 - "$PREFIX" <<'PY'
import ipaddress, sys
n = ipaddress.ip_network(sys.argv[1], strict=False)
for plen in (48, 44, 40, 36, 32, 29, 24, 20, 16):
    if plen < n.prefixlen:
        print("  " + str(ipaddress.ip_network(f"{n.network_address}/{plen}", strict=False)))
PY

hr "3. ASN held by this org (empty = no ASN of its own)"
ORG=$($W "$PREFIX" 2>&1 | awk '/^org:/{print $2; exit}')
if [ -n "${ORG:-}" ]; then
  echo "  org: $ORG"
  $W "$ORG" 2>&1 | grep -E '^(org-name|org-type|country|address)' || true
  $W -T aut-num -i org "$ORG" 2>&1 | grep -E '^(aut-num|as-name)' || echo "  (no aut-num)"
else
  echo "  (no org attribute on the object)"
fi

hr "4. announcement state"
curl -s "$RS/prefix-overview/data.json?resource=$PREFIX" \
  | jq -c '.data | {announced, asns}' 2>/dev/null || echo "  (RIPEstat unreachable)"

hr "5. RPKI — which origin AS is authorized"
if [ -n "$ASN" ]; then
  curl -s "$RS/rpki-validation/data.json?resource=$ASN&prefix=$PREFIX" \
    | jq -c '.data | {status, validating_roas}' 2>/dev/null || echo "  (RIPEstat unreachable)"
else
  echo "  skipped — retry with an ASN: $0 $PREFIX AS206540"
  echo "  any plausible ASN works; the real origin appears in validating_roas even on invalid_asn"
fi

hr "6. /48 breakdown (the announcement unit)"
python3 - "$PREFIX" <<'PY'
import ipaddress, sys
n = ipaddress.ip_network(sys.argv[1], strict=False)
if n.prefixlen <= 48:
    for i, s in enumerate(n.subnets(new_prefix=48)):
        print(f"  {i:3d}  {s}")
else:
    print(f"  {n} is longer than /48 — not globally announceable")
PY
