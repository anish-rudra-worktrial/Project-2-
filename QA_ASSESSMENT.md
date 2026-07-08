# QA Assessment: SouthPark / Ballantyne Odyssey Task

Assessment date: 2026-07-07  
Assessed task key: `odyssey-real-estate-pe-underwriting-full_243edf59_v1`  
Assessed deployed environment: `real-estate-pe-underwriting-office-bash`

## Verdict

The task is authentic and domain-realistic, but the repository and the deployed assignment are
currently out of alignment.

The repository contains a rich local bash/file task: `/data` source files, `/tmp/outputs`
deliverables, a 73-file world, ground-truth workbooks, and a deterministic full-grid grader. That
local package self-tests successfully against its own ground truth.

The deployed Fleet assignment uses a different interface: Outlook plus Fropbox/Docket, final uploads
to `/SouthPark Centre Underwriting/Outputs`, and a deployed evidence-weighted verifier. The deployed
prompt explicitly removed the LibreOffice requirement and tells the agent to use Python spreadsheet
libraries such as `openpyxl` or `xlsxwriter`.

This drift is the main QA issue. A maintainer reading only this repo could fix or run the wrong task
surface.

## Reviewer Stance

I treated this as a production QA problem, not as a prompt rewrite exercise. The question I kept
coming back to was: can a competent agent solve the task from the visible world, and will the
verifier reward the same work the prompt asked for?

My answer is: the local repo task is coherent, but the deployed version still needs a seed and
verifier preflight before I would call it production-ready. The main risk is not the finance domain.
The main risk is that the task instructions, source-room shape, and verifier expectations can point
to different places.

I used scripts and Codex to move faster, but I did not treat tool output as the verdict. I manually
checked the key evidence: prompt text, verifier constants, repo docs, world-file inventory, deployed
environment snapshot counts, and extracted source facts from the visible attachments.

## What Was Verified

- The cloned repo contains the full intended local world:
  - 9 HTML emails
  - 46 PDFs
  - 18 XLSX files
  - 73 total files under `world_files/`
- The local repo grader self-test passes identity:
  - `30797/30797` checks pass on ground truth.
  - tracker phase snapshots pass.
  - injected-error detection passes.
- The current local self-test robustness fixture reports `27621/30797` rather than the older
  README/HANDOFF claim of about `30295/30797`.
- The deployed environment snapshot inspected through the Fleet workbench exposed:
  - 9 Outlook emails
  - 8 email attachments
  - no generic `drive_items`, `file_storage`, or `task_linked_resources` rows in the manager
    snapshot I could inspect.
- The deployed verifier expects a Fropbox source room with at least 64 source files and six source
  folders. That source-room expectation should be confirmed directly against a fresh deployed seed.

## Major Findings

### 1. Two Task Surfaces Are Mixed Together

Local repo surface:

- Inputs: `/data/**`
- Outputs: `/tmp/outputs/`
- Agent fills a pre-seeded workbook.
- Local grader reads workbook files from a submission directory.
- LibreOffice recalc is part of the local full-grid grading story.

Deployed Fleet surface:

- Inputs: Outlook plus Fropbox/Docket.
- Deal room root: `/SouthPark Centre Underwriting`
- Outputs: `/SouthPark Centre Underwriting/Outputs`
- Final artifacts:
  - `southpark_centre_underwriting.xlsx`
  - `ballantyne_wacc_screen.xlsx`
  - `Pipeline_Tracker_Q2_2026.xlsx`
- Agent is told to use Python spreadsheet libraries, not LibreOffice.
- Deployed verifier is evidence-weighted and does not use the local 30k-cell grader.

These can both exist, but they must be explicitly named as separate modes.

Why this matters: a model could do reasonable work and still fail because it saved to the path named
in an email instead of the path expected by the verifier. That is not a real model failure. It is a
task alignment failure.

### 2. Deployed Seed Email Conflicts With Deployed Prompt

The deployed Sarah email `FW: SouthPark Centre - Start Underwriting` says to save the model to
`/tmp/outputs/`.

The deployed prompt and verifier require Fropbox upload to:

`/SouthPark Centre Underwriting/Outputs`

For the deployed task, the email should be patched to match the prompt/verifier.

