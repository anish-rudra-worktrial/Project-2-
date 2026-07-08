# SouthPark Centre — Runtime & Grading Spec (reconciliation working doc)

Status: DRAFT / LOCAL FILE-BASED SPEC. Section 0-2 + Phase 1 are the agreed template. Phases 2-8
follow the same pattern. This doc is what an engineer + the local grader build from; the master
model is the reference, this doc is the authority where they disagree.

Deployment note (2026-07-07): the Fleet workbench task currently observed for
`odyssey-real-estate-pe-underwriting-full_243edf59_v1` is an Outlook + Fropbox/Docket adaptation,
not this exact `/data` + `/tmp/outputs` local task. See `QA_ASSESSMENT.md` and
`DEPLOYMENT_ALIGNMENT.md` before changing the deployed prompt, seed, or verifier.

---

## 0. Runtime environment & the anti-collapse principle

**Local environment:** a bash/file environment. The agent reads `/data/**` (PDFs + XLSX) and
writes its workbook(s) to `/tmp/outputs/`. PDFs are read with normal tooling (pdftotext /
python); XLSX with openpyxl/pandas. **LibreOffice (`soffice`) is required in the image** for the
recalc step below — this is a hard env dependency for grading.

**Deployed Fleet environment:** the observed deployed task uses Outlook + Fropbox/Docket. It expects
the deal room at `/SouthPark Centre Underwriting`, final uploads in
`/SouthPark Centre Underwriting/Outputs`, and Python spreadsheet libraries such as `openpyxl` or
`xlsxwriter`. The deployed verifier is evidence-weighted and does not run this local full-grid
grader. Do not copy the local `/tmp/outputs` or LibreOffice requirement into that prompt unless the
deployed harness is intentionally changed to match the local file-based contract.

**Runtime model — build the model, recalc, then grade (decided 2026-06-11).** The intended
workflow is the real analyst loop and is what makes this a maximum-manual-work task:
1. The agent **builds the full live-formula model** in the blank template — the rent-roll calc
   engine, the 60-month proforma, CapEx, debt schedule, and waterfall (~30,000 formula cells),
   plus the linked IC Summary ("every value links to another tab"). This is the bulk of the work.
2. The agent **recalculates** (LibreOffice headless) and **checks its outputs** against the
   stated anchors, fixes formula errors, and re-runs — a genuine build/verify loop.
3. **Grading recalcs the submission, then reads cached values.** The grader reads with
   `data_only=True` (cached values); openpyxl has no formula engine and writes/leaves formula
   cells with no cache, so a recalc pass is mandatory before grading. Run `tools/recalc.sh
   <submission_dir>` (LibreOffice headless, forces recalc-on-load) — or `python3 grade.py
   <dir> --recalc`, which recalcs a temp copy first. The deployed grading harness must run this
   by default. Without LibreOffice, formula cells read blank and the ~30k grid scores ~0.
   (An agent may instead write literal computed values, but for this task it is expected to build
   formulas and rely on recalc.)

**Why the call count won't collapse — by design, not by a verb layer.** A bash agent could
in principle emit the whole model from one script. It cannot here, because the work is
*irreducible per-item reasoning over unstructured inputs* that no single script can shortcut:

1. **46 PDFs must be opened and interpreted** — 20 lease abstracts, 3 term sheets, 3 bids,
   the OM, market reports, inspection reports. Each is a real read+extract+interpret. This is
   the primary reason the inputs were converted from spreadsheets to PDFs.
2. **Per-item judgment, graded individually.** Each of 75 comps gets an include/exclude
   decision + rationale; each of 20 tenants gets a market-rent benchmark + assumption
   selection + deviation note; each planted discrepancy gets a reconciliation entry citing the
   source cell. Because the grader scores *each item*, the agent must actually do each one.
3. **Verification passes.** After the VP revisions (Phase 6) the agent re-opens and confirms
   the cascade item-by-item.

**Grading model:** the agent's workbook is opened with values computed (`data_only`); the
grader extracts named **anchor values** and **per-item rows** and compares to the key with
tolerances. Grading is layout-independent (anchors found by section/label, not fixed cells),
because the agent builds its own layout.

---

## 1. Master-GT defects — RECONCILED & LOCKED (2026-06-10)

Master edited surgically in the underlying XML (NOT via openpyxl, which would have wiped all
~23K cached formula results — verified the cache is fully intact after editing). The exact
before→after of every change is in the table below, so the pre-fix state is fully reconstructable.

