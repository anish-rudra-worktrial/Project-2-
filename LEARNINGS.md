# Learnings: designing odyssey tasks that are genuinely hard and honestly 1,000+ calls

Distilled from building and reviewing several tasks in this repo. The throughline: it is easy to
build a task that *looks* like a long, hard, 1,000-call workflow but that a capable agent finishes in
a few dozen calls, or that measures volume while requiring almost no judgment. These notes are how to
avoid that.

## The short version: what we keep learning across tasks

The recurring lessons from building every task so far, pulled from each task's changelog and written
for any reader.

1. **The answer key we are handed is usually wrong somewhere.** Almost every task arrived with
   mistakes in its own "correct answers": numbers that did not add up, the same customer listed under
   several different IDs, a summary slide that disagreed with the report it summarized, even invented
   figures that appeared in no source document. We now assume the delivered answers contain errors and
   verify them before trusting them.

2. **Build the practice data and the answer key from one shared source.** When they are written
   separately they drift apart and start to contradict each other. We write the facts down once and
   generate both from it, then run a check that confirms the answer key scores 100% on itself.

3. **The data has to actually support the answer.** If a task claims a result that the underlying
   numbers do not produce, it is broken. We make sure every answer can really be computed from what the
   agent is given, and when a source leaves a rule unstated we supply it openly and write down that we
   did.

4. **A long task is not the same as a hard task.** Piling on more files makes the work lengthy without
   making it smart. Real difficulty comes when the agent has to connect things: take something it
   learned in one place and use it somewhere else. One task could be passed by a careless agent until
   we made each step genuinely depend on the earlier ones.

5. **If the agent can see everything at once, it will shortcut the work.** When all the data sits in
   plain files, a capable agent reads it in a few moves and skips the real effort. Putting the data
   behind a system it has to query piece by piece makes it do the job properly.

6. **Some work should happen inside the software instead of being handed in as files.** Real jobs are
   done inside systems: you enroll a patient, you post a transaction. Having the agent act inside a
   simulated system and grading the system's final state is more realistic and cannot be faked with one
   big file dump.

7. **Be honest about how much work a task truly needs.** It is easy to claim a task takes a thousand
   steps when a clever shortcut finishes it in fifty. We check what a capable agent would actually do
   and report that number. A common trend: experts ask a model (Claude and others) to estimate the tool
   calls and it over-reports, answering "over a thousand" because it counts the slow,
   one-record-at-a-time way of doing the work. The
   same task done sensibly (read a whole file at once, write a whole spreadsheet at once) is often under
   a couple hundred. Always ask which way it counted, and whether anything in the task actually forces
   the slow way.

8. **The instructions strongly steer the agent.** When we listed every required file up front, the
   agent wrote one generic template and copied it everywhere. When we revealed the work step by step
   and told it never to reuse a template, it did each piece properly.

9. **Do not promise help the system cannot give.** One task told the agent to "resubmit until
   approved," but there was no approver, so the agent waited for a signal that never came. Instructions
   have to match what the environment can actually do.

10. **Judgment and writing can be graded too, in a separate pass.** For outputs with no single right
    answer, like a written summary, we score them with a separate reviewer step that never changes the
    objective score. That lets us include real judgment while keeping the main grading exact.

