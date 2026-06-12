"""Build answer_key.json from the locked ground-truth files.

Anchors are extracted with the SAME label-search the grader uses, then frozen with
tolerances + phase + state (final | invariant | pre_only). Per-item tables (rent roll,
sales comps) are frozen as expected row sets. Run once after the master is locked.
"""
import json, os
import extract as E

# tools/grader/build_key.py -> repo root is three levels up; GT dir is ground_truth/
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GT = os.path.join(ROOT, "ground_truth")
MASTER = os.path.join(GT, "Master Model Output", "SouthPark_Centre_Model (Master).xlsx")
DEALB = os.path.join(GT, "Deal B Screening", "Ground_Truth_Deal_B_WACC_Screen.xlsx")
TRK = os.path.join(GT, "Pipeline Tracker")

# (id, phase, tab, label, kind, tol, state)   kind: num|text   state: final|invariant|pre_only
ANCHORS = [
    # ---- IC Summary (final-state aggregator) ----
    ("purchase_price", 7, "IC Summary", "Purchase Price", "num", 0, "final"),
    ("occupancy_reconciled", 1, "IC Summary", "Physical Occupancy (Corrected)", "num", 0.001, "invariant"),
    ("tenant_count", 1, "IC Summary", "Number of Tenants (Actual)", "num", 0, "invariant"),
    ("reconciled_noi", 1, "IC Summary", "Reconciled NOI", "num", 5000, "invariant"),
    ("broker_noi", 1, "IC Summary", "Broker's Stated NOI", "num", 1000, "invariant"),
    ("year1_noi", 5, "IC Summary", "Year 1 Proforma NOI", "num", 5000, "final"),
    ("stabilized_noi", 5, "IC Summary", "Stabilized NOI", "num", 10000, "final"),
    ("exit_noi", 5, "IC Summary", "Exit Year NOI", "num", 10000, "final"),
    ("unlevered_irr", 5, "IC Summary", "Unlevered IRR", "num", 0.002, "final"),
    ("selected_lender", 7, "IC Summary", "Selected Lender", "text", None, "final"),
    ("loan_amount", 7, "IC Summary", "Loan Amount", "num", 50000, "final"),
    ("gp_irr", 8, "IC Summary", "GP IRR", "num", 0.003, "final"),
    ("lp_irr", 8, "IC Summary", "LP IRR", "num", 0.003, "final"),
    ("lp_equity_multiple", 8, "IC Summary", "LP Equity Multiple", "num", 0.02, "final"),
    ("total_project_irr", 8, "IC Summary", "Total Project IRR", "num", 0.003, "final"),
    ("recommendation", 8, "IC Summary", "Go / No-Go", "text", None, "final"),
    # ---- Exit Analysis ----
    ("exit_cap_rate", 5, "Exit Analysis", "Exit Cap Rate", "num", 0.0001, "final"),
    ("gross_exit_value", 5, "Exit Analysis", "Gross Exit Value", "num", 50000, "final"),
    ("net_sale_proceeds", 5, "Exit Analysis", "Net Sale Proceeds", "num", 50000, "final"),
    ("unlev_equity_multiple", 5, "Exit Analysis", "Equity Multiple (unlevered)", "num", 0.02, "final"),
    # ---- Waterfall ----
    ("peak_equity_total", 8, "Waterfall", "Peak Equity Outstanding - Total", "num", 50000, "final"),
    ("gp_profit_share", 8, "Waterfall", "GP Share of Total Profit", "num", 0.005, "final"),
    ("deal_irr", 8, "Waterfall", "Deal IRR (Total Equity)", "num", 0.003, "final"),
    # ---- SENSE CHECKS (the model must TIE): residual must be ~0 (a hardcoded "OK" can't fake this) ----
    ("chk_tier_dists", 8, "Waterfall", "Tier dists = Available, every month", "num", 1.0, "invariant"),
    ("chk_partner_cf", 8, "Waterfall", "LP + GP Net CF = Levered CF, every month", "num", 1.0, "invariant"),
    ("chk_unreturned_capital", 8, "Waterfall", "Unreturned capital = 0 after exit", "num", 1.0, "invariant"),
    ("chk_accrued_pref", 8, "Waterfall", "Accrued unpaid pref = 0 after exit", "num", 1.0, "invariant"),
    ("chk_rrsf_eq_bldgsf", 5, "Exit Analysis", "Rent Roll SF = Building SF", "num", 1.0, "invariant"),
    # ---- Assumptions (leasing / JV / spec-suite) ----
    ("spec_suite_ti", 6, "Assumptions", "Spec Suite TI ($/SF)", "num", 0, "final"),   # pre-revision = 35
    ("spec_buildout_dur", 4, "Assumptions", "Spec Suite Buildout Duration (mo)", "num", 0, "invariant"),
    ("gp_equity_share", 4, "Assumptions", "GP Equity Share", "num", 0, "invariant"),
    ("preferred_return", 4, "Assumptions", "Preferred Return (effective annual)", "num", 0, "invariant"),
    ("residual_gp", 8, "Assumptions", "Residual Split - GP", "num", 0, "invariant"),
    # ---- LOI (Phase 8) — deal terms from model + Email 4 ----
    ("loi_purchase_price", 8, "LOI", "Purchase Price", "num", 0, "final"),
    ("loi_deposit", 8, "LOI", "Deposit", "num", 0, "final"),
    ("loi_total_sf", 8, "LOI", "Total SF", "num", 0, "final"),
    ("loi_dd_period", 8, "LOI", "Due Diligence Period", "num", 0, "final"),
    ("loi_financing_contingency", 8, "LOI", "Financing Contingency", "num", 0, "final"),
    ("loi_expires", 8, "LOI", "This LOI expires", "num", 0, "final"),
    ("loi_buyer", 8, "LOI", "Buyer", "text", None, "final"),
    ("loi_exclusivity", 8, "LOI", "Exclusivity", "text", None, "final"),
    ("loi_estoppels", 8, "LOI", "Tenant Estoppels", "text", None, "final"),
    # ---- SouthPark Submarket (Phase 3) — reproduced market data ----
    ("sub_vacancy", 3, "SouthPark Submarket", "Overall Vacancy Rate", "text", None, "invariant"),
    ("sub_class_a_rent", 3, "SouthPark Submarket", "Class A", "text", None, "invariant"),
    ("sub_net_absorption", 3, "SouthPark Submarket", "Net Absorption (TTM)", "text", None, "invariant"),
    ("sub_under_construction", 3, "SouthPark Submarket", "Under Construction", "text", None, "invariant"),
    ("sub_rent_growth", 3, "SouthPark Submarket", "12-Month Rent Growth (Class B+)", "text", None, "invariant"),
    # ---- Leverage Options (Phase 7) — selected (active) lender terms ----
    ("lev_rate", 7, "Leverage Options", "All-In Rate (indicative)", "text", None, "final"),
    ("lev_ltc", 7, "Leverage Options", "Maximum LTC", "text", None, "final"),
    ("lev_perm_loan", 7, "Leverage Options", "Max Permanent Loan (LTV stabilized)", "num", 50000, "final"),
    ("lev_orig_fee", 7, "Leverage Options", "Origination Fee", "text", None, "final"),
]

