#!/usr/bin/env python3
"""Convert HetrixTools epochs/local times to Vietnam time."""
import argparse
from datetime import datetime, timedelta, timezone
TZ = timezone(timedelta(hours=7))

def fmt(ts):
    return datetime.fromtimestamp(int(ts), TZ).strftime('%Y-%m-%d %H:%M:%S')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('epochs', nargs='*')
    ap.add_argument('--local')
    ap.add_argument('--utc', action='store_true')
    args = ap.parse_args()
    if args.local:
        naive = datetime.strptime(args.local, '%Y-%m-%d %H:%M')
        zone = timezone.utc if args.utc else TZ
        dt = naive.replace(tzinfo=zone)
        label = 'UTC' if args.utc else '(+07)'
        print(f'{args.local} {label} = {dt.astimezone(TZ).strftime("%Y-%m-%d %H:%M")} (+07), epoch {int(dt.timestamp())}')
    elif args.epochs:
        for value in args.epochs:
            print(f'{value} -> {fmt(value)} (+07)')
    else:
        ap.error('provide epochs or --local')
if __name__ == '__main__':
    main()