11. **Keep the realistic clutter, and make sure the clutter is correct.** Real work is full of
    distracting documents (old versions, other people's files), and including them tests whether the
    agent picks the right one. But a distractor with a wrong label can ruin the task, so the clutter
    itself must be accurate.

12. **Actually run an agent through the task.** A self-check proves the answer key is consistent, but
    running a real agent is what reveals the real problems: a clue with no way to find it, or a habit
    of cutting corners. Several of our most important fixes only appeared after a live run.

The rest of this document is the more technical version of these same lessons for task authors.

## 1. File-based tasks collapse under a capable agent

A task where the agent reads world spreadsheets, computes, and writes deliverable spreadsheets (graded
by cell comparison) does **not** genuinely require 1,000 tool calls when the agent has bash/pandas.
Deterministic derivations (threshold checks, formulas like Cockcroft-Gault, lookups) all vectorize, so
the agent loads every file in a handful of calls, computes over the whole frame, and writes each
deliverable in one call, often finishing in well under 100 calls.

- Example in this repo: `healthcare-clinical-research-trial-data-management` (v1) modeled ~5,497
  "granular" calls but collapses to under ~100 under pandas. Its README now says so.
- A `call_budget.py` that models a granular per-record catalog is a **false-green** if nothing
  enforces that catalog. The file task always allows the coarse path.

**Test before claiming 1,000+:** "Could a pandas/SQL-capable agent batch the graded work?" If yes, the
claim is inflated and the task needs a different shape.

## 2. Put the work in a stateful environment instead of a folder of files

The reliable way to make a long-horizon task real is to model the system of record (ERP, EHR, LMS) as
a **stateful environment** with granular per-record verbs and **no batch verb**. The agent acts
through the verbs; grading reads the environment's final state.

- Examples: `education-ib-biology-curriculum-design-iteration` (`classroom_server.py`, an LMS),
  `accounting-oracle-month-end-close` (`oracle_sim.py`, an ERP close),
  `v2-healthcare-clinical-research-trial-data-management` (`epic_sim.py`, an EHR research module).
- Why it holds: the per-record **write floor** is unavoidable because each governed transaction
  (enroll a subject, post a receipt, document an adverse event) is a separate action. Reads can be
  bulk/SQL and that is fine; the writes carry the volume.

## 3. Seed data into the environment per task, grade by reading final state

The environment contract that works: load a canonical starting state into the hosted env per task, let
the agent do the work through the env's actions, and grade by reading the env's final state. Pair it
with reconcile-by-construction (see section 7) so the seed and the answer key come from one source.

- Ship a **self-contained reference implementation** of the environment (a `*_sim.py` plus a
  `grade_state.py`) so the task fully specifies and self-tests today, and so the behavior the hosted
  env must reproduce is unambiguous. Mapping the reference verbs and state fields onto the live env is
  then a documented integration step (see the HANDOFF docs in the Oracle and Epic v2 tasks).
- Deliverables can be hybrid: most work as in-environment state, plus a few exported files graded by
  cell checks. Both are deterministic.

## 4. Per-record volume is interface-driven; the math usually batches

Be honest about *why* a task takes many actions. In the clinical and ERP tasks, almost every
calculation vectorizes: eligibility thresholds, CTCAE grade lookups, response rules, even the stateful
ibrutinib dose ladder (a `groupby(subject)` cumulative scan). What makes the work per-record is the
**write interface**, the system of record exposes governed per-action endpoints (each with
attribution, validation, audit trail, and workflow triggers) and typically no bulk-commit. That is a
faithful modeling choice that reflects how clinicians and accountants actually operate these systems,
and it is also a choice: a real EDC with a batch-import API would lower the floor.

**Implication for docs:** lead the call-profile claim with the genuine per-record write floor. Do not
present interface-driven volume as computation that cannot be batched. If the volume leans on
per-record *reads* (fetching each chart), say it is an upper estimate, because a warehouse-capable
agent could bulk-pull. See the v2 clinical README and `call_budget.py` for the honest framing.

## 5. Volume and difficulty are different goals; use the right lever for each

Two things often get conflated:

- **Long-horizon volume** (many steps): bought with the per-record environment interface. Real, but it
  is only volume.
- **Genuine difficulty** (intelligence): bought with judgment, search, and constrained synthesis.

The 1,000-call metric measures volume only. Buying volume by applying a formula N times gives a long
task with little difficulty. The most valuable tasks deliberately include both.

## 6. The deterministic-grading / formula trap, and the fix

Deterministic grading pushes toward answers that are rule-derivable, and rule-derivable answers
vectorize, which is exactly what makes them batchable. But determinism does not require a formula.
Gradable shapes that resist batching:

- **Hard-won answers:** a reconciliation that ties out only after a chain of interdependent
  adjustments; the tie-out is a clean check, the path is sequential reasoning.
- **Search / diagnosis:** find the root cause, the one inconsistency, the anomaly; the answer is
  verifiable, finding it is not a query.
- **Constrained synthesis:** build an artifact that satisfies many interacting constraints; validity
  is checkable, construction needs judgment.

**Adding subjective work the right way:** put genuine judgment outputs (a causality narrative, a
benefit-risk assessment, a monitor's rationale, query text) into a **separately-scored LLM-judge
layer** that never affects the deterministic total. The repo already has this pattern in
`airline-bi-operational-analytics/grade_llm.py`. Ungraded subjective outputs are decorative: an agent
optimizes to what is graded, so it will skip or phone in anything that does not count. Score them
separately so they are real, and keep the deterministic backbone clean.

## 7. Reconcile-by-construction

Use one single source of truth (a `facts.py`) to generate both the world/seed and the answer key with
the same rules, so the grader's `--self-test` is 100% by construction. When a submission ships
defective or non-derivable ground truth, flag the defects rather than silently fixing them, lock
canonical values with the author, and supply any rules the source defers (for example, organ-function
thresholds a protocol defers to the prescribing information) as world inputs that are documented.
Confirm the grader actually discriminates with a mutation check.

## 8. Honest call-profile reporting

Always report both the coarse and the granular profile and, above all, what a capable agent actually
does. If the task is file-based, state plainly that a pandas agent collapses it. If it is
interface-driven, lead with the write floor. Never let a granular model that the task does not enforce
stand in as the headline number.

### A trend: asking a model to estimate the tool-call count over-reports granular

A recurring trend when authors assess a task: experts are asking Claude and other models to estimate
a task's tool-call count, and the model over-reports. It returns the **granular** profile and says the
task is "over 1,000 tool calls," because it counts per-record reads, row-level and cell-level writes,
and a verify/repair loop. That is the number the task would take *if the tool catalog forced one call
per record*. Most file tasks do not force that. A **coarse**-capable agent (whole-file reads,
whole-deliverable writes, no loop) does the same work in a fraction of the calls, often under ~150. So
the model's "1,000+" is the granular ceiling rather than what a bash/SQL agent actually does.

When a model gives you a tool-call estimate, ask it which profile it counted, and then ask the real
question: **does anything in the task force the granular path?** If reads can be bulk and writes can be
whole-file, the honest number is the coarse one. Only an environment with per-record verbs and no batch
write (sections 2 and 4) makes the granular count the floor. Treat an unqualified "over 1,000" from a
model as the granular ceiling until you have confirmed the task enforces it.

## Author checklist

- [ ] Could a pandas/SQL agent batch the graded work in a few calls? If yes, change the shape.
- [ ] Is the volume from governed per-record writes (real) or from per-record reads (often
      contrivable and bulk-pullable)?
- [ ] Is the difficulty genuine (reasoning, search, synthesis, judgment) or a formula applied N times?
- [ ] Are subjective outputs scored in a separate LLM-judge layer rather than left ungraded?
- [ ] Reconcile-by-construction, with a grader that self-tests to 100% and passes a mutation check.
- [ ] Are the call-profile claims honest, leading with the genuine floor?
- [ ] For an in-environment task: is there a self-contained reference sim and a documented mapping to
      the hosted environment?

## Worked examples in this repo

- `accounting-oracle-month-end-close` and `v2-healthcare-clinical-research-trial-data-management`:
  in-environment, per-record verbs, state-read grading, self-contained reference sim.
- `education-ib-biology-curriculum-design-iteration`: the original in-environment (LMS) task and the
  precedent for shipping a reference server plus a state grader.
- `airline-bi-operational-analytics`: a deterministic core with a separately-scored LLM-judge layer.
- `healthcare-clinical-research-trial-data-management` (v1): a file task kept as the honest
  counter-example of the collapse described in section 1.
