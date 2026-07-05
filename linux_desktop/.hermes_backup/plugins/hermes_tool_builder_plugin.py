"""
Hermes Tool Builder Plugin

This plugin helps Hermes generate, validate, and save Hermes-compatible tool
plugin files.

Security model
--------------
This plugin deliberately does not execute generated plugin code. It only:

1. drafts starter plugin source as text,
2. performs structural AST-based validation, and
3. writes validated plugin files into a restricted local workspace.

Important: AST validation is a lint/safety screen, not a sandbox. Passing this
validator does not prove generated code is safe to execute. Review generated
files before loading them into Hermes.
"""

from __future__ import annotations

import ast
import keyword
import re
import tempfile
import textwrap
from pathlib import Path
from typing import Any

from hermes_agent.tools import Toolset, tool


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BANNED_IMPORTS = {
    "langchain",
    "llama_index",
    "llamaindex",
    "openai",
}

CAUTION_IMPORTS = {
    "os": (
        "The plugin imports os. Make sure it does not expose sensitive "
        "environment variables or filesystem paths."
    ),
    "subprocess": "The plugin imports subprocess. Review carefully before enabling this tool.",
    "shutil": "The plugin imports shutil. Review file operations carefully before enabling this tool.",
    "socket": "The plugin imports socket. Review network access carefully before enabling this tool.",
    "importlib": (
        "The plugin imports importlib. Review dynamic imports carefully as "
        "they can bypass security filters."
    ),
    "requests": "The plugin imports requests. Review network access carefully before enabling this tool.",
    "httpx": "The plugin imports httpx. Review network access carefully before enabling this tool.",
    "urllib": "The plugin imports urllib. Review network access carefully before enabling this tool.",
}

CAUTION_CALLS = {
    "eval": "The plugin calls eval(). This can execute arbitrary code.",
    "exec": "The plugin calls exec(). This can execute arbitrary code.",
    "compile": "The plugin calls compile(). Review carefully before enabling this tool.",
    "__import__": "The plugin calls __import__(). Review dynamic imports carefully.",
    "import_module": "The plugin calls import_module(). Review dynamic tool loading/imports carefully.",
    "open": "The plugin calls open(). Review filesystem access carefully before enabling this tool.",
}

REQUIRED_TOOL_KWARGS = {"name", "category", "description"}

MAX_FILENAME_STEM_LENGTH = 80
MAX_PLUGIN_FILE_BYTES = 256 * 1024
MAX_LLM_TOOL_NAME_LENGTH = 64
MAX_CATEGORY_LENGTH = 80
MAX_DESCRIPTION_LENGTH = 1024

# Common LLM provider-friendly function/tool name shape. This is intentionally
# conservative and should work for OpenAI/Anthropic-style tool schemas.
TOOL_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

STRUCTURAL_VALIDATION_NOTE = (
    "This validator checks Hermes plugin structure and some obvious risk signals. "
    "It does not prove the code is safe to execute."
)

# Keep the generated-plugin review workspace stable and independent of the
# process current working directory. Change this constant if your Hermes setup
# expects generated plugins somewhere else.
SAFE_BASE_DIR = (Path.home() / ".local" / "share" / "hermes" / "generated_hermes_plugins").resolve()
_DEFAULT_PLUGIN_DIR_ALIASES = {".", "./generated_hermes_plugins", "generated_hermes_plugins"}


# ---------------------------------------------------------------------------
# Path and name helpers
# ---------------------------------------------------------------------------

def _is_relative_to(path: Path, base: Path) -> bool:
    """Compatibility wrapper for Path.is_relative_to."""
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def _safe_filename(name: str) -> str:
    """
    Convert a user-provided plugin name into a safe local Python filename.

    Rules:
    - remove path separators and unsupported characters,
    - strip an optional .py suffix before cleaning,
    - cap the filename stem length, and
    - always return a filename ending in .py.
    """
    raw = str(name).strip().lower()

    if raw.endswith(".py"):
        raw = raw[:-3]

    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", raw).strip("_-")
    cleaned = cleaned or "generated_hermes_plugin"
    cleaned = cleaned[:MAX_FILENAME_STEM_LENGTH].strip("_-") or "generated_hermes_plugin"

    return f"{cleaned}.py"


