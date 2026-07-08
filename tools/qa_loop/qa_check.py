#!/usr/bin/env python3
"""Batch QA checks for Odyssey task consistency.

This tool focuses on one failure mode:

    The prompt, repo docs, verifier, and environment disagree about files,
    paths, or runtime assumptions.

It is intentionally conservative. It flags evidence for a human reviewer
instead of deciding whether a task is good or bad.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import re
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".py",
    ".sh",
    ".html",
    ".json",
}

SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
}

SKIP_PATH_PARTS = {
    "sample_reports",
}

SKIP_FILES = {
    "SUBMISSION.md",
}

FILE_TOKEN_RE = re.compile(
    r"[^\s`\"'<>{}\[\]]+\.(?:pdf|xlsx|xls|xlsm|csv|tsv|html|md|txt|json|py|sh)",
    re.IGNORECASE,
)

ABS_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_:])(/(?:[A-Za-z0-9_.()#&+\- ]+/?){1,})"
)

BACKTICK_RE = re.compile(r"`([^`]+)`")

COUNT_RE = re.compile(r"(\d+)[- ]file world", re.IGNORECASE)
TYPE_COUNT_RE = re.compile(
    r"(\d+)\s*PDFS?\s*/\s*(\d+)\s*XLSX\s*/\s*(\d+)\s*HTML",
    re.IGNORECASE,
)


@dataclass
class SourceDoc:
    label: str
    path: str
    text: str
    kind: str


@dataclass
class Finding:
    check_id: str
    severity: str
    title: str
    evidence: str
    human_action: str
    sources: list[str] = field(default_factory=list)


def read_text(path: Path, limit: int = 2_000_000) -> str:
    try:
        data = path.read_bytes()
    except OSError:
        return ""
    if len(data) > limit:
        data = data[:limit]
    for encoding in ("utf-8", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def iter_text_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if "tools" in path.parts and "qa_loop" in path.parts:
            continue
        if any(part in SKIP_PATH_PARTS for part in path.parts):
            continue
        if path.name in SKIP_FILES:
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def load_repo_docs(repo: Path) -> list[SourceDoc]:
    docs: list[SourceDoc] = []
    for path in iter_text_files(repo):
        label = rel(path, repo)
        kind = "repo_text"
        if label.startswith("prompts/"):
            kind = "prompt"
        elif label.startswith("tools/"):
            kind = "tool"
        elif label in {"README.md", "HANDOFF.md", "WORLD_LAYOUT.md"}:
            kind = "primary_doc"
        docs.append(SourceDoc(label=label, path=str(path), text=read_text(path), kind=kind))
    return docs


def load_task_json(path: Path | None) -> SourceDoc | None:
    if not path:
        return None
    try:
        data = json.loads(path.read_text())
    except Exception:
        return SourceDoc(
            label="deployed_task_json",
            path=str(path),
            text=read_text(path),
            kind="deployed_task",
        )
    prompt = data.get("prompt")
    if prompt is None and isinstance(data.get("task"), dict):
        prompt = data["task"].get("prompt")
    if prompt is None:
        prompt = json.dumps(data, indent=2, sort_keys=True)
    return SourceDoc(
        label="deployed_task_prompt",
        path=str(path),
        text=str(prompt),
        kind="deployed_task",
    )


def load_verifier(path: Path | None) -> SourceDoc | None:
    if not path:
        return None
    return SourceDoc(
        label="deployed_verifier",
        path=str(path),
        text=read_text(path),
        kind="verifier",
    )


def extract_file_refs(text: str) -> set[str]:
    refs: set[str] = set()
    for match in FILE_TOKEN_RE.finditer(text):
        ref = match.group(0)
        ref = ref.strip(".,;:)]}(")
        ref = ref.split("/")[-1]
        if ref.startswith(".") or ref.startswith("_"):
            continue
        if ref.count("(") != ref.count(")"):
            continue
        refs.add(ref)
    return refs


def extract_paths(text: str) -> set[str]:
    paths: set[str] = set()
    for match in BACKTICK_RE.finditer(text):
        raw = match.group(1).strip()
        if raw.startswith("/") or "/data" in raw or "/tmp" in raw or "/SouthPark" in raw:
            paths.add(raw.strip(".,;"))
    for match in ABS_PATH_RE.finditer(text):
        raw = match.group(1).strip()
        raw = raw.rstrip(".,;:)])}")
        if raw and not raw.startswith("//"):
            paths.add(raw)
    return paths


def world_inventory(repo: Path) -> dict:
    world = repo / "world_files"
    files = [p for p in world.rglob("*") if p.is_file()] if world.exists() else []
    by_suffix = Counter(p.suffix.lower().lstrip(".") for p in files)
    basenames = {p.name for p in files}
    repo_files = {p.name for p in repo.rglob("*") if p.is_file() and ".git" not in p.parts}
    return {
        "world_exists": world.exists(),
        "world_total": len(files),
        "world_by_suffix": dict(sorted(by_suffix.items())),
        "world_basenames": basenames,
        "repo_basenames": repo_files,
    }


def classify_path_family(text: str) -> set[str]:
    families: set[str] = set()
    if "/data" in text or "/tmp/outputs" in text:
        families.add("local_file")
    if "/SouthPark Centre Underwriting" in text or "Fropbox" in text or "Docket" in text:
        families.add("fropbox")
    if "LibreOffice" in text or "soffice" in text:
        families.add("libreoffice")
    if "openpyxl" in text or "xlsxwriter" in text:
        families.add("python_spreadsheet")
    return families


def source_claims(doc: SourceDoc) -> list[tuple[str, tuple[int, ...]]]:
    claims: list[tuple[str, tuple[int, ...]]] = []
    for match in COUNT_RE.finditer(doc.text):
        claims.append(("file_total", (int(match.group(1)),)))
    for match in TYPE_COUNT_RE.finditer(doc.text):
        claims.append(
            (
                "type_counts",
                (int(match.group(1)), int(match.group(2)), int(match.group(3))),
            )
        )
    return claims


def parse_verifier_assignments(text: str) -> dict:
    out: dict[str, object] = {}
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return out
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        name = node.targets[0].id
        if name not in {
            "EXPECTED_FILES",
            "SOURCE_FILE_FOR_OUTPUT",
            "TASK_ROOT",
            "OUTPUT_DIR",
        }:
            continue
        try:
            out[name] = ast.literal_eval(node.value)
        except Exception:
            continue
    return out


def sqlite_counts(path: Path | None) -> dict:
    if not path or not path.exists():
        return {}
    out: dict[str, int | str] = {}
    try:
        conn = sqlite3.connect(path)
    except Exception as exc:
        return {"error": repr(exc)}
    try:
        tables = [
            row[0]
            for row in conn.execute(
                "select name from sqlite_master where type='table' order by name"
            )
        ]
        out["tables"] = len(tables)
        for table in (
            "messages",
            "attachments",
            "drive_items",
            "file_storage",
            "task_linked_resources",
        ):
            if table in tables:
                out[table] = conn.execute(f"select count(*) from {table}").fetchone()[0]
        if "messages" in tables:
            columns = [
                row[1]
                for row in conn.execute("pragma table_info(messages)").fetchall()
            ]
            text_cols = [
                col
                for col in columns
                if col
                in {
                    "subject",
                    "bodyPreview",
                    "body",
                    "body_content",
                    "content",
                    "html",
                }
            ]
            if text_cols:
                expr = " || ' ' || ".join(f"coalesce({col}, '')" for col in text_cols)
                rows = conn.execute(f"select {expr} from messages").fetchall()
                out["message_text"] = "\n".join(row[0] for row in rows)
    except Exception as exc:
        out["error"] = repr(exc)
    finally:
        conn.close()
    return out


def add(
    findings: list[Finding],
    check_id: str,
    severity: str,
    title: str,
    evidence: str,
    human_action: str,
    sources: list[str] | None = None,
) -> None:
    findings.append(
        Finding(
            check_id=check_id,
            severity=severity,
            title=title,
            evidence=evidence,
            human_action=human_action,
            sources=sources or [],
        )
    )


def check_world_counts(docs: list[SourceDoc], inv: dict) -> list[Finding]:
    findings: list[Finding] = []
    seen: set[tuple[str, str, tuple[int, ...]]] = set()
    if not inv["world_exists"]:
        add(
            findings,
            "WORLD_MISSING",
            "review",
            "No world_files directory found",
            "The repo does not have a world_files directory.",
            "Confirm whether this task uses another seed format.",
        )
        return findings
    actual_total = int(inv["world_total"])
    suffixes = inv["world_by_suffix"]
    actual_types = (
        int(suffixes.get("pdf", 0)),
        int(suffixes.get("xlsx", 0)),
        int(suffixes.get("html", 0)),
    )
    for doc in docs:
        for kind, values in source_claims(doc):
            key = (doc.label, kind, values)
            if key in seen:
                continue
            seen.add(key)
            if kind == "file_total" and values[0] != actual_total:
                severity = "high" if doc.label in {"README.md", "WORLD_LAYOUT.md"} else "review"
                add(
                    findings,
                    "WORLD_COUNT_MISMATCH",
                    severity,
                    "World file count claim does not match the repo",
                    f"{doc.label} claims {values[0]} files; world_files currently has {actual_total}.",
                    "Decide whether this is a stale doc, a missing seed file, or historical changelog text.",
                    [doc.label],
                )
            if kind == "type_counts" and values != actual_types:
                severity = "high" if doc.label in {"README.md", "WORLD_LAYOUT.md"} else "review"
                add(
                    findings,
                    "WORLD_TYPE_COUNT_MISMATCH",
                    severity,
                    "World file type count claim does not match the repo",
                    (
                        f"{doc.label} claims PDF/XLSX/HTML = {values}; "
                        f"world_files currently has {actual_types}."
                    ),
                    "Update the claim or explain why the text is historical.",
                    [doc.label],
                )
    return findings


def check_missing_file_refs(docs: list[SourceDoc], inv: dict) -> list[Finding]:
    findings: list[Finding] = []
    known = set(inv["world_basenames"]) | set(inv["repo_basenames"])
    output_names = {
        "southpark_centre_underwriting.xlsx",
        "ballantyne_wacc_screen.xlsx",
        "Pipeline_Tracker_Q2_2026.xlsx",
    }
    checked_sources = [
        doc
        for doc in docs
        if doc.kind in {"prompt", "primary_doc"} or doc.label == "setup_env.sh"
    ]
    missing: dict[str, list[str]] = defaultdict(list)
    for doc in checked_sources:
        for ref in extract_file_refs(doc.text):
            if ".." in ref or "*" in ref or "RUNTIME_PROMPT_v1.md" in ref:
                continue
            base_ref = Path(ref).name
            if base_ref in output_names:
                continue
            if base_ref not in known:
                missing[base_ref].append(doc.label)
    for ref, sources in sorted(missing.items()):
        add(
            findings,
            "MISSING_FILE_REFERENCE",
            "review",
            "A prompt or primary doc references a file name not found in the repo",
            f"`{ref}` is referenced in {', '.join(sorted(set(sources)))}.",
            "Check whether this is a renamed file, a generated output, a legacy prompt, or a real missing source.",
            sorted(set(sources)),
        )
    return findings


def check_path_family_conflicts(
    docs: list[SourceDoc],
    deployed_task: SourceDoc | None,
    verifier: SourceDoc | None,
) -> list[Finding]:
    findings: list[Finding] = []
    repo_families: dict[str, set[str]] = {}
    for doc in docs:
        fam = classify_path_family(doc.text)
        if fam:
            repo_families[doc.label] = fam
    deployed_families = classify_path_family(deployed_task.text) if deployed_task else set()
    verifier_families = classify_path_family(verifier.text) if verifier else set()

    local_docs = [label for label, fam in repo_families.items() if "local_file" in fam]
    fropbox_docs = [label for label, fam in repo_families.items() if "fropbox" in fam]

    if deployed_families and "fropbox" in deployed_families and local_docs:
        add(
            findings,
            "DEPLOYED_REPO_PATH_SPLIT",
            "review",
            "Repo docs and deployed prompt use different path contracts",
            (
                "The deployed prompt uses Fropbox paths, while repo files still mention "
                f"/data or /tmp/outputs. Examples: {', '.join(local_docs[:8])}."
            ),
            "Confirm this is an intentional local-vs-deployed split. If not, pick one contract.",
            ["deployed_task_prompt"] + local_docs[:8],
        )

    for label, fam in repo_families.items():
        if "local_file" in fam and "fropbox" in fam:
            add(
                findings,
                "MIXED_PATHS_IN_ONE_FILE",
                "review",
                "One file mentions both local and Fropbox path contracts",
                f"{label} contains both local file paths and Fropbox/Docket references.",
                "This can be fine in an alignment note. In an agent prompt, it is usually confusing.",
                [label],
            )

    if deployed_families and "python_spreadsheet" in deployed_families:
        libre_docs = [label for label, fam in repo_families.items() if "libreoffice" in fam]
        if libre_docs:
            add(
                findings,
                "RUNTIME_TOOL_SPLIT",
                "review",
                "Runtime tool claims differ between repo and deployed prompt",
                (
                    "The deployed prompt mentions Python spreadsheet libraries, while repo docs "
                    f"mention LibreOffice. Examples: {', '.join(libre_docs[:8])}."
                ),
                "Decide whether LibreOffice is local-only or expected in deployment.",
                ["deployed_task_prompt"] + libre_docs[:8],
            )

    if verifier_families and "fropbox" in verifier_families and not deployed_families:
        add(
            findings,
            "VERIFIER_PROMPT_PATH_GAP",
            "high",
            "Verifier path contract is not visible in the deployed prompt",
            "The verifier mentions Fropbox paths, but no deployed task prompt was supplied.",
            "Pass the deployed task JSON to compare prompt and verifier directly.",
            ["deployed_verifier"],
        )

    if fropbox_docs and local_docs:
        add(
            findings,
            "REPO_HAS_TWO_SURFACES",
            "info",
            "The repo now documents both local and deployed task surfaces",
            (
                f"Local path docs: {len(local_docs)}. Fropbox docs: {len(fropbox_docs)}. "
                "This is useful if clearly labeled, risky if copied into one prompt."
            ),
            "Keep the split explicit in README and handoff docs.",
            sorted(set(local_docs[:5] + fropbox_docs[:5])),
        )
    return findings


def check_verifier_prompt_alignment(
    deployed_task: SourceDoc | None,
    verifier: SourceDoc | None,
) -> list[Finding]:
    findings: list[Finding] = []
    if not deployed_task or not verifier:
        return findings

    prompt_refs = extract_file_refs(deployed_task.text)
    verifier_refs = extract_file_refs(verifier.text)
    verifier_assignments = parse_verifier_assignments(verifier.text)
    expected = set()
    if isinstance(verifier_assignments.get("EXPECTED_FILES"), list):
        expected = set(str(v) for v in verifier_assignments["EXPECTED_FILES"])
    if not expected:
        expected = {r for r in verifier_refs if r.endswith(".xlsx")}

    missing_from_prompt = sorted(ref for ref in expected if ref not in prompt_refs)
    if missing_from_prompt:
        add(
            findings,
            "VERIFIER_EXPECTS_FILE_NOT_IN_PROMPT",
            "review",
            "Verifier expects output files not plainly named in the prompt",
            "Verifier-only file names: " + ", ".join(missing_from_prompt),
            "Check whether the prompt names these indirectly or whether the verifier is stale.",
            ["deployed_task_prompt", "deployed_verifier"],
        )

    prompt_paths = extract_paths(deployed_task.text)
    verifier_paths = extract_paths(verifier.text)
    if any("/SouthPark Centre Underwriting/Outputs" in p for p in verifier_paths):
        if not any("/SouthPark Centre Underwriting/Outputs" in p for p in prompt_paths):
            add(
                findings,
                "OUTPUT_PATH_NOT_IN_PROMPT",
                "high",
                "Verifier checks an output folder not named in the prompt",
                "Verifier references `/SouthPark Centre Underwriting/Outputs`, but the prompt does not.",
                "Update the prompt or verifier so the output location is not hidden.",
                ["deployed_task_prompt", "deployed_verifier"],
            )
    return findings


def check_env_snapshot(
    deployed_task: SourceDoc | None,
    verifier: SourceDoc | None,
    env_counts: dict,
) -> list[Finding]:
    findings: list[Finding] = []
    if not env_counts:
        return findings
    prompt_text = deployed_task.text if deployed_task else ""
    verifier_text = verifier.text if verifier else ""
    message_text = str(env_counts.get("message_text", ""))

    if "/SouthPark Centre Underwriting/Outputs" in prompt_text and "/tmp/outputs" in message_text:
        add(
            findings,
            "SEED_EMAIL_OUTPUT_CONFLICT",
            "high",
            "Seed email gives an output path that conflicts with the deployed prompt",
            (
                "The deployed prompt tells the agent to upload to "
                "`/SouthPark Centre Underwriting/Outputs`, but an email body mentions `/tmp/outputs`."
            ),
            "Patch the seed email or prompt. The agent should not have to guess which instruction wins.",
            ["env_snapshot", "deployed_task_prompt"],
        )

    expects_source_room = "expected_source_files" in verifier_text or "source_files >= 64" in verifier_text
    drive_count = env_counts.get("drive_items")
    storage_count = env_counts.get("file_storage")
    if expects_source_room and drive_count == 0 and storage_count == 0:
        add(
            findings,
            "SOURCE_ROOM_NEEDS_PREFLIGHT",
            "review",
            "Verifier expects a source room, but the manager snapshot does not show drive files",
            (
                f"Snapshot counts: drive_items={drive_count}, file_storage={storage_count}. "
                "This may be a manager snapshot limitation, so treat it as a preflight item."
            ),
            "Run the verifier's own source-room check against a fresh seed or query the Fropbox DB directly.",
            ["env_snapshot", "deployed_verifier"],
        )

    if env_counts.get("attachments") and not drive_count:
        add(
            findings,
            "EMAIL_ATTACHMENT_ONLY_SURFACE",
            "info",
            "Snapshot looks email-attachment heavy",
            (
                f"Snapshot counts: messages={env_counts.get('messages')}, "
                f"attachments={env_counts.get('attachments')}, drive_items={drive_count}."
            ),
            "If the intended task needs a Fropbox source room, confirm it is visible through the task tools.",
            ["env_snapshot"],
        )
    return findings


def check_call_budget(repo: Path, docs: list[SourceDoc]) -> list[Finding]:
    findings: list[Finding] = []
    budget = repo / "tools" / "call_budget.py"
    if not budget.exists():
        return findings
    text = read_text(budget)
    if "~705" in text or "705" in text:
        if "cannot force the granular profile" not in text:
            add(
                findings,
                "CALL_BUDGET_OVERCLAIM",
                "review",
                "Call-budget script may overstate the forced floor",
                "The script mentions a granular 705-call profile without a caveat.",
                "Label this as a target or ceiling unless the interface forces item-by-item actions.",
                ["tools/call_budget.py"],
            )
        else:
            add(
                findings,
                "CALL_BUDGET_CAVEATED",
                "info",
                "Call-budget script separates coarse and granular profiles",
                "The script reports both 336 and 705 calls and says the granular path is not forced by interface alone.",
                "Keep this style for other batch-reviewed tasks.",
                ["tools/call_budget.py"],
            )
    return findings


def severity_counts(findings: list[Finding]) -> Counter:
    return Counter(f.severity for f in findings)


def write_markdown(
    out_path: Path,
    repo: Path,
    findings: list[Finding],
    inv: dict,
    env_counts: dict,
    docs: list[SourceDoc],
) -> None:
    counts = severity_counts(findings)
    lines: list[str] = []
    lines.append("# QA Loop Report")
    lines.append("")
    lines.append("Failure mode checked: prompt, environment, verifier, and repo docs disagree about files, paths, or runtime assumptions.")
    lines.append("")
    lines.append("This report flags issues for a human reviewer. It does not decide whether the task is good or bad.")
    lines.append("")
    lines.append("Recommended review loop:")
    lines.append("")
    lines.append("1. Read the high findings first and confirm them against source files or the live seed.")
    lines.append("2. Sample a few review findings and mark each as confirmed, expected, false positive, or needs more data.")
    lines.append("3. Only change the task after a person can explain the failure mode in plain language.")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("- Repo: `current repo`")
    lines.append(f"- Text files scanned: {len(docs)}")
    if inv.get("world_exists"):
        lines.append(f"- world_files count: {inv['world_total']}")
        lines.append(f"- world_files by suffix: `{json.dumps(inv['world_by_suffix'], sort_keys=True)}`")
    if env_counts:
        visible_counts = {k: v for k, v in env_counts.items() if k != "message_text"}
        lines.append(f"- Env snapshot counts: `{json.dumps(visible_counts, sort_keys=True)}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    for sev in ("high", "review", "info"):
        lines.append(f"- {sev}: {counts.get(sev, 0)}")
    lines.append("")
    if not findings:
        lines.append("No findings from these checks.")
    else:
        lines.append("## Findings")
        lines.append("")
        for idx, finding in enumerate(findings, start=1):
            lines.append(f"### {idx}. {finding.title}")
            lines.append("")
            lines.append(f"- Severity: `{finding.severity}`")
            lines.append(f"- Check: `{finding.check_id}`")
            if finding.sources:
                lines.append("- Sources: " + ", ".join(f"`{s}`" for s in finding.sources))
            lines.append(f"- Evidence: {finding.evidence}")
            lines.append(f"- Human review: {finding.human_action}")
            lines.append("")
        lines.append("## Reviewer Decision Worksheet")
        lines.append("")
        lines.append("| # | Check | Severity | Human decision | Owner | Next action |")
        lines.append("|---:|---|---|---|---|---|")
        for idx, finding in enumerate(findings, start=1):
            lines.append(
                f"| {idx} | `{finding.check_id}` | `{finding.severity}` |  |  |  |"
            )
        lines.append("")
    lines.append("## Manual Review Notes")
    lines.append("")
    lines.append("Fill this in after checking the report.")
    lines.append("")
    lines.append("- Tool was right about:")
    lines.append("- Tool was wrong or too broad about:")
    lines.append("- Final human decision:")
    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def write_csv(out_path: Path, findings: list[Finding]) -> None:
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "severity",
                "check_id",
                "title",
                "evidence",
                "human_action",
                "sources",
                "review_status",
                "reviewer_notes",
                "next_action",
            ],
        )
        writer.writeheader()
        for finding in findings:
            writer.writerow(
                {
                    "severity": finding.severity,
                    "check_id": finding.check_id,
                    "title": finding.title,
                    "evidence": finding.evidence,
                    "human_action": finding.human_action,
                    "sources": "; ".join(finding.sources),
                    "review_status": "",
                    "reviewer_notes": "",
                    "next_action": "",
                }
            )


def write_json(out_path: Path, findings: list[Finding], inv: dict, env_counts: dict) -> None:
    payload = {
        "summary": dict(severity_counts(findings)),
        "world": {
            "exists": inv.get("world_exists"),
            "total": inv.get("world_total"),
            "by_suffix": inv.get("world_by_suffix"),
        },
        "env_snapshot": {k: v for k, v in env_counts.items() if k != "message_text"},
        "findings": [
            {
                "severity": f.severity,
                "check_id": f.check_id,
                "title": f.title,
                "evidence": f.evidence,
                "human_action": f.human_action,
                "sources": f.sources,
            }
            for f in findings
        ],
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    docs = load_repo_docs(repo)
    deployed_task = load_task_json(Path(args.task_json).resolve() if args.task_json else None)
    verifier = load_verifier(Path(args.verifier).resolve() if args.verifier else None)
    all_docs = list(docs)
    if deployed_task:
        all_docs.append(deployed_task)
    if verifier:
        all_docs.append(verifier)

    inv = world_inventory(repo)
    env_counts = sqlite_counts(Path(args.env_snapshot).resolve() if args.env_snapshot else None)

    findings: list[Finding] = []
    findings.extend(check_world_counts(docs, inv))
    findings.extend(check_missing_file_refs(docs, inv))
    findings.extend(check_path_family_conflicts(docs, deployed_task, verifier))
    findings.extend(check_verifier_prompt_alignment(deployed_task, verifier))
    findings.extend(check_env_snapshot(deployed_task, verifier, env_counts))
    findings.extend(check_call_budget(repo, docs))

    report_name = args.report_name or "qa_report.md"
    if not report_name.endswith(".md"):
        report_name += ".md"
    md_path = out_dir / report_name
    csv_path = out_dir / report_name.replace(".md", ".csv")
    json_path = out_dir / report_name.replace(".md", ".json")

    write_markdown(md_path, repo, findings, inv, env_counts, docs)
    write_csv(csv_path, findings)
    write_json(json_path, findings, inv, env_counts)

    print(f"Wrote {md_path}")
    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    counts = severity_counts(findings)
    print(f"Findings: high={counts.get('high', 0)} review={counts.get('review', 0)} info={counts.get('info', 0)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Odyssey task consistency QA checks.")
    parser.add_argument("--repo", default=".", help="Repo root to scan.")
    parser.add_argument("--task-json", help="Optional deployed task JSON.")
    parser.add_argument("--verifier", help="Optional deployed verifier Python file.")
    parser.add_argument("--env-snapshot", help="Optional SQLite snapshot from a deployed environment.")
    parser.add_argument("--out-dir", default="tools/qa_loop/sample_reports", help="Output directory.")
    parser.add_argument("--report-name", default="qa_report.md", help="Markdown report filename.")
    return parser


def main() -> int:
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
