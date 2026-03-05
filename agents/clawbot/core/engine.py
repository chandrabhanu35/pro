"""
ClawBot Corporate Engine

The main execution engine that:
1. Receives a goal from the user (the "Owner")
2. CEO breaks it into strategic initiatives
3. VPs break initiatives into manager tasks
4. Managers execute the actual work
5. Results flow back up the chain
6. Dashboard gets real-time updates
"""

import json
import time
import os
import anyio
from typing import Optional

from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

from .hierarchy import (
    CorporateAgent,
    TaskAssignment,
    AgentStatus,
    Rank,
    build_default_corporation,
    AGENT_NAME_MAP,
)
from .state import CorporationState


class CorporateEngine:
    """Main engine that drives the corporate agent hierarchy."""

    def __init__(self, work_dir: str = ".", max_turns: int = 15):
        self.work_dir = os.path.abspath(work_dir)
        self.max_turns = max_turns
        self.agents = build_default_corporation()
        self.state = CorporationState()
        self.state.agents = self.agents

    def _log(self, agent_name: str, message: str):
        timestamp = time.strftime("%H:%M:%S")
        rank = ""
        for a in self.agents.values():
            if a.name.lower() == agent_name.lower():
                rank = f"[{a.rank.value.upper()}]"
                break
        print(f"  [{timestamp}] {rank} {agent_name}: {message}")
        self.state.add_log(agent_name, message)

    async def run(self, goal: str) -> str:
        """Execute a goal through the corporate hierarchy."""
        print("\n" + "=" * 65)
        print("  CLAWBOT CORPORATION — ACTIVATED")
        print("=" * 65)
        print(f"\n  OWNER'S DIRECTIVE: {goal}\n")
        print("=" * 65)

        self.state.current_goal = goal
        self.state.start_time = time.time()

        # Step 1: CEO plans
        ceo = self.agents["ceo-001"]
        ceo.status = AgentStatus.THINKING
        self._log("Atlas", f"Analyzing goal: {goal}")

        initiatives = await self._ceo_plan(goal)
        ceo.status = AgentStatus.DELEGATING
        self._log("Atlas", f"Created {len(initiatives)} initiatives")

        # Step 2: Delegate to VPs
        vp_tasks = []
        for init in initiatives:
            vp_name = init.get("vp", "nova")
            vp_id = AGENT_NAME_MAP.get(vp_name, "vp-eng-001")
            vp = self.agents.get(vp_id)
            if not vp:
                continue

            task = TaskAssignment(
                title=init.get("title", "Initiative"),
                description=init.get("description", ""),
                assigned_by="ceo-001",
                assigned_to=vp_id,
                earnings=init.get("estimated_earnings", 0.0),
            )
            vp_tasks.append((vp, task))

        # Step 3: VPs break down and delegate to managers
        all_manager_tasks = []
        for vp, vp_task in vp_tasks:
            vp.status = AgentStatus.WORKING
            vp.current_task = vp_task
            vp_task.status = "in_progress"
            self._log(vp.name, f"Working on: {vp_task.title}")
            self.state.notify()

            manager_tasks = await self._vp_delegate(vp, vp_task)
            all_manager_tasks.extend(manager_tasks)

            vp_task.status = "completed"
            vp.status = AgentStatus.DONE
            vp.current_task = None
            self._log(vp.name, f"Delegated {len(manager_tasks)} tasks to managers")

        # Step 4: Managers execute work
        print(f"\n{'─' * 65}")
        print(f"  EXECUTING {len(all_manager_tasks)} TASKS...")
        print(f"{'─' * 65}\n")

        for mgr, mgr_task in all_manager_tasks:
            mgr.status = AgentStatus.WORKING
            mgr.current_task = mgr_task
            mgr_task.status = "in_progress"
            self._log(mgr.name, f"Executing: {mgr_task.title}")
            self.state.notify()

            result = await self._execute_work(mgr, mgr_task)

            mgr_task.result = result
            mgr_task.status = "completed"
            mgr_task.completed_at = time.time()
            mgr.completed_tasks.append(mgr_task)
            mgr.total_earnings += mgr_task.earnings
            mgr.status = AgentStatus.DONE
            mgr.current_task = None
            self.state.total_earnings += mgr_task.earnings
            self._log(mgr.name, f"Completed: {mgr_task.title}")
            self.state.notify()

        # Step 5: CEO summarizes
        ceo.status = AgentStatus.REPORTING
        self._log("Atlas", "Generating final report...")
        summary = await self._ceo_summarize(goal, all_manager_tasks)

        self.state.end_time = time.time()
        elapsed = self.state.end_time - self.state.start_time

        print(f"\n{'=' * 65}")
        print(f"  MISSION COMPLETE — {elapsed:.0f}s elapsed")
        print(f"  Estimated Revenue: ${self.state.total_earnings:,.2f}")
        print(f"{'=' * 65}\n")
        print(summary)

        # Reset all agents
        for agent in self.agents.values():
            agent.status = AgentStatus.IDLE
        self.state.notify()

        return summary

    async def _ceo_plan(self, goal: str) -> list[dict]:
        """CEO breaks down the goal into VP-level initiatives."""
        ceo = self.agents["ceo-001"]

        prompt = (
            f"The owner has given you this directive:\n\n"
            f"GOAL: {goal}\n\n"
            f"Break this into strategic initiatives for your VPs.\n"
            f"Available VPs: nova (engineering), sage (business), luna (marketing)\n\n"
            f"Return ONLY a JSON object:\n"
            f'{{"initiatives": [{{"vp": "nova|sage|luna", "title": "...", '
            f'"description": "detailed instructions...", "priority": 1, '
            f'"estimated_earnings": 0.0}}]}}'
        )

        result = await self._run_agent(ceo, prompt)
        return self._parse_json_field(result, "initiatives")

    async def _vp_delegate(self, vp: CorporateAgent, task: TaskAssignment) -> list[tuple]:
        """VP breaks down initiative into manager tasks."""
        prompt = (
            f"You received this initiative from the CEO:\n\n"
            f"INITIATIVE: {task.title}\n"
            f"DETAILS: {task.description}\n\n"
            f"Break this into specific tasks for your managers.\n"
            f"Your managers: {', '.join(self.agents[sid].name.lower() for sid in vp.subordinate_ids)}\n\n"
            f"Return ONLY a JSON object:\n"
            f'{{"tasks": [{{"manager": "name", "title": "...", '
            f'"description": "very detailed instructions..."}}]}}'
        )

        result = await self._run_agent(vp, prompt)
        parsed_tasks = self._parse_json_field(result, "tasks")

        manager_tasks = []
        for t in parsed_tasks:
            mgr_name = t.get("manager", "").lower()
            mgr_id = AGENT_NAME_MAP.get(mgr_name)
            if not mgr_id or mgr_id not in self.agents:
                # Default to first subordinate
                mgr_id = vp.subordinate_ids[0] if vp.subordinate_ids else None
                if not mgr_id:
                    continue

            mgr = self.agents[mgr_id]
            mgr_task = TaskAssignment(
                title=t.get("title", "Task"),
                description=t.get("description", ""),
                assigned_by=vp.id,
                assigned_to=mgr_id,
                earnings=task.earnings / max(len(parsed_tasks), 1),
            )
            manager_tasks.append((mgr, mgr_task))

        return manager_tasks

    async def _execute_work(self, agent: CorporateAgent, task: TaskAssignment) -> str:
        """A manager executes actual work."""
        prompt = (
            f"You have been assigned this task by your manager:\n\n"
            f"TASK: {task.title}\n"
            f"DETAILS: {task.description}\n\n"
            f"Complete this task thoroughly. Create all necessary files in the "
            f"working directory. Produce production-quality output.\n"
            f"When creating files, put them in a project-specific subdirectory."
        )

        return await self._run_agent(agent, prompt)

    async def _ceo_summarize(self, goal: str, tasks: list[tuple]) -> str:
        """CEO generates final summary report."""
        ceo = self.agents["ceo-001"]

        task_results = []
        for mgr, task in tasks:
            task_results.append(
                f"- {mgr.name} ({mgr.role}): {task.title}\n"
                f"  Status: {task.status}\n"
                f"  Result: {task.result[:300] if task.result else 'No output'}"
            )

        prompt = (
            f"As CEO, summarize what your corporation accomplished.\n\n"
            f"ORIGINAL GOAL: {goal}\n\n"
            f"TASK RESULTS:\n" + "\n".join(task_results) + "\n\n"
            f"Provide:\n"
            f"1. Executive Summary\n"
            f"2. What was built/delivered\n"
            f"3. Files and artifacts created\n"
            f"4. Revenue potential/estimates\n"
            f"5. Next steps for the owner"
        )

        return await self._run_agent(ceo, prompt)

    async def _run_agent(self, agent: CorporateAgent, prompt: str) -> str:
        """Run a single agent and return its output."""
        result_text = ""
        try:
            async for message in query(
                prompt=prompt,
                options=ClaudeAgentOptions(
                    cwd=self.work_dir,
                    allowed_tools=agent.tools,
                    max_turns=self.max_turns,
                    system_prompt=agent.system_prompt,
                ),
            ):
                if isinstance(message, ResultMessage):
                    result_text = message.result
        except Exception as e:
            result_text = f"Agent error: {e}"
            self._log(agent.name, f"ERROR: {e}")

        return result_text

    def _parse_json_field(self, text: str, field: str) -> list[dict]:
        """Extract a JSON field from agent output."""
        try:
            # Try direct parse
            if "{" in text:
                start = text.find("{")
                end = text.rfind("}") + 1
                data = json.loads(text[start:end])
                return data.get(field, [])
        except (json.JSONDecodeError, KeyError):
            pass

        try:
            # Try finding JSON in code block
            if "```" in text:
                block = text.split("```")[1]
                if block.startswith("json"):
                    block = block[4:]
                data = json.loads(block.strip())
                return data.get(field, [])
        except (json.JSONDecodeError, KeyError, IndexError):
            pass

        # Fallback: create a single default task
        return [{"title": "Execute the directive", "description": text[:500]}]

    def get_dashboard_data(self) -> dict:
        """Get current state for the dashboard."""
        return {
            "goal": self.state.current_goal,
            "agents": {aid: a.to_dict() for aid, a in self.agents.items()},
            "total_earnings": self.state.total_earnings,
            "logs": self.state.logs[-50:],
            "elapsed": (time.time() - self.state.start_time) if self.state.start_time else 0,
        }
