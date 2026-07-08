# SouthPark Centre - Grader

Deterministic, layout-tolerant grader for the SouthPark Centre underwriting odyssey task.

## Files
- `extract.py` - label-search + table-read helpers (shared).
- `build_key.py` - extracts `answer_key.json` from the locked ground-truth files. Re-run after
  any change to the master / Deal-B / tracker GT.
- `answer_key.json` - frozen anchors + per-item rows + tolerances + per-phase tracker snapshots.
- `grade.py` - grade a submission directory.
- `selftest.py` - validate the grader against the ground truth.

## Grade a submission
```
python3 grade.py /path/to/submission_dir            # tracker graded vs final (P8)
python3 grade.py /path/to/submission_dir --tracker-phase 3
```
The submission dir must contain `southpark_centre_underwriting.xlsx`,
`ballantyne_wacc_screen.xlsx`, and `Pipeline_Tracker_Q2_2026.xlsx` (see `RUNTIME_PROMPT_v1.md`).

## Self-test
```
python3 selftest.py
```
Expected from the current repo state, observed 2026-07-07: Identity **30797/30797**, Tracker
per-phase **PASS**, Robustness **27621/30797**, Detection **PASS** (all injected errors caught).

## How grading works (~30,360 checks - every calculation + every phase deliverable)
- **Layout-tolerant:** every cell is addressed by **(tab, block, row-label, occurrence, column)**
  - found by label/header search, never by fixed cell reference. Time columns match by month
  index, year roll-ups by year, scalar columns by header text. The agent's layout doesn't
  matter, only the tab names + standard labels + a period (`Month #`) header (see
  `RUNTIME_PROMPT_v1.md`).
- **Three grading layers:**
  1. **Full calculation grid (~29,840):** EVERY numeric formula cell of the four calc tabs vs
     GT - Rent Roll Calc (23,175, the per-tenant engine), Property Cash Flow (2,973), Waterfall
     (3,129), CapEx (563). Tolerance max(0.01, 1%). Coverage = ~99% of all numeric formulas;
     the residual <1% are dates/flags and a few unkeyable scalars.
  2. **Reconciliation invariants (180):** 3 relationships × 60 months on the submission's **own**
     values (EGI · NOI · Levered CF) - catch **hardcoded-but-inconsistent** values.
  3. **Per-phase deliverables (~340):** 46 anchors (summary outputs + LOI deal terms + Submarket
     + selected-lender) · per-item tables (rent roll incl. benchmark, **25 sales + 50 lease**
     comps each classified, leasing-by-size buckets) · matrices (per-lender Leverage Options,
     the 3 sensitivity tables) · per-phase tracker statuses. **Every phase (1–8) is covered.**
- **Fixed-denominator, per-phase:** score = passed / total.
- **Proven to detect errors:** `selftest.py` injects known-wrong values (stale lender, Brightpath
  trap, a hardcoded monthly NOI, a **per-tenant Rent Roll Calc cell**, broken invariants) and
  asserts the grader fails exactly those.

## Dependencies
`openpyxl` (read xlsx). Standard library otherwise.

## Note on the master
The master is read with cached formula values (`data_only`). It was edited **surgically in XML**
(not via openpyxl, which strips the ~23k cached results). If you ever resave it from Excel/
LibreOffice that's fine - it will recompute. The exact edits are logged in
`RUNTIME_AND_GRADING_SPEC.md` §1 (pre-fix state is reconstructable from that table).
