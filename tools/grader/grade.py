"""Grade an agent submission against answer_key.json.

Usage:
    python3 grade.py <submission_dir>
    python3 grade.py <submission_dir> --tracker-phase 8

The submission dir must contain the workbook, the Deal-B file, and the pipeline tracker
(names per answer_key.json). Grading is layout-tolerant (label search), fixed-denominator,
and reported per-phase + overall. Run with no args to self-test against the ground truth.
"""
import json, os, sys
import extract as E

HERE = os.path.dirname(os.path.abspath(__file__))
KEY = json.load(open(os.path.join(HERE, "answer_key.json")))


def _check_num(got, exp, tol):
    return E.approx(got, exp, tol if tol is not None else 0.0)


def grade(sub_dir, tracker_phase="8"):
    results = []  # (phase, id, ok, got, exp)

    def add(phase, cid, ok, got, exp):
        results.append((phase, cid, bool(ok), got, exp))

    # ---- SouthPark workbook anchors ----
    wbp = os.path.join(sub_dir, KEY["workbook"])
    if os.path.exists(wbp):
        wb = E.load(wbp)
        for a in KEY["anchors"]:
            ws = wb[a["tab"]] if a["tab"] in wb.sheetnames else None
            got = E.find_value(ws, a["label"]) if ws else None
            ok = E.text_eq(got, a["expected"]) if a["kind"] == "text" else _check_num(got, a["expected"], a["tol"])
            add(a["phase"], a["id"], ok, got, a["expected"])
        # per-item tables (rent roll, sales/lease comps, leasing buckets) - per-field checks
        for pid, ri in KEY["per_item"].items():
            ws = wb[ri["tab"]] if ri["tab"] in wb.sheetnames else None
            got_rows = E.read_table(ws, ri["key_header"], ri["want"]) if ws else []
            mk = ri["match"]
            by_key = {E._norm(r.get(mk)): r for r in got_rows}
            for exp in ri["rows"]:
                g = by_key.get(E._norm(exp.get(mk)))
                rowlabel = str(exp.get(mk))
                for fld, tol in ri["fields"].items():
                    gv = (g or {}).get(fld)
                    if tol is None:
                        ok = bool(g) and E.text_eq(gv, exp.get(fld))
                    else:
                        ok = bool(g) and _check_num(gv, exp.get(fld), tol)
                    add(ri["phase"], f"{pid}:{rowlabel}:{fld}", ok, gv, exp.get(fld))
    else:
        print(f"  !! workbook missing: {wbp}")

    # ---- CALCULATION LAYER 1: FULL CELL GRIDS - every numeric formula cell vs GT ----
    if os.path.exists(wbp) and "calc_grids" in KEY:
        for tab, spec in KEY["calc_grids"].items():
            phase = spec["phase"]
            ws = wb[tab] if tab in wb.sheetnames else None
            sub = {E.cell_key_str(k): v for k, v in E.full_grid(ws).items()} if ws else {}
            for kstr, exp in spec["cells"].items():
                g = sub.get(kstr)
                try:
                    tol = max(0.01, abs(float(exp)) * 0.01)
                except (TypeError, ValueError):
                    tol = 0.01
                add(phase, f"cell:{tab}:{kstr}", E.approx(g, exp, tol), g, exp)

    # ---- CALCULATION LAYER 2: per-month reconciliation invariants on the submission's OWN values ----
    if os.path.exists(wbp) and "calc" in KEY:
        calc = KEY["calc"]
        ws = wb[calc["tab"]] if calc["tab"] in wb.sheetnames else None
        months = calc["months"]
        mmap = E.month_map(ws) if ws else {}
        sub_series = {}
        def getseries(label):
            if label not in sub_series:
                sub_series[label] = (E.series(ws, label, mmap, months) or {}) if ws else {}
            return sub_series[label]
        for inv in calc["invariants"]:
            tgt = getseries(inv["target"])
            for mo in months:
                lhs = tgt.get(mo)
                try:
                    rhs = sum(sign * float(getseries(lbl).get(mo, 0)) for lbl, sign in inv["terms"])
                    ok = (lhs is not None) and abs(float(lhs) - rhs) <= 1.0
                except (TypeError, ValueError):
                    ok = False
                add(5, f"invariant:{inv['name']}[m{mo}]", ok, lhs, "=sum(terms)")

    # ---- MATRICES: Leverage Options (metric × lender) + sensitivity tables ----
    def _smart_eq(a, b):
        try:
            return abs(float(a) - float(b)) <= max(0.01, abs(float(b)) * 0.01)
        except (TypeError, ValueError):
            return E.text_eq(a, b)
    if os.path.exists(wbp) and "matrices" in KEY:
        for mid, mx in KEY["matrices"].items():
            ws = wb[mx["tab"]] if mx["tab"] in wb.sheetnames else None
            if mx.get("header_label"):                       # Leverage: precise metric×lender
                hdr = E.find_label_row(ws, mx["header_label"]) if ws else None
                if hdr is None and ws and mx.get("col_anchors"):
                    for r in range(1, min(ws.max_row, 60) + 1):
                        rowvals = {E._norm(c.value) for c in ws[r]}
                        if sum(E._norm(a) in rowvals for a in mx["col_anchors"]) >= 2:
                            hdr = r; break
                got = E.read_matrix(ws, hdr, mx["row_key_col"]) if (ws and hdr) else {}
                for kstr, exp in mx["cells"].items():
                    metric, lender = kstr.split("||")
                    gv = got.get((metric, lender))
                    add(mx["phase"], f"matrix:{mid}:{kstr}", _smart_eq(gv, exp), gv, exp)
            else:                                            # sensitivity: presence of result strings
                vals = set()
                if ws:
                    for row in ws.iter_rows():
                        for c in row:
                            if c.value not in (None, ""):
                                vals.add(E._norm(c.value))
                for kstr, exp in mx["cells"].items():
                    ok = E._norm(exp) in vals
                    add(mx["phase"], f"matrix:{mid}:{kstr}", ok, None if not ok else exp, exp)

    # ---- Deal B ----
    bp = os.path.join(sub_dir, KEY["dealb_file"])
    if os.path.exists(bp):
        bwb = E.load(bp); bt = bwb[bwb.sheetnames[0]]
        for a in KEY["dealb_anchors"]:
            got = E.find_value(bt, a["label"])
            add(a["phase"], a["id"], _check_num(got, a["expected"], a["tol"]), got, a["expected"])
    else:
        print(f"  !! Deal-B file missing: {bp}")

    # ---- Tracker (graded vs the requested phase snapshot) ----
    tp = os.path.join(sub_dir, KEY["tracker_file"])
    if os.path.exists(tp):
        tw = E.load(tp); ts = tw[tw.sheetnames[0]]
        rows = E.read_table(ts, "Deal Name", {"deal": "Deal Name", "status": "Status",
                                              "broker": "Broker", "strategy": "Strategy"})
        by_deal = {E._norm(r["deal"]): r for r in rows}
        for deal, exp in KEY["tracker"][tracker_phase]["rows"].items():
            g = by_deal.get(E._norm(deal))
            ok = bool(g) and E.text_eq(g.get("status"), exp["status"])
            add(int(tracker_phase) if tracker_phase.isdigit() else 8,
                f"tracker[{deal}]", ok, (g or {}).get("status"), exp["status"])
    else:
        print(f"  !! tracker missing: {tp}")

    return results


