# Runtime Prompt — SouthPark Centre Underwriting — **v1: BUILD FROM SCRATCH**

> **Version:** v1 (build-from-scratch). The agent creates the entire 14-tab workbook from a blank
> file, following the prescriptive steps below (exact assumptions, line items, and formulas, keyed
> by tab + row label — no pre-built template, no hard cell coordinates). This preserves the
> ~700-call profile and feeds the cell-level grader. A separate **v2 (template-fill)** variant
> hands the agent a pre-structured workbook and uses exact cell references — to be written next.
> All prescribed values are verified against the locked ground truth (`grader/answer_key.json`).

---

The task is to underwrite two office acquisitions for Harborview Capital Partners (Fund III) over
one week and produce a full institutional model. **Deal A — SouthPark Centre** (NYSE-style ticker
n/a; 4800 Sharon Road, Charlotte, NC 28211; 280,000 RSF Class B+ value-add office, broker Crestline
Advisors, $52,000,000 guidance) gets a full 14-tab model, IC package, and LOI. **Deal B — Ballantyne
Office Centre** (120,000 SF stabilized Class A-, broker Ashford Partners) gets a quick WACC screen.

You are a second-year acquisitions associate. It is the week of **June 1, 2026**. Your inputs are an
email inbox (`/data/emails/`, read in chronological order Email_01 → Email_09) and a data room
(`/data/dataroom/`, `/data/dataroom_deal_b/`, `/data/internal/`, `/data/lenders/`,
`/data/construction/`, `/data/market_research/`). Build Deal A in
`/tmp/outputs/southpark_centre_underwriting.xlsx`, Deal B in
`/tmp/outputs/ballantyne_wacc_screen.xlsx`, and maintain `/tmp/outputs/Pipeline_Tracker_Q2_2026.xlsx`
(start from the copy in `/data/internal/`). Use the exact tab names and row labels given below — the
grader locates values by them. Where an assumption is given "for simplicity," use exactly that value
(it is graded); where you are asked to make a recommendation, put it in the noted space (not graded).

---

## Phase 1 — Deal Intake, Reconciliation & Pipeline Setup
Tabs created: **Assumptions, Rent Roll, Rent Roll Calc.**

→ Read `Offering_Memorandum_SouthPark_Centre.pdf` (`/data/dataroom/`). On the **Assumptions** tab, in a
"Deal Summary" section with two columns (Broker's Stated Value | Reconciled Value), record the broker
headline metrics: Asking Price **$52,000,000**, Total SF **280,000**, Stated Occupancy **78.0%**,
Stated Trailing NOI **$3,880,000**, Stated In-Place Cap **7.5%**, Price/SF, Year Built **2001**, Last
Renovated **2014**, Parking 840 spaces.
→ Open `Rent_Roll_Current_05-2026.xlsx` (`/data/dataroom/`). Build the **Rent Roll** tab preserving all
**20 tenant rows** with columns: #, Tenant, Suite, Floor, SF, Rent $/SF, Annual Rent, Esc %, Esc Mo,
Lease Start, Expiry, Renewal, Status.
→ Open all **20 lease abstracts** in `/data/dataroom/lease_abstracts/`
(`Lease_Abstract_01_Meridian_Financial.pdf` … `Lease_Abstract_20_SouthPark_Dental.pdf`) and verify each
tenant's terms against the rent roll, one tenant at a time.
→ Reconcile the broker's numbers. Log one entry per discrepancy (source file, broker value, reconciled
value, decision):
  - **Tenant #20 SouthPark Dental** — rent roll shows it leased, but the lease expired **3/31/2026** and
    the suite is vacant. The broker counts it in occupancy. **Correct occupancy from 78.0% (218,400 SF)
    to 77.4% (216,600 SF)** and zero this tenant.
  - **Tenant #6 Brightpath Insurance** — rent roll shows **$21.25/SF**; the lease abstract shows
    **$20.75/SF** (escalation applied to the wrong base year). **Use $20.75** (Annual Rent $163,925).
  - **Lease termination fee $42,000** (Westlake Analytics, Nov 2025) in the OM other-income — **exclude**
    (non-recurring).
  - **Antenna income $62,000** — Sprint's $30,000 contract **expired Feb 2026**; only T-Mobile's
    **$32,000** is active. Verify against `Vendor_Contracts_Summary.xlsx`. **Use $32,000.**
