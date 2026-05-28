#!/bin/bash
cd "$(dirname "$0")"
python3 _process_temp.py > _run.log 2>&1
echo "Exit code: $?" >> _run.log
