# Catalog and Duplicate Handling for LobeHub Imports

Use this when a user repeatedly asks to import marketplace skills or asks what has been learned.

## Duplicate import rule

Before writing a new skill, compare the requested LobeHub identifier and likely local skill name against existing user-local skills.

If the skill already exists:

1. Open it with `skill_view(name)`.
2. Confirm the installed path and source metadata.
3. Do not reinstall or overwrite unless the user asked to update, re-import, or the installed metadata is clearly stale.
4. If the user asked to install the same URL again, report: already installed, loaded/opened, supporting files present, and any provenance limitation.

## Catalog update rule

When the user maintains an Obsidian or notes catalog of imported skills, update it after each successful new import. Include:

- local skill name
- local path
- LobeHub identifier and version
- upstream repository or provenance limitation
- installed supporting files
- Hermes adaptation notes
- safety/confirmation boundary

If a later import was already installed, do not duplicate the catalog entry; only patch it if new metadata or support files were added.

## Import summary format

Use a concise final summary:

```text
Installed/opened:
- Skill: `<name>`
- Path: `<path>`
- Source: LobeHub `<identifier>` v<version>
- Upstream: <url or provenance note>

I did not run marketplace registration/CLI because it involves external registration/credentials.
Key rules: ...
```

## Naming rule

Prefer class-level local names. If the upstream name collides with a bundled skill, add a source prefix (for example `openclaw-obsidian`). Do not create one-off names tied to a single session URL when a class-level umbrella already exists.