→ Build the **Rent Roll Calc** tab structure: one block per tenant/suite with rows for Occupancy Flag,
In-Place Rent, Re-Let Flag, Re-Let Rent (gross), Free Rent Adj, Net Base Rent, Opex Recovery (NNN),
TI (capital), LC (capital), and monthly columns (Month 0 = close). Populate the in-place tenant data
now; the cash-flow engine is completed in Phase 5.
→ Read **Email 7** (Sarah mentions a Ballantyne deal). On **Pipeline_Tracker_Q2_2026.xlsx** add two rows:
SouthPark Centre — Status **Screening**, Broker Crestline Advisors, SF 280,000, Asking $52M, Strategy
Value-Add; Ballantyne Office Centre — Status **Awaiting Info**, Broker Ashford Partners, SF 120,000,
Asking TBD, Strategy Stabilized Core.

## Phase 2 — Deal B Quick Screen (Ballantyne)
→ Read **Email 8** (Sarah forwards the Ballantyne IM and rent roll) and `Ballantyne_Office_Centre_IM.pdf`
(`/data/dataroom_deal_b/`). Extract: Asking Price **$28,000,000**, SF **120,000**, Occupancy **94%**,
Trailing NOI **$1,550,000**, Projected Rental Growth **2.0%**.
→ Open `Ballantyne_Rent_Roll.xlsx` and sanity-check tenant count (12) and total SF vs the IM. No
lease-by-lease analysis.
→ In `ballantyne_wacc_screen.xlsx`, compute the WACC screen with these exact labels/values:
  - **Going-In Cap Rate** = NOI / Price = 1,550,000 / 28,000,000 = **5.54%**
  - **Unlevered IRR (Cap Rate + Growth)** = 5.54% + 2.0% = **7.54%**
  - **Cost of Debt (All-In)** = **5.5%** (per Email 8, Rachel Kim indication); **Assumed LTV** = **60%**;
    Equity Weight = 40%.
  - **Implied Cost of Equity (Re)** = (Unlevered IRR − LTV × Rd) / (1 − LTV)
    = (0.0754 − 0.60 × 0.055) / 0.40 = **10.59%**
  - **Fund Minimum Levered IRR** = **15%** (`Fund_Investment_Criteria.pdf`, `/data/internal/`);
    **Shortfall to Hurdle** = 10.59% − 15% = **−4.41%**.
→ Write a 2–3 sentence **Pass** recommendation (priced too tight; no value-add angle). Update the tracker:
Ballantyne Status → **Screened - Pass**.

## Phase 3 — Market Research & Comparable Analysis
Tabs created: **Sales Comp Analysis, Rental Comp Analysis, SouthPark Submarket.**

→ Read `Charlotte_Office_Market_Report_Q1_2026.pdf` and `SouthPark_Submarket_Report_Q1_2026.pdf`
(`/data/market_research/`). Build the **SouthPark Submarket** tab reproducing: Overall Vacancy Rate
**14.8%**, Class A asking rent **$28.50/SF**, Net Absorption (TTM) **185,000 SF**, Under Construction
**320,000 SF**, 12-Month Rent Growth (Class B+) **2.8%**.
→ Open `Comparable_Sales_Data_Charlotte_Office.xlsx` (25 transactions). Build **Sales Comp Analysis**
with a **Comp Type** column classifying **each** comp on this 4-level scale: **1** = usable current
(**12** comps), **2** = older / crisis-era (**5**), **3** = wrong submarket or type (**4**),
**4** = incomplete (**4**). Evaluate every comp individually — do not bulk-filter.
→ Open `Comparable_Lease_Data_SouthPark.xlsx` (50 transactions). Build **Rental Comp Analysis** with a
**Comp Type** column on this 6-level scale: **1** = large-block build-to-suit (**1** — the Meridian BTS,
80,000 SF in Ballantyne), **2** = usable current small/medium (**25**), **3** = older (**8**),
**4** = wrong submarket (**6**), **5** = wrong type (**5**), **6** = incomplete (**5**). The single
large-block comp confirms there is **no comp** supporting leasing the 76,000 SF anchor space as one
block.
→ Extend the **Rent Roll** tab with a rent-benchmark section mapping each of the 20 tenants to a market
rent by size bucket, with the in-place-vs-market spread.
→ Update tracker: SouthPark → **Underwriting - Market Research**.

