# Deployment Alignment Notes

This repo currently contains a rich local file-based Odyssey task. The Fleet workbench deployment
for `odyssey-real-estate-pe-underwriting-full_243edf59_v1` is not the same surface.

## Local Repo Surface

Use this when running the repo locally with `setup_env.sh` and `grade.py`.

- Source files staged under `/data`.
- Outputs written to `/tmp/outputs`.
- Model template and tracker are seeded into `/tmp/outputs`.
- Local deterministic grader reads:
  - `southpark_centre_underwriting.xlsx`
  - `ballantyne_wacc_screen.xlsx`
  - `Pipeline_Tracker_Q2_2026.xlsx`
- Local full-grid grading relies on cached workbook values. `--recalc` uses LibreOffice when
  available.

## Deployed Fleet Surface

Observed in the Fleet workbench on 2026-07-07.

- Agent works from Outlook plus Fropbox/Docket.
- Deal room root is `/SouthPark Centre Underwriting`.
- Starting files are expected at:
  - `/SouthPark Centre Underwriting/Internal/SouthPark_Centre_Model_Template.xlsx`
  - `/SouthPark Centre Underwriting/Internal/Pipeline_Tracker_Q2_2026.xlsx`
- Final uploads go to:
  - `/SouthPark Centre Underwriting/Outputs/southpark_centre_underwriting.xlsx`
  - `/SouthPark Centre Underwriting/Outputs/ballantyne_wacc_screen.xlsx`
  - `/SouthPark Centre Underwriting/Outputs/Pipeline_Tracker_Q2_2026.xlsx`
- Deployed prompt says Python spreadsheet libraries such as `openpyxl` or `xlsxwriter` are
  available. It does not promise LibreOffice.
- Deployed verifier is evidence-weighted and checks workbook substance, Fropbox uploads, emails,
  tracker state, and cross-artifact consistency. It does not run the local 30k-cell full-grid grader.

## Required Deployment Preflight

Run this before treating the deployed task as production-ready:

1. Confirm the Fropbox seed has `/SouthPark Centre Underwriting`.
2. Confirm the six source folders exist:
   - `Dataroom`
   - `Ballantyne Office Centre`
   - `Internal`
   - `Lenders`
   - `Construction`
   - `Market Research`
3. Confirm at least 64 source files are visible to the deployed verifier, if that integrity check
   remains.
4. Confirm the model template, tracker, and Ballantyne rent roll resolve at the exact verifier paths.
5. Confirm Sarah's deployed email no longer instructs `/tmp/outputs`.
6. Run one capped eval and inspect whether the agent can find the Fropbox files without falling back
   to hidden paths or nonexistent `/data` paths.

## Human Review Gate

The preflight should produce a short reviewer note with three fields:

- confirmed seed state
- confirmed verifier contract
- remaining risk

The task should not move forward based only on a static checker. A person should confirm that the
agent-facing prompt, source-room files, seed emails, output folders, and verifier constants all point
to the same task surface.

## Recommended Canonicalization

Do not silently mix the two surfaces.

If the production benchmark is the deployed Outlook/Fropbox task, port the rich repo world into
Fropbox and update docs/prompts around Fropbox. Keep the local `/data` setup as a development harness.

If the production benchmark is the local full-grid task, deploy a file-based environment that exposes
the same `/data` and `/tmp/outputs` contract and includes a recalc path compatible with the grader.