def _truncate_name(value: str, fallback: str, max_length: int) -> str:
    """Trim a generated name without returning an empty string."""
    trimmed = value[:max_length].strip("_-")
    return trimmed or fallback


def _safe_tool_name(value: str, fallback: str = "generated_tool") -> str:
    """
    Convert user text into a provider-friendly tool metadata name.

    This is distinct from a Python identifier. LLM tool names usually allow
    letters, numbers, underscores, and hyphens, with a 64-character limit.
    """
    name = re.sub(r"[^A-Za-z0-9_-]+", "_", str(value).strip()).strip("_-")
    name = name or fallback
    name = _truncate_name(name, fallback, MAX_LLM_TOOL_NAME_LENGTH)

    if not TOOL_NAME_PATTERN.fullmatch(name):
        return fallback

    return name


def _safe_identifier(value: str, fallback: str, *, max_length: int = MAX_LLM_TOOL_NAME_LENGTH) -> str:
    """
    Convert user-provided text into a valid Python identifier.

    The result is suitable for generated function names and module-level
    variable names.
    """
    ident = re.sub(r"[^A-Za-z0-9_]+", "_", str(value).strip()).strip("_")
    ident = ident or fallback

    if ident[0].isdigit():
        ident = f"{fallback}_{ident}"

    ident = _truncate_name(ident, fallback, max_length)

    if keyword.iskeyword(ident):
        ident = f"{ident}_"

    if not ident.isidentifier():
        ident = fallback

    return ident


def _resolve_plugin_directory(plugins_dir: str) -> Path:
    """
    Resolve a plugin output directory inside SAFE_BASE_DIR.

    The default aliases ".", "./generated_hermes_plugins", and
    "generated_hermes_plugins" all resolve to SAFE_BASE_DIR. Other relative
    paths are treated as subdirectories inside SAFE_BASE_DIR. Absolute paths
    are allowed only when they resolve inside SAFE_BASE_DIR.
    """
    raw_text = str(plugins_dir).strip() or "."
    raw = Path(raw_text).expanduser()

    if raw_text in _DEFAULT_PLUGIN_DIR_ALIASES:
        candidate = SAFE_BASE_DIR
    elif raw.is_absolute():
        candidate = raw.resolve()
    else:
        candidate = (SAFE_BASE_DIR / raw).resolve()

    if not _is_relative_to(candidate, SAFE_BASE_DIR):
        raise ValueError(
            f"Requested directory '{plugins_dir}' is outside the allowed workspace '{SAFE_BASE_DIR}'."
        )

    return candidate


def _resolve_plugin_file(file_path: str) -> Path:
    """
    Resolve a plugin file path inside SAFE_BASE_DIR.

    Passing just a filename, such as "my_tool.py", resolves to
    SAFE_BASE_DIR / "my_tool.py". Absolute paths are accepted only if they are
    inside SAFE_BASE_DIR.
    """
    raw_text = str(file_path).strip()
    raw = Path(raw_text).expanduser()

    if raw.is_absolute():
        candidate = raw.resolve()
    elif raw.parts and raw.parts[0] == "generated_hermes_plugins":
        candidate = (SAFE_BASE_DIR / Path(*raw.parts[1:])).resolve()
    else:
        candidate = (SAFE_BASE_DIR / raw).resolve()

    if not _is_relative_to(candidate, SAFE_BASE_DIR):
        raise ValueError(
            f"Requested file '{file_path}' is outside the allowed workspace '{SAFE_BASE_DIR}'."
        )

    return candidate


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------

def _call_name(node: ast.AST) -> str | None:
    """
    Return a simple function/class name for calls like Toolset(...), tool(...),
    eval(...), or module.func(...).

    Attribute calls return only the final attribute name.
    """
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        return node.attr

    return None


def _string_literal_kw(call: ast.Call, key: str) -> str | None:
    """Return a string literal keyword value from a call, if present."""
    for kw in call.keywords:
        if (
            kw.arg == key
            and isinstance(kw.value, ast.Constant)
            and isinstance(kw.value.value, str)
        ):
            return kw.value.value
    return None


def _assignment_target_names(target: ast.AST) -> list[str]:
    """Extract simple assignment target names."""
    if isinstance(target, ast.Name):
        return [target.id]

    if isinstance(target, (ast.Tuple, ast.List)):
        names: list[str] = []
        for item in target.elts:
            names.extend(_assignment_target_names(item))
        return names

    return []


