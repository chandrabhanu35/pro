"""
Git Worker — Agents commit their own work to Git.

Each agent's output gets committed to a project-specific branch
so the owner can review, merge, or roll back any agent's work.
"""

import subprocess
import os
import time


class GitWorker:
    """Handles git operations for agent-produced work."""

    def __init__(self, work_dir: str):
        self.work_dir = os.path.abspath(work_dir)

    def _run(self, *args: str) -> str:
        result = subprocess.run(
            ["git"] + list(args),
            cwd=self.work_dir,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def init_repo(self):
        """Initialize a git repo if one doesn't exist."""
        if not os.path.exists(os.path.join(self.work_dir, ".git")):
            self._run("init")
            self._run("checkout", "-b", "main")

    def create_branch(self, branch_name: str):
        """Create and switch to a new branch for agent work."""
        safe_name = branch_name.replace(" ", "-").lower()[:50]
        self._run("checkout", "-b", f"clawbot/{safe_name}")

    def commit_work(self, agent_name: str, task_title: str, files: list[str] = None):
        """Commit the agent's work."""
        if files:
            for f in files:
                self._run("add", f)
        else:
            self._run("add", "-A")

        timestamp = time.strftime("%Y-%m-%d %H:%M")
        message = f"[ClawBot:{agent_name}] {task_title}\n\nAutonomous agent work - {timestamp}"
        self._run("commit", "-m", message)

    def get_status(self) -> str:
        return self._run("status", "--short")

    def get_branch(self) -> str:
        return self._run("branch", "--show-current")

    def switch_to_main(self):
        """Switch back to main branch."""
        try:
            self._run("checkout", "main")
        except Exception:
            self._run("checkout", "master")