| # | Location | Was | Now | Status |
|---|----------|-----|-----|--------|
| 1 | IC Summary D9 (Year Built) | 2014 | **2001** | ✅ FIXED (literal). OM: built 2001, renovated 2014. |
| 2 | IC Summary D34 (Broker's Stated NOI) | `='T-12'!N28` → 3,860,366 | **literal 3,880,000** | ✅ FIXED. Must equal the OM figure the agent reads; D34 is display-only (nothing references it). |
| 3 | Address (Assumptions A2 → IC D5, LOI B7) | "...NC 2821" | **"...NC 28211"** | ✅ FIXED (shared string + 2 cached formula values). |
| 4 | Leverage Options D34/D35 = `ERROR` | `ERROR` | `ERROR` | ✅ NOT A DEFECT — this is the **Atlantic Life (stale)** column; the formula intentionally returns "ERROR" for the stale quote (`IF(quote="STALE","ERROR",…)`). Piedmont (col F) computes fine. Left as-is. |
| 5 | IC Summary D14 (Tenant count = 18) | 18 | 18 | ✅ NOT A DEFECT — `=COUNTIF('Rent Roll'!N5:N32,"Occupied")`. Flags: Meridian="Departing", Dental="Ghost", 18 others="Occupied". **Rule:** occupied-and-staying = 20 leased − Meridian − ghost = 18. |
| 6 | Tracker P8 status (`GT_Pipeline_Tracker_P8`) | "LOI Submitted" | **"LOI Sent"** | ✅ FIXED (I5 + K5 note) to match spec Phase 8 wording. |

Also pinned: **Going-In Cap Rate** semantics — IC D12 = 5.74% is the **Year-1 proforma NOI**
basis; reconciled-NOI/price = 7.5%. Grader must check the intended one by label, not assume.

---

## 2. Per-phase structure (pre- vs post-revision)

**TEMPLATE-FILL (decided 2026-06-11).** The agent is given a pre-structured workbook
(`world_files/internal/SouthPark_Centre_Model_Template.xlsx`, seeded by `setup_env.sh` to
`/tmp/outputs/southpark_centre_underwriting.xlsx`) that carries all 14 tabs, every section/row
label, and the Month # period headers, with all value cells blank. The agent fills in the
values; it does not invent the layout. This is what makes the ~30k full-grid grade fair: the
grader locates cells by (tab, row-label, occurrence, column), so the agent's labels match the
key by construction. (A build-from-scratch agent, by contrast, would have to reproduce ~477
verbatim master labels and would score ~2% on the grid — which is why the template route was
chosen.) The template is verified to leak no answers: graded as-is it scores ~0.8%, with every
keyed cell located-but-blank.

**GRADING IS END-STATE (decided 2026-06-10).** The agent's *final* workbook (after Phase 8) is
graded against the master. The phases below describe the agent's *path*, but only the end state
is scored — there are no pre-revision checkpoint workbooks, and none are needed. The VP revision
is still verified, because the final post-revision values ($50M / $40 TI / months 6-8-10) are
graded anchors and the reconciliation invariants confirm the model is linked. Accepted
trade-off: an agent could build the final state directly and skip the ~33-call (~5%) revision
loop without detection — acceptable given every final cell is still graded.

| Phase | State | Key shifts vs master |
|-------|-------|----------------------|
| 1 Intake/Reconcile | pre | price $52M asking |
| 2 Deal B screen | n/a | separate file |
| 3 Market comps | pre | — |
| 4 Lease-by-lease | **pre** | spec-suite TI **$35**, buildout start **M4/M6/M8** |
| 5 Monthly proforma | **pre** | $52M, TI $35, M4/M6/M8 |
| 6 VP revisions | applies | → $50M, TI $40, M6/M8/M10 |
| 7 Debt | post | $50M |
| 8 Waterfall/IC/LOI | post | $50M |

---

## PHASE 1 — Deal Intake, Screening & Pipeline Setup  (TEMPLATE)

### Deliverables the agent produces
- `southpark_centre_underwriting.xlsx` → tabs **Assumptions** (Deal Summary), **Rent Roll**
  (20 rows), **Rent Roll Calc** (structure + in-place data).
- A **Reconciliation Log** (new graded artifact — see below).
- `Pipeline_Tracker_Q2_2026.xlsx` updated (2 new rows).

### 1A. Reconciliation Log  — *forces manual cross-referencing*
One row per planted discrepancy. The agent must open each cited source to fill it, so this
cannot be batch-derived. Columns: `Item | Source file + location | Broker/Rent-roll value |
Reconciled value | Decision | Citation`.

| Item | Source to open | Broker value | Reconciled value | Decision |
|------|----------------|--------------|------------------|----------|
| Ghost tenant #20 SouthPark Dental | Rent roll + Lease_Abstract_20 (exp 3/31/2026) | counted in occ | vacated → exclude | occupancy 78.0% → **77.4%** |
| Brightpath #6 rent | Rent roll ($21.25) vs Lease_Abstract_06_Brightpath ($20.75) | $21.25/SF | **$20.75/SF** ($163,925) | use abstract |
| Westlake termination fee | OM other-income | $42,000 | **exclude** | non-recurring |
| Antenna income | OM + Vendor_Contracts_Summary | $62,000 | **$32,000** | Sprint ($30K) expired Feb 2026; T-Mobile only |

*Manual-work driver:* requires opening the OM (PDF), the rent roll, Lease_Abstract_06 (PDF),
Lease_Abstract_20 (PDF), and Vendor_Contracts_Summary — 5+ distinct reads, each with a
reasoned decision.

### 1B. Rent Roll tab — *forces 20 PDF reads*
20 tenant rows transcribed from `Rent_Roll_Current_05-2026.xlsx` **and cross-verified against
the 20 lease-abstract PDFs** (each a separate open). Graded **per row** on: tenant name, suite,
SF, rent $/SF, escalation %, expiry. Anchor specifics:
- #1 Meridian: 76,000 SF, $19.50, exp **10/31/2026**.
- #6 Brightpath: 7,900 SF, **$20.75** (corrected), annual **$163,925**.
- #20 SouthPark Dental: 1,800 SF, exp **3/31/2026** (vacated).
- Total leased SF **216,600** after removing the ghost (broker showed 218,400).

*Manual-work driver:* 20 lease-abstract PDFs must each be opened to verify terms. Per-row
grading means skipping any tenant loses points.

### 1C. Assumptions — Deal Summary (broker vs reconciled), anchor values + tolerances
| Metric | Broker stated | Reconciled (key) | Tolerance |
|--------|---------------|------------------|-----------|
| Asking/Purchase price | $52,000,000 | $52,000,000 (Phase 1) | exact |
| Total SF | 280,000 | 280,000 | exact |
| Occupancy | 78.0% | **77.4%** (216,600/280,000) | ±0.1% |
| Trailing NOI | $3,880,000 | reconciled NOI (per model) | ±$5,000 |
| In-place cap | 7.5% | reconciled cap | ±0.05% |

### 1D. Pipeline Tracker (P1) — exact-match rows
- SouthPark Centre: Status **Screening**, Broker Crestline Advisors, SF 280,000, Asking $52M, Strategy Value-Add.
- Ballantyne Office Centre: Status **Screening**, Broker Ashford Partners, SF 120,000, Asking TBD, Strategy Core.

### Phase 1 grading summary
- ~4 reconciliation-log rows (each: decision + citation correct).
- 20 rent-roll rows × ~6 fields (per-row credit).
- 5 Deal Summary anchors.
- 2 tracker rows × 6 fields.
Grade = fixed-denominator over all the above. **Manual-work floor for Phase 1 alone:** ≥ ~25
PDF/file reads (OM + 20 abstracts + vendor contracts + rent roll + tracker) plus per-item writes.

---

## PHASE 2 — Deal B Quick Screen
- **Deliverable:** `ballantyne_wacc_screen.xlsx`; tracker → Ballantyne "Screened - Pass".
- **Manual-work driver:** read the Ballantyne IM (PDF) + rent roll; sanity-check tenant count/SF.
- **Anchors (key, ±0.001–0.002):** Going-In Cap Rate 0.0554 · Unlevered IRR (cap+growth) 0.0754
  · Implied Cost of Equity (Re) 0.1059 · Fund Minimum Levered IRR 0.15 · Shortfall to Hurdle −0.0441.
  Verdict = **Fail/Pass on the deal** (Re < hurdle).

## PHASE 3 — Market & Comparable Analysis  (biggest fan-out)
- **Deliverables:** `Sales Comp Analysis`, `Rental Comp Analysis`, `SouthPark Submarket` tabs;
  Rent Roll rent-benchmark section; tracker → "Underwriting - Market Research".
- **Per-item graded deliverable (anti-collapse):** each of **25 sales comps** and **50 lease
  comps** gets a `Comp Type` classification (1 usable / 2 older / 3 wrong submarket·type /
  4 incomplete). Graded **per comp #**. Sales-comp truth: type1=13, type2=6, type3=4, type4=4.
- **Manual-work driver:** 75 comps each read + judged; two market-report PDFs read.

## PHASE 4 — Lease-by-lease Underwriting & Assumptions   *(pre-revision)*
- **Deliverable:** Assumptions leasing-by-size table + spec-suite plan + JV terms.
- **Per-item driver:** 20 tenants each benchmarked to a market rent (size bucket) with renewal
  prob / downtime / TI / LC / free rent; Meridian (#1) → 0% renewal, 6 spec suites.
- **Anchors:** Spec Suite Buildout Duration 6 · GP Equity Share 0.10 · Preferred Return 0.08.
  **Pre-revision only (needs a P4 snapshot to grade):** Spec Suite TI = **$35**, buildout start
  **M4/M6/M8**. (Master holds the post-revision $40 / M6/M8/M10.)

## PHASE 5 — Monthly Proforma (initial build)   *(pre-revision)*
- **Deliverables:** `Property Cash Flow` (unlevered), `CapEx Schedule`, `Exit Analysis`.
- **Anchors:** Year 1 Proforma NOI 2,957,772 · Stabilized NOI 6,027,050 · Exit Year NOI
  6,545,315 · Exit Cap Rate 0.0775 · Gross Exit Value 84,455,681 · Net Sale Proceeds 82,766,567
  · Unlevered IRR 0.1147 · Equity Multiple (unlevered) 1.808.
  *(NOTE: at $52M pre-revision the IRR/value differ slightly; a P5 snapshot is needed to grade
  the pre-revision build exactly. The frozen anchors are the final-state values.)*

## PHASE 6 — VP Revisions
- **Deliverable:** Assumptions + Property Cash Flow + CapEx updated; tracker → "Underwriting -
  VP Revisions Applied".
- **Manual-work driver:** read Email 9; apply 3 changes; **re-verify the cascade item-by-item**.
- **Anchors:** Purchase Price → **$50,000,000** · Spec Suite TI → **$40**. (Timing → M6/M8/M10.)

## PHASE 7 — Construction Loan & Debt
- **Deliverable:** `Leverage Options` tab; Property Cash Flow debt + levered sections.
- **Manual-work driver:** read 3 term-sheet PDFs + Email 6; mark Atlantic Life STALE; underwrite
  the two viable lenders (size loan, construction interest, conversion, levered IRR).
- **Anchors:** Selected Lender = **First Southeast Bank** · Loan Amount 57,936,597.
  (First Southeast levered IRR 23.57% > Piedmont 21.43%; Atlantic = stale trap.)

## PHASE 8 — Waterfall, Returns, IC & LOI
- **Deliverables:** `Waterfall`, `IC Summary`, `LOI` tabs; Assumptions sensitivity tables;
  tracker → "LOI Sent".
- **Anchors:** GP IRR 0.3295 · LP IRR 0.2212 · LP Equity Multiple 2.120 · Total Project IRR
  0.2357 · Deal IRR (Total Equity) 0.2357 · Peak Equity Outstanding 15,049,175 · GP Share of
  Total Profit 0.20 · Residual Split GP 0.20 · Recommendation **GO**.

---

## Build status (2026-06-10)
- ✅ Master locked (§1). ✅ `tools/grader/answer_key.json` (**~30,360 checks — every cell + every
  phase deliverable**). ✅ `tools/grader/grade.py` + `tools/grader/selftest.py` (run via top-level `grade.py --self-test`). ✅ `prompts/agent_prompt_buildcontract_v1.md`.
- **Grading verifies every calculation AND every phase deliverable** — three layers:
  (1) **~29,840 full-grid cells** — EVERY numeric formula cell of the four calc tabs (RRC 23,175,
  PCF 2,973, Waterfall 3,129, CapEx 563; ~99%); (2) **180 reconciliation invariants**; (3)
  **~340 per-phase deliverable checks** — anchors + LOI terms + Submarket + per-item tables
  (rent roll w/ benchmark, **25 sales + 50 lease** comps, leasing buckets) + Leverage per-lender
  matrix + 3 sensitivity tables + tracker. **All 8 phases covered** (P3/P7/P8 holes closed).
- **Self-test result observed 2026-07-07:** Identity **30797/30797**, Tracker per-phase **PASS**,
  Layout-robustness **27621/30797**, **Detection PASS** (stale lender,
  Brightpath trap, hardcoded monthly NOI, a per-tenant Rent Roll Calc cell, broken invariants,
  a mis-classified comp — all caught).
- **Grading mode: END-STATE, TEMPLATE-FILL** (final workbook scored; the agent fills the provided
  pre-structured template so its labels match the grader's keys — decided 2026-06-10/06-11).
- **Remaining before production:** (1) run a real agent in a deployed Fleet env (self-tested vs
  GT only so far; ~705-call estimate + 0.90 threshold unverified until a live run); (2) the ~1%
  non-grid cells (dates/flags/scalars) are covered indirectly; (3) cosmetic docx boilerplate.
