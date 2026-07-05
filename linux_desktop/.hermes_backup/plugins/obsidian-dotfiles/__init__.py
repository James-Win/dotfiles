"""Hermes plugin: safe Obsidian + GNU Stow dotfile migration.

Install location:
    ~/.hermes/plugins/obsidian-dotfiles/

Files:
    plugin.yaml
    __init__.py

Safety model:
    - Dry-run by default.
    - Real changes require dry_run=False AND confirm=True.
    - Secret-bearing paths are blocked.
    - Unknown paths are refused unless allow_unlisted=True.
    - Originals are backed up and moved aside before Stow.
    - Stow symlinks are verified before success is returned.
    - Handler returns a JSON string, as Hermes tools expect.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


# Paths that should almost never be migrated into Obsidian/git by an agent.
# They commonly contain private keys, tokens, cloud credentials, browser profiles, or secrets.
BLOCKED_PREFIXES = {
    (".ssh",),
    (".gnupg",),
    (".aws",),
    (".azure",),
    (".kube",),
    (".docker",),
    (".pki",),
    (".mozilla",),
    (".config", "Bitwarden"),
    (".config", "Proton Pass"),
    (".config", "1Password"),
    (".git-credentials",),
    (".netrc",),
    (".npmrc",),
    (".pypirc",),
    (".env",),
}

# A conservative allowlist is safer for an agent than allowing arbitrary dotfiles.
# The user can override this with allow_unlisted=True, but blocked paths still stay blocked.
SAFE_ALLOWLIST = {
    (".bashrc",),
    (".bash_profile",),
    (".zshrc",),
    (".profile",),
    (".gitconfig",),
    (".tmux.conf",),
    (".vimrc",),
    (".config", "i3"),
    (".config", "polybar"),
    (".config", "rofi"),
    (".config", "alacritty"),
    (".config", "kitty"),
    (".config", "nvim"),
    (".config", "picom"),
    (".config", "dunst"),
    (".config", "fontconfig"),
}


def _validate_package_name(package_name: str) -> str:
    """Require a simple one-folder Stow package name."""
    name = str(package_name).strip()

    if not name:
        raise ValueError("package_name cannot be empty.")

    if name in {".", ".."}:
        raise ValueError("package_name cannot be '.' or '..'.")

    if "/" in name or "\\" in name:
        raise ValueError("package_name must be a single folder name, not a path.")

    return name


def _path_has_prefix(
    rel_path: Path,
    prefixes: set[tuple[str, ...]],
    *,
    case_sensitive: bool,
) -> bool:
    """Check whether a relative path starts with one of the configured prefixes."""
    parts = rel_path.parts

    if not case_sensitive:
        parts = tuple(part.lower() for part in parts)
        prefixes = {tuple(part.lower() for part in prefix) for prefix in prefixes}

    for prefix in prefixes:
        if parts[: len(prefix)] == prefix:
            return True

    return False


def _is_blocked(rel_path: Path) -> bool:
    """Blocked paths win over allowed paths."""
    return _path_has_prefix(rel_path, BLOCKED_PREFIXES, case_sensitive=False)


def _is_allowed(rel_path: Path) -> bool:
    """Only known-safe desktop config paths are allowed by default."""
    return _path_has_prefix(rel_path, SAFE_ALLOWLIST, case_sensitive=True)


def _copy_any(src: Path, dst: Path) -> None:
    """Copy a file or directory while preserving metadata."""
    dst.parent.mkdir(parents=True, exist_ok=True)

    if src.is_dir():
        # symlinks=True prevents copying the contents of symlink targets inside a directory.
        shutil.copytree(src, dst, symlinks=True)
    else:
        shutil.copy2(src, dst)


def _run_checked(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a command and preserve stdout/stderr for useful error reporting."""
    result = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            cmd,
            output=result.stdout,
            stderr=result.stderr,
        )

    return result


def _format_command_error(error: subprocess.CalledProcessError) -> str:
    """Turn subprocess errors into logs that are useful to a human."""
    stdout = error.output.strip() if error.output else ""
    stderr = error.stderr.strip() if error.stderr else ""

    message = f"Command failed: {' '.join(map(str, error.cmd))}"

    if stdout:
        message += f"\nstdout:\n{stdout}"

    if stderr:
        message += f"\nstderr:\n{stderr}"

    return message


