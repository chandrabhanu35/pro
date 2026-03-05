"""
Corporation State Manager

Tracks the real-time state of all agents, tasks, earnings, and logs.
Provides data for the dashboard and persistence.
"""

import json
import time
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LogEntry:
    timestamp: float
    agent_name: str
    message: str

    def to_dict(self) -> dict:
        return {
            "time": time.strftime("%H:%M:%S", time.localtime(self.timestamp)),
            "agent": self.agent_name,
            "message": self.message,
        }


@dataclass
class CorporationState:
    """Global state of the corporation."""
    current_goal: str = ""
    agents: dict = field(default_factory=dict)
    total_earnings: float = 0.0
    logs: list[LogEntry] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    _listeners: list = field(default_factory=list)

    def add_log(self, agent_name: str, message: str):
        entry = LogEntry(
            timestamp=time.time(),
            agent_name=agent_name,
            message=message,
        )
        self.logs.append(entry)

    def notify(self):
        """Notify listeners (dashboard) of state changes."""
        for listener in self._listeners:
            try:
                listener(self)
            except Exception:
                pass

    def on_change(self, callback):
        """Register a state change listener."""
        self._listeners.append(callback)

    def to_dict(self) -> dict:
        return {
            "goal": self.current_goal,
            "total_earnings": self.total_earnings,
            "agents": {
                aid: a.to_dict() for aid, a in self.agents.items()
            },
            "logs": [log.to_dict() for log in self.logs[-100:]],
            "elapsed": (
                (self.end_time or time.time()) - self.start_time
                if self.start_time else 0
            ),
        }

    def save(self, filepath: str = "clawbot_state.json"):
        """Save state to disk."""
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def get_org_chart(self) -> str:
        """Return ASCII org chart."""
        lines = []
        lines.append("ClawBot Corporation")
        lines.append("=" * 40)

        for agent in self.agents.values():
            if agent.rank.value == "ceo":
                indent = ""
            elif agent.rank.value == "vp":
                indent = "  ├── "
            else:
                indent = "  │   ├── "

            status_icon = {
                "idle": "○",
                "thinking": "◐",
                "working": "●",
                "delegating": "◈",
                "reporting": "◉",
                "blocked": "✗",
                "done": "✓",
            }.get(agent.status.value, "?")

            lines.append(
                f"{indent}{status_icon} {agent.name} — {agent.role} "
                f"[{agent.status.value}] ${agent.total_earnings:.0f}"
            )

        return "\n".join(lines)
