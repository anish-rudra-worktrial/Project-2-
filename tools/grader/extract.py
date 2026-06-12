"""Shared, layout-tolerant extraction helpers used by both the key builder and the grader.

The agent builds its own workbook layout, so we locate values by *label search* within a
named tab (find a cell whose text matches the anchor label, then read the first value to its
right on the same row). This is the contract the runtime prompt enforces: required tab names
and the labels that must appear in column A (value to the right).
"""
import re
import openpyxl


def _norm(s):
    if s is None:
        return ""
    return re.sub(r"\s+", " ", str(s)).strip().lower().replace("’", "'").replace("—", "-")


def load(path, data_only=True):
    return openpyxl.load_workbook(path, data_only=data_only)


def find_value(ws, label, max_scan_cols=14):
    """Find a cell matching `label` (normalized exact, else 'startswith'); return the first
    non-empty cell value to its right on the same row. None if not found."""
    target = _norm(label)
    # exact first, then startswith
    for mode in ("exact", "prefix"):
        for row in ws.iter_rows():
            for c in row:
                cv = _norm(c.value)
                if not cv:
                    continue
                hit = (cv == target) if mode == "exact" else cv.startswith(target)
                if hit:
                    for cc in ws[c.row]:
                        if cc.column > c.column and cc.value not in (None, ""):
                            return cc.value
    return None


def read_table(ws, key_header, want_headers, header_scan_rows=120):
    """Find a header row containing `key_header`, return list of dict rows keyed by the
    headers we care about. `want_headers` maps output-key -> header text to match."""
    hdr_row = None
    colmap = {}
    for r in range(1, header_scan_rows + 1):
        cells = {_norm(c.value): c.column for c in ws[r] if c.value not in (None, "")}
        if _norm(key_header) in cells:
            hdr_row = r
            # map requested headers to columns (prefix match tolerant)
            for outk, htext in want_headers.items():
                ht = _norm(htext)
                col = cells.get(ht)
                if col is None:
                    for cv, cc in cells.items():
                        if cv.startswith(ht) or ht.startswith(cv):
                            col = cc
                            break
                colmap[outk] = col
            break
    if hdr_row is None:
        return []
    rows = []
    for r in range(hdr_row + 1, ws.max_row + 1):
        rec = {}
        any_val = False
        for outk, col in colmap.items():
            v = ws.cell(r, col).value if col else None
            rec[outk] = v
            if v not in (None, ""):
                any_val = True
        if any_val:
            rows.append(rec)
    return rows


def _longest_consec_run(ws, row):
    seq = [(c, ws.cell(row, c).value) for c in range(1, ws.max_column + 1)
           if isinstance(ws.cell(row, c).value, int) and not isinstance(ws.cell(row, c).value, bool)]
    best, cur = [], []
    for c, v in seq:
        if cur and v == cur[-1][1] + 1:
            cur.append((c, v))
        else:
            cur = [(c, v)]
        if len(cur) > len(best):
            best = cur[:]
    return best  # list of (col, month_index)


def period_header_row(ws, scan_rows=12, min_run=6):
    """Find the period-header row = the top row with the longest consecutive-integer run
    (handles 'Month #' rows AND CapEx-style 'Work Item | ... | 1 2 3 ...' rows)."""
    best_row, best_len = None, 0
    for r in range(1, min(ws.max_row, scan_rows) + 1):
        run = _longest_consec_run(ws, r)
        if len(run) > best_len:
            best_len, best_row = len(run), r
    return best_row if best_len >= min_run else None


def month_map(ws, header_label=None):
    """{month_index: column} for the monthly period strip (longest consecutive-int run)."""
    hdr = period_header_row(ws)
    if hdr is None:
        return {}
    return {v: c for c, v in _longest_consec_run(ws, hdr)}


def grid_series(ws, months=None):
    """Full monthly grid of a calculation tab -> {(block, row_label, month): value}.
    block = most recent text value in col A (tenant/section header); row_label = col B if it is a
    text label (per-tenant sub-rows), else col A. Layout-independent in rows and columns."""
    hdr = period_header_row(ws)
    if hdr is None:
        return {}
    mmap = {v: c for c, v in _longest_consec_run(ws, hdr)}
    if months is not None:
        mmap = {m: c for m, c in mmap.items() if m in months}
    out, block = {}, None
    for r in range(hdr + 1, ws.max_row + 1):
        a, b = ws.cell(r, 1).value, ws.cell(r, 2).value
        a_txt = a if (a not in (None, "") and not isinstance(a, (int, float))) else None
        if a_txt is not None:
            block = str(a_txt).strip()
        if b not in (None, "") and not isinstance(b, (int, float)):
            label = str(b).strip()
        elif a_txt is not None:
            label = str(a_txt).strip()
        else:
            continue
        for mo, col in mmap.items():
            v = ws.cell(r, col).value
            if v not in (None, ""):
                out[(block, label, mo)] = v
    return out


