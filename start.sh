#!/bin/bash
set -e

# Force unbuffered output for Python
export PYTHONUNBUFFERED=1

echo "=== Starting Railway deployment script ===" >&2
echo "Executing wait_for_db.py..." >&2

# Execute the wait_for_db.py script and pass through all output
exec python wait_for_db.py