def sync_dotfiles_to_obsidian_impl(
    vault_path: str,
    dotfile_paths: list[str],
    package_name: str = "linux_desktop",
    dry_run: bool = True,
    confirm: bool = False,
    commit_to_git: bool = True,
    allow_unlisted: bool = False,
    backup_root: str = "~/.dotfiles_migration_backup",
) -> dict[str, Any]:
    """Safely migrate selected dotfiles into an Obsidian vault folder using GNU Stow."""
    logs: list[str] = []
    errors: list[str] = []
    plan: list[dict[str, str]] = []

    try:
        package_name = _validate_package_name(package_name)
    except ValueError as exc:
        return {"status": "error", "errors": [str(exc)], "logs": logs}

    home = Path.home().resolve()
    vault = Path(vault_path).expanduser().resolve(strict=False)
    package_dir = vault / package_name
    backup_base = Path(backup_root).expanduser().resolve(strict=False)

    if not isinstance(dotfile_paths, list) or not dotfile_paths:
        return {
            "status": "error",
            "errors": ["dotfile_paths must be a non-empty list of strings."],
            "logs": logs,
        }

    # Dry-run can report missing tools as warnings.
    # A real run refuses to continue without required tools.
    stow_path = shutil.which("stow")
    git_path = shutil.which("git")

    if not stow_path:
        message = "GNU Stow was not found in PATH."
        if dry_run:
            logs.append(f"Warning: {message}")
        else:
            errors.append(message)

    if commit_to_git and not git_path:
        message = "git was not found in PATH, but commit_to_git=True."
        if dry_run:
            logs.append(f"Warning: {message}")
        else:
            errors.append(message)

    for path_str in dotfile_paths:
        if not isinstance(path_str, str) or not path_str.strip():
            errors.append(f"Invalid dotfile path: {path_str!r}")
            continue

        raw_path = Path(path_str).expanduser()

        # Treat relative paths like ".bashrc" as relative to the user's home.
        src = raw_path if raw_path.is_absolute() else home / raw_path

        # Important: check symlink status before calling resolve().
        # resolve() follows symlinks, which would hide the fact that the original
        # source was already a symlink.
        if src.is_symlink():
            logs.append(f"Skipped {src}: already a symlink.")
            continue

        if not src.exists():
            logs.append(f"Skipped {src}: does not exist.")
            continue

        src_abs = src.resolve(strict=False)

        if src_abs == home:
            errors.append("Refusing to migrate the entire home directory.")
            continue

        try:
            rel_path = src_abs.relative_to(home)
        except ValueError:
            errors.append(f"Refusing {src_abs}: path is outside the home directory.")
            continue

        # Do not let the tool migrate files that are already inside the vault.
        try:
            src_abs.relative_to(vault)
            errors.append(f"Refusing {src_abs}: source is already inside the vault.")
            continue
        except ValueError:
            pass

        if _is_blocked(rel_path):
            errors.append(f"Refusing {src_abs}: path is blocked because it may contain secrets.")
            continue

        if not allow_unlisted and not _is_allowed(rel_path):
            errors.append(
                f"Refusing {src_abs}: path is not in SAFE_ALLOWLIST. "
                "Use allow_unlisted=True only after human review."
            )
            continue

        target = package_dir / rel_path

        # A migration tool should not silently merge or overwrite existing package files.
        # Existing target content may represent the user's canonical dotfile version.
        if target.exists() or target.is_symlink():
            errors.append(
                f"Refusing {src_abs}: target already exists at {target}. "
                "Resolve this conflict manually before migrating."
            )
            continue

        plan.append(
            {
                "source": str(src_abs),
                "relative_path": str(rel_path),
                "stow_target": str(target),
                "future_symlink": str(home / rel_path),
            }
        )

    if errors:
        return {
            "status": "error",
            "errors": errors,
            "logs": logs,
            "planned_actions": plan,
        }

    if not plan:
        return {
            "status": "no_changes",
            "logs": logs,
            "planned_actions": plan,
        }

    if dry_run:
        logs.append("Dry run only. No files were changed.")
        logs.append("To execute, call again with dry_run=False and confirm=True.")

        if commit_to_git:
            logs.append("A successful real run would initialize git if needed and commit the package.")

        return {
            "status": "dry_run",
            "logs": logs,
            "planned_actions": plan,
        }

    if not confirm:
        return {
            "status": "refused",
            "errors": [
                "Refusing to modify files without confirm=True. "
                "Run a dry run first, review planned_actions, then call with dry_run=False and confirm=True."
            ],
            "logs": logs,
            "planned_actions": plan,
        }

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = backup_base / timestamp
    moved_originals: list[tuple[Path, Path]] = []

    try:
        vault.mkdir(parents=True, exist_ok=True)
        package_dir.mkdir(parents=True, exist_ok=True)
        backup_dir.mkdir(parents=True, exist_ok=True)

        logs.append(f"Using vault: {vault}")
        logs.append(f"Using Stow package: {package_dir}")
        logs.append(f"Using backup directory: {backup_dir}")

        for item in plan:
            src = Path(item["source"])
            rel_path = Path(item["relative_path"])
            target = Path(item["stow_target"])

            backup_copy = backup_dir / "original_copies" / rel_path
            moved_original = backup_dir / "moved_originals" / rel_path

            # Step 1: copy original to a timestamped backup.
            # This gives the user a recovery copy independent of the Obsidian vault.
            _copy_any(src, backup_copy)
            logs.append(f"Backed up {src} to {backup_copy}")

            # Step 2: copy original into the Stow package.
            # The original still exists at this point.
            _copy_any(src, target)
            logs.append(f"Copied {src} into Stow package at {target}")

            # Step 3: move the live original aside.
            # We do not delete it. If Stow fails, rollback can move it back.
            moved_original.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(moved_original))
            moved_originals.append((src, moved_original))
            logs.append(f"Moved live original {src} to {moved_original}")

        # Step 4: apply Stow.
        _run_checked(
            [
                "stow",
                "--target",
                str(home),
                "--dir",
                str(vault),
                package_name,
            ]
        )
        logs.append("Stow applied successfully.")

        # Step 5: verify that each original path is now a symlink to the package copy.
        # This catches cases where Stow exited successfully but did not create what we expected.
        for item in plan:
            future_symlink = Path(item["future_symlink"])
            expected_target = Path(item["stow_target"]).resolve(strict=False)

            if not future_symlink.is_symlink():
                raise RuntimeError(f"Verification failed: {future_symlink} is not a symlink.")

            actual_target = future_symlink.resolve(strict=False)

            if actual_target != expected_target:
                raise RuntimeError(
                    f"Verification failed: {future_symlink} points to {actual_target}, "
                    f"expected {expected_target}."
                )

            logs.append(f"Verified symlink: {future_symlink} -> {expected_target}")

        # Step 6: git initialization and commit happen only after migration is verified.
        if commit_to_git:
            try:
                if not (vault / ".git").exists():
                    _run_checked(["git", "-C", str(vault), "init"])
                    logs.append("Initialized local git repository.")

                _run_checked(["git", "-C", str(vault), "add", package_name])

                status = _run_checked(["git", "-C", str(vault), "status", "--porcelain"]).stdout.strip()

                if status:
                    commit_message = f"Migrate dotfiles into Stow package: {package_name}"
                    _run_checked(["git", "-C", str(vault), "commit", "-m", commit_message])
                    logs.append(f"Committed changes to git: {commit_message}")
                else:
                    logs.append("No git changes to commit.")
            except Exception as git_exc:
                if isinstance(git_exc, subprocess.CalledProcessError):
                    logs.append(_format_command_error(git_exc))
                else:
                    logs.append(f"Git error: {git_exc}")
                logs.append("Warning: Git bookkeeping failed, but file migration succeeded. Skipping rollback.")

        return {
            "status": "success",
            "logs": logs,
            "backup_dir": str(backup_dir),
            "planned_actions": plan,
        }

    except subprocess.CalledProcessError as exc:
        logs.append(_format_command_error(exc))
        logs.append("Attempting rollback because a command failed.")

    except Exception as exc:
        logs.append(f"Error: {exc}")
        logs.append("Attempting rollback because migration failed.")

    # Rollback path.
    # The goal is to restore live originals if Stow or verification failed.
    try:
        if stow_path:
            try:
                _run_checked(
                    [
                        "stow",
                        "--delete",
                        "--target",
                        str(home),
                        "--dir",
                        str(vault),
                        package_name,
                    ]
                )
                logs.append("Rollback: removed Stow symlinks.")
            except Exception as exc:
                logs.append(f"Rollback warning: could not remove Stow symlinks cleanly: {exc}")

        for original_path, moved_path in reversed(moved_originals):
            if original_path.is_symlink():
                original_path.unlink()
                logs.append(f"Rollback: removed symlink {original_path}")

            if original_path.exists():
                logs.append(
                    f"Rollback warning: {original_path} already exists. "
                    f"Leaving moved original at {moved_path}"
                )
                continue

            if moved_path.exists():
                original_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(moved_path), str(original_path))
                logs.append(f"Rollback: restored {original_path} from {moved_path}")

        logs.append(
            "Rollback completed as far as possible. "
            "Copied package files may remain in the vault for manual review."
        )

    except Exception as rollback_exc:
        logs.append(f"Rollback failed: {rollback_exc}")

    return {
        "status": "error",
        "logs": logs,
        "backup_dir": str(backup_dir),
        "planned_actions": plan,
    }


