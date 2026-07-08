# QA Loop Report

Failure mode checked: prompt, environment, verifier, and repo docs disagree about files, paths, or runtime assumptions.

This report flags issues for a human reviewer. It does not decide whether the task is good or bad, and it should not be treated as the final answer.

Recommended review loop:

1. Read the high findings first and confirm them against source files or the live seed.
2. Sample a few review findings and mark each as confirmed, expected, false positive, or needs more data.
3. Only change the task after a person can explain the failure mode in plain language.

## Scope

- Repo: `/Users/fleettrial_candidate/Documents/Codex/2026-07-07/thia/work/odyssey-work-trial`
- Text files scanned: 31
- world_files count: 73
- world_files by suffix: `{"html": 9, "pdf": 46, "xlsx": 18}`
- Env snapshot counts: `{"attachments": 8, "drive_items": 0, "file_storage": 0, "messages": 9, "tables": 59, "task_linked_resources": 0}`

## Summary

- high: 1
- review: 11
- info: 2

## Findings

### 1. World file type count claim does not match the repo

- Severity: `review`
- Check: `WORLD_TYPE_COUNT_MISMATCH`
- Sources: `CHANGELOG.md`
- Evidence: CHANGELOG.md claims PDF/XLSX/HTML = (46, 17, 9); world_files currently has (46, 18, 9).
- Human review: Update the claim or explain why the text is historical.

### 2. A prompt or primary doc references a file name not found in the repo

- Severity: `review`
- Check: `MISSING_FILE_REFERENCE`
- Sources: `prompts/agent_prompt_buildcontract_v1.md`
- Evidence: `Lease_Abstract_01_Meridian_Financial.pdf` is referenced in prompts/agent_prompt_buildcontract_v1.md.
- Human review: Check whether this is a renamed file, a generated output, a legacy prompt, or a real missing source.

### 3. A prompt or primary doc references a file name not found in the repo

- Severity: `review`
- Check: `MISSING_FILE_REFERENCE`
- Sources: `prompts/agent_prompt_buildcontract_v1.md`
- Evidence: `Lease_Abstract_20_SouthPark_Dental.pdf` is referenced in prompts/agent_prompt_buildcontract_v1.md.
- Human review: Check whether this is a renamed file, a generated output, a legacy prompt, or a real missing source.

### 4. Repo docs and deployed prompt use different path contracts

- Severity: `review`
- Check: `DEPLOYED_REPO_PATH_SPLIT`
- Sources: `deployed_task_prompt`, `CHANGELOG.md`, `DEPLOYMENT_ALIGNMENT.md`, `HANDOFF.md`, `QA_ASSESSMENT.md`, `README.md`, `WORLD_LAYOUT.md`, `prompts/agent_prompt_buildcontract_v1.md`, `prompts/agent_prompt_narrative.txt`
- Evidence: The deployed prompt uses Fropbox paths, while repo files still mention /data or /tmp/outputs. Examples: CHANGELOG.md, DEPLOYMENT_ALIGNMENT.md, HANDOFF.md, QA_ASSESSMENT.md, README.md, WORLD_LAYOUT.md, prompts/agent_prompt_buildcontract_v1.md, prompts/agent_prompt_narrative.txt.
- Human review: Confirm this is an intentional local-vs-deployed split. If not, pick one contract.

### 5. One file mentions both local and Fropbox path contracts

- Severity: `review`
- Check: `MIXED_PATHS_IN_ONE_FILE`
- Sources: `DEPLOYMENT_ALIGNMENT.md`
- Evidence: DEPLOYMENT_ALIGNMENT.md contains both local file paths and Fropbox/Docket references.
- Human review: This can be fine in an alignment note. In an agent prompt, it is usually confusing.

### 6. One file mentions both local and Fropbox path contracts

- Severity: `review`
- Check: `MIXED_PATHS_IN_ONE_FILE`
- Sources: `HANDOFF.md`
- Evidence: HANDOFF.md contains both local file paths and Fropbox/Docket references.
- Human review: This can be fine in an alignment note. In an agent prompt, it is usually confusing.

### 7. One file mentions both local and Fropbox path contracts

- Severity: `review`
- Check: `MIXED_PATHS_IN_ONE_FILE`
- Sources: `QA_ASSESSMENT.md`
- Evidence: QA_ASSESSMENT.md contains both local file paths and Fropbox/Docket references.
- Human review: This can be fine in an alignment note. In an agent prompt, it is usually confusing.

### 8. One file mentions both local and Fropbox path contracts

- Severity: `review`
- Check: `MIXED_PATHS_IN_ONE_FILE`
- Sources: `README.md`
- Evidence: README.md contains both local file paths and Fropbox/Docket references.
- Human review: This can be fine in an alignment note. In an agent prompt, it is usually confusing.

### 9. One file mentions both local and Fropbox path contracts

- Severity: `review`
- Check: `MIXED_PATHS_IN_ONE_FILE`
- Sources: `WORLD_LAYOUT.md`
- Evidence: WORLD_LAYOUT.md contains both local file paths and Fropbox/Docket references.
- Human review: This can be fine in an alignment note. In an agent prompt, it is usually confusing.

### 10. Runtime tool claims differ between repo and deployed prompt

