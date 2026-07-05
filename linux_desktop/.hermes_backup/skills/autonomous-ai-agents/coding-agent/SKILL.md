---
name: coding-agent
description: Delegate coding work to Codex, Claude Code, or OpenCode as background workers; not simple edits or read-only code lookup. Installed from LobeHub openclaw-openclaw-coding-agent.
metadata:
  source: LobeHub openclaw-openclaw-coding-agent v1.0.6
  github: https://github.com/openclaw/openclaw/blob/main/skills/coding-agent/SKILL.md
  original_platform: OpenClaw
  adapted_for: Hermes Agent
---

# Coding Agent

Use for background feature builds, PR reviews, large refactors, and issue-to-PR loops. Do not use for simple edits, read-only lookup, ACP/thread-bound work, or any run inside active agent state directories.

## Hermes Adaptation

This skill came from OpenClaw. In Hermes:

- Prefer Hermes `delegate_task` for isolated reasoning-heavy coding/review work when a leaf subagent is enough.
- Use `terminal(background=true, notify_on_complete=true)` for long-running CLI agents or builds with a defined end.
- Use `process` to poll, read logs, submit input, or kill background terminal sessions.
- Use existing Hermes skills (`codex`, `claude-code`, `opencode`) when the user requests a specific coding agent.
- Do not use OpenClaw-specific notification commands such as `openclaw message send`; Hermes background jobs should use `notify_on_complete=true`, or return results in this chat/session when complete.

## When to Use

Use when:

- Building or creating new features/apps
- Reviewing PRs in a temporary checkout or worktree
- Refactoring large codebases
- Iterative coding that needs file exploration and test runs
- Issue-to-PR workflows that benefit from an autonomous coding CLI

Do **not** use when:

- The fix is a simple one-liner; edit directly
- The task is just reading code; use file/search tools
- The task needs user interaction that a background worker cannot ask for
- The task touches secrets or external services without explicit confirmation
- The work would run inside another agent's state/config directory

## Hard Rules

- Scope the worker to a specific repository/workdir.
- Check repo status before spawning: branch, remotes, dirty files, and user constraints.
- Do not spawn agents inside `~/.hermes/`, `~/.openclaw/`, `~/clawd`, or other agent state directories unless explicitly asked and scoped.
- For long-running bounded tasks, use `terminal(background=true, notify_on_complete=true)`.
- For long-lived watchers/servers, use `terminal(background=true)` and verify readiness separately.
- Monitor with `process`; do not kill slow workers without cause.
- If the user asked for a specific agent, use that agent.
- If a worker fails/hangs, report the failure and either respawn with a corrected prompt or ask; do not silently hand-code instead if the user explicitly requested delegation.
- Never push, force-push, publish tags, open PRs, use credentials, install global tools, or modify external services without explicit confirmation.

## Agent Launch Guidance

### Claude Code

Use non-PTY print mode when invoking Claude Code as a bounded worker:

```bash
claude --permission-mode bypassPermissions --print < "$PROMPT"
```

In Hermes, run with `terminal(background=true, notify_on_complete=true, workdir=/path/repo)` for long bounded jobs.

### Codex / OpenCode

Codex and OpenCode often need a PTY for interactive CLIs:

```bash
codex exec - < "$PROMPT"
opencode run < "$PROMPT"
```

In Hermes, use `pty=true` when required, and background tracking for long jobs.

## Prompt File Pattern

Write the worker prompt to a temp file first to avoid shell quoting bugs:

```bash
PROMPT=$(mktemp -t hermes-worker-prompt.XXXXXX)
cat >"$PROMPT" <<'EOF'
Task:
- Repository:
- Base branch:
- Goal:
- Constraints:
- Required verification:
- Report back with changed files, tests run, and any blockers.
EOF
printf 'prompt file: %s\n' "$PROMPT"
```

Then launch the selected agent from the repo workdir.

## Long Issue-to-PR Work

1. Create or identify a durable spec: issue URL, ticket, plan, or explicit user request.
2. Include repo, base branch, expected deliverable, tests, constraints, and confirmation boundaries.
3. Tell worker to branch, implement, test, review, and report exact results.
4. Return background `session_id` immediately if launched via terminal.
5. Monitor with `process`; verify claims before telling the user work is done.

## Scratch Worktree Pattern

For parallel PR review or risky experiments, use a separate clone/worktree rather than the main working tree:

```bash
git worktree add /tmp/repo-review-branch <branch>
```

Remove after completion only after confirming no needed files remain:

```bash
git worktree remove /tmp/repo-review-branch
```

## Process Actions in Hermes

- `process(action="list")`: running/recent sessions
- `process(action="poll", session_id="...")`: new output/status
- `process(action="log", session_id="...")`: full output window
- `process(action="submit", session_id="...", data="...")`: send input + Enter
- `process(action="write", session_id="...", data="...")`: raw stdin
- `process(action="kill", session_id="...")`: terminate

## Status to User

- Say what started, where, which agent, and the Hermes `session_id`.
- Update only on milestone, worker question, error, user action needed, or finish.
- If killed, say why.
- Verify worker self-reports by reading files, checking git diff/status, and running tests where possible.