SYNC_DOTFILES_SCHEMA = {
    "name": "sync_dotfiles_to_obsidian",
    "description": (
        "Safely migrate selected home-directory dotfiles into an Obsidian-backed "
        "GNU Stow package. Defaults to dry-run mode. Real changes require "
        "dry_run=false and confirm=true."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "vault_path": {
                "type": "string",
                "description": (
                    "Path to the Stow root, usually inside or near an Obsidian vault. "
                    "Example: ~/ObsidianVault/Sources/dotfiles"
                ),
            },
            "dotfile_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Existing home-directory dotfiles/config directories to migrate. "
                    "Example: ['~/.config/i3', '~/.config/polybar']"
                ),
            },
            "package_name": {
                "type": "string",
                "description": "Name of the Stow package folder inside vault_path.",
                "default": "linux_desktop",
            },
            "dry_run": {
                "type": "boolean",
                "description": "If true, only report the migration plan and make no changes.",
                "default": True,
            },
            "confirm": {
                "type": "boolean",
                "description": (
                    "Must be true together with dry_run=false before real file changes happen."
                ),
                "default": False,
            },
            "commit_to_git": {
                "type": "boolean",
                "description": "If true, initialize git if needed and commit after successful verification.",
                "default": True,
            },
            "allow_unlisted": {
                "type": "boolean",
                "description": (
                    "If false, only paths in the conservative allowlist are accepted. "
                    "Blocked secret paths are never accepted."
                ),
                "default": False,
            },
            "backup_root": {
                "type": "string",
                "description": "Where timestamped backups are placed.",
                "default": "~/.dotfiles_migration_backup",
            },
        },
        "required": ["vault_path", "dotfile_paths"],
    },
}


def _handle_sync_dotfiles(params: dict[str, Any], **kwargs: Any) -> str:
    """Hermes tool handler. Must return a JSON string."""
    del kwargs

    result = sync_dotfiles_to_obsidian_impl(
        vault_path=params.get("vault_path", ""),
        dotfile_paths=params.get("dotfile_paths", []),
        package_name=params.get("package_name", "linux_desktop"),
        dry_run=params.get("dry_run", True),
        confirm=params.get("confirm", False),
        commit_to_git=params.get("commit_to_git", True),
        allow_unlisted=params.get("allow_unlisted", False),
        backup_root=params.get("backup_root", "~/.dotfiles_migration_backup"),
    )

    return json.dumps(result, indent=2)


def register(ctx: Any) -> None:
    """Register the plugin tool with Hermes."""
    ctx.register_tool(
        name="sync_dotfiles_to_obsidian",
        toolset="obsidian_dotfiles",
        schema=SYNC_DOTFILES_SCHEMA,
        handler=_handle_sync_dotfiles,
        description=(
            "Dry-run-first migration of selected dotfiles into an Obsidian-backed GNU Stow package."
        ),
    )
