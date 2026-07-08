# Project 2 Presentation Prep

## Plain-English Summary

Project 2 asked me to check whether one Odyssey task was actually ready to use. I treated that as a
QA problem: does the prompt describe a real workflow, does the environment contain the needed files,
can the answer be derived from those files, and does the verifier grade the same thing the prompt
asks for?

My main finding was that the task itself is realistic, but the local repo and the deployed Fleet
version are not the same surface. The local repo is a `/data` and `/tmp/outputs` bash task with a
full-grid grader. The deployed task is Outlook plus Fropbox/Docket, with final uploads expected in
`/SouthPark Centre Underwriting/Outputs`.

That mismatch matters because it can create fake model failures. If a model follows an email that
says to save to `/tmp/outputs`, but the verifier expects Fropbox uploads, the model may fail for a
task-packaging reason instead of a real reasoning failure.

## What I Did

- Pulled and read the deployed prompt and verifier.
- Inspected the deployed environment snapshot and visible attachments.
- Read the repo docs, prompts, grader, setup script, and world-file layout.
- Ran the local grader self-test to check whether the repo was internally coherent.
- Compared the local task surface against the deployed task surface.
- Added repo docs that separate the local task from the deployed task.
- Built a reusable QA loop that flags path, file, prompt, verifier, and runtime mismatches.

## What I Personally Verified

- The local repo has 73 world files: 46 PDFs, 18 XLSX files, and 9 HTML emails.
- The local full-grid grader self-test passes against ground truth.
- The deployed prompt expects Fropbox outputs.
- The deployed verifier also expects Fropbox outputs and source-room evidence.
- One deployed seed email mentions `/tmp/outputs`, which conflicts with the deployed prompt.
- The environment snapshot I inspected was email-heavy and did not show Fropbox drive rows, so the
  source room needs a fresh preflight before production.

## What I Changed

- Added `QA_ASSESSMENT.md` to explain the task quality, risks, and production blockers.
- Added `DEPLOYMENT_ALIGNMENT.md` to make the local-vs-deployed split explicit.
- Added `prompts/deployed_fropbox_prompt.md` to preserve the deployed prompt surface.
- Updated README and handoff docs so maintainers do not mix local paths with deployed Fropbox paths.
- Built `tools/qa_loop/qa_check.py` as a reusable consistency checker for batch QA.
- Added sample Markdown, CSV, and JSON reports with manual review notes.

## How I Would Present The QA Loop

The QA loop is built around one failure mode: prompt, environment, verifier, and repo docs disagree
about files, paths, or runtime assumptions.

It scans the task package and flags likely mismatches. It does not decide whether a task is good.
The reviewer still has to confirm the evidence, mark false positives, and decide whether the task
should ship, be fixed, get more evals, or be pruned.

The important point is that the loop turns one-off judgment into a repeatable review process for
20-30 tasks at a time.

## What I Would Say If Asked Why This Was Fast

The assignment looked long because the workflow covers a lot: prompt review, verifier review,
environment inspection, evals, task fixing, and a reusable QA loop. We moved quickly because the
main defect was a structural alignment issue, not a hidden finance calculation issue. Once I compared
the prompt, verifier, repo, and environment side by side, the highest-value fix was to make that
drift explicit and build a checker that would catch the same class of issue in future tasks.

I would not claim that every production question is closed. The deployed seed still needs a fresh
Fropbox preflight and trace review. The honest result is: the local repo package is cleaned up and
the reusable QA loop is built, while the remaining production checks are clearly named.

## Likely Panel Questions

**Why not just trust the verifier?**  
Because a verifier can be strict, loose, or pointed at the wrong state. I checked whether the verifier
matched the prompt and the visible environment before treating its score as meaningful.

**What makes this task authentic?**  
The real estate underwriting workflow is realistic: intake, rent-roll reconciliation, market comps,
debt sizing, revisions, waterfall, IC summary, and LOI.

**What is the biggest risk?**  
The biggest risk is not the real estate math. It is task-surface drift. The deployed task and local
repo can send the agent to different paths or assumptions.

**Where did automation help?**  
Automation helped scan for repeated consistency issues across files. It did not make the final QA
decision. I used it to focus human review.

**What would you build next?**  
I would add a trace analyzer that compares model actions against static QA warnings. That would show
whether agents actually searched for missing files, used the wrong path, skipped source evidence, or
finished much faster than the task claims.

