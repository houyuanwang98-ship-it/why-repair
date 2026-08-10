# Cross-Agent Skill Packaging and Execution Standard

## 1. Scope

This repository follows the open Agent Skills specification for portable skill
packages. The objective is direct discovery and activation by compatible host
agents, including Codex, Claude Code, Gemini CLI, OpenCode, and OpenClaw.

This standard separates:

1. the portable Agent Skills package format;
2. client-specific discovery directories; and
3. the execution boundary between a host agent and bundled deterministic
   scripts.

Primary sources:

- Agent Skills specification: <https://agentskills.io/specification>
- Agent Skills overview: <https://agentskills.io/home>
- Claude Code skills: <https://code.claude.com/docs/en/slash-commands>
- Gemini CLI Agent Skills: <https://geminicli.com/docs/cli/using-agent-skills/>
- OpenCode Agent Skills: <https://dev.opencode.ai/docs/skills>
- OpenClaw skills: <https://docs.openclaw.ai/skills>

## 2. Normative package format

A skill is a directory whose name matches its `name` field:

```text
skill-name/
  SKILL.md
  scripts/
  references/
  assets/
```

Only `SKILL.md` is required. The other directories are optional.

`SKILL.md` must begin with YAML frontmatter:

```yaml
---
name: skill-name
description: What the skill does and when the host agent should activate it.
---
```

Requirements:

- `name` is 1-64 characters;
- `name` uses lowercase letters, digits, and single hyphens only;
- `name` matches the parent directory;
- `description` is nonempty and no longer than 1024 characters;
- `description` states both capability and activation conditions;
- optional standard fields are `license`, `compatibility`, `metadata`, and the
  experimental `allowed-tools` field;
- client-specific frontmatter is avoided in the portable core.

## 3. Progressive disclosure

The host agent discovers only `name` and `description` initially. When the task
matches the description, the host activates the skill and loads `SKILL.md`.
References and scripts are loaded only when the instructions require them.

Rules:

- keep `SKILL.md` below 500 lines and approximately 5000 tokens;
- move detailed contracts into focused files under `references/`;
- reference files with paths relative to the skill root;
- keep references one level deep from `SKILL.md`; and
- treat bundled scripts as optional deterministic helpers, not as the skill's
  model runtime.

## 4. Host-agent execution boundary

The host agent that activates the skill is the reasoning model. A portable
skill must not assume that a bundled Python process can access the host
session's model.

The required execution pattern is:

```text
host agent activates SKILL.md
  -> agent runs deterministic helper if useful
  -> helper emits unresolved obligations
  -> host agent adjudicates those obligations
  -> helper validates and merges the adjudications
  -> host agent reports the result
```

Bundled scripts may:

- parse files;
- construct proof obligations;
- retrieve deterministic candidates;
- validate schemas;
- verify that an adjudication uses allowed axioms; and
- merge validated results.

Bundled scripts must not require a provider API merely to access the host
agent. A provider-specific API mode may exist as an explicit optional adapter,
but it must not be the default portable workflow.

## 5. Portable adjudication exchange

When model reasoning is required, the helper emits a JSON adjudication template
containing stable proof and node identifiers, the local context, the target,
and the required response schema.

The host agent fills the response directly and reruns the helper with that JSON.
The helper then checks:

- response-schema validity;
- source and target preservation;
- allowed-axiom membership;
- missing or introduced assumptions;
- internal length and classification consistency; and
- deterministic output-schema validity.

Portable adjudication kinds are `graph`, `proof`, `calculation`, `diagnosis`,
and `theorem`. Run `diagnosis` only after proof or calculation adjudication has
produced a non-closed preliminary status. A diagnosis response must locate the
failed inference edge, cite concrete input evidence, independently return
`confirmed`, `false_positive`, or `uncertain`, and may replace the preliminary
error category. Reject vague or internally inconsistent explanations.

Emit `theorem` only when a diagnosis makes a positive or gap classification
depend on a specific theorem whose existence or applicability is disputed.
The host checks emitted local candidates first. If none verifies the theorem,
the host searches authoritative web sources, verifies the exact statement and
premises, and judges whether direct use is acceptable or an omitted bridge.
Do not run theorem search for disputes already settled by direct context,
calculation, target comparison, counterexample, or OCR reliability.

Missing, malformed, or unverifiable adjudications remain `undetermined`.
Emit only the earliest unresolved node of each proof in a round. After a host
response is validated, rebuild later node contexts before emitting the next
round. Repeat until no pending node remains or no progress is possible.

## 6. Discovery profiles

The open package format is portable, but discovery roots are client-specific.

| Client | User roots | Workspace roots |
| --- | --- | --- |
| Codex | `$CODEX_HOME/skills` or `~/.codex/skills` | `.agents/skills` |
| Claude Code | `~/.claude/skills` | `.claude/skills` |
| Gemini CLI | `~/.gemini/skills`, `~/.agents/skills` | `.gemini/skills`, `.agents/skills` |
| OpenCode | `~/.config/opencode/skills`, `~/.claude/skills`, `~/.agents/skills` | `.opencode/skills`, `.claude/skills`, `.agents/skills` |
| OpenClaw | `~/.agents/skills`, `~/.openclaw/skills` | `skills`, `.agents/skills` |
| Generic compatible agent | client-configured root | `.agents/skills` when supported |

`.agents/skills` is the preferred shared workspace target because Gemini CLI,
OpenCode, and OpenClaw document native discovery there. Client-native targets
remain available where required.

Automatic discovery cannot be guaranteed for an agent that does not implement
Agent Skills and does not expose a configurable skills directory. Such a client
can still read `SKILL.md` manually or execute the helper, but that is not native
skill activation.

## 7. OpenClaw-specific compatibility

OpenClaw discovers skills from workspace `skills/`, workspace
`.agents/skills`, user `~/.agents/skills`, managed `~/.openclaw/skills`, and
configured extra directories. It applies precedence, environment gating, and
per-agent allowlists.

Portable packages must not require `metadata.openclaw`. If OpenClaw-specific
metadata is later added, it must be optional and namespaced under
`metadata.openclaw`; the core workflow must continue to function without it.

OpenClaw allowlists and environment injection are deployment configuration,
not part of the portable mathematical skill logic.

## 8. Security and permissions

- Do not embed API keys or credentials.
- Do not treat a skill as a shell-authorization boundary.
- Keep deterministic scripts scoped to declared input and output paths.
- Require explicit activation or the host client's normal consent mechanism.
- Treat external theorem banks and model adjudications as untrusted inputs.
- Validate every structured response before it changes mathematical status.

## 9. Validation checklist

A release is portable only when:

1. `skills-ref validate <skill-dir>` or an equivalent reference validator
   passes;
2. the directory name and frontmatter name match;
3. the description triggers on proof diagnosis and does not over-trigger;
4. all resource references are relative to the skill root;
5. deterministic scripts run on Windows, macOS, and Linux with documented
   Python requirements;
6. offline mode does not require a provider SDK or API key;
7. unresolved work can be emitted for host-agent adjudication and resumed;
8. Codex, Claude, Gemini, OpenCode, OpenClaw, and generic installation profiles
   resolve to documented roots;
9. malformed host adjudication remains `undetermined`; and
10. schema and regression tests pass.
