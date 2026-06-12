#!/usr/bin/env python3
"""Tool-call budget for the SouthPark Centre odyssey task (bash environment).

Reports two profiles per the odyssey convention:
  - COARSE  : an efficient agent that batches reads and scripts the model build.
  - GRANULAR: the 'thorough' working style this package targets — files read/interpreted
              individually, per-item deliverables produced item-by-item, model built and
              verified in cycles. This is the ~700-call version.

Each phase is decomposed into: file reads, per-item operations (the graded fan-outs),
model build/edit-run cycles, and verification steps. Coarse applies realistic batching
compression to each component.
"""

# phase: (file_reads, per_item_ops, model_build_cycles, verify_ops, note)
PHASES = {
    1: (26, 24, 28, 12, "OM+rent roll+20 lease-abstract PDFs+vendor; reconcile 4 traps; 3 tabs; tracker"),
    2: (4,   2, 14,  5, "Ballantyne IM+rent roll; WACC screen; tracker"),
    3: (6,  75, 20,  9, "2 market PDFs+2 comp sheets; classify 25 sales + 50 lease comps; 3 tabs"),
    4: (2,  26, 30, 12, "guide; 20 tenant underwrites + 6 spec suites"),
    5: (3,   0,100, 27, "60-month proforma + CapEx + Exit (circular mgmt fee); iteration-heavy"),
    6: (2,   0, 18, 15, "Email 9; 3 revisions; cascade re-verify"),
    7: (6,   0, 70, 19, "3 term sheets; size + underwrite 2 lenders; draw schedules; levered CF"),
    8: (2,  15,110, 23, "waterfall + 3 sensitivity tables + IC summary + LOI + tracker"),
}

# coarse compression factors (batching reads, scripting items, fewer build cycles)
C = dict(reads=0.6, items=0.35, build=0.5, verify=0.5)
OVERHEAD = 0.0  # already included implicitly in per-phase verify/build

def main():
    print(f"{'Phase':<6}{'reads':>6}{'items':>7}{'build':>7}{'verify':>8}{'COARSE':>9}{'GRAN':>7}  note")
    tot_c = tot_g = 0
    for ph, (rd, it, bd, vf, note) in PHASES.items():
        gran = rd + it + bd + vf
        coarse = round(rd * C['reads'] + it * C['items'] + bd * C['build'] + vf * C['verify'])
        tot_c += coarse; tot_g += gran
        print(f"{ph:<6}{rd:>6}{it:>7}{bd:>7}{vf:>8}{coarse:>9}{gran:>7}  {note}")
    print("-" * 110)
    print(f"{'TOTAL':<6}{'':>6}{'':>7}{'':>7}{'':>8}{tot_c:>9}{tot_g:>7}")
    print(f"\nCOARSE (efficient/scripted) ~{tot_c} calls   |   GRANULAR (thorough, this package) ~{tot_g} calls")
    print("The packaged prompt + per-item graded deliverables target the GRANULAR profile.")

if __name__ == "__main__":
    main()
