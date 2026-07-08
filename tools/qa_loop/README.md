# QA Loop: Path And Source Consistency Checker

This is a small QA loop for batch Odyssey task review. It checks one failure mode:

Prompt, environment, verifier, and repo docs disagree about files, paths, or runtime assumptions.

It is meant to help review 20-30 tasks at a time. It does not decide whether a task passes QA. It
points a human reviewer to concrete evidence.

This is intentionally not an automated judge. The tool is a fast consistency pass that helps a reviewer
spend their time on the places where a task is most likely to be unfair: missing files, mixed paths,
stale verifier assumptions, or seed data that disagrees with the prompt.

## Why This Check

This task surfaced a real version of the problem:

- local repo docs use `/data` and `/tmp/outputs`
- the deployed prompt uses Outlook plus Fropbox/Docket
- one deployed email still mentions `/tmp/outputs`
- the deployed verifier expects a Fropbox source room
- the local repo has a separate full-grid grader

That kind of drift is easy to miss when a task has several prompts, handoff docs, seed files, and
verifiers. It is also common enough to make a reusable checker worthwhile.

The judgment behind this check is simple: when a model fails because the world is inconsistent, that
is not a useful model failure. A good Odyssey task should make the model struggle with the workflow,
not with hidden contradictions in the task package.

## What It Checks

- file count claims in docs against `world_files`
- prompt file names against the repo inventory
- local path contracts such as `/data` and `/tmp/outputs`
- deployed path contracts such as `/SouthPark Centre Underwriting`
- runtime claims such as LibreOffice vs Python spreadsheet libraries
- verifier expected files against prompt file names
- deployed email output-path conflicts when an env snapshot is supplied
- call-budget scripts that report a granular count without saying whether the interface forces it

## How To Run

From the repo root:

```bash
python3 tools/qa_loop/qa_check.py --repo .
```

With deployed artifacts from the Fleet workbench:

```bash
python3 tools/qa_loop/qa_check.py \
  --repo . \
  --task-json ../api/task.json \
  --verifier ../api/deployed_verifier.py \
  --env-snapshot ../api/env_snapshot.sqlite \
  --out-dir tools/qa_loop/sample_reports \
  --report-name southpark_alignment_report.md
```

For this Codex workspace, the command I used was:

```bash
python3 tools/qa_loop/qa_check.py \
  --repo . \
  --task-json ../project2/api/task.json \
  --verifier ../project2/api/deployed_verifier.py \
  --env-snapshot ../project2/api/env_snapshot.json \
  --out-dir tools/qa_loop/sample_reports \
  --report-name southpark_alignment_report.md
```

The tool writes:

- a Markdown report for reviewers
- a CSV file for batch triage
- a JSON file for dashboards or later automation

The CSV includes blank reviewer fields so a batch owner can mark each item as confirmed, expected,
false positive, or needs more data.

## How Humans Stay In Control

Every finding has:

- severity
- evidence
- source files
- the human decision needed

The tool uses `review` severity when it sees a likely issue that may also be intentional. For
example, `/data` and Fropbox paths in the same repo are not automatically wrong if the repo clearly
separates local and deployed modes.

Suggested review rhythm for a 20-30 task batch:

1. Run the checker for each task package.
2. Sort by high severity findings.
3. Manually confirm the top issues against the prompt, verifier, seed, and any trace evidence.
4. Label each issue as confirmed, expected, false positive, or needs more data.
5. Only then decide whether the task is safe to ship, needs a fix, needs more eval, or should be
   pruned.

## Sample Checks I Verified

Right:

- It flags the deployed email/output conflict when a snapshot contains `/tmp/outputs` but the
  deployed prompt requires `/SouthPark Centre Underwriting/Outputs`.
- It flags the repo/deployed path split. That is the main Part 1 issue.
- It treats the call-budget number as a target or ceiling unless the interface forces the slow path.

Too broad:

- It can flag legacy prompt files that are kept for history. A human should decide whether those
  should be ignored, archived, or updated.
- It cannot prove that Fropbox files are absent from the deployed task if the snapshot does not expose
  the Fropbox app DB. It correctly turns that into a preflight item instead of a hard failure.

## Known Limitations

- It is a static checker. It does not replace a live agent run.
- It looks for file names and path contracts, not full semantic derivability.
- It cannot inspect hidden app databases unless you pass an exported snapshot or query result.
- It may report historical docs or legacy prompts unless the batch runner filters them.
- It only handles common file/path patterns today.

## What I Would Build Next With Two Weeks

I would add a trace analyzer that reads model-run traces and compares actual behavior against these
warnings. For example, it would show whether the agent searched for nonexistent paths, got stuck on a
missing file, skipped the source room, or finished in far fewer calls than the task claims. I would
also add a small batch dashboard that ranks tasks by QA risk and lets a reviewer drill into the exact
prompt, verifier, seed, and trace evidence behind each warning.
