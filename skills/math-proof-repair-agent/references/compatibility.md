# Compatibility Reference

## Portable skill layout

The required entrypoint is `SKILL.md`. The checker and contract are bundled as:

```text
math-proof-repair-agent/
  SKILL.md
  scripts/
    check_obligations.py
    proof_repair/
      __init__.py
      contracts.py
      text.py
      io_session.py
      retrieval.py
      parsing.py
      graph.py
      subquestions.py
      calculation.py
      diagnosis.py
      adjudication.py
      codex_cli.py
      pipeline.py
      cli.py
  references/data_contract.md
  references/compatibility.md
  agents/openai.yaml
```

`agents/openai.yaml` is optional client metadata. Clients that do not recognize
it should ignore it. The mathematical workflow does not depend on that file.
The entrypoint imports the adjacent `proof_repair` package, so copy or install
the complete Skill directory rather than the entrypoint file alone.

## Supported operating systems

The checker and installer use Python and `pathlib` without shell scripts:

- Windows with Python 3.9 or newer;
- macOS with Python 3.9 or newer; and
- Linux with Python 3.9 or newer.

Use `python` or the platform's equivalent Python launcher. Commands in this
reference are shown on one line so they work in PowerShell, Command Prompt,
Bash, Zsh, and Fish after substituting paths.

The portable checker has no third-party dependencies. It emits unresolved
obligations for the active host agent and validates responses supplied through
`--adjudications`. The optional `--uncertain-policy model` adapter requires an
installed, authenticated Codex CLI. It uses saved CLI account authentication,
not an API SDK or key, and stores per-call evidence in `codex-evidence/`.

## Native discovery profiles

The repository installer supports these profiles:

| Target | User skill root | Workspace skill root |
| --- | --- | --- |
| Codex | `$CODEX_HOME/skills` or `~/.codex/skills` | `.agents/skills` |
| Claude Code | `$CLAUDE_CONFIG_DIR/skills` or `~/.claude/skills` | `.claude/skills` |
| Gemini CLI | `$GEMINI_CLI_HOME/skills` or `~/.gemini/skills` | `.gemini/skills` |
| OpenCode | `~/.config/opencode/skills` | `.opencode/skills` |
| OpenClaw | `~/.openclaw/skills` | `skills` |
| Agent Skills standard | `~/.agents/skills` | `.agents/skills` |

Install one user profile:

```text
python scripts/install_local_skill.py install --skill-dir skills/math-proof-repair-agent --target claude --scope user
```

Install every distinct user profile:

```text
python scripts/install_local_skill.py install --skill-dir skills/math-proof-repair-agent --target all --scope user
```

Install into a workspace:

```text
python scripts/install_local_skill.py install --skill-dir skills/math-proof-repair-agent --target gemini --scope workspace --workspace-root <project-directory>
```

For another CLI, use an explicit skill root:

```text
python scripts/install_local_skill.py install --skill-dir skills/math-proof-repair-agent --dest-root <client-skill-root>
```

If a client does not implement Agent Skills discovery, invoke
`scripts/check_obligations.py` directly or reference `SKILL.md` from that
client's persistent instruction file.

## Portability boundaries

No package can guarantee automatic discovery by every coding CLI. A client must
either support the Agent Skills `SKILL.md` convention, expose a configurable
skill directory, or allow direct script execution. The custom destination mode
covers configurable directories; direct execution covers clients without
native skill support.

The theorem bank and input dataset are external runtime inputs. They are not
hardcoded into the skill, which keeps the installed package portable but means
the caller must supply valid `--input` and `--theorem-bank` paths.
