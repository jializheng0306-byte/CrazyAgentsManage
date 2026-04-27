---
name: build-fix
description: |
  Build error auto-recovery cycle. Adapted from OMX $build-fix for Trae IDE.
  Use when: compilation, lint, typecheck, or test fails during ralph/team execution.
  Automatically diagnoses, fixes, and retries up to a limit.
---

# Build-Fix (Auto-Recovery — Trae IDE Adaptation)

## Purpose

Automatically recover from **build, test, lint, or typecheck failures** without user intervention, up to a configurable retry limit.

## When Triggered

- Part of `ralph` main loop (automatic)
- Explicitly invoked when error detected
- After `RunCommand` returns non-zero exit

## Recovery Pipeline

```
ERROR DETECTED
     │
     ▼
┌─────────────────┐
│ 1. CAPTURE      │ ← Get full error output, exit code, signal
└────────┬────────┘
         ▼
┌─────────────────┐
│ 2. CLASSIFY     │ ← Categorize error type
└────────┬────────┘
         ▼
   ┌─────┴─────┐
   │           │
Compile    Test    Lint    Type    Runtime
Error     Fail   Error   Error   Error
   │           │       │        │        │
   ▼           ▼       ▼        ▼        ▼
┌────────┐ ┌────────┐ ┌──────┐ ┌────────┐ ┌────────┐
│3.FIX   │ │3.FIX   │ │3.FIX │ │3.FIX   │ │3.FIX   │
│compile │ │test    │ │lint  │ │type    │ │runtime │
└───┬────┘ └───┬────┘ └──┬───┘ └───┬────┘ └───┬────┘
    │          │         │         │         │
    ▼          ▼         ▼         ▼         ▼
┌───────────────────────────────────────────────────┐
│ 4. VERIFY                                           │
│  Re-run the failing command                        │
└──────────────────────┬────────────────────────────┘
                       │
                 ┌───────┴───────┐
                 │ Pass?        │
                 └───┬───────┬───┘
                   Yes       No
                    │   ┌──────┘
                    │   │ retry < 3?
                    │   ├── Yes → Loop to CLASSIFY
                    │   └── No ──→ ESCALATE to user
                    ▼
              ┌───────────┐
              │ 5. ADVANCE │
              └───────────┘
```

## Error Classification

| Category | Examples | Default Fix Strategy |
|----------|---------|---------------------|
| **Compile** | Syntax errors, missing imports, type mismatches | Read error, locate file, apply targeted fix |
| **Test** | Assertion failure, mock issues, flaky test | Analyze failure, fix assertion or implementation |
| **Lint** | Style violations, unused code, complexity | Auto-fix if available, manual fix otherwise |
| **Type** | Type errors, missing generics, wrong signatures | Add/fix type annotations |
| **Runtime** | Null pointer, timeout, missing env | Debug runtime state, add guard/fix config |

## Retry Limits

- **Per-step**: Max 3 recovery attempts (OMX default)
- **Per-session**: Max 10 total build-fix cycles across all steps
- **Same-error shortcut**: If same error occurs twice → escalate immediately

## Escalation

When recovery exhausted:
1. Stop current step
2. Report to user with:
   - Original error
   - Fix attempts made
   - Why auto-recovery failed
   - Suggested manual action
3. Update `.omx/state.md` status → `blocked`
4. Wait for user guidance

## Integration with Harness

Record build-fix events in trace:
- Successful recovery → note in success trace as "recovered: {error_type}"
- Failed recovery → note in failure trace with diagnosis
- Repeated same error → candidate for `harness/memory/failure-patterns.md`
