#!/usr/bin/env python3
"""
ClawBot AI — Corporate Autonomous Agent System

Main entry point. Run from command line:

    python -m clawbot.main                          # Interactive mode
    python -m clawbot.main "Make me $5000"          # Direct goal
    python -m clawbot.main --dashboard              # Dashboard only
    python -m clawbot.main --docker "Build an app"  # With Docker workspace
"""

import sys
import os
import anyio

# Add parent dir to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawbot.core.engine import CorporateEngine
from clawbot.core.hierarchy import build_default_corporation
from clawbot.dashboard.app import run_dashboard, update_dashboard_state
from clawbot.workers.git_worker import GitWorker
from clawbot.workers.docker_worker import DockerWorker


BANNER = r"""
 ╔═══════════════════════════════════════════════════════════╗
 ║                                                           ║
 ║     ██████╗██╗      █████╗ ██╗    ██╗██████╗  ██████╗ ████████╗   ║
 ║    ██╔════╝██║     ██╔══██╗██║    ██║██╔══██╗██╔═══██╗╚══██╔══╝   ║
 ║    ██║     ██║     ███████║██║ █╗ ██║██████╔╝██║   ██║   ██║      ║
 ║    ██║     ██║     ██╔══██║██║███╗██║██╔══██╗██║   ██║   ██║      ║
 ║    ╚██████╗███████╗██║  ██║╚███╔███╔╝██████╔╝╚██████╔╝   ██║      ║
 ║     ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚═════╝  ╚═════╝    ╚═╝      ║
 ║                                                           ║
 ║     Corporate Autonomous AI Agent System                  ║
 ║     "Give me a goal. My agents will deliver."             ║
 ╚═══════════════════════════════════════════════════════════╝
"""

MENU = """
 Your AI Corporation:
 ────────────────────────────────────────────────
   CEO:  Atlas    — Strategic planning & delegation
   VP:   Nova     — Engineering (apps, websites, APIs)
   VP:   Sage     — Business (revenue, clients, sales)
   VP:   Luna     — Marketing (social, content, brand)
   MGR:  Bolt     — Frontend development
   MGR:  Forge    — Backend development
   MGR:  Circuit  — DevOps & deployment
   MGR:  Hunter   — Sales & client acquisition
   MGR:  Mint     — Finance & pricing
   MGR:  Pixel    — Content creation
   MGR:  Echo     — Social media
 ────────────────────────────────────────────────

 Example goals:
   > "Make me $5000 through freelancing"
   > "Build a SaaS landing page and set up social media"
   > "Create an e-commerce store for handmade jewelry"
   > "Start a YouTube channel about AI"
   > "Build a mobile app for fitness tracking"

 Type your goal (or 'quit' to exit):
"""


async def run_clawbot(
    goal: str,
    work_dir: str = ".",
    use_dashboard: bool = True,
    use_docker: bool = False,
    use_git: bool = True,
):
    """Run the ClawBot corporate agent system."""

    # Set up workspace
    workspace_dir = os.path.abspath(work_dir)
    os.makedirs(os.path.join(workspace_dir, "clawbot_output"), exist_ok=True)
    output_dir = os.path.join(workspace_dir, "clawbot_output")

    # Initialize git
    if use_git:
        git = GitWorker(output_dir)
        git.init_repo()
        safe_goal = goal[:30].replace(" ", "-").lower()
        git.create_branch(f"project-{safe_goal}")

    # Initialize Docker if requested
    if use_docker:
        docker = DockerWorker()
        if docker.is_docker_available():
            workspace = docker.create_workspace(f"project-{safe_goal[:20]}")
            print(f"  Docker workspace: {workspace}")
        else:
            print("  Docker not available, using local workspace")

    # Start dashboard
    if use_dashboard:
        run_dashboard(port=5050)

    # Create and run engine
    engine = CorporateEngine(work_dir=output_dir, max_turns=15)

    # Wire up dashboard updates
    if use_dashboard:
        def on_state_change(state):
            update_dashboard_state(state.to_dict())
        engine.state.on_change(on_state_change)

        # Push initial state
        update_dashboard_state(engine.state.to_dict())

    # Run the goal
    result = engine.run(goal)
    summary = await result

    # Commit results to git
    if use_git:
        git.commit_work("ClawBot", goal)

    return summary


async def interactive_mode():
    """Run ClawBot in interactive mode."""
    print(BANNER)
    print(MENU)

    while True:
        try:
            goal = input("\n > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nClawBot signing off.")
            break

        if not goal or goal.lower() in ("quit", "exit", "q"):
            print("\nClawBot signing off.")
            break

        await run_clawbot(goal)

        print("\n" + "=" * 60)
        print("  Ready for next goal. Type 'quit' to exit.")
        print("=" * 60)


async def main():
    args = sys.argv[1:]

    if not args:
        await interactive_mode()
        return

    # Parse flags
    use_dashboard = "--no-dashboard" not in args
    use_docker = "--docker" in args
    use_git = "--no-git" not in args

    # Remove flags from args
    goal_parts = [a for a in args if not a.startswith("--")]
    goal = " ".join(goal_parts)

    if not goal:
        await interactive_mode()
        return

    print(BANNER)
    await run_clawbot(
        goal=goal,
        use_dashboard=use_dashboard,
        use_docker=use_docker,
        use_git=use_git,
    )


if __name__ == "__main__":
    anyio.run(main)
