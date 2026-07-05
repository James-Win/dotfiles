---
name: openclaw-obsidian
description: "Work with Obsidian vaults using the official obsidian CLI: read/search/create/edit notes, tasks, links, properties, plugins. Installed from LobeHub openclaw-openclaw-obsidian."
homepage: https://obsidian.md/cli
metadata:
  source: LobeHub openclaw-openclaw-obsidian v1.0.3
  github: https://github.com/openclaw/openclaw/blob/main/skills/obsidian/SKILL.md
  original_name: obsidian
  openclaw:
    emoji: "💎"
    requires:
      bins: ["obsidian"]
---

# Obsidian

Use the official `obsidian` CLI for Obsidian vault work. Vault files are plain Markdown, so direct file edits are still fine when safer/faster.

## Requirements

- Obsidian 1.12.7+ installed.
- Settings -> General -> Command line interface enabled.
- `obsidian` registered on PATH.
- Obsidian app running; the CLI connects to the running app.

Check:

```bash
obsidian version
obsidian help
```

macOS registration creates `/usr/local/bin/obsidian` pointing at the app-bundled CLI. Linux registration copies the binary to `~/.local/bin/obsidian`.

## Vault model

- Notes: `*.md`.
- Config: `.obsidian/`; avoid editing unless asked.
- Canvases: `*.canvas` JSON.
- Attachments: vault-configured folder.
- Multiple vaults are common; pass `vault=""` when ambiguous.

Obsidian desktop tracks vaults here:

- macOS: `~/Library/Application Support/obsidian/obsidian.json`
- Linux: `~/.config/obsidian/obsidian.json`
- Windows: `%APPDATA%/obsidian/obsidian.json`

This machine's known vault is `~/ObsidianVault/`.

## Command pattern

```bash
obsidian <command> [name=value] [flag]
obsidian vault="Notes" search query="meeting notes" format=json
```

Parameter values with spaces need quotes. Add `--copy` to copy output where useful.

## Common commands

Open/read:

```bash
obsidian open file=Recipe
obsidian open path="Inbox/Idea.md" newtab
obsidian read
obsidian read file=Recipe
```

Search:

```bash
obsidian search query="TODO" matches
obsidian search query="status::active" format=json
obsidian search:open query="project notes"
```

Create/modify:

```bash
obsidian create name="New Note"
obsidian create path="Inbox/Idea.md" content="# Idea"
obsidian append file=Note content="New line"
obsidian prepend file=Note content="After frontmatter"
```

Move/delete:

```bash
obsidian move file=Note to=Archive/
obsidian move path="Inbox/Old.md" to="Projects/New.md"
obsidian delete file=Note
```

Daily/tasks:

```bash
obsidian daily
obsidian daily:read
obsidian daily:append content="- [ ] Review inbox"
obsidian tasks all todo
obsidian task file=Note line=8 done
```

Properties/links:

```bash
obsidian tags all counts
obsidian property:read file=Note name=status
obsidian property:set file=Note name=status value=done
obsidian backlinks file=Note
obsidian unresolved verbose counts
```

Developer/debug:

```bash
obsidian plugin:reload my-plugin
obsidian dev:errors
obsidian dev:screenshot file=shot.png
obsidian eval "app.vault.getFiles().length"
```

## Notes

- `file=` uses Obsidian-style file resolution; `path=` is exact.
- Prefer CLI move/delete/property commands for Obsidian-aware updates.
- Prefer direct Markdown edits for bulk text changes after locating the vault path.
- Do not rely on third-party `obsidian-cli` unless user explicitly asks for it.
- Do not edit `.obsidian/` configuration unless the user explicitly asks.
- Do not enable plugins, install plugins, configure sync, use credentials, or interact with external services without explicit confirmation.

## Applied Workflow

When using this skill:
1. Discover the vault path from Obsidian config or known user context; do not hardcode if uncertain.
2. Use direct Markdown file operations for safe bulk note edits.
3. Use official `obsidian` CLI commands when the app is running and the CLI is registered, especially for Obsidian-aware moves, deletes, tasks, properties, links, and plugin/debug operations.
4. Verify note changes by reading the changed file or running a read/search command.
