# World Layout — Real Estate PE Underwriting (SouthPark Centre)

The local file-based world contains 73 files (**46 PDF / 18 XLSX / 9 HTML**) staged at `/data` by
`setup_env.sh`, mapped
to its simulated source system. Files flagged `[RH]` are red herrings: present and plausible,
but not needed to complete the task. Do not delete them; recognizing and excluding them is part
of the work.

Deployment note: the observed Fleet workbench task is an Outlook + Fropbox/Docket adaptation. If
this world is deployed through Fropbox, preserve the same folder semantics under
`/SouthPark Centre Underwriting`:

- `Dataroom` maps to `world_files/dataroom`
- `Ballantyne Office Centre` maps to `world_files/dataroom_deal_b`
- `Internal` maps to `world_files/internal`
- `Lenders` maps to `world_files/lenders`
- `Construction` maps to `world_files/construction`
- `Market Research` maps to `world_files/market_research`

See `DEPLOYMENT_ALIGNMENT.md` for the required deployed seed preflight.

## `/data/emails/`: the local inbox (read Email_01 -> Email_09 in order)
Nine HTML emails that drive the week: broker offering (01), VP start-underwriting (02), partner
JV structure (03), VP forward structure / LOI terms (04), dev-head capex (05), capital-markets
financing + Atlantic Life "no capacity" flag (06), Deal B mention (07), Deal B forward with IM
(08), VP revisions (09). The chronological order is load-bearing: Deal B only "exists" after
Email 7/8, and the Phase 6 revisions arrive in Email 9.

## `/data/dataroom/` — Deal A data room (SouthPark Centre)
- `Offering_Memorandum_SouthPark_Centre.pdf` — broker headline metrics (the figures to reconcile).
- `Rent_Roll_Current_05-2026.xlsx` — 20 NNN tenant rows (carries the two planted traps).
- `lease_abstracts/Lease_Abstract_Tenant_01.pdf … _20.pdf` — 20 abstracts to cross-verify the
  rent roll (Tenant 06 Brightpath $20.75 vs roll's $21.25; Tenant 20 Dental expired 3/31/2026).
- `T12_Operating_Statement_2025.xlsx`, `T3_Historical_Operating_Statements_2023-2025.xlsx`,
  `Historical_Capital_Expenditures_2019-2025.xlsx` — operating history.
- `Vendor_Contracts_Summary.xlsx` — confirms antenna income (Sprint expired, T-Mobile only).
- `Tenant_Financials_Meridian_2025.xlsx`, `Parking_Agreement.pdf`,
  `Property_Management_Agreement.pdf`, `Insurance_Certificate_2025.pdf`.
- `property_reports/` — Property Condition, HVAC, Roof (2024), Elevator inspection.
- `Insurance_Quote_Expired_2024.pdf` `[RH]`, `Tenant_Credit_Report_Expired_2024.pdf` `[RH]`.
- `archive/Draft_LOI_Morrison_Rejected.pdf` `[RH]`, `archive/Old_Appraisal_SouthPark_Centre_2022.pdf` `[RH]`.

## `/data/dataroom_deal_b/` — Deal B (Ballantyne)
`Ballantyne_Office_Centre_IM.pdf`, `Ballantyne_Rent_Roll.xlsx` — the quick-screen inputs.

## `/data/internal/` — Harborview internal
`Pipeline_Tracker_Q2_2026.xlsx` (the running tracker the agent edits), `Fund_Investment_Criteria.pdf`
(return hurdles), `Standard_Lease_Assumptions_Guide.pdf` (leasing defaults by size bucket),
`IC_Summary_Template.xlsx`, `LOI_Template.xlsx`.

## `/data/lenders/` — three construction term sheets
`Term_Sheet_First_Southeast_Bank.pdf`, `Term_Sheet_Piedmont_Capital.pdf`,
`Term_Sheet_Atlantic_Life_Insurance.pdf`. Atlantic Life has the **best terms but no capacity**
(flagged stale in Email 6); selecting it is the planted Phase 7 failure.

## `/data/construction/` — renovation scope
`Renovation_Timeline_Gantt.pdf`, `Area_Schedule_SouthPark_Centre.xlsx`, and three GC bids
(`Contractor_Bid_Pinnacle_Builders.pdf`, `_Summit_Construction.pdf`, `_Trident_GC.pdf`).

## `/data/market_research/` — comps and submarket
`Charlotte_Office_Market_Report_Q1_2026.pdf`, `SouthPark_Submarket_Report_Q1_2026.pdf`,
`Comparable_Sales_Data_Charlotte_Office.xlsx` (25 sales, ~13 usable),
`Comparable_Lease_Data_SouthPark.xlsx` (50 leases, ~25 usable), `Construction_Pipeline_Charlotte_Office.xlsx`,
`Employment_Growth_Data_Charlotte_MSA.xlsx`, `Charlotte_Office_Vacancy_Trends_2020-2026.xlsx`,
`US_Inflation_Data.xlsx` (CPI for opex escalation), `CBJ_Meridian_HQ_Relocation.pdf` (the article
that confirms Meridian is departing). `Charlotte_Office_Market_Report_Uptown_Q1_2026.pdf` `[RH]`
(wrong submarket — Uptown, not SouthPark).

## Ground truth (`ground_truth/`, the answer key — not staged to `/data`)
- `Master Model Output/SouthPark_Centre_Model (Master).xlsx` — the locked 14-tab final model
  (post-revision: $50M / $40 TI / months 6-8-10). End-state grading target.
- `Deal B Screening/Ground_Truth_Deal_B_WACC_Screen.xlsx` — the Phase 2 screen.
- `Pipeline Tracker/GT_Pipeline_Tracker_P{1,2,3,6,8}_*.xlsx` — five tracker snapshots for the
  per-phase status checks.