This is the highest-confidence issue because it came from direct prompt and seed evidence, not from
an inference.

### 3. Source-Room Integrity Needs A Fresh Seed Preflight

The deployed verifier checks source-room integrity by counting Fropbox `entries` whose metadata
contains `world_files/`, and it expects at least 64 source files plus these folders:

- `Dataroom`
- `Ballantyne Office Centre`
- `Internal`
- `Lenders`
- `Construction`
- `Market Research`

Before accepting the deployed task, run a fresh-seed preflight that evaluates the verifier's
source-room status. If it reports missing source files or folders, seed the missing Fropbox room or
relax the deployed prompt/verifier to the smaller email-attachment world.

This is a review item rather than a confirmed failure. The snapshot I could inspect did not expose
Fropbox drive rows, but that may be a limitation of the manager snapshot rather than the live task.

### 4. Deployed Verifier Is Directionally Good But Loose In Places

Good:

- Grades final files, workbook content, tracker state, replies, and cross-artifact consistency.
- Separates compact result checks from source/diligence support.
- Avoids total-zeroing most partial mistakes.

Risks:

- Ballantyne verdict detection is broad enough that contradictory text can receive some credit.
- SouthPark lender result accepts First Southeast or Piedmont. The local repo's full-grid ground
  truth expects First Southeast.
- Several source-trail checks are keyword based rather than value/source reconciliation based.

## Part 1 Answers

Authentic?  
Yes. The work resembles a real acquisitions-associate underwriting workflow.

Matches the environment?  
Partially. The repo matches its local `/data` sandbox. The deployed assignment matches an
Outlook/Fropbox task. The repo did not previously make that split explicit.

Ground truth derivable?  
For the local repo, yes: the world files and ground-truth workbooks self-test. For the deployed
assignment, core facts are derivable from visible emails/attachments, but the full Fropbox source
room must be preflighted.

Verifier grades the right thing?  
Local grader: yes for the local full-grid workbook task.  
Deployed verifier: mostly, but it should tighten path/source/lender/verdict checks.

Odyssey-like?  
The local repo is Odyssey-like in breadth but file-based and therefore partially batchable. The
deployed task is more realistic because it uses Outlook/Fropbox state, but it needs source-room
confirmation and trace review.

Too easy?  
If only the deployed 9 emails and 8 attachments are available, yes: likely under 150 competent-agent
tool calls. With the full Fropbox source room and stricter source reconciliation, it can plausibly
target 250-300 calls for the work trial.

Likely competent-agent tool calls?  

- Local file-based repo: coarse path roughly 100-200 despite granular estimates above 700.
- Deployed email-attachment-only world: roughly 75-150.
- Deployed full Fropbox source room with sequential source reconciliation: roughly 250-350.

## Fixes Applied In This Repo

- Added this QA assessment.
- Added `DEPLOYMENT_ALIGNMENT.md` to make local-vs-deployed drift explicit.
- Added `prompts/deployed_fropbox_prompt.md` as the observed deployed prompt surface.
- Updated docs to identify the local `/data` task and deployed Outlook/Fropbox task as separate
  surfaces.
- Updated stale self-test numbers in docs to match the observed local run.

## Evidence Trail I Would Show In Review

- Repo self-test proves the local file task is internally consistent.
- World inventory proves the local data room has the intended 73-file source set.
- Deployed prompt proves the production-facing task is Fropbox-based.
- Deployed verifier proves production grading expects Fropbox uploads and source-room evidence.
- Environment snapshot proves the visible deployed surface I inspected was email-heavy.
- Seed email text proves the `/tmp/outputs` conflict.

This is the chain of evidence behind the recommendation. The QA loop in Part 2 is built to make
this same chain easier to check across a batch.

## Remaining Before Production

1. Patch deployed seed email `1002` so it no longer says `/tmp/outputs/`.
2. Run the deployed source-room preflight on a fresh seed and confirm 64+ files and 6/6 folders.
3. Run at least one capped deployed eval and review trace/tool-call profile.
4. Tighten deployed verifier checks for path, Ballantyne verdict, lender decision, and source/value
   reconciliation.
5. Decide whether the intended production benchmark is the rich local full-grid model, the deployed
   Outlook/Fropbox evidence-weighted version, or a merged version.
