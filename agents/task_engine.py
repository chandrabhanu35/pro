"""
Autonomous Task Engine - The core brain that breaks down any high-level goal
into subtasks and runs specialized agents until the goal is complete.

Usage:
    from task_engine import AutonomousTaskEngine
    engine = AutonomousTaskEngine()
    await engine.run("Build me a portfolio website")
"""

import json
import time
import anyio
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AgentDefinition,
    ResultMessage,
)


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class SubTask:
    id: int
    title: str
    description: str
    agent_type: str
    status: TaskStatus = TaskStatus.PENDING
    result: str = ""
    depends_on: list[int] = field(default_factory=list)
    retries: int = 0
    max_retries: int = 2


@dataclass
class TaskPlan:
    goal: str
    subtasks: list[SubTask] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    final_summary: str = ""


# --- Agent definitions for different specializations ---

AGENT_REGISTRY = {
    "planner": AgentDefinition(
        description="Strategic planner that breaks down high-level goals into actionable subtasks.",
        prompt=(
            "You are an expert project planner. Given a high-level goal, break it down "
            "into concrete, actionable subtasks. For each subtask, specify:\n"
            "1. A clear title\n"
            "2. Detailed description of what needs to be done\n"
            "3. Which agent_type should handle it (choose from: researcher, coder, "
            "content_creator, social_media, business_strategist, designer, devops)\n"
            "4. Dependencies (which subtask IDs must complete first)\n\n"
            "Return your plan as a JSON array of objects with keys: "
            "title, description, agent_type, depends_on (list of indices).\n"
            "Return ONLY the JSON array, no other text."
        ),
        tools=["WebSearch", "WebFetch"],
    ),
    "researcher": AgentDefinition(
        description="Deep researcher that finds information, market data, competitors, and trends.",
        prompt=(
            "You are an expert researcher. Search the web thoroughly to gather "
            "comprehensive information on the given topic. Provide actionable insights, "
            "data points, competitor analysis, and recommendations. Always cite sources."
        ),
        tools=["WebSearch", "WebFetch"],
    ),
    "coder": AgentDefinition(
        description="Full-stack developer that writes, debugs, and deploys code.",
        prompt=(
            "You are a senior full-stack developer. Write clean, production-ready code. "
            "Create complete, working files - not snippets. Include proper error handling, "
            "comments, and follow best practices. Use modern frameworks and patterns. "
            "Always create complete project structures with all necessary config files."
        ),
        tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    ),
    "content_creator": AgentDefinition(
        description="Content writer that creates posts, articles, copy, and marketing material.",
        prompt=(
            "You are an expert content creator and copywriter. Create engaging, "
            "high-quality content optimized for the target platform. Consider SEO, "
            "audience engagement, and call-to-actions. Write content that converts."
        ),
        tools=["WebSearch", "WebFetch", "Write", "Read"],
    ),
    "social_media": AgentDefinition(
        description="Social media manager that plans content calendars, writes posts, and strategizes growth.",
        prompt=(
            "You are a social media marketing expert. Create comprehensive social media "
            "strategies including content calendars, post templates, hashtag strategies, "
            "engagement tactics, and growth plans. Consider platform-specific best practices "
            "for Instagram, Twitter/X, LinkedIn, TikTok, and YouTube."
        ),
        tools=["WebSearch", "WebFetch", "Write", "Read"],
    ),
    "business_strategist": AgentDefinition(
        description="Business strategist that finds opportunities, plans monetization, and creates business plans.",
        prompt=(
            "You are a business strategist and entrepreneur. Analyze opportunities, "
            "create monetization strategies, develop business plans, and identify "
            "revenue streams. Be practical and actionable - focus on things that can "
            "be started immediately with minimal investment."
        ),
        tools=["WebSearch", "WebFetch", "Write", "Read"],
    ),
    "designer": AgentDefinition(
        description="UI/UX designer that creates designs, wireframes, and style guides.",
        prompt=(
            "You are a UI/UX designer. Create detailed design specifications, "
            "wireframe descriptions, color palettes, typography choices, and component "
            "layouts. Output designs as CSS/HTML when possible, or as detailed specs "
            "that a developer can implement."
        ),
        tools=["Write", "Read", "WebSearch", "WebFetch"],
    ),
    "devops": AgentDefinition(
        description="DevOps engineer that handles deployment, CI/CD, and infrastructure.",
        prompt=(
            "You are a DevOps engineer. Set up deployment configurations, CI/CD pipelines, "
            "Docker configurations, and hosting. Create deployment-ready configurations "
            "using modern cloud platforms and tools."
        ),
        tools=["Read", "Write", "Edit", "Bash", "Glob"],
    ),
}


