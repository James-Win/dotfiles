# Self-Improving Agent — Provenance Notes

## Source
- LobeHub listing: https://lobehub.com/skills/openclaw-skills-self-improving-agent-1-0-0
- Upstream project: https://github.com/openclaw/skills
- Archived path pattern: `skills/<author>/self-improving-agent-1-0-0/`
- Exact GitHub path from LobeHub (`dc-acronym/self-improving-agent-1-0-0`) returned 404 in July 2026; the LobeHub page preserved the full `SKILL.md` text.

## LobeHub → Hermes import pattern
This skill was obtained without `hermes skills install`:
1. Extract the full skill body from the LobeHub listing page.
2. Validate format compatibility with Hermes SKILL.md conventions (YAML frontmatter, markdown body).
3. Write to `~/.hermes/skills/<name>/SKILL.md`.
4. Add any referenced templates/assets under `assets/`, `references/`, `templates/`, or `scripts/`.
5. Reload Hermes or restart session to pick up the new skill.

Caveat: Skill ID formats differ between LobeHub/OpenClaw and Hermes. If a LobeHub skill name collides with a bundled skill, namespace it under a Hermes-compatible name before writing.
