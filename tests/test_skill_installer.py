import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/install_local_skill.py"
SPEC = importlib.util.spec_from_file_location("install_local_skill", SCRIPT)
INSTALLER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSTALLER)


class SkillInstallerTest(unittest.TestCase):
    def test_user_target_roots(self):
        with tempfile.TemporaryDirectory() as temp, mock.patch.object(
            INSTALLER.Path, "home", return_value=Path(temp)
        ), mock.patch.dict(INSTALLER.os.environ, {}, clear=True):
            expected = {
                "codex": Path(temp) / ".codex/skills",
                "claude": Path(temp) / ".claude/skills",
                "gemini": Path(temp) / ".gemini/skills",
                "opencode": Path(temp) / ".config/opencode/skills",
                "openclaw": Path(temp) / ".openclaw/skills",
                "agents": Path(temp) / ".agents/skills",
            }
            for target, root in expected.items():
                with self.subTest(target=target):
                    self.assertEqual(
                        root, INSTALLER.target_dest_root(target, "user")
                    )

    def test_workspace_target_roots(self):
        with tempfile.TemporaryDirectory() as temp:
            expected = {
                "codex": ".agents/skills",
                "claude": ".claude/skills",
                "gemini": ".gemini/skills",
                "opencode": ".opencode/skills",
                "openclaw": "skills",
                "agents": ".agents/skills",
            }
            for target, suffix in expected.items():
                with self.subTest(target=target):
                    self.assertEqual(
                        Path(temp).resolve() / suffix,
                        INSTALLER.target_dest_root(target, "workspace", temp),
                    )

    def test_install_and_restore_round_trip(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            skill = temp / "sample-skill"
            skill.mkdir()
            (skill / "SKILL.md").write_text("first", encoding="utf-8")
            dest_root = temp / "client/skills"
            backup_root = temp / "backups"

            first = INSTALLER.install_one(
                skill, dest_root, backup_root, "custom", "user"
            )
            self.assertFalse(first["dest_existed"])
            installed = Path(first["installed"])
            self.assertEqual("first", (installed / "SKILL.md").read_text())

            (skill / "SKILL.md").write_text("second", encoding="utf-8")
            second = INSTALLER.install_one(
                skill, dest_root, backup_root, "custom", "user"
            )
            self.assertTrue(second["dest_existed"])
            self.assertEqual("second", (installed / "SKILL.md").read_text())

            manifest = json.loads(Path(second["manifest"]).read_text())
            backup = Path(manifest["backup_dir"])
            self.assertEqual("first", (backup / "SKILL.md").read_text())


if __name__ == "__main__":
    unittest.main()
