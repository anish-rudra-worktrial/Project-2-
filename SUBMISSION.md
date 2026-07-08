# Project 2 Submission

Task key: `odyssey-real-estate-pe-underwriting-full_243edf59_v1`  
Environment: `real-estate-pe-underwriting-office-bash`  
Review date: 2026-07-07

## Executive Summary

I reviewed the Odyssey real estate private equity underwriting task as a QA and task-extension
exercise. The task is authentic: it asks an agent to work through a real acquisitions workflow with
intake, diligence, rent-roll reconciliation, market comps, financing, revisions, waterfall, IC
summary, LOI, and tracker updates.

The main issue is alignment. The local repo is a file-based bash task with `/data` inputs,
`/tmp/outputs` outputs, and a deterministic full-grid grader. The deployed Fleet workbench version
uses Outlook plus Fropbox/Docket, expects uploads under `/SouthPark Centre Underwriting/Outputs`,
and uses a different evidence-weighted verifier.

That mismatch can create fake model failures. A model should fail because the underwriting workflow
is hard, not because the seed email, prompt, repo docs, and verifier point to different places.

## What Changed

- Added `QA_ASSESSMENT.md` with the Part 1 assessment, evidence, risks, and production blockers.
- Added `DEPLOYMENT_ALIGNMENT.md` to separate the local repo surface from the deployed Fleet
  surface.
- Added `prompts/deployed_fropbox_prompt.md` to preserve the observed deployed prompt contract.
- Updated README, handoff, world-layout, grader docs, and call-budget notes so maintainers do not
  mix local and deployed assumptions.
- Added `tools/qa_loop/` with a reusable consistency checker for batch QA.

## Part 1: Assessment And Fixes

The local repo is internally coherent. It contains 73 world files, including 46 PDFs, 18 XLSX files,
and 9 HTML emails. The local self-test passes against ground truth:

```text
Identity:      30797/30797
Tracker/phase: PASS
Robustness:    27621/30797
Detection:     PASS
```

The deployed task is realistic but needs a production preflight. The highest-confidence issue is
that one deployed seed email mentions `/tmp/outputs`, while the deployed prompt and verifier require
uploads to `/SouthPark Centre Underwriting/Outputs`.

My task fix was to make the two surfaces explicit and preserve a corrected deployed prompt contract
in the repo. That gives the team a clean basis for either shipping the local bash/file task or
shipping the Outlook/Fropbox task after patching the deployed seed.

Key docs:

- `QA_ASSESSMENT.md`
- `DEPLOYMENT_ALIGNMENT.md`
- `WORLD_LAYOUT.md`
- `HANDOFF.md`
- `prompts/deployed_fropbox_prompt.md`

## Tool-Call Profile And Extension

The current local task is broad, but a capable bash agent can batch parts of it. The call-budget
script now reports two profiles:

- coarse efficient run: about 336 calls
- granular item-by-item run: about 705 calls

For the assignment target, the deployed task should be pushed toward roughly 250 to 300 calls by
making the Fropbox source room load-bearing, preserving sequential source reconciliation, and
tightening the verifier around source-backed evidence. If the deployed task only exposes emails and
8 attachments, it is likely too easy and may sit closer to 75 to 150 calls.

I also ran one capped live eval on the deployed task with `pass_k=1`. The run completed 250 steps
and scored `0.04`. The trace showed the agent reached the Fropbox/Docket workflow and found the
SouthPark source folders, then spent many later steps trying to work around missing practical access
to bash/Python execution for workbook creation and upload. I read that as evidence of a deployed
tooling/interface problem, not as a clean underwriting-reasoning failure.

Run:

```bash
python3 tools/call_budget.py
```

## Part 2: Reusable QA Loop

I built a QA loop for this failure mode:

Prompt, environment, verifier, and repo docs disagree about files, paths, or runtime assumptions.

That failure mode is worth automating because it is repetitive, easy to miss, and directly affects
whether a task failure is real. The tool scans the task package, flags likely mismatches, and writes
Markdown, CSV, and JSON outputs. It does not decide whether a task passes. It gives a reviewer
evidence and a place to record the human decision.

Run from the repo root:

```bash
python3 tools/qa_loop/qa_check.py --repo .
```

Run with deployed artifacts:

```bash
python3 tools/qa_loop/qa_check.py \
  --repo . \
  --task-json ../project2/api/task.json \
  --verifier ../project2/api/deployed_verifier.py \
  --env-snapshot ../project2/api/env_snapshot.json \
  --out-dir tools/qa_loop/sample_reports \
  --report-name southpark_alignment_report.md
```

Sample outputs:

- `tools/qa_loop/sample_reports/southpark_alignment_report.md`
- `tools/qa_loop/sample_reports/southpark_alignment_report.csv`
- `tools/qa_loop/sample_reports/southpark_alignment_report.json`

## Human Review Sample

I manually checked the sample QA report against the repo, deployed prompt, verifier, and environment
snapshot.

The tool was right about:

- the deployed seed email output-path conflict
- the local-vs-deployed path split
- the need for a fresh Fropbox source-room preflight

The tool was too broad about:

- mixed paths in reviewer docs that intentionally explain both surfaces
- historical file-count notes in `CHANGELOG.md`

This is the intended human-in-the-loop pattern. The script finds likely drift. A person confirms
what is real, what is expected context, what is a false positive, and what needs more data.

## Known Limits

- I could not patch the live deployed seed email from this repo.
- I confirmed the live eval could reach the Fropbox folder structure, but I did not verify every
  expected source file in that live source room.
- The sample QA loop is static. It helps prioritize trace review, but it does not replace it.
- The live eval result is one run, so it is useful evidence but not a stable solve-rate estimate.

## What I Would Build Next With Two Weeks

I would add a trace analyzer that compares model actions against the static QA warnings. It would
show whether agents searched for nonexistent paths, got stuck on missing files, skipped source
evidence, or completed the task in far fewer calls than claimed. I would also add a small batch
dashboard for 20 to 30 tasks, with each warning linked back to the prompt, verifier, seed, and trace
evidence. The goal would be to let a reviewer spend time on judgment rather than manually hunting
for mismatches across every file.