## Phase 4 — Lease-by-Lease Underwriting & Assumptions
Tab extended: **Assumptions** (leasing-by-size, spec-suite parameters, JV terms).

→ Read `Standard_Lease_Assumptions_Guide.pdf` (`/data/internal/`). On **Assumptions**, add a
"Leasing Assumptions by Size" table (use exactly these — they are graded):

| Bucket | Mkt Rent $/SF | Renew % | Downtime (mo) | New TI $/SF | Ren TI $/SF | LC % | Free New (mo) | Free Ren (mo) |
|---|---|---|---|---|---|---|---|---|
| < 2,000 | 24.0 | 0.50 | 7 | 28 | 10 | 0.06 | 3 | 1 |
| 2,000–5,000 | 25.0 | 0.55 | 6 | 32 | 12 | 0.06 | 2 | 1 |
| 5,000–15,000 | 25.5 | 0.65 | 5 | 36 | 16 | 0.05 | 2 | 1 |
| > 15,000 | 25.0 | 0.75 | 4 | 40 | 20 | 0.04 | 2 | 0 |

  - Renewal market rent = **95%** of new-lease market rent (renewal discount).
  - **Spec Suite TI = $35/SF** and **Buildout Duration = 6 months** (these are revised in Phase 6).
  - JV / Equity Waterfall: **GP Equity Share 10% / LP 90%**, **Preferred Return 8.0%** (compounding,
    accruing on both GP and LP equity), **50/50 catch-up to a 20% GP profit share**, **residual 80% LP /
    20% GP** (per Emails 3 and 4).
→ Apply per-tenant assumptions on Rent Roll / Rent Roll Calc, one tenant at a time, using the bucket the
tenant's SF falls into; document any deviation with a supporting comp.
  - **Tenant #20** (ghost): Renewal % **0**, vacated.
  - **Tenant #1 Meridian** (76,000 SF): Renewal % **0**, departing per the CBJ article
    (`CBJ_Meridian_HQ_Relocation.pdf`); **underwrite Meridian's rent through its 10/31/2026 expiry**, not
    the article's move date.
  - The three near-term rollovers (Carter exp 9/2027, Lakeview 7/2027, Queen City 1/2028): probability-
    weight renewal vs. vacancy.
→ Model the Meridian departure as **6 spec suites** on Rent Roll Calc (SF, floor, buildout start month):
Suite 610 = 14,000 (fl 6), 620 = 13,000 (fl 6), 710 = 13,000 (fl 7), 720 = 12,000 (fl 7), 810 = 12,500
(fl 8), 820 = 11,500 (fl 8); total **76,000**. Buildout start: **floor 6 = month 4, floor 7 = month 6,
floor 8 = month 8** (revised in Phase 6).

## Phase 5 — Monthly Proforma (initial build)
Tabs created: **Property Cash Flow, CapEx Schedule, Exit Analysis.** 60-month model, Month 0 = close.