- Severity: `review`
- Check: `RUNTIME_TOOL_SPLIT`
- Sources: `deployed_task_prompt`, `CHANGELOG.md`, `DEPLOYMENT_ALIGNMENT.md`, `HANDOFF.md`, `QA_ASSESSMENT.md`, `grade.py`, `prompts/agent_prompt_prescriptive.txt`, `prompts/agent_prompt_prescriptive_v2.txt`, `tools/grader/README.md`
- Evidence: The deployed prompt mentions Python spreadsheet libraries, while repo docs mention LibreOffice. Examples: CHANGELOG.md, DEPLOYMENT_ALIGNMENT.md, HANDOFF.md, QA_ASSESSMENT.md, grade.py, prompts/agent_prompt_prescriptive.txt, prompts/agent_prompt_prescriptive_v2.txt, tools/grader/README.md.
- Human review: Decide whether LibreOffice is local-only or expected in deployment.

### 11. The repo now documents both local and deployed task surfaces

- Severity: `info`
- Check: `REPO_HAS_TWO_SURFACES`
- Sources: `CHANGELOG.md`, `DEPLOYMENT_ALIGNMENT.md`, `HANDOFF.md`, `QA_ASSESSMENT.md`, `README.md`, `WORLD_LAYOUT.md`
- Evidence: Local path docs: 12. Fropbox docs: 6. This is useful if clearly labeled, risky if copied into one prompt.
- Human review: Keep the split explicit in README and handoff docs.

### 12. Seed email gives an output path that conflicts with the deployed prompt

- Severity: `high`
- Check: `SEED_EMAIL_OUTPUT_CONFLICT`
- Sources: `env_snapshot`, `deployed_task_prompt`
- Evidence: The deployed prompt tells the agent to upload to `/SouthPark Centre Underwriting/Outputs`, but an email body mentions `/tmp/outputs`.
- Human review: Patch the seed email or prompt. The agent should not have to guess which instruction wins.

### 13. Verifier expects a source room, but the manager snapshot does not show drive files

- Severity: `review`
- Check: `SOURCE_ROOM_NEEDS_PREFLIGHT`
- Sources: `env_snapshot`, `deployed_verifier`
- Evidence: Snapshot counts: drive_items=0, file_storage=0. This may be a manager snapshot limitation, so treat it as a preflight item.
- Human review: Run the verifier's own source-room check against a fresh seed or query the Fropbox DB directly.

### 14. Snapshot looks email-attachment heavy

- Severity: `info`
- Check: `EMAIL_ATTACHMENT_ONLY_SURFACE`
- Sources: `env_snapshot`
- Evidence: Snapshot counts: messages=9, attachments=8, drive_items=0.
- Human review: If the intended task needs a Fropbox source room, confirm it is visible through the task tools.

## Reviewer Decision Worksheet

| # | Check | Severity | Human decision | Owner | Next action |
|---:|---|---|---|---|---|
| 1 | `WORLD_TYPE_COUNT_MISMATCH` | `review` |  |  |  |
| 2 | `MISSING_FILE_REFERENCE` | `review` |  |  |  |
| 3 | `MISSING_FILE_REFERENCE` | `review` |  |  |  |
| 4 | `DEPLOYED_REPO_PATH_SPLIT` | `review` |  |  |  |
| 5 | `MIXED_PATHS_IN_ONE_FILE` | `review` |  |  |  |
| 6 | `MIXED_PATHS_IN_ONE_FILE` | `review` |  |  |  |
| 7 | `MIXED_PATHS_IN_ONE_FILE` | `review` |  |  |  |
| 8 | `MIXED_PATHS_IN_ONE_FILE` | `review` |  |  |  |
| 9 | `MIXED_PATHS_IN_ONE_FILE` | `review` |  |  |  |
| 10 | `RUNTIME_TOOL_SPLIT` | `review` |  |  |  |
| 11 | `REPO_HAS_TWO_SURFACES` | `info` |  |  |  |
| 12 | `SEED_EMAIL_OUTPUT_CONFLICT` | `high` |  |  |  |
| 13 | `SOURCE_ROOM_NEEDS_PREFLIGHT` | `review` |  |  |  |
| 14 | `EMAIL_ATTACHMENT_ONLY_SURFACE` | `info` |  |  |  |

## Manual Review Notes

- Tool was right about: the deployed seed email conflict is real. Email `1002` tells the agent to
  save to `/tmp/outputs`, while the deployed prompt says to upload to
  `/SouthPark Centre Underwriting/Outputs`.
- Tool was right about: the repo and deployed task have different path contracts. The repo is a
  local `/data` task, while the deployed task is Outlook plus Fropbox/Docket.
- Tool was right about: the source room needs a deployed preflight. The verifier expects source-room
  files, but the manager snapshot I inspected only showed emails and attachments.
- Tool was too broad about: `MIXED_PATHS_IN_ONE_FILE` findings in `README.md`, `HANDOFF.md`, and
  `QA_ASSESSMENT.md`. Those files now intentionally document both surfaces. That is acceptable
  because they are reviewer docs, not agent prompts.
- Tool was too broad about: `CHANGELOG.md` file-count mismatches. Those may be historical notes, so
  they should not block production by themselves.
- Final human decision: fix the deployed email conflict, run a Fropbox source-room preflight, and
  keep the local-vs-deployed split explicit in repo docs.
