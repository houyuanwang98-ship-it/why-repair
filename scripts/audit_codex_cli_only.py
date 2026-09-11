#!/usr/bin/env python3
"""Fail when production Python reintroduces direct paid OpenAI API calls."""

from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_ROOTS = (ROOT / "harness", ROOT / "scripts", ROOT / "skills")
BANNED_IMPORTS = {"openai"}
BANNED_ENV_KEYS = {"OPENAI_API_KEY", "CODEX_API_KEY"}


def findings() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for base in PRODUCTION_ROOTS:
        for path in sorted(base.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".", 1)[0] in BANNED_IMPORTS:
                            rows.append({"path": path.relative_to(ROOT).as_posix(),
                                         "line": node.lineno, "kind": "banned_import"})
                elif isinstance(node, ast.ImportFrom):
                    if (node.module or "").split(".", 1)[0] in BANNED_IMPORTS:
                        rows.append({"path": path.relative_to(ROOT).as_posix(),
                                     "line": node.lineno, "kind": "banned_import"})
                elif isinstance(node, ast.Subscript):
                    key = node.slice.value if isinstance(node.slice, ast.Constant) else None
                    if key in BANNED_ENV_KEYS:
                        rows.append({"path": path.relative_to(ROOT).as_posix(),
                                     "line": node.lineno, "kind": "api_key_read", "key": key})
                elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if node.func.attr == "get":
                        key = node.args[0].value if node.args and isinstance(node.args[0], ast.Constant) else None
                        if key in BANNED_ENV_KEYS:
                            rows.append({"path": path.relative_to(ROOT).as_posix(),
                                         "line": node.lineno, "kind": "api_key_read", "key": key})
    return rows


def main() -> int:
    rows = findings()
    print(json.dumps({"runtime_policy": "saved_codex_cli_auth_only", "findings": rows},
                     ensure_ascii=False, indent=2))
    return 1 if rows else 0


if __name__ == "__main__":
    raise SystemExit(main())
