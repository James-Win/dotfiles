#!/usr/bin/env python3

import time
import i3ipc

MAX_WINDOWS = 2
OVERFLOW_WORKSPACE = "9: overflow"

# A little longer delay gives i3 time to apply floating/dialog rules.
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


def get_window_properties(node):
    return getattr(node, "window_properties", None) or {}


def get_window_type(node):
    value = getattr(node, "window_type", None)
    if value:
        return value

    props = get_window_properties(node)
    return props.get("window_type")


def get_window_role(node):
    value = getattr(node, "window_role", None)
    if value:
        return value

    props = get_window_properties(node)
    return props.get("window_role")


def is_floating(node):
    return getattr(node, "floating", "auto_off") in FLOATING_STATES


def ignore_reason(node):
    if node.window is None:
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


def count_counted_windows_on_workspace(workspace):
    if workspace is None:
        return 0

    count = 0

    for node in workspace.leaves():
        if node.window is None:
            continue

        if ignore_reason(node):
            continue

        count += 1

    return count


def on_window_new(conn, event):
    time.sleep(ATTACH_DELAY)

    tree = conn.get_tree()
    con = tree.find_by_id(event.container.id)

    if con is None:
        print("New window disappeared before handling; skipping", flush=True)
        return

    workspace = con.workspace()

    if workspace is None:
        print("No workspace found; skipping", flush=True)
        return

    window_type = get_window_type(con)
    window_role = get_window_role(con)
    floating = getattr(con, "floating", "unknown")

    print(
        f"New window: workspace={workspace.name}, "
        f"type={window_type}, role={window_role}, floating={floating}",
        flush=True,
    )

    if workspace.name == OVERFLOW_WORKSPACE:
        print("Window opened on overflow workspace; skipping", flush=True)
        return

    reason = ignore_reason(con)
    if reason:
        print(f"Ignoring new window because {reason}", flush=True)
        return

    window_count = count_counted_windows_on_workspace(workspace)
    print(f"Workspace {workspace.name} has {window_count} counted windows", flush=True)

    if window_count > MAX_WINDOWS:
        print(f"Moving extra window to {OVERFLOW_WORKSPACE}", flush=True)
        con.command(f'move to workspace "{OVERFLOW_WORKSPACE}"')


def main():
    conn = i3ipc.Connection()
    print("max-2-windows script started", flush=True)
    conn.on("window::new", on_window_new)
    conn.main()


if __name__ == "__main__":
    main()
