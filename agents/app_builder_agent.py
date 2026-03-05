"""
App Builder Autonomous Agent
Takes an app idea and builds a complete application autonomously -
mobile app (React Native), web app (Next.js/React), or API backend.

Usage:
    python app_builder_agent.py "A todo app with authentication and cloud sync"
"""

import sys
import anyio
from task_engine import AutonomousTaskEngine


APP_BUILDER_GOAL_TEMPLATE = """
Build a COMPLETE, working application: {app_idea}

Follow this process:
1. RESEARCH: Research the best tech stack, similar apps, and architecture patterns
2. DESIGN: Create the UI/UX design specification with component layouts and user flows
3. SETUP: Create the project structure with all config files (package.json, etc.)
4. BACKEND: Build the backend API with database models, routes, and authentication
5. FRONTEND: Build the frontend with all pages, components, and state management
6. INTEGRATION: Connect frontend to backend, handle error states and loading
7. DEPLOYMENT: Create Docker/deployment configs for production deployment

Requirements:
- Use modern frameworks (React/Next.js for web, React Native for mobile, FastAPI/Express for backend)
- Include authentication if applicable
- Write clean, documented code
- Create a proper README with setup instructions
- All code should be in a properly structured project directory

Save everything in an 'app_output/' directory with proper project structure.
"""


async def run_app_builder(app_idea: str):
    print("=" * 60)
    print("  AUTONOMOUS APP BUILDER AGENT")
    print("=" * 60)
    print(f"\n  App Idea: {app_idea}\n")

    engine = AutonomousTaskEngine(
        work_dir=".",
        max_turns_per_agent=20,
        verbose=True,
    )

    goal = APP_BUILDER_GOAL_TEMPLATE.format(app_idea=app_idea)
    result = await engine.run(goal)
    return result


if __name__ == "__main__":
    idea = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "A task management app with teams and real-time updates"
    anyio.run(run_app_builder, idea)
