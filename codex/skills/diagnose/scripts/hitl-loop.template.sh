#!/usr/bin/env bash
set -euo pipefail

# Human-in-the-loop diagnosis template.
# Use only when no fully automated reproduction loop is possible.

echo "Describe the exact manual action to perform:"
echo "1. <step one>"
echo "2. <step two>"
echo "3. <step three>"
echo
read -r -p "Press Enter after performing the steps..."

echo "Record the observed result:"
read -r observed

echo "Observed: ${observed}"
echo "Expected: <fill expected result here>"
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
