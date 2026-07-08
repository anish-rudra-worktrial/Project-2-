# Changelog - Real Estate PE Underwriting (SouthPark Centre)

## v2 - TMT-model standard (built on branch real-estate-pe-underwriting-v2)
Elevates v1 to the Cloudflare 3-statement reference standard. All four moves built and verified
(self-test 30797/30797, Detection PASS):
- **(a) Cell-explicit prompt** (`prompts/agent_prompt_prescriptive_v2.txt`): all 8 phases rewritten
  as a line-item spec (tab → A-row label → cell/period → driver or pinned assumption). Drives an
  honest per-cell call count, unambiguous grading, and structurally removes the prompt↔template
  mismatch class (v1's mismatches existed only because the prompt was narrative).
- **(b) Check = 0**: wired the template's built-in SENSE CHECKS into the grader as residual-~0
  anchors - Waterfall tier-dists / partner-CF=levered-CF / unreturned-capital=0 / accrued-pref=0,
  and Exit "Rent Roll SF = Building SF". A hardcoded "OK" can't fake a zero residual; bite-tested
  (a forced 5,000 residual fails the check).
- **(c) Primary-source sourcing volume**: added the T-12 Operating Statement reproduction as a
  graded per-item table (21 line items × 13 columns = 273 cells the agent transcribes from
  T12_Operating_Statement_2025.xlsx). 0/273 pass on the blank template = genuine sourcing work.
- **(d) Recommended-assumption rows**: ungraded "RECOMMENDED" lines throughout the prompt
  (Assumptions A128–135 + per-phase), not in the answer key, for the analytical/judgment layer.
- Recalc-dependent live-formula model: carried over from v1.
- Still to do for v2: deployed-env recalc + live run (shared with v1); optional further sourcing
  grids (Submarket reproduction).

## v1 history (below)

## Recalc-based grading (option #1) + prompt/world reconciliation (2026-06-11)
A full-workflow sub-agent run surfaced that the ~30k formula-grid cells (98% of checks) cannot be
graded without a recalc engine: the grader reads cached values, openpyxl does not compute, and the
env had none. Resolved by the "build the model, recalc, then grade" loop: the agent builds the
formulas, not just inputs.
- **LibreOffice is now a required env dependency** (HANDOFF §0).
- Added `tools/recalc.sh` (LibreOffice headless, forces recalc-on-load) and `grade.py --recalc`
  (recalcs a temp copy before grading; opt-in locally, run by default in the deployed harness).
  Self-test unaffected (30519/30519); `--recalc` degrades gracefully when LibreOffice is absent.
- Prompt: added the build → recalc → verify → fix working-method note; kept "IC Summary links
  everything" (correct under recalc).
- Fixed prompt↔template wording mismatches (found by the run): Deal Summary lives on the **IC
  Summary** tab (not Assumptions); comp tabs use a single **Comp Type** classification column (not
  Data Quality/Relevance); the **"Pure Reference--->"** separator tab already exists (don't add);
  pipeline tracker Ballantyne = **"Awaiting Info"** (P1) / **"Screened - Pass"** (P2), Strategy
  **"Stabilized Core"**, Asking **$28M** at P2.
- Fixed world: Email 8 IM attachment name `.xlsx` → `.pdf` (the file on disk is the PDF).
- **Broker-NOI inconsistency resolved (Option A).** The broker's *stated* NOI must equal what the
  OM prints (**$3,880,000**); the $3,860,366 was the T-12 *actual*. Set master IC Summary D34 to a
  literal $3,880,000 (XML surgery - the cell is display-only, nothing references it) and rebuilt
  `answer_key.json` (exactly one entry changed: `broker_noi` 3,860,366 → 3,880,000; self-test still
  30519/30519). An agent that reads the OM now passes that check.
- **Leverage Options layout documented.** Added the template's fixed column convention to the Phase 7
  prompt: an "Active Selection" column (chosen lender, repeated) + Atlantic Life (under "STALE QUOTE")
  / First Southeast / Piedmont, keyed off the "Term" row.
- **Still open:** the recalc grading path is verified only structurally here (no LibreOffice locally);
  end-to-end recalc grading and a real live run are to be confirmed in the deployed env.

## Converted to template-fill (2026-06-11)
Resolved the grader-vs-prompt mismatch (a build-from-scratch agent scored ~2% on the ~30k-cell
grid because it could not reproduce the master's ~477 verbatim labels). The agent is now given a
pre-structured workbook to fill:
- `world_files/internal/SouthPark_Centre_Model_Template.xlsx` - all 14 tabs, every section/row
  label, and the Month # period headers in place; all value cells blank. `setup_env.sh` seeds it
  to `/tmp/outputs/southpark_centre_underwriting.xlsx` (the grader's expected filename).
- The prescriptive prompt's "Create the workbook" step is now "fill in the provided workbook,"
  with a preamble describing the template and a keep-labels-intact instruction.
- HANDOFF grading-mode note updated to END-STATE + TEMPLATE-FILL.
- **Grader unchanged** - it keys cells by (tab, row-label, occurrence, column), which now match by
  construction. Verified: graded as-is the template scores ~0.8% (no answer leakage), with every
  keyed cell located-but-blank; all monthly period headers intact (grid columns map).
- Built the template by blanking values/formulas via **XML surgery**, not openpyxl resave
  (openpyxl wipes the ~30k cached formula values, which destroyed the formula-based Month #
  headers - caught and reverted). Also blanked 5 leftover summary formulas (Property Cash Flow
  Required Capital / Profit / Repayment) that had cached to 0.

## World PDFs restyled to Times 12pt / grayscale / industry prose (2026-06-11)
Re-rendered all 46 world PDFs so they read as genuine industry documents rather than
draft-like output, preserving every fact and figure (verified zero lost numeric tokens,
so the planted traps and all extractable values are intact):
- **Times New Roman throughout** (Times-Roman/Times-Bold only) and **grayscale only** (zero
  colored spans).
- **Prose at 12pt** (body, labels, values) - the dominant text size. Table cells stay 10pt
  (8pt for wide tables like the 14-column rent roll and the comp sheets, which cannot fit at
  12pt); section headers 13pt, document titles 17pt, for normal document hierarchy.
- **Punctuation style normalized** to use hyphens consistently; no literal em dashes remain.
- The existing prose was already industry-grade (the OM reads as a real broker offering; lease
  abstracts and term sheets use the correct terse label:value format) and was preserved.
- Ground-truth output files were NOT touched.

## Restructured into the artemis-odyssey convention (2026-06-11)
Moved the packaged task from the standalone working folder into the repo layout the other tasks
use, no grader logic changed:
- Grader package -> `tools/grader/` (`grade.py`, `extract.py`, `build_key.py`, `answer_key.json`,
  `selftest.py`); new top-level `grade.py` shim delegates to it and adds `--self-test`.
- `World Files/` → `world_files/`; `Ground Truth Files/` → `ground_truth/` (subdirs preserved so
  the key builder/self-test paths hold); `call_budget.py` → `tools/`; `setup_env.sh` paths updated.
- The 20 lease abstracts renamed `Lease_Abstract_NN_<Tenant>.pdf` → `Lease_Abstract_Tenant_NN.pdf`
  to match the prescriptive prompt's file references.
- `prompts/agent_prompt_prescriptive.txt` = the author's 8-phase prompt, **verbatim**.
  `prompts/agent_prompt_buildcontract_v1.md` = the detailed build-from-scratch contract (exact
  tab/row labels the grader keys on). `HANDOFF.md` = the full runtime & grading spec.
- **Verified after the move:** `grade.py --self-test` = Identity **30519/30519**, Tracker PASS,
  Robustness 99.8%, Detection PASS; `tools/call_budget.py` = coarse **336** / granular **705**;
  world = 46 PDF / 17 XLSX / 9 HTML, all 20 leases renamed.

## Master ground truth reconciled & locked (2026-06-10)
The author shipped a single final-state master model (not per-phase iterations). Reconciled six
items by surgical XML edits that preserve the ~23k cached formula values (logged in HANDOFF §1):
Year Built 2014→2001, Broker NOI display cell → literal $3,880,000, address "...2821"→"...28211",
tracker P8 "LOI Submitted"→"LOI Sent"; two flagged cells confirmed **not** defects (the Atlantic
"ERROR" stale column and the 18-tenant occupied count). Grading decided to be **end-state**: the
final workbook is scored against the master; the VP revision cascade is verified via the final
$50M / $40 TI / month-6-8-10 anchors plus the reconciliation invariants. Accepted trade-off: an
agent could build the final state directly and skip the ~5% revision loop undetected.

## Grader built & self-tested (2026-06-10)
Deterministic, layout-tolerant, end-state grader: ~30,500 checks across three layers - the full
calculation grid (~29,840 formula cells of the four calc tabs, ~99% coverage), 180 reconciliation
invariants on the submission's own values, and ~340 per-phase deliverable checks (anchors, LOI
terms, 25 sales + 50 lease comp classifications, leasing buckets, the per-lender leverage matrix,
the 3 sensitivity tables, per-phase tracker statuses). Self-test injects the stale-lender trap,
the Brightpath value, a hardcoded NOI, a per-tenant engine cell, broken invariants, and a
mis-classified comp, and confirms the grader fails exactly those.

## World format-reconciled (2026-06-10)
The author's source files were spreadsheets/Sheets exports. Converted the document-type inputs
(OM, 20 lease abstracts, term sheets, GC bids, inspection/market reports) to **PDF** so each is a
genuine read-and-interpret (the primary reason the bash agent's call count does not collapse);
data tables kept as XLSX; emails as HTML. Result: 46 PDF / 17 XLSX / 9 HTML, 0 broken references.

## Open items
- **Not yet run by a real agent in a deployed Fleet env** - self-tested against ground truth only;
  the ~705-call estimate and the 0.90 pass threshold are unverified until a live run.
- ~1% of formula cells (dates/flags + a few unkeyable scalars) are not grid-graded; covered
  indirectly via downstream cells + invariants.
- The author's original `.docx` submission still carries the template's example boilerplate
  (cosmetic).
