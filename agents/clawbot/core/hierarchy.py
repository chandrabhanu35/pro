"""
Corporate Hierarchy Engine

Defines the agent hierarchy: CEO → VPs → Managers → Workers
Each agent has a role, rank, skills, and reporting chain.
"""

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Rank(Enum):
    CEO = "ceo"
    VP = "vp"
    MANAGER = "manager"
    WORKER = "worker"


class AgentStatus(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    DELEGATING = "delegating"
    REPORTING = "reporting"
    BLOCKED = "blocked"
    DONE = "done"


@dataclass
class TaskAssignment:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    description: str = ""
    assigned_by: str = ""
    assigned_to: str = ""
    status: str = "pending"  # pending, in_progress, completed, failed
    result: str = ""
    earnings: float = 0.0
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    subtasks: list["TaskAssignment"] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "assigned_by": self.assigned_by,
            "assigned_to": self.assigned_to,
            "status": self.status,
            "result": self.result[:200] if self.result else "",
            "earnings": self.earnings,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "subtasks": [s.to_dict() for s in self.subtasks],
        }


@dataclass
class CorporateAgent:
    """An agent in the corporate hierarchy."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    role: str = ""
    rank: Rank = Rank.WORKER
    department: str = ""
    skills: list[str] = field(default_factory=list)
    status: AgentStatus = AgentStatus.IDLE
    boss_id: Optional[str] = None
    subordinate_ids: list[str] = field(default_factory=list)
    current_task: Optional[TaskAssignment] = None
    completed_tasks: list[TaskAssignment] = field(default_factory=list)
    total_earnings: float = 0.0

    # Agent personality/prompt
    system_prompt: str = ""
    tools: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "rank": self.rank.value,
            "department": self.department,
            "skills": self.skills,
            "status": self.status.value,
            "boss_id": self.boss_id,
            "subordinate_ids": self.subordinate_ids,
            "current_task": self.current_task.to_dict() if self.current_task else None,
            "completed_tasks_count": len(self.completed_tasks),
            "total_earnings": self.total_earnings,
        }


# ── Pre-defined Corporate Structure ─────────────────────────────

def build_default_corporation() -> dict[str, CorporateAgent]:
    """Build the default corporate hierarchy."""

    agents = {}

    # ─── CEO ───
    ceo = CorporateAgent(
        id="ceo-001",
        name="Atlas",
        role="Chief Executive Officer",
        rank=Rank.CEO,
        department="Executive",
        skills=["strategy", "delegation", "planning", "decision_making"],
        system_prompt=(
            "You are Atlas, the CEO of ClawBot Corporation. You receive high-level "
            "goals from the owner (user) and break them into strategic initiatives. "
            "You delegate work to your VPs. You think like a startup CEO - fast, "
            "practical, revenue-focused. For every goal, create a concrete action "
            "plan with revenue estimates and timelines.\n\n"
            "Your VPs:\n"
            "- Nova (VP Engineering): Handles all technical work - apps, websites, APIs\n"
            "- Sage (VP Business): Handles revenue, clients, freelancing, sales\n"
            "- Luna (VP Marketing): Handles social media, content, branding, growth\n\n"
            "Return your delegation plan as JSON:\n"
            '{"initiatives": [{"vp": "nova|sage|luna", "title": "...", '
            '"description": "...", "priority": 1-5, "estimated_earnings": 0.0}]}'
        ),
        tools=["WebSearch", "WebFetch"],
    )
    agents[ceo.id] = ceo

    # ─── VPs ───
    vp_eng = CorporateAgent(
        id="vp-eng-001",
        name="Nova",
        role="VP of Engineering",
        rank=Rank.VP,
        department="Engineering",
        skills=["architecture", "code_review", "technical_planning", "devops"],
        boss_id="ceo-001",
        system_prompt=(
            "You are Nova, VP of Engineering at ClawBot. You receive technical "
            "initiatives from the CEO and break them into development tasks for "
            "your engineering managers. You make architecture decisions, choose "
            "tech stacks, and ensure quality.\n\n"
            "Your managers:\n"
            "- Bolt (Frontend Manager): React, Vue, mobile, UI/UX\n"
            "- Forge (Backend Manager): APIs, databases, servers, auth\n"
            "- Circuit (DevOps Manager): Docker, deployment, CI/CD, cloud\n\n"
            "Return task assignments as JSON:\n"
            '{"tasks": [{"manager": "bolt|forge|circuit", "title": "...", '
            '"description": "...", "tech_stack": ["..."]}]}'
        ),
        tools=["WebSearch", "WebFetch", "Read", "Glob"],
    )
    agents[vp_eng.id] = vp_eng

    vp_biz = CorporateAgent(
        id="vp-biz-001",
        name="Sage",
        role="VP of Business",
        rank=Rank.VP,
        department="Business",
        skills=["sales", "strategy", "pricing", "client_management"],
        boss_id="ceo-001",
        system_prompt=(
            "You are Sage, VP of Business at ClawBot. You handle revenue generation, "
            "client acquisition, and business strategy. You find opportunities to "
            "earn money through freelancing, digital products, and services.\n\n"
            "Your managers:\n"
            "- Hunter (Sales Manager): Finds clients, writes proposals, handles deals\n"
            "- Mint (Finance Manager): Pricing, invoicing, revenue tracking\n\n"
            "Return task assignments as JSON:\n"
            '{"tasks": [{"manager": "hunter|mint", "title": "...", '
            '"description": "...", "revenue_target": 0.0}]}'
        ),
        tools=["WebSearch", "WebFetch", "Read", "Write"],
    )
    agents[vp_biz.id] = vp_biz

    vp_mkt = CorporateAgent(
        id="vp-mkt-001",
        name="Luna",
        role="VP of Marketing",
        rank=Rank.VP,
        department="Marketing",
        skills=["branding", "content_strategy", "social_media", "growth"],
        boss_id="ceo-001",
        system_prompt=(
            "You are Luna, VP of Marketing at ClawBot. You handle all marketing, "
            "social media, content creation, and brand building.\n\n"
            "Your managers:\n"
            "- Pixel (Content Manager): Blog posts, copywriting, content calendars\n"
            "- Echo (Social Media Manager): Posts, engagement, platform strategy\n\n"
            "Return task assignments as JSON:\n"
            '{"tasks": [{"manager": "pixel|echo", "title": "...", '
            '"description": "..."}]}'
        ),
        tools=["WebSearch", "WebFetch", "Read", "Write"],
    )
    agents[vp_mkt.id] = vp_mkt

    # ─── Managers ───
    managers = [
        CorporateAgent(
            id="mgr-fe-001", name="Bolt", role="Frontend Manager",
            rank=Rank.MANAGER, department="Engineering", boss_id="vp-eng-001",
            skills=["react", "vue", "css", "mobile", "ui_ux"],
            system_prompt=(
                "You are Bolt, Frontend Engineering Manager. You build beautiful, "
                "responsive UIs. You write production-ready React/Vue/HTML code. "
                "Create complete, working frontend code with all files needed."
            ),
            tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
        ),
        CorporateAgent(
            id="mgr-be-001", name="Forge", role="Backend Manager",
            rank=Rank.MANAGER, department="Engineering", boss_id="vp-eng-001",
            skills=["python", "nodejs", "databases", "apis", "auth"],
            system_prompt=(
                "You are Forge, Backend Engineering Manager. You build robust APIs, "
                "databases, and server infrastructure. Write production-ready backend "
                "code with proper error handling, auth, and documentation."
            ),
            tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
        ),
        CorporateAgent(
            id="mgr-devops-001", name="Circuit", role="DevOps Manager",
            rank=Rank.MANAGER, department="Engineering", boss_id="vp-eng-001",
            skills=["docker", "ci_cd", "cloud", "deployment", "monitoring"],
            system_prompt=(
                "You are Circuit, DevOps Manager. You handle Docker configs, CI/CD "
                "pipelines, cloud deployments, and infrastructure. Create complete "
                "deployment-ready configurations."
            ),
            tools=["Read", "Write", "Edit", "Bash", "Glob"],
        ),
        CorporateAgent(
            id="mgr-sales-001", name="Hunter", role="Sales Manager",
            rank=Rank.MANAGER, department="Business", boss_id="vp-biz-001",
            skills=["proposals", "client_outreach", "negotiation", "freelancing"],
            system_prompt=(
                "You are Hunter, Sales Manager. You find freelance opportunities, "
                "write winning proposals, create service listings, and identify "
                "potential clients. Be practical and action-oriented."
            ),
            tools=["WebSearch", "WebFetch", "Write", "Read"],
        ),
        CorporateAgent(
            id="mgr-finance-001", name="Mint", role="Finance Manager",
            rank=Rank.MANAGER, department="Business", boss_id="vp-biz-001",
            skills=["pricing", "invoicing", "budgeting", "revenue_tracking"],
            system_prompt=(
                "You are Mint, Finance Manager. You handle pricing strategies, "
                "create invoices, track revenue, and manage budgets. Create "
                "spreadsheets and financial plans."
            ),
            tools=["Write", "Read", "WebSearch"],
        ),
        CorporateAgent(
            id="mgr-content-001", name="Pixel", role="Content Manager",
            rank=Rank.MANAGER, department="Marketing", boss_id="vp-mkt-001",
            skills=["copywriting", "blogging", "seo", "content_calendars"],
            system_prompt=(
                "You are Pixel, Content Manager. You write engaging blog posts, "
                "website copy, email campaigns, and content calendars. Focus on "
                "SEO and conversion-optimized content."
            ),
            tools=["WebSearch", "WebFetch", "Write", "Read"],
        ),
        CorporateAgent(
            id="mgr-social-001", name="Echo", role="Social Media Manager",
            rank=Rank.MANAGER, department="Marketing", boss_id="vp-mkt-001",
            skills=["social_media", "engagement", "hashtags", "growth_hacking"],
            system_prompt=(
                "You are Echo, Social Media Manager. You create social media posts, "
                "hashtag strategies, engagement plans, and growth tactics for all "
                "platforms (X, Instagram, LinkedIn, TikTok)."
            ),
            tools=["WebSearch", "WebFetch", "Write", "Read"],
        ),
    ]

    for mgr in managers:
        agents[mgr.id] = mgr

    # Wire up subordinate IDs
    ceo.subordinate_ids = [vp_eng.id, vp_biz.id, vp_mkt.id]
    vp_eng.subordinate_ids = ["mgr-fe-001", "mgr-be-001", "mgr-devops-001"]
    vp_biz.subordinate_ids = ["mgr-sales-001", "mgr-finance-001"]
    vp_mkt.subordinate_ids = ["mgr-content-001", "mgr-social-001"]

    return agents


# Map friendly names to IDs for delegation
AGENT_NAME_MAP = {
    "atlas": "ceo-001",
    "nova": "vp-eng-001",
    "sage": "vp-biz-001",
    "luna": "vp-mkt-001",
    "bolt": "mgr-fe-001",
    "forge": "mgr-be-001",
    "circuit": "mgr-devops-001",
    "hunter": "mgr-sales-001",
    "mint": "mgr-finance-001",
    "pixel": "mgr-content-001",
    "echo": "mgr-social-001",
}
