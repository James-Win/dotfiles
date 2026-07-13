#!/usr/bin/env python3
"""
workspace-warden.py

An i3ipc daemon that enforces workspace management policies:

1. Max-windows rule (enabled by default): All non-exempt workspaces may have
   at most MAX_WINDOWS counted tiled windows. Extra counted windows are moved
   to OVERFLOW_WORKSPACE. Floating windows, dialogs, utilities, popups,
   notifications, and other transient window types/roles are ignored.

2. Exclusive workspace rule (optional, disabled by default): Reserve a workspace
   for a specific set of app classes. Any window whose WM_CLASS is not in the
   allowed list is relocated to a configurable destination workspace.
   Enable via warden_config.json: "exclusive_rule_enabled": true

3. Floating app rules (enabled by default): Automatically make specific app
   classes float (popup) instead of embedding in the tiled layout.
   Configure via warden_config.json: "floating_rules": [{"class": "thunar"}, ...]

Config is loaded from warden_config.json (in the same directory) if present.
All constants below are defaults that are overridden by the JSON config.

Recommended i3 config autostart line:
    exec --no-startup-id ~/.config/i3/scripts/workspace-warden.py
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
import time
from typing import Optional

import i3ipc
from i3ipc import Event


# -----------------------------------------------------------------------------
# Config loading
# -----------------------------------------------------------------------------

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(_SCRIPT_DIR, "warden_config.json")


def load_config() -> dict:
    """Load config from JSON file, return defaults if file missing or invalid."""
    defaults = {
        # Exclusive workspace rule
        "exclusive_rule_enabled": False,
        "exclusive_workspace_num": 1,
        "exclusive_allowed_classes": [],
        "exclusive_punt_workspace_num": 2,

        # Max-windows rule
        "max_windows": 2,
        "overflow_workspace": "9: overflow",
        "max_window_exempt_workspace_nums": [9],
        "max_window_exempt_workspace_names": ["9: overflow"],
        "max_window_rule_enabled": True,

        # Floating app rules
        "floating_rule_enabled": True,
        "floating_rules": [],

        # Timing / misc
        "attach_delay": 0.50,
        "log_level": "INFO",
    }

    if not os.path.exists(CONFIG_FILE):
        return defaults

    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)

        # Migrate old steam_* key names transparently
        _migrate_steam_keys(data)

        merged = {**defaults, **data}
        return merged
    except Exception as e:
        print(f"Warning: Could not load {CONFIG_FILE}: {e}", file=sys.stderr)
        return defaults


def _migrate_steam_keys(data: dict) -> None:
    """Silently migrate legacy steam_* config keys to exclusive_* names."""
    mapping = {
        "steam_rule_enabled": "exclusive_rule_enabled",
        "steam_workspace_num": "exclusive_workspace_num",
        "allowed_steam_classes": "exclusive_allowed_classes",
        "steam_punt_workspace_num": "exclusive_punt_workspace_num",
    }
    for old, new in mapping.items():
        if old in data and new not in data:
            data[new] = data.pop(old)


# Load config at module level
_cfg = load_config()

# -----------------------------------------------------------------------------
# Configuration (defaults, overridden by JSON config)
# -----------------------------------------------------------------------------

# Exclusive workspace rule
EXCLUSIVE_RULE_ENABLED: bool = bool(_cfg["exclusive_rule_enabled"])
EXCLUSIVE_WORKSPACE_NUM: int = int(_cfg["exclusive_workspace_num"])
EXCLUSIVE_ALLOWED_CLASSES: set = set(c.lower() for c in _cfg["exclusive_allowed_classes"])
EXCLUSIVE_PUNT_WORKSPACE_NUM: int = int(_cfg["exclusive_punt_workspace_num"])

# Max-windows rule
MAX_WINDOWS: int = _cfg["max_windows"]
OVERFLOW_WORKSPACE: str = _cfg["overflow_workspace"]
MAX_WINDOW_EXEMPT_WORKSPACE_NUMS: set = set(_cfg["max_window_exempt_workspace_nums"])
MAX_WINDOW_EXEMPT_WORKSPACE_NAMES: set = set(_cfg["max_window_exempt_workspace_names"])
MAX_WINDOW_RULE_ENABLED: bool = bool(_cfg["max_window_rule_enabled"])

# Floating app rules
FLOATING_RULE_ENABLED: bool = bool(_cfg["floating_rule_enabled"])
FLOATING_RULES: list[dict] = _cfg["floating_rules"]  # [{"class": "thunar"}, ...]

# Delay gives i3 time to apply assign/floating/dialog rules before we inspect.
ATTACH_DELAY: float = float(_cfg["attach_delay"])

FLOATING_STATES = {"auto_on", "user_on"}

IGNORED_WINDOW_TYPES = {
    "dialog",
    "utility",
    "toolbar",
    "splash",
    "menu",
    "dropdown_menu",
    "popup_menu",
    "tooltip",
    "notification",
    "combo",
    "dnd",
}

IGNORED_WINDOW_ROLES = {
    "pop-up",
    "popup",
    "dialog",
    "task_dialog",
    "bubble",
}


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def setup_logging() -> None:
    level = getattr(logging, _cfg.get("log_level", "INFO").upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s: %(message)s",
    )


def get_window_properties(node) -> dict:
    return getattr(node, "window_properties", None) or {}


def get_window_class(node) -> Optional[str]:
    value = getattr(node, "window_class", None)
    if value:
        return value
    props = get_window_properties(node)
    return props.get("class")


def get_window_type(node) -> Optional[str]:
    value = getattr(node, "window_type", None)
    if value:
        return value
    props = get_window_properties(node)
    if props:
        return props.get("window_type")
    ipc_data = getattr(node, "ipc_data", None) or {}
    return ipc_data.get("window_type")


def get_window_role(node) -> Optional[str]:
    value = getattr(node, "window_role", None)
    if value:
        return value
    props = get_window_properties(node)
    if props:
        return props.get("window_role")
    ipc_data = getattr(node, "ipc_data", None) or {}
    window_props = ipc_data.get("window_properties") or {}
    return window_props.get("role")


def is_real_window(node) -> bool:
    return getattr(node, "window", None) is not None


def is_floating(node) -> bool:
    return getattr(node, "floating", "auto_off") in FLOATING_STATES


def workspace_num(workspace) -> Optional[int]:
    return getattr(workspace, "num", None) if workspace is not None else None


def workspace_name(workspace) -> Optional[str]:
    return getattr(workspace, "name", None) if workspace is not None else None


def workspace_is_number(workspace, number: int) -> bool:
    if workspace is None:
        return False
    num = workspace_num(workspace)
    if num == number:
        return True
    return workspace_name(workspace) == str(number)


def ignore_reason_for_max_window_rule(node) -> Optional[str]:
    if not is_real_window(node):
        return "not a real window"
    if is_floating(node):
        return "floating"
    window_type = get_window_type(node)
    if window_type in IGNORED_WINDOW_TYPES:
        return f"window_type={window_type}"
    window_role = get_window_role(node)
    if window_role and window_role.lower() in IGNORED_WINDOW_ROLES:
        return f"window_role={window_role}"
    return None


def workspace_is_exempt_from_max_window_rule(workspace) -> bool:
    if workspace is None:
        return True
    num = workspace_num(workspace)
    name = workspace_name(workspace)
    if num in MAX_WINDOW_EXEMPT_WORKSPACE_NUMS:
        return True
    if name in MAX_WINDOW_EXEMPT_WORKSPACE_NAMES:
        return True
    return False


def counted_windows_on_workspace(workspace) -> list:
    if workspace is None:
        return []
    counted = []
    for node in workspace.leaves():
        if ignore_reason_for_max_window_rule(node):
            continue
        counted.append(node)
    return counted


def describe_window(node) -> str:
    cls = get_window_class(node) or "<no class>"
    title = getattr(node, "window_title", None) or getattr(node, "name", None) or "<no title>"
    return f"class={cls!r} title={title!r}"


# -----------------------------------------------------------------------------
# Rule 1: Exclusive workspace (optional)
# -----------------------------------------------------------------------------

def is_allowed_on_exclusive_workspace(node) -> bool:
    if not is_real_window(node):
        return True
    if not EXCLUSIVE_ALLOWED_CLASSES:
        return True  # No class restriction configured — allow everything
    window_class = get_window_class(node)
    if not window_class:
        return False
    return window_class.lower() in EXCLUSIVE_ALLOWED_CLASSES


def enforce_exclusive_workspace(node) -> bool:
    """
    If the exclusive rule is enabled, ensure only allowed classes land on the
    designated workspace. Returns True if the node was moved (caller should stop
    further processing for this event).
    """
    if not EXCLUSIVE_RULE_ENABLED:
        return False

    workspace = node.workspace()
    if not workspace_is_number(workspace, EXCLUSIVE_WORKSPACE_NUM):
        return False

    if is_allowed_on_exclusive_workspace(node):
        return False

    logging.info(
        "Exclusive workspace %s violation: moving %s to workspace number %s",
        EXCLUSIVE_WORKSPACE_NUM,
        describe_window(node),
        EXCLUSIVE_PUNT_WORKSPACE_NUM,
    )
    node.command(f"move container to workspace number {EXCLUSIVE_PUNT_WORKSPACE_NUM}")
    return True


# -----------------------------------------------------------------------------
# Rule 2: Max windows per non-exempt workspace
# -----------------------------------------------------------------------------

def enforce_max_windows_for_container(node) -> bool:
    """Returns True if the container was moved to overflow."""
    if not MAX_WINDOW_RULE_ENABLED:
        return False

    workspace = node.workspace()
    if workspace is None:
        return False

    if workspace_is_exempt_from_max_window_rule(workspace):
        return False

    reason = ignore_reason_for_max_window_rule(node)
    if reason:
        logging.debug("Ignoring %s for max-window rule because %s", describe_window(node), reason)
        return False

    counted = counted_windows_on_workspace(workspace)
    logging.info(
        "Workspace %s has %s counted window(s)",
        workspace_name(workspace),
        len(counted),
    )

    if len(counted) <= MAX_WINDOWS:
        return False

    logging.info(
        "Max-window violation: moving %s to %s",
        describe_window(node),
        OVERFLOW_WORKSPACE,
    )
    node.command(f'move container to workspace "{OVERFLOW_WORKSPACE}"')
    return True


def enforce_max_windows_for_workspace(workspace) -> int:
    """Startup cleanup. Returns the number of windows moved."""
    if not MAX_WINDOW_RULE_ENABLED:
        return 0

    if workspace_is_exempt_from_max_window_rule(workspace):
        return 0

    counted = counted_windows_on_workspace(workspace)
    extra = counted[MAX_WINDOWS:]

    for node in extra:
        logging.info(
            "Startup max-window cleanup: moving %s from workspace %s to %s",
            describe_window(node),
            workspace_name(workspace),
            OVERFLOW_WORKSPACE,
        )
        node.command(f'move container to workspace "{OVERFLOW_WORKSPACE}"')

    return len(extra)


# -----------------------------------------------------------------------------
# Rule 3: Floating app rules
# -----------------------------------------------------------------------------

def _build_floating_class_set() -> set:
    """Return a lowercase set of all WM_CLASS values that should float."""
    classes = set()
    for rule in FLOATING_RULES:
        cls = rule.get("class", "").strip().lower()
        if cls:
            classes.add(cls)
    return classes


_FLOATING_CLASSES: set = _build_floating_class_set()


def enforce_floating_rules(node) -> bool:
    """
    If the node's WM_CLASS matches a floating rule, send 'floating enable'.
    Returns True if the command was issued.
    """
    if not FLOATING_RULE_ENABLED or not _FLOATING_CLASSES:
        return False

    if not is_real_window(node):
        return False

    if is_floating(node):
        return False  # Already floating

    window_class = get_window_class(node)
    if not window_class:
        return False

    if window_class.lower() not in _FLOATING_CLASSES:
        return False

    logging.info("Floating rule: enabling floating for %s", describe_window(node))
    node.command("floating enable")
    return True


# -----------------------------------------------------------------------------
# Event handling and startup sweep
# -----------------------------------------------------------------------------

def _deferred_enforce_rules(con_id: int) -> None:
    time.sleep(ATTACH_DELAY)

    thread_conn = i3ipc.Connection()
    try:
        tree = thread_conn.get_tree()
        con = tree.find_by_id(con_id)
        if con is None:
            logging.info("Window disappeared before handling; skipping")
            return

        # Rule 3: Make floating if matching a floating rule (before layout decisions)
        enforce_floating_rules(con)

        # Rule 1: Exclusive workspace check (highest eviction priority)
        moved = enforce_exclusive_workspace(con)
        if moved:
            return

        # Rule 2: Max-windows per workspace
        enforce_max_windows_for_container(con)
    except Exception:
        logging.exception("Error checking container in background thread")
    finally:
        thread_conn.main_quit()


def on_window_event(conn: i3ipc.Connection, event) -> None:
    threading.Thread(
        target=_deferred_enforce_rules,
        args=(event.container.id,),
        daemon=True
    ).start()


def initial_sweep(conn: i3ipc.Connection) -> None:
    """Clean up existing violations when the daemon starts."""
    logging.info("Running startup sweep")

    tree = conn.get_tree()
    exclusive_moves = 0
    for node in tree.leaves():
        if enforce_exclusive_workspace(node):
            exclusive_moves += 1

    if exclusive_moves:
        time.sleep(ATTACH_DELAY)

    tree = conn.get_tree()
    max_window_moves = 0
    for workspace in tree.workspaces():
        max_window_moves += enforce_max_windows_for_workspace(workspace)

    logging.info(
        "Startup sweep complete: moved %s exclusive-workspace violation(s), "
        "%s max-window violation(s)",
        exclusive_moves,
        max_window_moves,
    )


def main() -> int:
    setup_logging()

    logging.info(
        "Config loaded from: %s",
        CONFIG_FILE if os.path.exists(CONFIG_FILE) else "defaults"
    )

    try:
        conn = i3ipc.Connection()
    except Exception:
        logging.exception(
            "Could not connect to i3. Is i3 running, and is I3SOCK/DISPLAY available?"
        )
        return 1

    logging.info(
        "workspace-warden started | "
        "exclusive_rule=%s ws=%s classes=%s | "
        "max_window_rule=%s max=%s overflow=%s | "
        "floating_rule=%s classes=%s | "
        "attach_delay=%.2fs",
        EXCLUSIVE_RULE_ENABLED,
        EXCLUSIVE_WORKSPACE_NUM,
        sorted(EXCLUSIVE_ALLOWED_CLASSES),
        MAX_WINDOW_RULE_ENABLED,
        MAX_WINDOWS,
        OVERFLOW_WORKSPACE,
        FLOATING_RULE_ENABLED,
        sorted(_FLOATING_CLASSES),
        ATTACH_DELAY,
    )

    conn.on(Event.WINDOW_NEW, on_window_event)
    conn.on(Event.WINDOW_MOVE, on_window_event)

    initial_sweep(conn)

    try:
        conn.main()
    except KeyboardInterrupt:
        logging.info("workspace-warden stopped")
        return 0
    except Exception:
        logging.exception("workspace-warden crashed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
