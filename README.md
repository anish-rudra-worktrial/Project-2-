# Project 2: Odyssey Task Review

This repo contains a corrected Odyssey task package and a reusable QA loop for reviewing real
estate underwriting tasks in batches.

## Start Here

Read `SUBMISSION.md` first. It gives the plain-English assessment, what changed, how the QA loop
works, what I verified manually, and what limits remain.

## What Is Included

| File or folder | Purpose |
|---|---|
| `SUBMISSION.md` | Main reviewer-facing summary and final package |
| `QA_ASSESSMENT.md` | Detailed task QA notes, defects, and fixes |
| `DEPLOYMENT_ALIGNMENT.md` | Local repo surface compared with the deployed task surface |
| `tools/qa_loop/` | Batch QA checker for prompt, verifier, file, and environment drift |
| `tools/grader/` and `grade.py` | Deterministic local grader and supporting utilities |
| `TASK_OVERVIEW.md` | Full task spec and original workflow detail |
| `WORLD_LAYOUT.md` | Map of the local world files and red herrings |
| `HANDOFF.md` | Runtime, grading, and environment notes |

## Main Result

The draft is coherent as a local bash and file-based underwriting task, but it does not fully align
with the deployed Outlook, Fropbox, and Docket surface. I corrected the local task package, documented
the deployment mismatch, added deterministic grading support, and built a reusable QA loop that flags
the same class of problems across a batch.

The live capped eval finished at 250 steps with score `0.04`. The run failed around practical
execution and upload flow, which supports the assessment that the task needs tighter surface alignment
before it should be treated as production-ready.

## Run The QA Loop

```bash
python3 tools/qa_loop/qa_check.py --repo .
```

The tool writes review artifacts under `qa_outputs/`, which is ignored by Git. A checked sample
report is included at `tools/qa_loop/sample_reports/southpark_alignment_report.md`.

## Run The Local Grader

```bash
pip install -r requirements.txt
python3 grade.py --self-test
python3 grade.py <submission_dir>
```

The grader requires `openpyxl`. Recalculation also needs LibreOffice when using `--recalc`.

## Review Path

1. Read `SUBMISSION.md`.
2. Check `QA_ASSESSMENT.md` for the task findings.
3. Check `DEPLOYMENT_ALIGNMENT.md` before using the deployed task.
4. Run `python3 tools/qa_loop/qa_check.py --repo .`.
5. Use `TASK_OVERVIEW.md` only when you need the full task spec.
