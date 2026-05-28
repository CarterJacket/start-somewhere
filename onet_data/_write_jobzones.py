#!/usr/bin/env python3
import sys
# This script will be fed Job Zones data via stdin
data = sys.stdin.read()
with open('/sessions/focused-jolly-faraday/mnt/outputs/onet_data/Job Zones.txt', 'w') as f:
    f.write(data)
print(f"Wrote {len(data)} bytes")
