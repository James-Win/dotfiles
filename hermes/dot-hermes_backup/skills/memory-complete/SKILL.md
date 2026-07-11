---
name: memory-complete
description: Complete memory protocol for persistent facts, context recovery, searchable recall, hot session state, and memory maintenance. Adapted from LobeHub openclaw-skills-memory-complete for Hermes Agent.
metadata:
  source: LobeHub openclaw-skills-memory-complete v1.0.2
  github_listed: https://github.com/openclaw/skills/tree/main/skills/rosepuppy/memory-complete
  adapted_for: Hermes Agent
---

# Memory Complete

A complete memory protocol for agent work: decide what to save, keep hot context, recall past context by keyword, and periodically consolidate stale or duplicated memory.

## Hermes Adaptation

Hermes already has native durable memory (`memory` tool), session history search (`session_search`), skills, and Obsidian notes. Use those first:

- **Durable user/project facts** → Hermes `memory` tool.
- **Past conversation recall** → `session_search`.
- **Reusable procedures** → create/update a Hermes skill.
- **Project-local notes/docs** → Obsidian or project files.
- **Temporary task state** → `todo` or a project `SESSION-STATE.md`, not persistent memory.

This skill is useful as an additional **project-local memory pattern** when working in repositories that need file-based context (`MEMORY.md`, `SESSION-STATE.md`, `RECENT_CONTEXT.md`, and `memory/` logs).

## Memory Protocol

### Save write-ahead when the user provides durable facts

Save before continuing when the user states:

- A stable preference or correction
- A durable environment/project fact
- A convention that should apply in future sessions
- A recurring workflow rule
- A reusable lesson from a non-trivial failure

In Hermes, use the native `memory` tool for high-value durable facts. For project-local memories, use `scripts/capture.py` or append to `MEMORY.md`.

### Do not save stale task progress

Do **not** save:

- Completed task logs
- PR/issue numbers that will go stale
- Temporary TODOs
- One-off command output
- Secrets, tokens, credentials, private keys
- Sensitive personal data unless explicitly requested and appropriate

### Promote procedures to skills

If a lesson is procedural and reusable, promote it to a Hermes skill rather than storing it as prose memory.

## Project-Local File Layout

Recommended in a repository root:

```text
MEMORY.md              # curated project memory
SESSION-STATE.md       # hot current context, manually maintained
RECENT_CONTEXT.md      # short recent highlights
memory/                # append-only daily JSONL logs
  YYYY-MM-DD.jsonl
```

Use templates from `references/SESSION-STATE.md` and `references/RECENT_CONTEXT.md`.

## Hot Context: SESSION-STATE.md

Use `SESSION-STATE.md` for active context that must survive compaction or session reset:

- Current objective
- Decisions made
- Files touched
- Commands/tests run
- Blockers
- Next action

Keep it short and update it at natural breakpoints.

## Recent Context: RECENT_CONTEXT.md

Use `RECENT_CONTEXT.md` for compact, auto-updated or manually curated recent highlights:

- Last 5-10 important facts
- Current branch/task
- Recent blockers and resolutions
- Links to relevant memory IDs or files

## Capture / Recall / Consolidate

This skill includes simple scripts:

- `scripts/capture.py` — append facts to `memory/YYYY-MM-DD.jsonl`
- `scripts/recall.py` — keyword search memory logs with simple scoring
- `scripts/consolidate.py` — summarize counts and duplicate-looking entries

Examples:

```bash
python ~/.hermes/skills/memory-complete/scripts/capture.py --area project --priority medium --text "Project uses pnpm, not npm"
python ~/.hermes/skills/memory-complete/scripts/recall.py pnpm project
python ~/.hermes/skills/memory-complete/scripts/consolidate.py
```

By default, scripts operate in the current working directory and create/use `./memory/`.

## Recall Before Answering

When the user asks “what did we discuss about X?” or “where did we leave X?”:

1. Use the direct source first if they provide one (file, URL, repo, app, account, etc.).
2. Use Hermes `session_search` for conversation history.
3. Use project-local `scripts/recall.py` if the repository has `memory/` logs.
4. State uncertainty and source of recall.

## Consolidation

At natural breakpoints:

- Remove duplicates
- Promote durable rules to Hermes memory or `MEMORY.md`
- Promote procedures to skills
- Mark stale project-local notes as superseded
- Keep `SESSION-STATE.md` current and short

## Safety

- Never store secrets, tokens, private keys, passwords, or credential material.
- Avoid storing sensitive personal data.
- Keep memories declarative, concise, and source-aware.
- Ask before enabling automated capture hooks, heartbeat jobs, external sync, or modifying global agent configuration.

## Verification Checklist

- [ ] Durable user facts saved with native Hermes `memory` when appropriate
- [ ] Project-local facts captured to `memory/` only when useful to the repo
- [ ] Procedures promoted to skills instead of memory prose
- [ ] `SESSION-STATE.md` captures active hot context, not stale history
- [ ] No secrets or sensitive data stored
- [ ] Recall cites whether it came from Hermes session search, native memory, or project-local files
