import argparse
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path


TARGETS = ("codex", "claude", "gemini", "opencode", "openclaw", "agents")


def copy_tree(src, dst):
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")
    shutil.copytree(src, dst, ignore=ignore)


def target_dest_root(target, scope, workspace_root=None):
    if scope == "workspace":
        root = Path(workspace_root or Path.cwd()).expanduser().resolve()
        names = {
            "codex": ".agents/skills",
            "claude": ".claude/skills",
            "gemini": ".gemini/skills",
            "opencode": ".opencode/skills",
            "openclaw": "skills",
            "agents": ".agents/skills",
        }
        return root / names[target]

    home = Path.home()
    if target == "codex":
        return Path(os.environ.get("CODEX_HOME", home / ".codex")).expanduser() / "skills"
    if target == "claude":
        return Path(os.environ.get("CLAUDE_CONFIG_DIR", home / ".claude")).expanduser() / "skills"
    if target == "gemini":
        return Path(os.environ.get("GEMINI_CLI_HOME", home / ".gemini")).expanduser() / "skills"
    if target == "opencode":
        return Path(os.environ.get("XDG_CONFIG_HOME", home / ".config")).expanduser() / "opencode" / "skills"
    if target == "openclaw":
        return Path(os.environ.get("OPENCLAW_HOME", home / ".openclaw")).expanduser() / "skills"
    return home / ".agents" / "skills"


def timestamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def install_one(skill_dir, dest_root, backup_root, target, scope):
    skill_name = skill_dir.name
    dest = dest_root / skill_name
    backup_root.mkdir(parents=True, exist_ok=True)
    dest_root.mkdir(parents=True, exist_ok=True)

    run_id = f"{skill_name}-{target}-{scope}-{timestamp()}"
    backup_dir = backup_root / run_id
    manifest_path = backup_root / f"{run_id}.manifest.json"

    manifest = {
        "action": "install_skill",
        "skill_name": skill_name,
        "source": str(skill_dir),
        "dest_root": str(dest_root),
        "dest": str(dest),
        "backup_dir": str(backup_dir),
        "dest_existed": dest.exists(),
        "target": target,
        "scope": scope,
    }

    if dest.exists():
        copy_tree(dest, backup_dir)
        shutil.rmtree(dest)
    else:
        backup_dir.mkdir(parents=True, exist_ok=True)

    copy_tree(skill_dir, dest)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2), encoding="utf-8")

    return {
        "installed": str(dest),
        "manifest": str(manifest_path),
        "backup_dir": str(backup_dir),
        "dest_existed": manifest["dest_existed"],
        "target": target,
        "scope": scope,
    }


def install(args):
    skill_dir = Path(args.skill_dir).expanduser().resolve()
    if not (skill_dir / "SKILL.md").exists():
        raise SystemExit(f"Not a skill directory: {skill_dir}")

    backup_root = Path(args.backup_root).expanduser().resolve()
    if args.dest_root:
        roots = [("custom", Path(args.dest_root).expanduser().resolve())]
    else:
        targets = TARGETS if args.target == "all" else (args.target,)
        roots = [
            (target, target_dest_root(target, args.scope, args.workspace_root))
            for target in targets
        ]

    results = []
    seen_roots = set()
    for target, dest_root in roots:
        normalized = str(dest_root.resolve())
        if normalized in seen_roots:
            continue
        seen_roots.add(normalized)
        results.append(
            install_one(skill_dir, dest_root, backup_root, target, args.scope)
        )
    print(json.dumps({"installations": results}, ensure_ascii=True))


def restore(args):
    manifest_path = Path(args.manifest).expanduser().resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dest = Path(manifest["dest"])
    backup_dir = Path(manifest["backup_dir"])

    if dest.exists():
        shutil.rmtree(dest)

    if manifest.get("dest_existed"):
        copy_tree(backup_dir, dest)
        restored = str(dest)
    else:
        restored = None

    print(json.dumps({
        "restored_dest": restored,
        "removed_installed_dest": str(dest),
        "manifest": str(manifest_path),
    }, ensure_ascii=True))


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install")
    install_parser.add_argument("--skill-dir", required=True)
    install_parser.add_argument("--dest-root")
    install_parser.add_argument(
        "--target",
        choices=[*TARGETS, "all"],
        default="codex",
        help="Native CLI profile. Ignored when --dest-root is supplied.",
    )
    install_parser.add_argument("--scope", choices=["user", "workspace"], default="user")
    install_parser.add_argument("--workspace-root")
    install_parser.add_argument("--backup-root", default=".codex_skill_backups")

    restore_parser = subparsers.add_parser("restore")
    restore_parser.add_argument("--manifest", required=True)

    args = parser.parse_args()
    if args.command == "install":
        install(args)
    elif args.command == "restore":
        restore(args)


if __name__ == "__main__":
    main()