def report(results):
    from collections import defaultdict
    byph = defaultdict(lambda: [0, 0])
    for ph, cid, ok, got, exp in results:
        byph[ph][0] += int(ok); byph[ph][1] += 1
    total_ok = sum(1 for r in results if r[2]); total = len(results)
    print("\n=== GRADE REPORT ===")
    for ph in sorted(byph):
        ok, n = byph[ph]
        print(f"  Phase {ph}: {ok}/{n}  ({100*ok/n:.0f}%)")
    print(f"  ---------------------------------")
    print(f"  TOTAL: {total_ok}/{total}  ({100*total_ok/total:.1f}%)")
    fails = [(ph, cid, got, exp) for ph, cid, ok, got, exp in results if not ok]
    if fails:
        print(f"\n  {len(fails)} FAILED checks:")
        for ph, cid, got, exp in fails[:40]:
            print(f"    [P{ph}] {cid}: got={got!r} expected={exp!r}")
    return total_ok, total


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    tphase = "8"
    if "--tracker-phase" in sys.argv:
        tphase = sys.argv[sys.argv.index("--tracker-phase") + 1]
    sub = args[0] if args else None
    if sub is None:
        print("provide a submission dir, or run selftest.py")
        sys.exit(1)
    report(grade(sub, tphase))
