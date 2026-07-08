#!/usr/bin/env bash
# Stage the SouthPark Centre task into a runnable bash sandbox.
#   ./setup_env.sh [TARGET_ROOT]   (default: /tmp/southpark_env)
# Creates  $TARGET/data  (the agent's /data)  and  $TARGET/outputs  (the agent's /tmp/outputs).
# In the Fleet harness, mount  World Files/  at  /data  and point outputs at  /tmp/outputs.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-/tmp/southpark_env}"

echo "Staging into $TARGET"
rm -rf "$TARGET"
mkdir -p "$TARGET/data" "$TARGET/outputs"

# World Files/<subdir> -> data/<subdir>  (emails, dataroom, dataroom_deal_b, internal,
# lenders, construction, market_research - incl. nested lease_abstracts/property_reports/archive)
cp -R "$HERE/world_files/." "$TARGET/data/"

# The pipeline tracker is edited by the agent and saved to outputs; seed a copy there too
cp "$HERE/world_files/internal/Pipeline_Tracker_Q2_2026.xlsx" "$TARGET/outputs/" 2>/dev/null || true

# The SouthPark model is a FILL-IN template: seed it at the grader's expected output filename.
# (Pre-structured 14-tab workbook with labels + Month # headers in place, value cells blank.)
cp "$HERE/world_files/internal/SouthPark_Centre_Model_Template.xlsx" "$TARGET/outputs/southpark_centre_underwriting.xlsx" 2>/dev/null || true

echo "data files:    $(find "$TARGET/data" -type f | wc -l | tr -d ' ')"
echo "  pdfs:        $(find "$TARGET/data" -name '*.pdf' | wc -l | tr -d ' ')"
echo "  xlsx:        $(find "$TARGET/data" -name '*.xlsx' | wc -l | tr -d ' ')"
echo "  html:        $(find "$TARGET/data" -name '*.html' | wc -l | tr -d ' ')"
echo
echo "Done. Agent reads:   $TARGET/data   (mount as /data)"
echo "      Agent writes:  $TARGET/outputs (mount as /tmp/outputs)"
echo "Grade with:  python3 \"$HERE/grade.py\" \"$TARGET/outputs\""
