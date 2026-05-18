import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.runtime.audit_hermes_ai_cron_jobs import audit_jobs


class HermesAiCronGuardAuditTests(unittest.TestCase):
    def make_git_repo(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="cam-git-"))
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True, capture_output=True, text=True)
        return root

    def test_audit_accepts_git_tracked_prompt_and_manifest_script(self):
        repo = self.make_git_repo()
        (repo / "scripts").mkdir()
        (repo / "scripts" / "daily-promise-review.py").write_text("print('ok')\n", encoding="utf-8")
        subprocess.run(["git", "add", "scripts/daily-promise-review.py"], cwd=repo, check=True, capture_output=True, text=True)
        subprocess.run(["git", "commit", "-m", "add script"], cwd=repo, check=True, capture_output=True, text=True)

        hermes_home = Path(tempfile.mkdtemp(prefix="cam-hermes-"))
        scripts_dir = hermes_home / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "daily-promise-review.py").write_text("print('mirror')\n", encoding="utf-8")

        manifest = {
            "scripts": {
                "daily-promise-review.py": {
                    "repo_root": str(repo),
                    "source_relpath": "scripts/daily-promise-review.py",
                }
            }
        }
        jobs = [
            {
                "id": "job123",
                "name": "good",
                "prompt": f"Run `{repo}/scripts/daily-promise-review.py` and summarize.",
                "script": "daily-promise-review.py",
            }
        ]

        findings = audit_jobs(jobs, manifest, hermes_home)
        self.assertEqual(findings, [])

    def test_audit_rejects_untracked_prompt_script(self):
        repo = self.make_git_repo()
        (repo / "scripts").mkdir()
        target = repo / "scripts" / "consume_feedback.py"
        target.write_text("print('bad')\n", encoding="utf-8")

        hermes_home = Path(tempfile.mkdtemp(prefix="cam-hermes-"))
        manifest = {"scripts": {}}
        jobs = [
            {
                "id": "job456",
                "name": "bad",
                "prompt": f"Run `{target}` and report.",
            }
        ]

        findings = audit_jobs(jobs, manifest, hermes_home)
        self.assertEqual(len(findings), 1)
        self.assertIn("not git-tracked", findings[0].message)

    def test_audit_accepts_prompt_reference_to_registered_mirror_script(self):
        repo = self.make_git_repo()
        (repo / "scripts").mkdir()
        (repo / "scripts" / "daily-promise-review.py").write_text("print('ok')\n", encoding="utf-8")
        subprocess.run(["git", "add", "scripts/daily-promise-review.py"], cwd=repo, check=True, capture_output=True, text=True)
        subprocess.run(["git", "commit", "-m", "add script"], cwd=repo, check=True, capture_output=True, text=True)

        hermes_home = Path(tempfile.mkdtemp(prefix="cam-hermes-"))
        scripts_dir = hermes_home / "scripts"
        scripts_dir.mkdir()
        mirror = scripts_dir / "daily-promise-review.py"
        mirror.write_text("print('mirror')\n", encoding="utf-8")

        manifest = {
            "scripts": {
                "daily-promise-review.py": {
                    "repo_root": str(repo),
                    "source_relpath": "scripts/daily-promise-review.py",
                }
            }
        }
        jobs = [
            {
                "id": "job789",
                "name": "mirror-ref",
                "prompt": f"Run `{mirror}` and summarize.",
            }
        ]

        findings = audit_jobs(jobs, manifest, hermes_home)
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
