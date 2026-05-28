#!/bin/bash
cd "$(dirname "$0")"
python3 _process_temp.py
echo ""
echo "Press any key to close..."
read -n 1