→ On **Property Cash Flow** build the monthly unlevered model with these rows: Occupancy %, Net Rental
Income, Expense Recovery (NNN), Other Income, Effective Gross Income, General Vacancy Adjustment,
Operating Expenses, Management Fee, Net Operating Income, then capital and cash-flow rows.
  - Contractual rent escalations apply on each lease's anniversary. Rolling tenants use expected-value
    blended revenue. Meridian pays through month 3 (Oct 2026), then the spec suites phase in per the
    buildout timing.
  - Reimbursement (NNN): each tenant's pro-rata share of the **reimbursable pool = all opex except
    management fee and marketing**; vacant suites = 0.
  - Other Income: Parking **$230,000/yr growing 2.5%**, Antenna **$32,000/yr growing 2.0%**, Storage
    **$20,000/yr flat**.
  - Operating Expenses: escalate from reconciled Year-1 levels at the **30-year CPI average of 2.7%**
    (`US_Inflation_Data.xlsx`). **Management Fee = 3.5% of EGI** (circular — solve iteratively or lag).
  - Reconciliation invariants the model must satisfy each month: **EGI = Net Rental + Expense Recovery +
    Other Income**; **NOI = EGI + Vacancy + Operating Expenses + Management Fee** (the latter three
    negative).
→ **CapEx Schedule**: renovation **$7,500,000 (Pinnacle)** phased per `Renovation_Timeline_Gantt.pdf`
(`/data/construction/`; select among the three `Contractor_Bid_*.pdf` on scope alignment with
`Area_Schedule_SouthPark_Centre.xlsx`, not lowest price); ongoing TI/LC per the leasing assumptions;
building reserves **$0.50/SF escalating 2.5%/yr**.
→ **Exit Analysis**: Exit Cap Rate **7.75%** applied to forward-12-month NOI at month 60; **2.0%**
disposition costs; compute Gross Exit Value, Net Sale Proceeds, and the unlevered Equity Multiple.

## Phase 6 — VP Revisions
Tabs modified: **Assumptions, Property Cash Flow, CapEx Schedule** (no new tabs — this tests model
linkage).

→ Read **Email 9** (Sarah Chen, Wed June 3). Apply exactly three changes:
  1. **Purchase Price: $52M → $50,000,000** (base case). Flows to loan sizing, equity, and all returns.
  2. **Spec Suite TI: $35 → $40/SF.** Cascades to all six suites, the CapEx Schedule, total project cost,
     loan sizing, equity.
  3. **Buildout timing: push floor 6 from month 4 → month 6, floor 7 → month 8, floor 8 → month 10**
     (shifts all spec-suite commencement +2 months).
→ Re-open Property Cash Flow, CapEx Schedule, and Exit Analysis and confirm the cascade. Update tracker:
SouthPark → **Underwriting - VP Revisions Applied**.

## Phase 7 — Construction Loan & Debt Schedule
Tab created: **Leverage Options.** Tab extended: **Property Cash Flow** (debt + levered sections).

→ Read the three term sheets in `/data/lenders/` and **Email 6** (Rachel Kim flags Atlantic Life's lack
of capacity). Build a **Leverage Options** lender comparison (one column per lender):

| Term | First Southeast Bank | Atlantic Life Insurance | Piedmont Capital |
|---|---|---|---|
| All-In Rate | 7.10% (SOFR+275) | 6.35% (SOFR+200) | 6.85% (SOFR+250) |
| Maximum LTC | 75% | 80% | 70% |
| Maximum LTV (stab.) | 70% | 75% | 65% |
| DSCR at Conversion | 1.25x | 1.15x | 1.20x |
| Interest-Only | 24 mo | 36 mo | 18 mo |
| Term | 5 yr | 10 yr | 7 yr |
| Origination Fee | 1.00% | 0.50% | 0.75% |

  - **Mark Atlantic Life "STALE — No Capacity"** (per Email 6). Atlantic has the *best* terms; selecting
    it fails the task.
  - **Underwrite BOTH viable lenders** (First Southeast and Piedmont): size the loan (LTC/LTV/DSCR
    constrained), compute capitalized PIK construction interest, the 18-month draw schedule, the
    conversion month (first month DSCR threshold is met), and the levered IRR for each.
  - Total project cost uses the revised **$50,000,000** price + closing costs **1.5%** + renovation
    **~$7,500,000** + capitalized construction interest + operating shortfall during lease-up + the
    selected lender's origination fee + a **$350,000** working-capital reserve.
  - **Select the lender with the higher levered IRR → First Southeast Bank** (≈23.6% vs Piedmont ≈21.4%).
