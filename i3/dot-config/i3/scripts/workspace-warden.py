#!/usr/bin/env python3
"""
workspace-warden.py

Single i3ipc daemon that enforces two workspace policies:

1. Workspace 1 is exclusive to Steam windows.
   - Any real window on workspace number 1 whose WM_CLASS is not in
     ALLOWED_STEAM_CLASSES is moved to workspace number STEAM_PUNT_WORKSPACE_NUM.

2. All non-exempt workspaces may have at most MAX_WINDOWS counted tiled windows.
   - Extra counted windows are moved to OVERFLOW_WORKSPACE.
   - Floating windows, dialogs, utilities, popups, notifications, and other
     transient window types/roles are ignored by the max-window rule.

Recommended i3 config autostart line:
    exec --no-startup-id ~/.config/i3/scripts/workspace-warden.py
"""

from __future__ import annotations

import logging
import sys
import time
from typing import Optional

import i3ipc
from i3ipc import Event


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Steam-only rule
STEAM_WORKSPACE_NUM = 1
ALLOWED_STEAM_CLASSES = {"steam"}
STEAM_PUNT_WORKSPACE_NUM = 2

# Max-window rule
MAX_WINDOWS = 2
OVERFLOW_WORKSPACE = "9: overflow"

# Workspaces where the max-window rule should not apply.
# Workspace 1 is handled by the Steam-only rule.
# Overflow is exempt so windows do not loop forever.
MAX_WINDOW_EXEMPT_WORKSPACE_NUMS = {STEAM_WORKSPACE_NUM, 9}
MAX_WINDOW_EXEMPT_WORKSPACE_NAMES = {OVERFLOW_WORKSPACE}

# Delay gives i3 time to apply assign/floating/dialog rules before we inspect.
ATTACH_DELAY = 0.50

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
    logging.basicConfig(
        level=logging.INFO,
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
    return props.get("window_type")


def get_window_role(node) -> Optional[str]:
    value = getattr(node, "window_role", None)
    if value:
        return value

    props = get_window_properties(node)
    return props.get("window_role")


def is_real_window(node) -> bool:
    return getattr(node, "window", None) is not None


def is_floating(node) -> bool:
    return getattr(node, "floating", "auto_off") in FLOATING_STATES


def workspace_num(workspace) -> Optional[int]:
    return getattr(workspace, "num", None) if workspace is not None else None


def workspace_name(workspace) -> Optional[str]:
    return getattr(workspace, "name", None) if workspace is not None else None


def workspace_is_number(workspace, number: int) -> bool:
    """
    Prefer i3's numeric workspace field, but keep a string-name fallback for
    simple configs where the workspace is literally named "1".
    """
    if workspace is None:
        return False

    num = workspace_num(workspace)
    if num == number:
        return True

    return workspace_name(workspace) == str(number)


def ignore_reason_for_max_window_rule(node) -> Optional[str]:
    """
    Returns a reason this node should not count toward MAX_WINDOWS, or None if
    the node should be counted.
    """
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
# Rule 1: Workspace 1 is Steam-only
# -----------------------------------------------------------------------------

def is_allowed_on_steam_workspace(node) -> bool:
    if not is_real_window(node):
        return True

    window_class = get_window_class(node)
    if not window_class:
        return False

    return window_class.lower() in ALLOWED_STEAM_CLASSES


def enforce_steam_only_workspace(node) -> bool:
    """
    Enforce the Steam-only workspace rule for a single container.

    Returns True if this function moved the container. The caller should stop
    processing the current event when True, because i3 will emit a later move
    event after the window lands on its new workspace.
    """
    workspace = node.workspace()

    if not workspace_is_number(workspace, STEAM_WORKSPACE_NUM):
        return False

    if is_allowed_on_steam_workspace(node):
        return False

    logging.info(
        "Workspace %s violation: moving %s to workspace number %s",
        STEAM_WORKSPACE_NUM,
        describe_window(node),
        STEAM_PUNT_WORKSPACE_NUM,
    )
    node.command(f"move container to workspace number {STEAM_PUNT_WORKSPACE_NUM}")
    return True


# -----------------------------------------------------------------------------
# Rule 2: Max two counted windows per non-exempt workspace
# -----------------------------------------------------------------------------

def enforce_max_windows_for_container(node) -> bool:
    """
    Enforce max-window rule by checking the current workspace of this container.

    Returns True if the container was moved to overflow.
    """
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
        "Max-window violation: moving newest/moved window %s to %s",
        describe_window(node),
        OVERFLOW_WORKSPACE,
    )
    node.command(f'move container to workspace "{OVERFLOW_WORKSPACE}"')
    return True


def enforce_max_windows_for_workspace(workspace) -> int:
    """
    Startup cleanup for an entire workspace.

    Keeps the first MAX_WINDOWS counted leaves and moves later counted leaves to
    overflow. Returns the number of windows moved.
    """
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
# Event handling and startup sweep
# -----------------------------------------------------------------------------

def refetch_container(conn: i3ipc.Connection, con_id: int):
    tree = conn.get_tree()
    return tree.find_by_id(con_id)


def on_window_event(conn: i3ipc.Connection, event) -> None:
    # Give i3 a moment to apply floating/dialog/assignment rules.
    time.sleep(ATTACH_DELAY)

    con = refetch_container(conn, event.container.id)
    if con is None:
        logging.info("Window disappeared before handling; skipping")
        return

    # Highest-priority rule: Workspace 1 belongs to Steam.
    moved = enforce_steam_only_workspace(con)
    if moved:
        return

    # Lower-priority rule: other workspaces get at most MAX_WINDOWS counted windows.
    enforce_max_windows_for_container(con)


def initial_sweep(conn: i3ipc.Connection) -> None:
    """
    Clean up existing violations when the daemon starts.
    """
    logging.info("Running startup sweep")

    # First pass: remove non-Steam windows from workspace 1.
    tree = conn.get_tree()
    steam_moves = 0
    for node in tree.leaves():
        if enforce_steam_only_workspace(node):
            steam_moves += 1

    # If anything moved, let i3 settle before checking max-window counts.
    if steam_moves:
        time.sleep(ATTACH_DELAY)

    # Second pass: enforce max windows on all non-exempt workspaces.
    tree = conn.get_tree()
    max_window_moves = 0
    for workspace in tree.workspaces():
        max_window_moves += enforce_max_windows_for_workspace(workspace)

    logging.info(
        "Startup sweep complete: moved %s Steam-workspace violation(s), %s max-window violation(s)",
        steam_moves,
        max_window_moves,
    )


def main() -> int:
    setup_logging()

    try:
        conn = i3ipc.Connection()
    except Exception:
        logging.exception("Could not connect to i3. Is i3 running, and is I3SOCK/DISPLAY available?")
        return 1

    logging.info(
        "workspace-warden started: workspace %s allows classes %s; other workspaces max %s counted windows; overflow=%s",
        STEAM_WORKSPACE_NUM,
        sorted(ALLOWED_STEAM_CLASSES),
        MAX_WINDOWS,
        OVERFLOW_WORKSPACE,
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
