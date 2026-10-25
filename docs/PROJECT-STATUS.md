# Tonight update: canonical project status and next plan

> This document is the short operational status for collaborators. The detailed system design remains in `docs/ARCHITECTURE-DESIGN.md`.

## Project status

`annotation-agent` is an early-stage educational question annotation agent. The repository currently contains the project skeleton, final architecture documents, Python 3.12/uv setup, basic dependencies, a smoke test, CI, and the first contract models and deterministic validators with unit tests.

It is **not yet** an OCR system, a production browser robot, or a production auto-submission service.

## Canonical architecture

The system is organized as three logical planes:

1. **Annotation intelligence**: page parsing, question structure, answer matching, annotation rules, and `AnnotationResult`.
2. **Platform execution**: `ActionPlan`, execution guards, browser adapter, save observation, and `ExecutionReceipt`.
3. **Control and audit**: FastAPI, LangGraph, checkpoints, action logs, review queue, package completion, and metrics.

The safety boundary is:

```text
model candidates
→ Pydantic contract
→ deterministic/business validation
→ AnnotationResult
→ ActionPlan
→ execution guard
→ browser/platform adapter
→ ExecutionReceipt
```

The browser must not infer business rules or freely act from raw model output.

## Current implementation state

### Present

- Python 3.12 pinned through uv;
- FastAPI, LangGraph, Pydantic v2, pytest, httpx, python-dotenv;
- repository structure under `app/`;
- `.env.example` and data-safety `.gitignore`;
- GitHub Actions for dependency installation, tests, and syntax checks;
- final architecture explanation and flow diagrams;
- mobile-friendly Word design document;
- one dependency smoke test;
- first contract models in `app/contracts/models.py`: `Page` (positive finite size), `BoundingBox` (positive area, finite non-negative coordinates), `QuestionNode`, `AnswerBox`, `Issue` (code, severity, message, refs), `AnnotationResult`, and enums for subject, question type, line type, answer mode, closedness, severity, and result status;
- `AnnotationResult` enforces that `status` matches its issues: any blocking issue requires `needs_review`, so a result never passes silently;
- first deterministic validators in `app/rules/validators.py`; each returns the full list of issues instead of stopping at the first, and `validate_annotation()` runs them all and builds an `AnnotationResult`. Stable error codes:
  - page bounds (checked against each page's own size): `DUPLICATE_PAGE_ID`, `PAGE_NOT_FOUND`, `COORDINATE_OUT_OF_BOUNDS`;
  - question hierarchy: `DUPLICATE_QUESTION_ID`, `PARENT_NOT_FOUND`, `PARENT_PAGE_MISMATCH`, `CHILD_OUTSIDE_PARENT`, `PARENT_CYCLE`;
  - answer bindings: `QUESTION_NOT_FOUND`, `DUPLICATE_ANSWER_ID`;
- unit tests for the contracts and validators.

### Not yet implemented

- remaining contracts: `TaskPackage`, question relations (cross-column, cross-page, independent answers);
- `RuleTrace`, `ActionPlan`, `ExecutionReceipt`, `ReviewRecord`;
- warning-level validators (the severity field exists, but every current check is blocking);
- math rule files (`rules/math.yaml`) and rule cases under `tests/rule_cases/`;
- redacted gold data;
- OCR/PP-Structure adapter;
- multimodal model adapter;
- annotation preview renderer;
- FakeExecutor;
- platform adapter or browser automation;
- production storage, queue, and automatic submission.

## Scope control

The first vertical slice is intentionally narrow:

- mathematics only;
- single-page input first;
- question types: choice, fill-in, true/false, mental arithmetic, calculation, word problem, matching/connection;
- question boxes, answer boxes, basic parent-child relationships;
- deterministic coordinate and relationship validation;
- offline `AnnotationResult` output;
- visual preview and fixed evaluation cases.

Do not expand to all subjects, listening, handwriting, complex drawing, QR extraction, or production submission before the narrow slice is measured.

## Next development plan

### Step 1 — Freeze the contract (in progress: page, box, question, answer, issue, and result models done; relations and answer sources pending)

Define Pydantic models and enums before adding model calls:

- coordinate system and bounding-box rules;
- question and answer IDs;
- relation types;
- line types;
- answer source types;
- closedness types;
- review reasons;
- result status.

Deliverable: contract models plus invalid/valid fixture tests.

### Step 2 — Build deterministic validators (in progress: bounds, hierarchy, and answer-binding checks done; issues are collected, not fail-fast)

Implement checks for:

- page bounds and coordinate ordering;
- parent box contains child boxes;
- question IDs and answer IDs match;
- no duplicate answer links;
- relation endpoints exist;
- invalid combinations of answer source, answer box, and line type;
- no silent success when warnings are blocking.

Deliverable: rule cases and readable error codes.

### Step 3 — Create the first math rule pack

Start with the smallest set of rules needed for the first fixture set. Keep rules explicit and versioned under `rules/`; do not hide them only in prompts.

Deliverable: `rules/math.yaml` and rule trace fixtures.

### Step 4 — Create a tiny gold dataset

Before OCR or a model, prepare a small, redacted set:

- 5–10 pages initially;
- corresponding answer pages where applicable;
- hand-confirmed question boxes, answer boxes, relations, types, line types, answers, and closedness;
- clear sample IDs and provenance.

Expand only after the schema and annotation format stop changing.

### Step 5 — Add a preview renderer

Render the structured result over the original page. The preview must show question boxes, answer boxes, relations, warnings, and confidence. This is the fastest way to catch coordinate errors.

### Step 6 — Add OCR, then model understanding

The order is deliberate:

```text
contracts → validators → fixtures → preview → OCR → multimodal model
```

OCR produces text blocks and coordinates. The model proposes structure. Neither bypasses the validators.

### Step 7 — Add LangGraph only around proven nodes

Use LangGraph for state, branching, timeout, checkpoint, human review, and one bounded correction. Do not put all domain logic into graph nodes or prompts.

### Step 8 — Add ActionPlan and FakeExecutor

Convert a validated `AnnotationResult` into a declarative `ActionPlan`. Run it against a fake executor first and produce an `ExecutionReceipt`. Only after this is stable should platform automation be investigated.

## Change control

Before implementing a new feature, answer:

1. Is this a business rule, model capability, or platform capability?
2. Can it be deterministic? If yes, keep it in code/rules.
3. What is the smallest fixture that proves it?
4. Which existing contract or state does it change?
5. What is the failure and human-review path?
6. Can it be tested offline without the platform?

If these answers are unclear, do not start implementation yet; clarify the contract first.

## Verification gates

Every change must pass:

```bash
uv run pytest
uv run python -m compileall app tests
git diff --check
```

Every model or rule change must also include a fixture or evaluation update. Every platform change must be tested against a fake or test environment before production use.

## Security and data policy

Do not commit:

- API keys, passwords, or login tokens;
- real question or answer images;
- user data;
- internal task IDs;
- unredacted platform details;
- sensitive model responses.

Keep secrets in local `.env`; keep real samples under ignored local directories; commit only redacted fixtures and gold data.

## Current decision

The project is not over-designed if the target is an end-to-end, auditable annotation workflow. It would be over-engineered to implement every plane at once. Therefore the architecture stays broad, while implementation proceeds as a narrow vertical slice:

```text
math single-page fixture
→ validated structured result
→ preview
→ evaluation
→ bounded execution simulation
```
