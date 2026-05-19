#!/usr/bin/env python3
"""Sync repo-tracked Hermes mirror scripts into ~/.hermes/scripts on ALI-HERMES."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
import stat


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "shared-context" / "hermes-script-mirror-manifest.json"
DEFAULT_TARGET = Path.home() / ".hermes" / "scripts"


def sync_script(source: Path, target: Path) -> dict:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    target.chmod(stat.S_IMODE(source.stat().st_mode))
    return {
        "source": str(source),
        "target": str(target),
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--target-dir", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    results = []
    for name, meta in sorted((manifest.get("scripts") or {}).items()):
        source = args.repo_root / meta["source_relpath"]
        if not source.exists():
            raise FileNotFoundError(f"missing source file: {source}")
        target = args.target_dir / name
        results.append(sync_script(source, target))

    mirrored = dict(manifest)
    mirrored["managed_at"] = datetime.now(timezone.utc).astimezone().isoformat()
    args.target_dir.mkdir(parents=True, exist_ok=True)
    (args.target_dir / ".mirror-manifest.json").write_text(
        json.dumps(mirrored, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({"ok": True, "synced": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