def _extract_toolset_function_refs(call: ast.Call) -> set[str]:
    """
    Extract direct function references from Toolset(..., tools=[fn_a, fn_b]).

    The validator intentionally accepts only direct function names. More dynamic
    constructions may work at runtime, but they are harder for a static validator
    to reason about and should be reviewed manually.
    """
    refs: set[str] = set()

    for kw in call.keywords:
        if kw.arg != "tools":
            continue

        if isinstance(kw.value, (ast.List, ast.Tuple, ast.Set)):
            for item in kw.value.elts:
                if isinstance(item, ast.Name):
                    refs.add(item.id)

    return refs


def _is_json_serializable_type(node: ast.AST) -> bool:
    """
    Recursively check whether a type annotation is likely JSON-schema friendly.

    Accepted examples:
    - str, int, float, bool, Any, None
    - list[str], dict[str, Any]
    - str | None
    - Optional[str], Union[str, int]

    This is intentionally conservative. Unknown custom objects should be returned
    as dictionaries or primitive values instead.
    """
    primitive_names = {"str", "int", "float", "bool", "Any", "None"}
    container_names = {"list", "dict", "Optional", "Union", "List", "Dict"}

    if isinstance(node, ast.Name):
        return node.id in primitive_names | container_names

    if isinstance(node, ast.Attribute):
        return node.attr in primitive_names | container_names

    if isinstance(node, ast.Constant) and node.value is None:
        return True

    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _is_json_serializable_type(node.left) and _is_json_serializable_type(node.right)

    if isinstance(node, ast.Subscript):
        if not _is_json_serializable_type(node.value):
            return False

        slice_node = node.slice
        if isinstance(slice_node, ast.Tuple):
            return all(_is_json_serializable_type(elt) for elt in slice_node.elts)

        return _is_json_serializable_type(slice_node)

    return False


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

