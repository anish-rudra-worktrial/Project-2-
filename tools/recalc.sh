#!/usr/bin/env bash
# Recompute xlsx formula caches with LibreOffice headless, so the grader (which reads
# cached values via openpyxl data_only) sees the agent's COMPUTED results.
#
# Why: the agent builds a live-formula model; openpyxl never recalculates, so without this
# step every formula cell reads back blank and scores zero. The grading harness runs this on
# the submission directory BEFORE grade.py (see HANDOFF.md "Runtime note").
#
# Usage: tools/recalc.sh <dir-with-xlsx>      (recalculates every .xlsx in place)
#
# Requires LibreOffice (soffice/libreoffice). If absent, exits 0 with a warning so callers
# degrade gracefully (the grader will then read uncached formulas as blank).
set -euo pipefail
DIR="${1:?usage: recalc.sh <dir-with-xlsx>}"
SOFFICE="$(command -v soffice || command -v libreoffice || echo /Applications/LibreOffice.app/Contents/MacOS/soffice)"
if [ ! -x "$SOFFICE" ] && ! command -v "$SOFFICE" >/dev/null 2>&1; then
  echo "recalc: LibreOffice not found — skipping recalc. Formula cells will read as blank." >&2
  exit 0
fi

# Force-recalc-on-load so convert-to writes fresh cached values. LibreOffice only recalculates
# Excel files on load when this user setting is enabled, so we seed a throwaway profile with it.
PROFILE="$(mktemp -d)"
mkdir -p "$PROFILE/user/registrymodifications.xcu.d" 2>/dev/null || true
cat > "$PROFILE/user/registrymodifications.xcu" <<'XCU'
<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema">
 <item oor:path="/org.openoffice.Office.Calc/Formula/Load"><prop oor:name="ODFRecalcMode" oor:op="fuse"><value>0</value></prop></item>
 <item oor:path="/org.openoffice.Office.Calc/Formula/Load"><prop oor:name="OOXMLRecalcMode" oor:op="fuse"><value>0</value></prop></item>
</oor:items>
XCU

for f in "$DIR"/*.xlsx; do
  [ -e "$f" ] || continue
  "$SOFFICE" -env:UserInstallation="file://$PROFILE" --headless --calc \
    --convert-to xlsx:"Calc MS Excel 2007 XML" --outdir "$DIR" "$f" >/dev/null 2>&1 || \
    echo "recalc: warning - failed to recalc $(basename "$f")" >&2
done
rm -rf "$PROFILE"
echo "recalc: done ($DIR)"