class AutonomousTaskEngine:
    """
    The main engine that takes a high-level goal and autonomously:
    1. Plans the work by breaking it into subtasks
    2. Assigns each subtask to a specialized agent
    3. Runs agents respecting dependencies
    4. Retries failed tasks
    5. Produces a final summary
    """

    def __init__(self, work_dir: str = ".", max_turns_per_agent: int = 15, verbose: bool = True):
        self.work_dir = work_dir
        self.max_turns = max_turns_per_agent
        self.verbose = verbose
        self.plan: Optional[TaskPlan] = None

    def _log(self, message: str):
        if self.verbose:
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] {message}")

    async def run(self, goal: str) -> str:
        """Run the full autonomous pipeline for a given goal."""
        self._log(f"GOAL: {goal}")
        print("=" * 60)

        # Step 1: Plan
        self._log("Phase 1: Planning...")
        self.plan = await self._create_plan(goal)
        self._print_plan()

        # Step 2: Execute subtasks
        self._log("Phase 2: Executing tasks...")
        self.plan.status = TaskStatus.IN_PROGRESS
        await self._execute_all_tasks()

        # Step 3: Summarize
        self._log("Phase 3: Generating final summary...")
        self.plan.final_summary = await self._generate_summary()
        self.plan.status = TaskStatus.COMPLETED

        print("\n" + "=" * 60)
        self._log("ALL TASKS COMPLETE")
        print("=" * 60)
        print(self.plan.final_summary)

        return self.plan.final_summary

    async def _create_plan(self, goal: str) -> TaskPlan:
        """Use the planner agent to break down the goal into subtasks."""
        plan_prompt = (
            f"Break down this goal into actionable subtasks:\n\n"
            f"GOAL: {goal}\n\n"
            f"Available agent types: researcher, coder, content_creator, "
            f"social_media, business_strategist, designer, devops\n\n"
            f"Return a JSON array. Each object must have: "
            f"title (string), description (string), agent_type (string), "
            f"depends_on (array of 0-based indices of tasks this depends on).\n"
            f"Return ONLY the JSON array."
        )

        raw_plan = ""
        async for message in query(
            prompt=plan_prompt,
            options=ClaudeAgentOptions(
                cwd=self.work_dir,
                allowed_tools=["WebSearch", "WebFetch"],
                agents={"planner": AGENT_REGISTRY["planner"]},
                max_turns=5,
            ),
        ):
            if isinstance(message, ResultMessage):
                raw_plan = message.result

        # Parse the plan
        plan = TaskPlan(goal=goal)
        try:
            # Extract JSON from the response
            json_str = raw_plan
            if "```" in json_str:
                json_str = json_str.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
                json_str = json_str.strip()
            # Try to find JSON array in the text
            start = json_str.find("[")
            end = json_str.rfind("]") + 1
            if start >= 0 and end > start:
                json_str = json_str[start:end]

            tasks_data = json.loads(json_str)
            for i, task_data in enumerate(tasks_data):
                plan.subtasks.append(SubTask(
                    id=i,
                    title=task_data.get("title", f"Task {i}"),
                    description=task_data.get("description", ""),
                    agent_type=task_data.get("agent_type", "researcher"),
                    depends_on=task_data.get("depends_on", []),
                ))
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            self._log(f"Plan parsing failed ({e}), creating default plan")
            plan.subtasks = [
                SubTask(id=0, title="Research the goal", description=f"Research: {goal}", agent_type="researcher"),
                SubTask(id=1, title="Create strategy", description=f"Create strategy for: {goal}", agent_type="business_strategist", depends_on=[0]),
                SubTask(id=2, title="Execute the plan", description=f"Execute: {goal}", agent_type="coder", depends_on=[1]),
            ]

        return plan

    def _print_plan(self):
        """Print the task plan in a readable format."""
        print(f"\n{'=' * 60}")
        print(f"TASK PLAN: {self.plan.goal}")
        print(f"{'=' * 60}")
        for task in self.plan.subtasks:
            deps = f" (after: {task.depends_on})" if task.depends_on else ""
            print(f"  [{task.id}] [{task.agent_type:20s}] {task.title}{deps}")
        print(f"{'=' * 60}\n")

    async def _execute_all_tasks(self):
        """Execute all subtasks, respecting dependencies."""
        while True:
            # Find tasks that are ready to run
            ready_tasks = [
                t for t in self.plan.subtasks
                if t.status == TaskStatus.PENDING and self._dependencies_met(t)
            ]

            if not ready_tasks:
                # Check if we're done or stuck
                pending = [t for t in self.plan.subtasks if t.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS)]
                if not pending:
                    break
                failed = [t for t in self.plan.subtasks if t.status == TaskStatus.FAILED]
                if failed and not ready_tasks:
                    self._log(f"BLOCKED: {len(failed)} tasks failed, no more tasks can run")
                    break
                # Some tasks are still in progress
                await anyio.sleep(1)
                continue

            # Run ready tasks (could be parallelized with task groups)
            for task in ready_tasks:
                await self._execute_task(task)

    def _dependencies_met(self, task: SubTask) -> bool:
        """Check if all dependencies for a task are completed."""
        for dep_id in task.depends_on:
            dep_task = self.plan.subtasks[dep_id]
            if dep_task.status != TaskStatus.COMPLETED:
                return False
        return True

    async def _execute_task(self, task: SubTask):
        """Execute a single subtask using the appropriate agent."""
        task.status = TaskStatus.IN_PROGRESS
        self._log(f"STARTING [{task.id}]: {task.title} (agent: {task.agent_type})")

        # Gather context from completed dependencies
        context_parts = []
        for dep_id in task.depends_on:
            dep = self.plan.subtasks[dep_id]
            context_parts.append(f"Results from '{dep.title}':\n{dep.result}")

        context = "\n\n---\n\n".join(context_parts) if context_parts else "No prior context."

        prompt = (
            f"You are working on a larger goal: {self.plan.goal}\n\n"
            f"Your current task: {task.title}\n"
            f"Description: {task.description}\n\n"
            f"Context from previous tasks:\n{context}\n\n"
            f"Complete this task thoroughly. Create any files needed in the "
            f"working directory. Be thorough and produce production-quality output."
        )

        agent_type = task.agent_type
        if agent_type not in AGENT_REGISTRY:
            agent_type = "researcher"  # fallback

        agent_def = AGENT_REGISTRY[agent_type]

        try:
            result_text = ""
            async for message in query(
                prompt=prompt,
                options=ClaudeAgentOptions(
                    cwd=self.work_dir,
                    allowed_tools=agent_def.tools,
                    max_turns=self.max_turns,
                ),
            ):
                if isinstance(message, ResultMessage):
                    result_text = message.result

            task.result = result_text
            task.status = TaskStatus.COMPLETED
            self._log(f"COMPLETED [{task.id}]: {task.title}")

        except Exception as e:
            task.retries += 1
            if task.retries <= task.max_retries:
                self._log(f"RETRY [{task.id}]: {task.title} (attempt {task.retries})")
                task.status = TaskStatus.PENDING  # will be picked up again
            else:
                task.status = TaskStatus.FAILED
                task.result = f"Failed after {task.retries} attempts: {e}"
                self._log(f"FAILED [{task.id}]: {task.title} - {e}")

    async def _generate_summary(self) -> str:
        """Generate a final summary of everything that was accomplished."""
        results = []
        for task in self.plan.subtasks:
            status_icon = {
                TaskStatus.COMPLETED: "[done]",
                TaskStatus.FAILED: "[FAILED]",
            }.get(task.status, "[?]")
            results.append(f"{status_icon} {task.title}:\n{task.result[:500]}")

        summary_prompt = (
            f"Summarize what was accomplished for the goal: {self.plan.goal}\n\n"
            f"Task results:\n" + "\n\n---\n\n".join(results) + "\n\n"
            f"Provide a clear summary of:\n"
            f"1. What was accomplished\n"
            f"2. Files/artifacts created\n"
            f"3. Next steps the user should take\n"
            f"4. Any tasks that failed and why"
        )

        summary = ""
        async for message in query(
            prompt=summary_prompt,
            options=ClaudeAgentOptions(
                cwd=self.work_dir,
                max_turns=3,
            ),
        ):
            if isinstance(message, ResultMessage):
                summary = message.result

        return summary


# --- Convenience functions for common goals ---

async def build_app(app_description: str, work_dir: str = ".") -> str:
    """Autonomous agent to build an app from description."""
    engine = AutonomousTaskEngine(work_dir=work_dir)
    return await engine.run(f"Build a complete application: {app_description}")


async def manage_social_media(business_description: str, work_dir: str = ".") -> str:
    """Autonomous agent to create a social media strategy and content."""
    engine = AutonomousTaskEngine(work_dir=work_dir)
    return await engine.run(
        f"Create a complete social media management plan with ready-to-post content "
        f"for: {business_description}"
    )


async def earn_money(skills_and_interests: str, work_dir: str = ".") -> str:
    """Autonomous agent to find and set up money-making opportunities."""
    engine = AutonomousTaskEngine(work_dir=work_dir)
    return await engine.run(
        f"Find practical ways to earn money online and create actionable plans "
        f"with all necessary setup for someone with these skills/interests: "
        f"{skills_and_interests}"
    )


async def build_website(site_description: str, work_dir: str = ".") -> str:
    """Autonomous agent to build a complete website."""
    engine = AutonomousTaskEngine(work_dir=work_dir)
    return await engine.run(f"Build a complete, deployable website: {site_description}")