DEALB_ANCHORS = [
    ("dealb_going_in_cap", 2, "Going-In Cap Rate", "num", 0.001),
    ("dealb_unlev_irr", 2, "Unlevered IRR (Cap Rate + Growth)", "num", 0.001),
    ("dealb_re", 2, "Implied Cost of Equity (Re)", "num", 0.002),
    ("dealb_hurdle", 2, "Fund Minimum Levered IRR", "num", 0),
    ("dealb_shortfall", 2, "Shortfall to Hurdle", "num", 0.002),
]

def build():
    key = {"workbook": "southpark_centre_underwriting.xlsx",
           "dealb_file": "ballantyne_wacc_screen.xlsx",
           "tracker_file": "Pipeline_Tracker_Q2_2026.xlsx",
           "anchors": [], "dealb_anchors": [], "per_item": {}, "tracker": {}}

    wb = E.load(MASTER)
    for aid, phase, tab, label, kind, tol, state in ANCHORS:
        ws = wb[tab]
        val = E.find_value(ws, label)
        key["anchors"].append({"id": aid, "phase": phase, "tab": tab, "label": label,
                               "kind": kind, "tol": tol, "state": state, "expected": val})

    bwb = E.load(DEALB); btab = bwb[bwb.sheetnames[0]]
    for aid, phase, label, kind, tol in DEALB_ANCHORS:
        key["dealb_anchors"].append({"id": aid, "phase": phase, "label": label,
                                     "kind": kind, "tol": tol, "expected": E.find_value(btab, label)})

    # ---- per-item: Rent Roll (20 tenants) — identity + benchmark assumptions (P1/P3/P4) ----
    rr_want = {"name": "Tenant", "sf": "SF", "rent": "Rent $/SF",
               "mkt_rent": "Mkt Rent $/SF", "renew": "Renew %", "new_ti": "New TI $/SF"}
    rr = E.read_table(wb["Rent Roll"], "Tenant", rr_want)
    rr = [r for r in rr if r["name"] and "vacant" not in str(r["name"]).lower()
          and str(r["name"]).upper() != "TOTAL"][:20]
    key["per_item"]["rent_roll"] = {"phase": 1, "tab": "Rent Roll", "key_header": "Tenant",
                                    "match": "name", "want": rr_want,
                                    "fields": {"sf": 0, "rent": 0.01, "mkt_rent": 0.5,
                                               "renew": 0.001, "new_ti": 1.0}, "rows": rr}

    # ---- per-item: Sales comps (25) + Lease comps (50) — each classified ----
    sc = [r for r in E.read_table(wb["Sales Comp Analysis"], "#", {"id": "#", "ctype": "Comp Type"})
          if isinstance(r["id"], (int, float))]
    key["per_item"]["sales_comps"] = {"phase": 3, "tab": "Sales Comp Analysis", "key_header": "#",
                                      "match": "id", "want": {"id": "#", "ctype": "Comp Type"},
                                      "fields": {"ctype": None}, "rows": sc}
    lc = [r for r in E.read_table(wb["Rental Comp Analysis"], "#", {"id": "#", "ctype": "Comp Type"})
          if isinstance(r["id"], (int, float))]
    key["per_item"]["lease_comps"] = {"phase": 3, "tab": "Rental Comp Analysis", "key_header": "#",
                                      "match": "id", "want": {"id": "#", "ctype": "Comp Type"},
                                      "fields": {"ctype": None}, "rows": lc}

    # ---- per-item: Leasing assumptions by size bucket (P4) ----
    lb_want = {"bucket": "Bucket Label", "renew": "Renew %", "downtime": "Downtime (mo)",
               "new_ti": "New TI $/SF", "lc": "LC %"}
    lb = [r for r in E.read_table(wb["Assumptions"], "Bucket Label", lb_want)
          if r["bucket"] and any(ch in str(r["bucket"]) for ch in "<>,")]   # size buckets only
    key["per_item"]["leasing_buckets"] = {"phase": 4, "tab": "Assumptions", "key_header": "Bucket Label",
                                          "match": "bucket", "want": lb_want,
                                          "fields": {"renew": 0.001, "downtime": 0, "new_ti": 0, "lc": 0.001},
                                          "rows": lb}

    # ---- per-item: T-12 Operating Statement reproduction (primary-source sourcing volume, P1) ----
    # The agent transcribes 12 months of reported figures per line item from T12_Operating_Statement_2025.xlsx
    t12 = wb["T-12 Operating Statement"]
    t12_hdr_row = next(r for r in t12.iter_rows()
                       if any(isinstance(c.value, str) and c.value.strip() == "Line Item" for c in r))
    t12_months = [c.value for c in t12_hdr_row
                  if isinstance(c.value, str) and c.value.strip() and c.value.strip() != "Line Item"]
    t12_want = {"item": "Line Item"}
    for i, m in enumerate(t12_months):
        t12_want[f"m{i:02d}"] = m
    t12_rows = [r for r in E.read_table(t12, "Line Item", t12_want)
                if r.get("item") and any(isinstance(r.get(f"m{i:02d}"), (int, float)) for i in range(len(t12_months)))]
    key["per_item"]["t12_reproduction"] = {"phase": 1, "tab": "T-12 Operating Statement",
                                            "key_header": "Line Item", "match": "item", "want": t12_want,
                                            "fields": {f"m{i:02d}": 1.0 for i in range(len(t12_months))},
                                            "rows": t12_rows}

    # ---- matrices: Leverage Options (metrics × lenders) + 3 sensitivity tables ----
    key["matrices"] = {}
    lev = wb["Leverage Options"]
    lev_hdr = E.find_label_row(lev, "Term")            # row whose col A = "Term", lenders across
    levm = E.read_matrix(lev, lev_hdr, row_key_col=1)
    lenders = ["First Southeast Bank", "Atlantic Life Insurance", "Piedmont Capital"]
    lev_cells = {f"{metric}||{lender}": levm.get((metric, lender))
                 for lender in lenders
                 for metric in ["All-In Rate (indicative)", "Maximum LTC",
                                "Max Permanent Loan (LTV stabilized)", "Max Dev Loan"]
                 if levm.get((metric, lender)) is not None}
    key["matrices"]["leverage"] = {"phase": 7, "tab": "Leverage Options", "header_label": "Term",
                                   "row_key_col": 1, "col_anchors": lenders, "cells": lev_cells}

    # sensitivity tables (Assumptions): grade by presence of each unique 'IRR / MoIC' result
    # string across the sensitivity region (one set; layout-independent presence check)
    A = wb["Assumptions"]
    import re as _re
    sens_pat = _re.compile(r"^-?\d+\.?\d*%\s*/\s*\d+\.?\d*x$")
    uniq = sorted({str(c.value).strip() for row in A.iter_rows() for c in row
                   if isinstance(c.value, str) and sens_pat.match(str(c.value).strip())})
    key["matrices"]["sensitivity"] = {"phase": 8, "tab": "Assumptions",
                                      "cells": {f"sens::{v}": v for v in uniq}}

    # ---- tracker: per-phase snapshots (final + checkpoints) ----
    snaps = {"1": "GT_Pipeline_Tracker_P1_May30.xlsx", "2": "GT_Pipeline_Tracker_P2_Jun01.xlsx",
             "3": "GT_Pipeline_Tracker_P3_Jun02.xlsx", "6": "GT_Pipeline_Tracker_P6_Jun03.xlsx",
             "8": "GT_Pipeline_Tracker_P8_Jun05.xlsx"}
    for ph, fn in snaps.items():
        tw = E.load(os.path.join(TRK, fn)); ts = tw[tw.sheetnames[0]]
        rows = E.read_table(ts, "Deal Name", {"deal": "Deal Name", "status": "Status",
                                              "broker": "Broker", "strategy": "Strategy"})
        want = {r["deal"]: r for r in rows if r["deal"] in ("SouthPark Centre", "Ballantyne Office Centre")}
        key["tracker"][ph] = {"snapshot": fn, "rows": want}

    # ---- CALCULATION LAYER 1: FULL CELL GRIDS — every numeric formula cell of every calc tab ----
    CALC_TABS = {"Rent Roll Calc": 4, "Property Cash Flow": 5, "CapEx Schedule": 5, "Waterfall": 8}
    grids = {}
    for tab, phase in CALC_TABS.items():
        fg = E.full_grid(wb[tab])
        grids[tab] = {"phase": phase, "cells": {E.cell_key_str(k): v for k, v in fg.items()}}
    key["calc_grids"] = grids
    n_grid = sum(len(g["cells"]) for g in grids.values())

    # ---- CALCULATION LAYER 2: reconciliation invariants (per month, on submission's own values) ----
    P = wb["Property Cash Flow"]
    mmap = E.month_map(P)
    months = list(range(1, 61))
    invariants = [
        {"name": "EGI = NetRental + ExpRecovery + OtherIncome",
         "target": "Effective Gross Income",
         "terms": [["Net Rental Income", 1], ["Expense Recovery (NNN)", 1], ["Other Income", 1]]},
        {"name": "NOI = EGI + Vacancy + OpEx + MgmtFee",
         "target": "Net Operating Income",
         "terms": [["Effective Gross Income", 1], ["General Vacancy Adjustment", 1],
                   ["Operating Expenses", 1], ["Management Fee", 1]]},
        {"name": "LeveredCF = UnleveredCF + FinancingCF",
         "target": "Total Levered Cash Flow",
         "terms": [["Total Unlevered Cash Flow", 1], ["Total CF from Financing", 1]]},
    ]
    key["calc"] = {"tab": "Property Cash Flow", "months": months, "invariants": invariants}

    out = os.path.join(os.path.dirname(__file__), "answer_key.json")
    with open(out, "w") as f:
        json.dump(key, f, indent=2, default=str)
    n_inv = len(invariants) * len(months)
    n_peritem = sum(len(v["rows"]) * len(v["fields"]) for v in key["per_item"].values())
    n_matrix = sum(len(m["cells"]) for m in key["matrices"].values())
    n = (len(key["anchors"]) + len(key["dealb_anchors"]) + n_peritem + n_matrix
         + sum(len(v["rows"]) for v in key["tracker"].values()) + n_grid + n_inv)
    print(f"wrote {out}:")
    print(f"  {len(key['anchors'])} SP anchors (incl LOI/Submarket/Leverage), {len(key['dealb_anchors'])} Deal-B")
    print(f"  per-item: " + ", ".join(f"{k}={len(v['rows'])}x{len(v['fields'])}" for k, v in key["per_item"].items())
          + f" = {n_peritem} checks")
    print(f"  matrices: " + ", ".join(f"{k}={len(m['cells'])}" for k, m in key["matrices"].items())
          + f" = {n_matrix} checks")
    print(f"  CALC GRIDS: " + ", ".join(f"{t}={len(g['cells'])}" for t, g in grids.items()) + f" = {n_grid}")
    print(f"  invariants={n_inv}, tracker snaps={len(key['tracker'])}")
    print(f"  ~{n:,} TOTAL CHECKS")
    # surface any anchor that failed to extract (label drift)
    miss = [a["id"] for a in key["anchors"] + key["dealb_anchors"] if a["expected"] is None]
    if miss:
        print("  WARNING unextracted anchors:", miss)

if __name__ == "__main__":
    build()
