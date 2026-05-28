#!/usr/bin/env python3
"""Script to strip HTTP headers from web_fetch temp files and save clean data."""
import sys, os

def strip_headers(input_path, output_path):
    """Read a web_fetch temp file, skip the HTTP header lines, write clean data."""
    with open(input_path, 'r') as f:
        lines = f.readlines()
    
    # Find the first line starting with O*NET or Job Zone (the header row of the TSV)
    start = 0
    for i, line in enumerate(lines):
        if line.startswith('O*NET-SOC Code\t') or line.startswith('Job Zone\t'):
            start = i
            break
    
    with open(output_path, 'w') as f:
        f.writelines(lines[start:])
    
    print(f"  Wrote {len(lines) - start} lines to {output_path}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python copy_temp_files.py <input> <output>")
        sys.exit(1)
    strip_headers(sys.argv[1], sys.argv[2])
