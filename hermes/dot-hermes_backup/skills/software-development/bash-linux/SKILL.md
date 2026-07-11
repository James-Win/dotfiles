---
name: bash-linux
description: Bash/Linux terminal patterns. Critical commands, piping, error handling, scripting. Use when working on macOS or Linux systems.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
metadata:
  source: LobeHub davila7-claude-code-templates-bash-linux v1.0.1
  github: https://github.com/davila7/claude-code-templates/blob/main/cli-tool/components/skills/development/bash-linux/SKILL.md
---

# Bash Linux Patterns

Essential patterns for Bash on Linux/macOS.

## Hermes Tooling Note

This skill is a Bash reference. In Hermes, prefer built-in file tools when available:

- Use `read_file` instead of `cat`, `head`, or `tail` for file reads.
- Use `search_files` instead of `grep`, `rg`, `find`, or `ls` for search/listing.
- Use `patch` instead of `sed`/`awk` for file edits.
- Use `terminal` for builds, package managers, process/service commands, network checks, scripts, and shell-specific behavior.
- Do not run shell background wrappers like trailing `&`; use `terminal(background=true)` for servers/watchers.

## 1. Operator Syntax

### Chaining Commands

| Operator | Meaning | Example |
|----------|---------|---------|
| `;` | Run sequentially | `cmd1; cmd2` |
| `&&` | Run if previous succeeded | `npm install && npm run dev` |
| `||` | Run if previous failed | `npm test || echo "Tests failed"` |
| `|` | Pipe output | `ls | grep ".js"` |

## 2. File Operations

### Essential Commands

| Task | Command |
|------|---------|
| List all | `ls -la` |
| Find files | `find . -name "*.js" -type f` |
| File content | `cat file.txt` |
| First N lines | `head -n 20 file.txt` |
| Last N lines | `tail -n 20 file.txt` |
| Follow log | `tail -f log.txt` |
| Search in files | `grep -r "pattern" --include="*.js"` |
| File size | `du -sh *` |
| Disk usage | `df -h` |

## 3. Process Management

| Task | Command |
|------|---------|
| List processes | `ps aux` |
| Find by name | `ps aux | grep node` |
| Kill by PID | `kill -9 <PID>` |
| Find port user | `lsof -i :3000` |
| Kill port | `kill -9 $(lsof -t -i :3000)` |
| Background | `npm run dev &` |
| Jobs | `jobs -l` |
| Bring to front | `fg %1` |

## 4. Text Processing

### Core Tools

| Tool | Purpose | Example |
|------|---------|---------|
| `grep` | Search | `grep -rn "TODO" src/` |
| `sed` | Replace | `sed -i 's/old/new/g' file.txt` |
| `awk` | Extract columns | `awk '{print $1}' file.txt` |
| `cut` | Cut fields | `cut -d',' -f1 data.csv` |
| `sort` | Sort lines | `sort -u file.txt` |
| `uniq` | Unique lines | `sort file.txt | uniq -c` |
| `wc` | Count | `wc -l file.txt` |

## 5. Environment Variables

| Task | Command |
|------|---------|
| View all | `env` or `printenv` |
| View one | `echo $PATH` |
| Set temporary | `export VAR="value"` |
| Set in script | `VAR="value" command` |
| Add to PATH | `export PATH="$PATH:/new/path"` |

## 6. Network

| Task | Command |
|------|---------|
| Download | `curl -O https://example.com/file` |
| API request | `curl -X GET https://api.example.com` |
| POST JSON | `curl -X POST -H "Content-Type: application/json" -d '{"key":"value"}' URL` |
| Check port | `nc -zv localhost 3000` |
| Network info | `ifconfig` or `ip addr` |

## 7. Script Template

```bash
#!/bin/bash
set -euo pipefail # Exit on error, undefined var, pipe fail

# Colors (optional)
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Functions
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# Main
main() {
  log_info "Starting..."
  # Your logic here
  log_info "Done!"
}

main "$@"
```

## 8. Common Patterns

### Check if command exists

```bash
if command -v node &> /dev/null; then
  echo "Node is installed"
fi
```

### Default variable value

```bash
NAME=${1:-"default_value"}
```

### Read file line by line

```bash
while IFS= read -r line; do
  echo "$line"
done < file.txt
```

### Loop over files

```bash
for file in *.js; do
  echo "Processing $file"
done
```

### Create file with block of text (Heredoc)
Instead of using `nano` or another interactive editor which hangs the agent or terminal, use `cat` with a heredoc (or use Hermes `write_file`).

```bash
cat << 'EOF' > /etc/systemd/system/myservice.service
[Unit]
Description=My Service
After=network.target

[Service]
ExecStart=/usr/bin/myservice
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
```

## 9. Differences from PowerShell

| Task | PowerShell | Bash |
|------|------------|------|
| List files | `Get-ChildItem` | `ls -la` |
| Find files | `Get-ChildItem -Recurse` | `find . -type f` |
| Environment | `$env:VAR` | `$VAR` |
| String concat | `"$a$b"` | `"$a$b"` (same) |
| Null check | `if ($x)` | `if [ -n "$x" ]` |
| Pipeline | Object-based | Text-based |

## 10. Error Handling

### Set options

```bash
set -e # Exit on error
set -u # Exit on undefined variable
set -o pipefail # Exit on pipe failure
set -x # Debug: print commands
```

### Trap for cleanup

```bash
cleanup() {
  echo "Cleaning up..."
  rm -f /tmp/tempfile
}
trap cleanup EXIT
```

## Applied Workflow

When using this skill in Hermes:
1. Decide whether the job truly needs shell execution; use native Hermes file tools for file read/search/edit tasks.
2. For shell scripts, include `set -euo pipefail`, quote variables, and add `trap` cleanup for temporary files.
3. For commands with side effects, explain the scope and verify with a follow-up command.
4. Ask for confirmation before credential use, external service setup, destructive deletes, package installs/removals, reboots, service disables, or irreversible changes.

> **Remember:** Bash is text-based. Use `&&` for success chains, `set -e` for safety, and quote your variables!

## 11. Systemd Wrappers for Network Tools
When writing systemd wrappers for network tools, mind the bind interface (`-B 0.0.0.0` vs default `127.0.0.1`) and the underlying protocol mode (e.g. `glances -w` REST API vs `glances -s` XML-RPC CLI). See `references/systemd-network-services.md` for pitfalls.
