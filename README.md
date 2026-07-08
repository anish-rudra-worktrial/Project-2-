# Domain/Profession: Real Estate Private Equity — Acquisitions & Underwriting

## Start Here

For the work-trial submission, start with `SUBMISSION.md`. It summarizes the Part 1 assessment, the
repo changes, the Part 2 QA loop, how to run the tooling, known limits, and presentation prep.

## QA status (2026-07-07)

This repository is internally coherent as a **local bash/file task** (`/data` inputs,
`/tmp/outputs` outputs, local deterministic full-grid grader). However, the currently deployed
Fleet workbench task `odyssey-real-estate-pe-underwriting-full_243edf59_v1` uses a different
**Outlook + Fropbox/Docket** surface and an evidence-weighted deployed verifier.

Read these before modifying or deploying:

- `QA_ASSESSMENT.md`: current assessment, defects, and required fixes.
- `DEPLOYMENT_ALIGNMENT.md`: local repo surface vs deployed Fleet surface.
- `prompts/deployed_fropbox_prompt.md`: observed deployed prompt surface.

Do not silently mix `/data` + `/tmp/outputs` instructions with the deployed Fropbox upload
contract. If production is the deployed task, the seed email and Fropbox source-room preflight need
to be reconciled before accepting the task as production-ready.

## Review Philosophy

The main QA judgment in this package is not "an evaluator said the task is good." The judgment is
that a task should only ship when a reviewer can trace the prompt, seed data, verifier, and expected
outputs back to the same world. I used automation to find likely drift, then checked the important
findings by reading the prompt, verifier, repo docs, environment snapshot, and source files myself.

That is why the Part 2 tool reports evidence and review actions instead of pass/fail decisions. It
is built to speed up a 20-30 task batch review while keeping the final call with a human reviewer.

## Task Title & One-Sentence Goal

**From Broker Package to IC Deck: Underwrite Two Deals in One Week.**
You are a second-year acquisitions associate at **Harborview Capital Partners (Fund III)**. Over
the week of **June 1, 2026** you work an email inbox and a multi-folder data room to underwrite
**Deal A — SouthPark Centre** (280,000 SF value-add office, Charlotte NC) into a full **14-tab
institutional model, IC package, and LOI**, and **Deal B — Ballantyne Office Centre** (120,000 SF
stabilized) into a quick **WACC screen** that you pass on. The work runs across **8 sequential
phases**, includes a mid-week VP revision cascade, and is tracked on a
running pipeline tracker. You write `southpark_centre_underwriting.xlsx`,
`ballantyne_wacc_screen.xlsx`, and an updated `Pipeline_Tracker_Q2_2026.xlsx` to `/tmp/outputs/`.

## Bullet-Point Description

- Read the inbox in order and the data room; reconcile the broker's Offering Memorandum against
  the rent roll, 20 lease abstracts, and vendor contracts (catching a ghost tenant, a wrong rent,
  a non-recurring fee, and expired antenna income).
- Quick-screen Deal B with a levered-return WACC calc against the fund hurdle, and pass it.
- Classify 25 sales comps and 50 lease comps (filtering crisis-era, wrong-submarket, incomplete,
  and non-comparable rows) and benchmark all 20 tenants to market rent.
- Underwrite lease-by-lease with size-bucket assumptions, model the 6-suite Meridian spec plan,
  and build a 60-month proforma + CapEx + Exit.
- Apply the VP's three revisions ($50M price, $40 spec-suite TI, 2-month buildout delay) and
  verify the cascade.
- Size the construction loan across two viable lenders (rejecting the stale-but-best Atlantic
  Life), build the debt schedule and levered cash flow, then the 4-tier equity waterfall, three
  sensitivity tables, the IC summary, and the LOI.

## Reusability / Representativeness

### Representativeness of Real Workflows

- This is the actual week-long arc of a REPE acquisitions associate: intake, reconcile, comp,
  underwrite, revise on principal feedback, finance, and package for Investment Committee. A
  human-in-the-loop step (the VP revision memo) is delivered as an email the agent must act on.
- The reconciliation traps (ghost tenant, mispriced lease, stale lender, expired income) are the
  everyday "the broker's number is wrong" judgment the job is built on.

### Generalization beyond this task

- Any cash-flow-model-to-IC workflow: development underwriting, portfolio acquisitions, debt
  origination, or corporate M&A models with a comparable-set and a returns waterfall.