→ Extend **Property Cash Flow** with a debt-service section (IO during construction, P&I after
conversion) and a levered cash-flow section (unlevered CF − debt service, plus exit equity proceeds =
net sale − loan payoff). Invariant: **Total Levered CF = Total Unlevered CF + Total CF from Financing**.

## Phase 8 — Waterfall, Returns, IC Package & LOI
Tabs created: **Waterfall, IC Summary, LOI.** Tab extended: **Assumptions** (sensitivity tables).

→ **Waterfall** — build the 4-tier GP/LP structure: Tier 1 return of capital; Tier 2 **8.0% preferred
return** (compounding, LP priority); Tier 3 **50/50 catch-up until GP has 20% of cumulative profit**;
Tier 4 **80% LP / 20% GP**. Build monthly capital ledgers and the distribution waterfall; produce a
return summary: GP IRR, LP IRR, GP & LP Equity Multiple, Peak Equity Outstanding — Total, GP Share of
Total Profit, Deal IRR (Total Equity). Sense checks: tier distributions = available cash each month; LP +
GP net CF = levered CF.
→ Extend **Assumptions** with **three two-way sensitivity tables** (cells show "IRR% / MoICx"):
  1. **Purchase Price ($46M–$50M) × Exit Cap Rate** (base 7.75% ± 50 bps in 25-bp steps).
  2. **Construction Cost Overrun (0/10/20/30%) × Lease-Up Delay (0/3/6/9 months).**
  3. **Purchase Price ($46M–$50M) × Rent Growth** (base 2.7% ± 200 bps in 50-bp steps).
→ **IC Summary** — read `IC_Summary_Template.xlsx` (`/data/internal/`). Every value links to another tab
(no hardcoded numbers). Required labeled rows: Purchase Price, Physical Occupancy (Corrected),
Number of Tenants (Actual), Reconciled NOI, Broker's Stated NOI, Year 1 Proforma NOI, Stabilized NOI,
Exit Year NOI, Unlevered IRR, Selected Lender, Loan Amount, GP IRR, LP IRR, LP Equity Multiple, Total
Project IRR, and **Go / No-Go = Go**.
→ **LOI** — read `LOI_Template.xlsx` (`/data/internal/`). Populate from the model + Email 4: Buyer
**Harborview Capital Partners (or its designee)**, Property SouthPark Centre, Purchase Price
**$50,000,000**, Deposit **$500,000** (1% hard), Due Diligence Period **45** days, Financing Contingency
**30** days from DD expiration, Exclusivity **60 days**, Tenant Estoppels **≥75% by occupied SF**, Total
SF 280,000, This LOI expires **10** business days, Target Close **August 1, 2026**.
→ Update tracker: SouthPark → **IC Ready**, then after the LOI → **LOI Sent**.

---

## Output Schema (REQUIRED — grading depends on it)

Files in `/tmp/outputs/`: `southpark_centre_underwriting.xlsx`, `ballantyne_wacc_screen.xlsx`,
`Pipeline_Tracker_Q2_2026.xlsx`.

**Workbook tabs (exact names):** `Assumptions`, `Rent Roll`, `Rent Roll Calc`, `Sales Comp Analysis`,
`Rental Comp Analysis`, `SouthPark Submarket`, `Property Cash Flow`, `CapEx Schedule`, `Exit Analysis`,
`Leverage Options`, `Waterfall`, `IC Summary`, `LOI`.

**Conventions the grader relies on:** every summary metric on its own row with the label in the left
column and the value to its right (use the exact labels above); monthly tabs (Rent Roll Calc, Property
Cash Flow, CapEx Schedule, Waterfall) have a `Month #` header row with consecutive month indices and one
column per month; the Rent Roll Calc per-tenant blocks have the tenant name in the left column and the
sub-row label (Net Base Rent, Opex Recovery (NNN), etc.) beside it; comp tabs have a `#` column and a
`Comp Type` column. Values may be formulas or numbers; computed values are read with tolerance.
