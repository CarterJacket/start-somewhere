#!/usr/bin/env python3
"""Copy web_fetch temp files to onet_data directory, stripping HTTP headers."""
import os, glob

TEMP_DIR = "/var/folders/c6/57rgyhd107j1skpms1n54rsc0000gn/T/claude-hostloop-plugins/7816c5c0fd4d4753/projects/-Users-carterjaquette-Library-Application-Support-Claude-local-agent-mode-sessions-aa0d90cb-2ece-4ddb-9f91-bfa4d812ea3c-ea837260-990f-415a-9b35-c7018fb6c9a3-local-c80393e3-4e86-4cb4-a8b8-6629ed8af56e--5nd84m/7f130e19-d0b9-4bae-828e-c031d36d993d/tool-results"

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Map temp files to output names based on URL in first line
URL_TO_NAME = {
    "Occupation%20Data.txt": "Occupation Data.txt",
    "Knowledge.txt": "Knowledge.txt",
    "Education.txt": "Education.txt",
}

for f in sorted(glob.glob(os.path.join(TEMP_DIR, "mcp-workspace-web_fetch-*.txt"))):
    with open(f, 'r') as fh:
        lines = fh.readlines()

    # Determine filename from URL in first line
    first_line = lines[0].strip()
    output_name = None
    for url_part, name in URL_TO_NAME.items():
        if url_part in first_line:
            output_name = name
            break

    if not output_name:
        print(f"Skipping {f} - no matching URL pattern in: {first_line}")
        continue

    # Find the data start (line starting with O*NET-SOC or Job Zone)
    start = 0
    for i, line in enumerate(lines):
        if line.startswith('O*NET-SOC Code\t') or line.startswith('Job Zone\t'):
            start = i
            break

    output_path = os.path.join(OUTPUT_DIR, output_name)
    with open(output_path, 'w') as fh:
        fh.writelines(lines[start:])

    print(f"Wrote {len(lines) - start} lines to {output_name}")

print("Done!")