- Multi-document reconciliation against a system of record (the same shape as audit, claims, and
  diligence work).

### How solving it moves toward a "mini-breakthrough"

- A model that can carry a linked 14-tab institutional model through a revision cascade — where
  one input change must flow correctly to loan sizing, returns, and the waterfall — is doing the
  core analytical work of an investment associate, not just spreadsheet data entry.

## What It Teaches the AI Model

- Institutional real-estate underwriting: NNN reimbursements, probability-weighted rollover, spec
  suite lease-up, construction-loan sizing with PIK interest, and a 4-tier promote waterfall.
- Comparable-set curation: filtering and classifying a noisy comp universe with documented rationale.
- Multi-source reconciliation and the discipline of citing the source cell for every correction.
- Planning, cross-referencing, and verification: each phase consumes prior tabs, and a mid-week
  revision must be cascaded and re-checked across a linked model.

## Why it's hard, and why it's 1,000+ tool calls

The hard part is that this is one **linked** model carried across 8 dependent phases: the
reconciled rent roll feeds the cash flow engine, which feeds the proforma, which feeds loan
sizing, which feeds the waterfall and the IC package, and a mid-week VP revision has to cascade
through all of it correctly. There is **no batch tool** that underwrites a deal; the volume is
irreducible per-item reasoning over unstructured inputs that no single script can shortcut.

The call count depends on the working style (reproduced by `tools/call_budget.py`):

| Profile | Tool calls | Who |
|---|---:|---|
| Coarse | **~336** | an efficient agent that batches reads and scripts the model build |
| **Granular** | **~705** | the thorough, item-by-item style this package's prompt requires |

The driver is the manual reading: **46 PDFs** opened and interpreted (the OM, 20 lease abstracts,
3 term sheets, 3 GC bids, market and inspection reports), **75 comps** each classified with
rationale, **20 tenants** each benchmarked and underwritten, and an item-by-item re-verification
of the VP revision cascade. The model itself contains **~31,000 formula cells** and **~1,200
sourced inputs**. (Honest note: the ~705 estimate is from the call-budget model; it has not yet
been confirmed by a live agent run in a deployed environment.)

**Phase-by-phase:** (1) intake, reconcile, pipeline setup; (2) Deal B WACC screen + pass;
(3) market research + 25 sales / 50 lease comp analysis; (4) lease-by-lease underwriting +
assumptions; (5) 60-month proforma + CapEx + Exit; (6) VP revision cascade; (7) construction loan
+ debt schedule across two lenders; (8) waterfall, sensitivity tables, IC summary, and LOI.

## More docs

- `HANDOFF.md`: full runtime & grading spec: the 8 phases, the locked-master reconciliation log,
  the end-state grading design, and per-phase anchors for the local file-based task.
- `WORLD_LAYOUT.md`: every world file, the system it represents, and the red herrings.
- `CHANGELOG.md`: how the task was built from the author submission and what was flagged.
- `QA_ASSESSMENT.md` / `DEPLOYMENT_ALIGNMENT.md`: current QA status and deployment drift notes.
- `PROJECT2_PRESENTATION_PREP.md`: plain-English presentation notes and likely panel questions.
- `tools/qa_loop/`: reusable QA loop for path, file, prompt, verifier, and environment consistency checks.
- Template-fill: the agent fills a pre-structured workbook
  (`world_files/internal/SouthPark_Centre_Model_Template.xlsx`, seeded to
  `/tmp/outputs/southpark_centre_underwriting.xlsx` by `setup_env.sh`): all 14 tabs, labels, and
  Month # headers in place, value cells blank — so its layout matches the grader's keys.
- Prompts: `prompts/agent_prompt_prescriptive.txt` (the 8-phase local file-based task), `agent_prompt_prescriptive_v2.txt`
  (the cell-explicit line-item spec), `agent_prompt_narrative.txt` (first-person, reasoning-forward,
  figures withheld), `agent_prompt_buildcontract_v1.md` (the legacy detailed tab/row build contract),
  and `deployed_fropbox_prompt.md` (the observed deployed Fleet prompt).
- Grading: `python3 grade.py <submission_dir>` (deterministic, end-state, ~30,500 checks);
  `python3 grade.py --self-test` (validates the grader vs ground truth); `tools/call_budget.py`.