class PluginValidator(ast.NodeVisitor):
    """
    Single-pass AST visitor that collects structural validation data.

    The visitor records:
    - imports and suspicious calls,
    - Hermes tool imports,
    - @tool-decorated functions,
    - Toolset exports,
    - type-hint/docstring quality signals, and
    - top-level import-time side-effect warnings.
    """

    def __init__(self) -> None:
        self.imports: set[str] = set()
        self.hermes_tool_imports: set[str] = set()
        self.tool_functions: list[str] = []
        self.tool_names: list[str] = []
        self.toolset_exports: list[dict[str, Any]] = []
        self.errors: list[str] = []
        self.warnings: list[str] = []

        self._function_depth = 0
        self._class_depth = 0
        self._current_tool_function: str | None = None

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.add(alias.name.split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.imports.add(node.module.split(".")[0])

            if node.module == "hermes_agent.tools":
                self.hermes_tool_imports.update(alias.name for alias in node.names)

        if node.level:
            self.warnings.append(
                "The plugin uses a relative import. Review import behavior before enabling it."
            )

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        if self._at_module_level():
            self._inspect_possible_toolset_export(node.value, node.targets)
            self._warn_for_top_level_call(node.value, context="assignment")
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if self._at_module_level():
            self._inspect_possible_toolset_export(node.value, [node.target] if node.value else [])
            self._warn_for_top_level_call(node.value, context="annotated assignment")
        self.generic_visit(node)

    def visit_Expr(self, node: ast.Expr) -> None:
        if self._at_module_level():
            self._warn_for_top_level_call(node.value, context="expression")
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        if self._at_module_level():
            self.warnings.append(
                "The plugin has a module-level with block. This executes during import; review carefully."
            )
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        if self._at_module_level():
            self.warnings.append(
                "The plugin has a module-level for loop. This executes during import; review carefully."
            )
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        if self._at_module_level():
            self.warnings.append(
                "The plugin has a module-level while loop. This executes during import; review carefully."
            )
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        if self._at_module_level():
            self.warnings.append(
                "The plugin has a module-level try block. This executes during import; review carefully."
            )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function_like(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function_like(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._class_depth += 1
        self.generic_visit(node)
        self._class_depth -= 1

    def visit_Call(self, node: ast.Call) -> None:
        name = _call_name(node.func)

        if name in CAUTION_CALLS:
            self.warnings.append(CAUTION_CALLS[name])

        if name == "print" and self._current_tool_function:
            self.warnings.append(
                f"Tool function '{self._current_tool_function}' calls print(). "
                "Return data from the tool instead; agent runtimes may not capture stdout."
            )

        self.generic_visit(node)

    def _at_module_level(self) -> bool:
        return self._function_depth == 0 and self._class_depth == 0

    def _warn_for_top_level_call(self, value: ast.AST | None, *, context: str) -> None:
        """
        Warn about import-time function calls outside the expected Toolset export.

        Function definitions and decorators are handled elsewhere. The generated
        scaffold only has a module-level Toolset(...) assignment, which is allowed.
        """
        if not isinstance(value, ast.Call):
            return

        call = _call_name(value.func)
        if call == "Toolset":
            return

        self.warnings.append(
            f"The plugin has a module-level function call in a {context}: {call or 'unknown'}(...). "
            "This executes during import; review carefully."
        )

    def _visit_function_like(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        tool_decorators = self._tool_decorators(node)
        is_tool = bool(tool_decorators)
        old_tool_context = self._current_tool_function

        if is_tool:
            if not self._at_module_level():
                self.errors.append(
                    f"Tool function '{node.name}' is nested inside another scope. "
                    "@tool functions should be module-level functions."
                )
            else:
                self._current_tool_function = node.name
                self._validate_tool_function(node, tool_decorators)

        self._function_depth += 1
        self.generic_visit(node)
        self._function_depth -= 1

        if is_tool:
            self._current_tool_function = old_tool_context

    def _inspect_possible_toolset_export(self, value: ast.AST | None, targets: list[ast.AST]) -> None:
        if not isinstance(value, ast.Call) or _call_name(value.func) != "Toolset":
            return

        target_names: list[str] = []
        for target in targets:
            target_names.extend(_assignment_target_names(target))

        toolset_name = _string_literal_kw(value, "name")
        tool_refs = _extract_toolset_function_refs(value)

        if not target_names:
            self.warnings.append("Toolset(...) export should be assigned to a module-level variable.")
        else:
            for target_name in target_names:
                if not target_name.endswith("_TOOLS"):
                    self.warnings.append(
                        f"Toolset export variable '{target_name}' should conventionally end with '_TOOLS'."
                    )

        if toolset_name is None or not toolset_name.strip():
            self.errors.append("Toolset(...) export is missing a non-empty string literal name=... field.")
        elif not TOOL_NAME_PATTERN.fullmatch(toolset_name):
            self.errors.append(
                f"Toolset name '{toolset_name}' must contain only letters, numbers, underscores, "
                f"or hyphens and be at most {MAX_LLM_TOOL_NAME_LENGTH} characters."
            )

        has_tools_kw = any(kw.arg == "tools" for kw in value.keywords)
        if not has_tools_kw:
            self.errors.append("Toolset(...) export is missing tools=[...] field.")
        elif not tool_refs:
            self.errors.append(
                "Toolset(...) tools=[...] must include at least one direct tool function reference."
            )

        self.toolset_exports.append(
            {
                "targets": target_names,
                "name": toolset_name,
                "tool_refs": sorted(tool_refs),
            }
        )

    @staticmethod
    def _tool_decorators(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.Call]:
        decorators: list[ast.Call] = []

        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and _call_name(dec.func) == "tool":
                decorators.append(dec)
            elif isinstance(dec, ast.Name) and dec.id == "tool":
                decorators.append(ast.Call(func=dec, args=[], keywords=[]))

        return decorators

    def _validate_tool_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        tool_decorators: list[ast.Call],
    ) -> None:
        self.tool_functions.append(node.name)

        if not node.name.isidentifier() or keyword.iskeyword(node.name):
            self.errors.append(f"Tool function name '{node.name}' is not a valid Python identifier.")

        if len(node.name) > MAX_LLM_TOOL_NAME_LENGTH:
            self.errors.append(
                f"Tool function name '{node.name}' exceeds {MAX_LLM_TOOL_NAME_LENGTH} characters."
            )

        for dec in tool_decorators:
            self._validate_tool_decorator(node, dec)

        self._validate_docstring(node)
        self._validate_signature(node)

    def _validate_tool_decorator(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        dec: ast.Call,
    ) -> None:
        kw_names = {kw.arg for kw in dec.keywords if kw.arg is not None}
        missing = sorted(REQUIRED_TOOL_KWARGS - kw_names)

        if missing:
            self.errors.append(
                f"Tool function '{node.name}' has @tool decorator but is missing "
                f"required field(s): {', '.join(missing)}."
            )

        for required_kw in sorted(REQUIRED_TOOL_KWARGS):
            value = _string_literal_kw(dec, required_kw)

            if value is None:
                if required_kw in kw_names:
                    self.errors.append(
                        f"Tool function '{node.name}' @tool field '{required_kw}' "
                        "must be a string literal."
                    )
                continue

            if not value.strip():
                self.errors.append(
                    f"Tool function '{node.name}' @tool field '{required_kw}' cannot be empty."
                )

            if required_kw == "name":
                self.tool_names.append(value)
                if not TOOL_NAME_PATTERN.fullmatch(value):
                    self.errors.append(
                        f"Tool meta-name '{value}' must contain only letters, numbers, underscores, "
                        f"or hyphens and be at most {MAX_LLM_TOOL_NAME_LENGTH} characters."
                    )

            if required_kw == "category" and len(value) > MAX_CATEGORY_LENGTH:
                self.warnings.append(
                    f"Tool function '{node.name}' category is long "
                    f"({len(value)} characters). Consider keeping it under {MAX_CATEGORY_LENGTH}."
                )

            if required_kw == "description":
                if len(value.strip()) < 15:
                    self.warnings.append(
                        f"Tool function '{node.name}' description is very short. "
                        "Longer descriptions usually improve agent tool selection."
                    )
                elif len(value) > MAX_DESCRIPTION_LENGTH:
                    self.warnings.append(
                        f"Tool function '{node.name}' description is long "
                        f"({len(value)} characters). Consider keeping it under {MAX_DESCRIPTION_LENGTH}."
                    )

    def _validate_docstring(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        docstring = ast.get_docstring(node)

        if not docstring or not docstring.strip():
            self.errors.append(f"Tool function '{node.name}' must have a docstring explaining what it does.")
            return

        if len(docstring.strip()) < 15:
            self.errors.append(
                f"Tool function '{node.name}' has a docstring, but it is too short to be useful."
            )
            return

        all_args = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
        if not all_args:
            return

        docstring_lower = docstring.lower()
        has_explicit_args_section = any(
            header in docstring_lower for header in ("args:", "parameters:", "arguments:")
        )

        if has_explicit_args_section:
            return

        missing_doc_params = [
            arg.arg
            for arg in all_args
            if not re.search(r"\b" + re.escape(arg.arg.lower()) + r"\b", docstring_lower)
        ]

        if missing_doc_params:
            self.warnings.append(
                f"Tool function '{node.name}' parameters {missing_doc_params} are not explicitly "
                "documented in the function docstring."
            )

    def _validate_signature(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        all_args = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]

        for arg in all_args:
            if arg.annotation is None:
                self.errors.append(f"Tool function '{node.name}' parameter '{arg.arg}' is missing a type hint.")
            elif not _is_json_serializable_type(arg.annotation):
                self.warnings.append(
                    f"Tool function '{node.name}' parameter '{arg.arg}' uses a type hint that may not "
                    "be JSON-schema friendly. Prefer primitives, dicts, lists, or typing.Any."
                )

        if node.args.vararg:
            self.errors.append(
                f"Tool function '{node.name}' should not use *args; explicit typed parameters are required."
            )

        if node.args.kwarg:
            self.errors.append(
                f"Tool function '{node.name}' should not use **kwargs; explicit typed parameters are required."
            )

        if node.returns is None:
            self.errors.append(f"Tool function '{node.name}' is missing a return type hint.")
        elif not _is_json_serializable_type(node.returns):
            self.warnings.append(
                f"Tool function '{node.name}' return type may not be JSON-schema friendly. "
                "Prefer primitives, dicts, lists, or typing.Any."
            )


def _code_too_large_error(size_bytes: int) -> dict[str, Any]:
    return {
        "valid": False,
        "errors": [
            f"Plugin code is too large to validate safely: {size_bytes} bytes "
            f"(limit: {MAX_PLUGIN_FILE_BYTES} bytes)."
        ],
        "warnings": [],
        "tool_functions": [],
        "tool_names": [],
        "toolset_exports": [],
        "security_note": STRUCTURAL_VALIDATION_NOTE,
    }


def _validate_plugin_code(python_code: str) -> dict[str, Any]:
    """
    Validate Hermes plugin Python source without executing it.

    Returns a dictionary that is intentionally JSON-serializable so Hermes or an
    LLM agent can inspect it safely.
    """
    size_bytes = len(python_code.encode("utf-8", errors="replace"))
    if size_bytes > MAX_PLUGIN_FILE_BYTES:
        return _code_too_large_error(size_bytes)

    try:
        tree = ast.parse(python_code)
    except SyntaxError as e:
        error_msg = f"Syntax error on line {e.lineno}, column {e.offset}: {e.msg}"
        if e.text:
            error_msg += f"\nCode snippet: {e.text.strip()}"
        return {
            "valid": False,
            "errors": [error_msg],
            "warnings": [],
            "tool_functions": [],
            "tool_names": [],
            "toolset_exports": [],
            "security_note": STRUCTURAL_VALIDATION_NOTE,
        }

    validator = PluginValidator()
    validator.visit(tree)

    errors = list(validator.errors)
    warnings = list(dict.fromkeys(validator.warnings))

    banned_found = sorted(validator.imports.intersection(BANNED_IMPORTS))
    if banned_found:
        errors.append("Banned imports found: " + ", ".join(banned_found))

    for import_name, warning in CAUTION_IMPORTS.items():
        if import_name in validator.imports:
            warnings.append(warning)

    warnings = list(dict.fromkeys(warnings))

    if not {"tool", "Toolset"}.issubset(validator.hermes_tool_imports):
        errors.append("Missing required import: from hermes_agent.tools import tool, Toolset")

    if not validator.tool_functions:
        errors.append("No @tool-decorated functions were found.")

    if not validator.toolset_exports:
        errors.append("No module-level Toolset(...) export was found.")

    duplicate_function_names = sorted(
        name for name in set(validator.tool_functions) if validator.tool_functions.count(name) > 1
    )
    if duplicate_function_names:
        errors.append("Duplicate @tool-decorated function names found: " + ", ".join(duplicate_function_names))

    duplicate_tool_names = sorted(
        name for name in set(validator.tool_names) if validator.tool_names.count(name) > 1
    )
    if duplicate_tool_names:
        errors.append("Duplicate @tool name values found: " + ", ".join(duplicate_tool_names))

    if validator.tool_functions and validator.toolset_exports:
        exported_refs = {
            ref
            for export in validator.toolset_exports
            for ref in export.get("tool_refs", [])
        }

        missing_exports = sorted(set(validator.tool_functions) - exported_refs)
        if missing_exports:
            errors.append(
                "The following @tool-decorated function(s) are not listed in any Toolset(...): "
                + ", ".join(missing_exports)
            )

        unknown_exports = sorted(exported_refs - set(validator.tool_functions))
        if unknown_exports:
            errors.append(
                "The following Toolset(...) function reference(s) do not match @tool functions: "
                + ", ".join(unknown_exports)
            )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "tool_functions": validator.tool_functions,
        "tool_names": validator.tool_names,
        "toolset_exports": validator.toolset_exports,
        "safe_base_dir": str(SAFE_BASE_DIR),
        "security_note": STRUCTURAL_VALIDATION_NOTE,
    }


# ---------------------------------------------------------------------------
# Public Hermes tools
# ---------------------------------------------------------------------------

@tool(
    name="draft_hermes_tool_plugin",
    category="Tool Building",
    description=(
        "Creates a starter Hermes plugin Python file as text. Use this when the user wants "
        "to make a new Hermes tool plugin from a natural-language description, but has not "
        "yet provided full Python code. This returns a scaffold for the agent or user to edit."
    ),
)
def draft_hermes_tool_plugin(
    plugin_name: str,
    tool_name: str,
    category: str,
    tool_description: str,
) -> str:
    """
    Create starter Hermes plugin source code from plugin and tool metadata.

    Args:
        plugin_name: Human-provided plugin name. It is sanitized before being
            used as a Toolset name or Python variable.
        tool_name: Human-provided tool name. It is sanitized before being used
            as the LLM-facing @tool name and Python function name.
        category: Human-readable tool category.
        tool_description: Human-readable tool description for agent selection.

    Returns:
        A string containing Python source code. The code is not written to disk
        until write_hermes_plugin_file is called.
    """
    try:
        safe_tool_meta_name = _safe_tool_name(tool_name)
        safe_toolset_name = _safe_tool_name(plugin_name, fallback="generated_plugin")
        safe_function_name = _safe_identifier(safe_tool_meta_name.lower(), "generated_tool")
        safe_plugin_var = _safe_identifier(safe_toolset_name, "generated_plugin").upper()

        clean_category = str(category).strip() or "Generated Tools"
        clean_description = str(tool_description).strip() or "Generated Hermes tool scaffold."

        code = textwrap.dedent(
            f'''\
            """
            Generated Hermes plugin.

            Review this file before loading it into Hermes.
            """

            from __future__ import annotations

            from typing import Any

            from hermes_agent.tools import Toolset, tool


            @tool(
                name={safe_tool_meta_name!r},
                category={clean_category!r},
                description={clean_description!r},
            )
            def {safe_function_name}(request: str) -> dict[str, Any]:
                """
                Starter implementation for this generated Hermes tool.

                Args:
                    request: Natural-language request or input for this tool.

                Returns:
                    A dictionary containing scaffold status and the echoed request.
                """
                return {{
                    "status": "success",
                    "message": "Tool scaffold is working. Replace this placeholder logic.",
                    "request": request,
                }}


            {safe_plugin_var}_TOOLS = Toolset(
                name={safe_toolset_name!r},
                tools=[{safe_function_name}],
            )
            '''
        )

        validation = _validate_plugin_code(code)
        if not validation["valid"]:
            return (
                "Error: generated scaffold failed internal validation: "
                + "; ".join(validation["errors"])
            )

        return code

    except Exception as e:
        return f"Error: Failed to draft Hermes plugin: {e}"


@tool(
    name="validate_hermes_plugin_code",
    category="Tool Building",
    description=(
        "Validates Hermes plugin Python code before saving or loading it. Use this to check "
        "whether generated plugin code follows Hermes rules: required imports, @tool decorators, "
        "type hints, docstrings, simple structure, Toolset export, and obvious risk signals."
    ),
)
def validate_hermes_plugin_code(python_code: str) -> dict[str, Any]:
    """
    Validate Hermes plugin Python source code without executing it.

    Args:
        python_code: Python source code for a candidate Hermes plugin.

    Returns:
        A dictionary containing structural validation results, warnings, detected
        tool functions, detected Toolset exports, the configured safe base
        directory, and a security note.
    """
    try:
        return _validate_plugin_code(python_code)
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Validation failed unexpectedly: {str(e)}"],
            "warnings": [],
            "tool_functions": [],
            "tool_names": [],
            "toolset_exports": [],
            "safe_base_dir": str(SAFE_BASE_DIR),
            "security_note": STRUCTURAL_VALIDATION_NOTE,
        }


@tool(
    name="write_hermes_plugin_file",
    category="Tool Building",
    description=(
        "Validates and writes a Hermes plugin Python file to the restricted generated plugin "
        "workspace. Use this only after Hermes or the user has generated complete plugin code. "
        "This tool does not execute or load the plugin; it only saves it for human review."
    ),
)
def write_hermes_plugin_file(
    plugin_name: str,
    python_code: str,
    plugins_dir: str = "./generated_hermes_plugins",
    overwrite: bool = False,
) -> dict[str, Any]:
    """
    Validate plugin source code and write it to a local .py file.

    Args:
        plugin_name: Desired plugin filename stem. The final filename is
            sanitized and forced to end in .py.
        python_code: Python source code to validate and write.
        plugins_dir: Optional output directory. It must resolve inside
            SAFE_BASE_DIR. Relative subdirectories are created inside
            SAFE_BASE_DIR.
        overwrite: Whether to replace an existing file with the same safe name.

    Returns:
        A dictionary with status, output path on success, and validation details.
    """
    try:
        validation = _validate_plugin_code(python_code)

        if not validation["valid"]:
            return {
                "status": "rejected",
                "reason": "Plugin code failed validation.",
                "validation": validation,
            }

        output_dir = _resolve_plugin_directory(plugins_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = _safe_filename(plugin_name)
        output_path = (output_dir / filename).resolve()

        if not _is_relative_to(output_path, SAFE_BASE_DIR):
            return {
                "status": "rejected",
                "reason": "Security exception: output path resolved outside of the plugin workspace.",
                "safe_base_dir": str(SAFE_BASE_DIR),
                "validation": validation,
            }

        if output_path.exists() and not overwrite:
            return {
                "status": "rejected",
                "reason": f"File already exists: {str(output_path)}",
                "suggestion": "Set overwrite=True or choose a different plugin_name.",
                "validation": validation,
            }

        tmp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=output_dir,
                prefix=f".{filename}.",
                suffix=".tmp",
                delete=False,
            ) as tmp_file:
                tmp_file.write(python_code)
                tmp_path = Path(tmp_file.name).resolve()

            if not _is_relative_to(tmp_path, SAFE_BASE_DIR):
                return {
                    "status": "rejected",
                    "reason": "Security exception: temporary path resolved outside of the plugin workspace.",
                    "safe_base_dir": str(SAFE_BASE_DIR),
                    "validation": validation,
                }

            tmp_path.replace(output_path)

        finally:
            if tmp_path and tmp_path.exists():
                tmp_path.unlink()

        return {
            "status": "success",
            "message": "Hermes plugin file written successfully. Review before loading.",
            "path": str(output_path),
            "safe_base_dir": str(SAFE_BASE_DIR),
            "validation": validation,
        }

    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to write Hermes plugin file: {str(e)}",
            "safe_base_dir": str(SAFE_BASE_DIR),
        }


@tool(
    name="validate_hermes_plugin_file",
    category="Tool Building",
    description=(
        "Reads and validates an existing Hermes plugin Python file from the restricted generated "
        "plugin workspace. Use this before enabling, moving, or loading a generated plugin."
    ),
)
def validate_hermes_plugin_file(file_path: str) -> dict[str, Any]:
    """
    Read and validate an existing Hermes plugin Python file without executing it.

    Args:
        file_path: File path or filename to validate. It must resolve inside
            SAFE_BASE_DIR. Passing just "my_plugin.py" validates
            SAFE_BASE_DIR / "my_plugin.py".

    Returns:
        A dictionary containing validation details and the resolved path.
    """
    try:
        path = _resolve_plugin_file(file_path)

        if not path.exists():
            return {
                "valid": False,
                "errors": [f"File does not exist: {str(path)}"],
                "warnings": [],
                "tool_functions": [],
                "tool_names": [],
                "toolset_exports": [],
                "path": str(path),
                "safe_base_dir": str(SAFE_BASE_DIR),
                "security_note": STRUCTURAL_VALIDATION_NOTE,
            }

        if not path.is_file():
            return {
                "valid": False,
                "errors": [f"Path is not a file: {str(path)}"],
                "warnings": [],
                "tool_functions": [],
                "tool_names": [],
                "toolset_exports": [],
                "path": str(path),
                "safe_base_dir": str(SAFE_BASE_DIR),
                "security_note": STRUCTURAL_VALIDATION_NOTE,
            }

        if path.suffix != ".py":
            return {
                "valid": False,
                "errors": [f"Refusing to validate non-Python file: {str(path)}"],
                "warnings": [],
                "tool_functions": [],
                "tool_names": [],
                "toolset_exports": [],
                "path": str(path),
                "safe_base_dir": str(SAFE_BASE_DIR),
                "security_note": STRUCTURAL_VALIDATION_NOTE,
            }

        size_bytes = path.stat().st_size
        if size_bytes > MAX_PLUGIN_FILE_BYTES:
            result = _code_too_large_error(size_bytes)
            result["path"] = str(path)
            result["safe_base_dir"] = str(SAFE_BASE_DIR)
            return result

        python_code = path.read_text(encoding="utf-8")
        validation = _validate_plugin_code(python_code)
        validation["path"] = str(path)
        validation["safe_base_dir"] = str(SAFE_BASE_DIR)
        validation["warnings"] = list(dict.fromkeys(validation["warnings"]))

        return validation

    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Failed to validate plugin file: {str(e)}"],
            "warnings": [],
            "tool_functions": [],
            "tool_names": [],
            "toolset_exports": [],
            "safe_base_dir": str(SAFE_BASE_DIR),
            "security_note": STRUCTURAL_VALIDATION_NOTE,
        }


HERMES_TOOL_BUILDER_TOOLS = Toolset(
    name="hermes_tool_builder_plugin",
    tools=[
        draft_hermes_tool_plugin,
        validate_hermes_plugin_code,
        write_hermes_plugin_file,
        validate_hermes_plugin_file,
    ],
)
