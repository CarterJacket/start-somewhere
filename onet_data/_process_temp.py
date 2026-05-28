#!/usr/bin/env python3
"""Process temp files from web_fetch into clean TSV data files.
Run this from the HOST machine (macOS), not from the sandbox.

Usage: python3 _process_temp.py
"""
import os, sys, re, urllib.request

TEMP_DIR = "/var/folders/c6/57rgyhd107j1skpms1n54rsc0000gn/T/claude-hostloop-plugins/7816c5c0fd4d4753/projects/-Users-carterjaquette-Library-Application-Support-Claude-local-agent-mode-sessions-aa0d90cb-2ece-4ddb-9f91-bfa4d812ea3c-ea837260-990f-415a-9b35-c7018fb6c9a3-local-c80393e3-4e86-4cb4-a8b8-6629ed8af56e--5nd84m/7f130e19-d0b9-4bae-828e-c031d36d993d/tool-results"

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_URL = "https://www.onetcenter.org/dl_files/database/db_30_3_text/"

# Files to download: (url_filename, output_name, header_pattern)
FILES = [
    ("Occupation%20Data.txt", "Occupation Data.txt", "O*NET-SOC Code\tTitle"),
    ("Knowledge.txt", "Knowledge.txt", "O*NET-SOC Code\tElement ID"),
    ("Education.txt", "Education.txt", "O*NET-SOC Code\tElement ID"),
    ("Essential%20Skills.txt", "Essential Skills.txt", "O*NET-SOC Code\tElement ID"),
    ("Transferable%20Skills.txt", "Transferable Skills.txt", "O*NET-SOC Code\tElement ID"),
]

# Map temp file suffixes to their content
TEMP_MAP = {
    "1779467019411": "Occupation Data.txt",
    "1779443636886": "Occupation Data.txt",
    "1779442020839": "Knowledge.txt",
    "1779442022345": "Education.txt",
}

def process_temp_file(temp_path, output_name, header_start):
    """Extract clean data from a web_fetch temp file."""
    with open(temp_path, 'r') as f:
        lines = f.readlines()

    start = None
    for i, line in enumerate(lines):
        if line.startswith(header_start):
            start = i
            break

    if start is None:
        return 0

    clean_lines = []
    for line in lines[start:]:
        stripped = line.rstrip('\n\r')
        if stripped:
            clean_lines.append(stripped + '\n')

    # Remove last line if it appears truncated (doesn't end with a complete field)
    if clean_lines and len(clean_lines) > 1:
        last = clean_lines[-1].rstrip('\n')
        tabs = last.count('\t')
        header_tabs = clean_lines[0].rstrip('\n').count('\t')
        if tabs < header_tabs:
            clean_lines.pop()

    output_path = os.path.join(OUTPUT_DIR, output_name)
    with open(output_path, 'w') as f:
        f.writelines(clean_lines)
    return len(clean_lines)

def download_file(url_filename, output_name, header_start):
    """Try to download directly from O*NET."""
    url = BASE_URL + url_filename
    output_path = os.path.join(OUTPUT_DIR, output_name)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=30)
        data = resp.read().decode('utf-8')
        lines = data.split('\n')

        start = None
        for i, line in enumerate(lines):
            if line.startswith(header_start):
                start = i
                break

        if start is None:
            return 0

        clean_lines = [l + '\n' for l in lines[start:] if l.strip()]
        with open(output_path, 'w') as f:
            f.writelines(clean_lines)
        return len(clean_lines)
    except Exception as e:
        print(f"  Download failed: {e}")
        return 0

# Download ALL files directly (host has no proxy restrictions)
print("=== Downloading all files from O*NET ===")
processed = set()
for url_filename, output_name, header_start in FILES:
    print(f"  Downloading {output_name}...")
    count = download_file(url_filename, output_name, header_start)
    if count > 0:
        print(f"  {output_name}: {count} lines downloaded")
        processed.add(output_name)
    else:
        # Fallback to temp files
        print(f"  Download failed, trying temp files...")
        for suffix, tname in TEMP_MAP.items():
            if tname == output_name:
                temp_path = os.path.join(TEMP_DIR, f"mcp-workspace-web_fetch-{suffix}.txt")
                if os.path.exists(temp_path):
                    tc = process_temp_file(temp_path, output_name, header_start)
                    if tc > 0:
                        print(f"  {output_name}: {tc} lines from temp file")
                        processed.add(output_name)
                        break
        if output_name not in processed:
            print(f"  {output_name}: FAILED")

# Step 3: Report
print("\n=== Final Report ===")
for _, output_name, _ in FILES:
    output_path = os.path.join(OUTPUT_DIR, output_name)
    if os.path.exists(output_path):
        with open(output_path) as f:
            lines = f.readlines()
        size = os.path.getsize(output_path)
        print(f"  {output_name}: {len(lines)} lines, {size:,} bytes")
    else:
        print(f"  {output_name}: MISSING")

print("\nDone!")
