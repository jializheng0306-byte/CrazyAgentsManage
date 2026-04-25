# Harness Infrastructure

This directory is the canonical repository-owned learning layer for CrazyAgentsManage.

## Principles

1. `harness/` is repository fact, not private agent scratch space.
2. `.omx/` is runtime/session-local and must not replace harness artifacts.
3. Codex/HermesAgent collaboration lessons become durable only after they are written here.

## Layout

- `exec-plans/` — round or slice execution plans
- `trace/failures/` — structured failed-round records
- `trace/successes/` — structured successful-round records
- `memory/situational.md` — current environment constraints
- `memory/procedural.md` — validated process improvements
- `memory/failure-patterns.md` — repeated failure registry

## Default Rule

If the current session learns something only relevant to this one runtime, keep it in `.omx/`.

If the lesson should survive this session and guide future work, promote it into `harness/`.