def _runs_by_step(vals, step):
    runs, cur = [], []
    for c, v in vals:
        if cur and v == cur[-1][1] + step:
            cur.append((c, v))
        else:
            cur = [(c, v)]
        if len(cur) >= 2:
            runs.append(list(cur))
    # return the longest such run
    return max(runs, key=len) if runs else []


def full_grid(ws):
    """EVERY populated numeric/computed cell of a calculation tab, addressed layout-independently
    as (block, row_label, col_key). col_key is:
      ('M', month)  monthly strip   |   ('Y', year)  annual roll-up strip
      (header_text)  labelled non-period column (e.g. 'Budget')   |   ('c', col) fallback.
    Captures monthly + annual + scalar cells -> ~full formula coverage."""
    hdr = period_header_row(ws)
    if hdr is None:
        return {}
    ints = [(c, ws.cell(hdr, c).value) for c in range(1, ws.max_column + 1)
            if isinstance(ws.cell(hdr, c).value, int) and not isinstance(ws.cell(hdr, c).value, bool)]
    monthly = _longest_consec_run(ws, hdr)              # step 1
    monthly_cols = {c: ("M", v) for c, v in monthly}
    annual = _runs_by_step(ints, 12)                    # step 12 (year roll-ups)
    annual_cols = {c: ("Y", v // 12) for c, v in annual if c not in monthly_cols}
    headers = {c: _norm(ws.cell(hdr, c).value) for c in range(1, ws.max_column + 1)
               if ws.cell(hdr, c).value not in (None, "") and not isinstance(ws.cell(hdr, c).value, int)}
    out, block = {}, None
    seen = {}  # (block,label) -> occurrence count, to disambiguate repeated row labels
    for r in range(hdr + 1, ws.max_row + 1):
        a, b = ws.cell(r, 1).value, ws.cell(r, 2).value
        a_txt = a if (a not in (None, "") and not isinstance(a, (int, float))) else None
        if a_txt is not None:
            block = str(a_txt).strip()
        label = (str(b).strip() if (b not in (None, "") and not isinstance(b, (int, float)))
                 else (str(a_txt).strip() if a_txt is not None else None))
        if label is None:
            continue
        occ = seen.get((block, label), 0)
        seen[(block, label)] = occ + 1
        for c in range(1, ws.max_column + 1):
            v = ws.cell(r, c).value
            if v in (None, "") or not isinstance(v, (int, float)) or isinstance(v, bool):
                continue
            if c in monthly_cols:
                ck = monthly_cols[c]
            elif c in annual_cols:
                ck = annual_cols[c]
            elif c in headers:
                ck = (headers[c],)
            else:
                ck = ("c", c)
            out[(block, label, occ, ck)] = v
    return out


def label_row(ws, label):
    t = _norm(label)
    for r in range(1, ws.max_row + 1):
        cv = _norm(ws.cell(r, 1).value)
        if cv == t or (cv and cv.startswith(t)):
            return r
    return None


def series(ws, label, mmap, months):
    """Return {month: value(0 if blank)} for a line item identified by its col-A label."""
    r = label_row(ws, label)
    if r is None:
        return None
    out = {}
    for mo in months:
        if mo in mmap:
            v = ws.cell(r, mmap[mo]).value
            out[mo] = 0 if v in (None, "") else v
    return out


def read_matrix(ws, col_key_row, row_key_col=1, scan_rows=120):
    """Read a 2D matrix -> {(row_label, col_label): value}. Column labels come from
    `col_key_row`; row labels from `row_key_col`. Used for Leverage Options (metrics × lenders)
    and the sensitivity tables (price × cap/growth)."""
    if not col_key_row:
        return {}
    col_labels = {}
    for c in range(1, ws.max_column + 1):
        v = ws.cell(col_key_row, c).value
        if v not in (None, ""):
            col_labels[c] = v
    out = {}
    for r in range(col_key_row + 1, min(ws.max_row, col_key_row + scan_rows) + 1):
        rk = ws.cell(r, row_key_col).value
        if rk in (None, ""):
            continue
        for c, cl in col_labels.items():
            if c == row_key_col:
                continue
            v = ws.cell(r, c).value
            if v not in (None, ""):
                out[(str(rk).strip(), str(cl).strip())] = v
    return out


def find_label_row(ws, label, col=1, scan=200):
    t = _norm(label)
    for r in range(1, min(ws.max_row, scan) + 1):
        if _norm(ws.cell(r, col).value) == t:
            return r
    return None


def cell_key_str(k):
    """Serialize a full_grid key (block, label, occ, colkey-tuple) to a JSON-able string."""
    import json
    block, label, occ, ck = k
    return json.dumps([block, label, occ, list(ck)], default=str)


def approx(a, b, tol):
    """Numeric closeness within tol (absolute). Handles % stored as fraction."""
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return False


def text_eq(a, b):
    return _norm(a) == _norm(b)
