#!/usr/bin/env python3
"""
grade.py - top-level entrypoint for the Real Estate PE Underwriting odyssey task.

Delegates to the layout-tolerant, deterministic grader in tools/grader/. End-state grading:
the agent's final workbook (after Phase 8) is scored against the locked ground truth.

Usage:
    python3 grade.py <submission_dir> [--tracker-phase N]   # grade a submission
    python3 grade.py <submission_dir> --recalc              # recalc formulas (LibreOffice) first
    python3 grade.py --self-test                            # validate the grader vs ground truth

The submission dir must contain southpark_centre_underwriting.xlsx,
ballantyne_wacc_screen.xlsx, and Pipeline_Tracker_Q2_2026.xlsx.

The grader reads CACHED cell values. The agent builds a live-formula model, so the submission
must be recalculated before grading (openpyxl does not compute formulas). Pass --recalc to run
tools/recalc.sh (LibreOffice headless) on a temp copy of the submission first; the deployed
grading harness should do this by default. Without recalc, formula cells read as blank.

Requires: openpyxl (and LibreOffice for --recalc).
"""
import os, sys, shutil, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GRADER = os.path.join(HERE, "tools", "grader")
sys.path.insert(0, GRADER)


def _recalc_into_temp(sub_dir):
    """Copy the submission to a temp dir and recalc its xlsx via tools/recalc.sh; return the
    temp dir (or the original if recalc is unavailable)."""
    tmp = tempfile.mkdtemp(prefix="repe_recalc_")
    for fn in os.listdir(sub_dir):
        if fn.lower().endswith(".xlsx"):
            shutil.copy(os.path.join(sub_dir, fn), os.path.join(tmp, fn))
    subprocess.run(["bash", os.path.join(HERE, "tools", "recalc.sh"), tmp], check=False)
    return tmp


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        import runpy
        runpy.run_path(os.path.join(GRADER, "selftest.py"), run_name="__main__")
        sys.exit(0)
    import grade as G
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    tphase = sys.argv[sys.argv.index("--tracker-phase") + 1] if "--tracker-phase" in sys.argv else "8"
    if not args:
        print("usage: python3 grade.py <submission_dir> [--tracker-phase N] [--recalc] | --self-test")
        sys.exit(1)
    sub = args[0]
    if "--recalc" in sys.argv:
        sub = _recalc_into_temp(sub)
    ok, total = G.report(G.grade(sub, tphase))
    sys.exit(0 if ok == total else 1)
