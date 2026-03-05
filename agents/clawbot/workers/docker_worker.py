"""
Docker Worker — Manages isolated workspaces for agents.

Each project gets its own Docker container as an isolated workspace,
so agents can install dependencies, run servers, and test without
affecting the host system.
"""

import subprocess
import os
import json


class DockerWorker:
    """Manages Docker containers as agent workspaces."""

    def __init__(self, project_name: str = "clawbot"):
        self.project_name = project_name

    def _run(self, *args: str, check: bool = True) -> str:
        result = subprocess.run(
            list(args),
            capture_output=True,
            text=True,
        )
        if check and result.returncode != 0:
            return f"Error: {result.stderr.strip()}"
        return result.stdout.strip()

    def is_docker_available(self) -> bool:
        """Check if Docker is installed and running."""
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def create_workspace(self, workspace_name: str, base_image: str = "python:3.12-slim") -> dict:
        """Create an isolated Docker workspace for a project."""
        container_name = f"clawbot-{workspace_name}".lower().replace(" ", "-")[:40]

        # Check if container already exists
        existing = self._run(
            "docker", "ps", "-a", "--filter", f"name={container_name}",
            "--format", "{{.Names}}"
        )
        if container_name in existing:
            return {"container": container_name, "status": "already_exists"}

        # Create container
        self._run(
            "docker", "run", "-d",
            "--name", container_name,
            "-v", f"{container_name}-data:/workspace",
            "-w", "/workspace",
            base_image,
            "tail", "-f", "/dev/null",  # Keep container running
        )

        return {"container": container_name, "status": "created"}

    def exec_in_workspace(self, container_name: str, command: str) -> str:
        """Execute a command inside a workspace container."""
        return self._run(
            "docker", "exec", container_name,
            "bash", "-c", command,
            check=False,
        )

    def copy_to_workspace(self, container_name: str, local_path: str, remote_path: str = "/workspace/"):
        """Copy files into a workspace container."""
        self._run("docker", "cp", local_path, f"{container_name}:{remote_path}")

    def copy_from_workspace(self, container_name: str, remote_path: str, local_path: str):
        """Copy files from a workspace container."""
        self._run("docker", "cp", f"{container_name}:{remote_path}", local_path)

    def list_workspaces(self) -> list[dict]:
        """List all ClawBot workspace containers."""
        output = self._run(
            "docker", "ps", "-a",
            "--filter", "name=clawbot-",
            "--format", '{"name":"{{.Names}}","status":"{{.Status}}","image":"{{.Image}}"}',
            check=False,
        )
        workspaces = []
        for line in output.strip().split("\n"):
            if line:
                try:
                    workspaces.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return workspaces

    def stop_workspace(self, container_name: str):
        """Stop a workspace container."""
        self._run("docker", "stop", container_name, check=False)

    def remove_workspace(self, container_name: str):
        """Remove a workspace container and its volume."""
        self._run("docker", "stop", container_name, check=False)
        self._run("docker", "rm", container_name, check=False)
        self._run("docker", "volume", "rm", f"{container_name}-data", check=False)

    def cleanup_all(self):
        """Stop and remove all ClawBot workspaces."""
        workspaces = self.list_workspaces()
        for ws in workspaces:
            self.remove_workspace(ws["name"])
