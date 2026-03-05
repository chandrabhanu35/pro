"""
Money Maker Autonomous Agent
Finds practical online income opportunities and creates everything needed
to start earning - from strategy to actual implementation.

Usage:
    python money_maker_agent.py "I know Python and web development"
"""

import sys
import anyio
from task_engine import AutonomousTaskEngine


MONEY_MAKER_GOAL_TEMPLATE = """
Find and SET UP practical ways to earn money online for someone with these
skills and interests: {skills}

Deliver these concrete outputs:
1. OPPORTUNITY RESEARCH: Find 10+ realistic online income opportunities that match
   these skills. Include estimated earnings, time investment, and difficulty level.
   Research current market demand and trending opportunities in 2025-2026.
2. TOP 3 STRATEGY: Create detailed action plans for the top 3 most promising
   opportunities including step-by-step setup guides
3. FREELANCING SETUP: Create professional profiles/templates for freelancing platforms
   (Fiverr, Upwork, Freelancer) - including bio, service descriptions, pricing strategy
4. DIGITAL PRODUCTS: If applicable, create templates or starter files for digital
   products that can be sold (templates, tools, courses outline)
5. PASSIVE INCOME: Research and plan passive income streams (affiliate marketing,
   content monetization, SaaS ideas) with actionable first steps
6. IMPLEMENTATION: Create actual files, scripts, or templates that the user can
   immediately use to start earning

Save all outputs in a 'money_making_output/' directory with clear organization.
"""


async def run_money_maker(skills: str):
    print("=" * 60)
    print("  AUTONOMOUS MONEY MAKER AGENT")
    print("=" * 60)
    print(f"\n  Skills/Interests: {skills}\n")

    engine = AutonomousTaskEngine(
        work_dir=".",
        max_turns_per_agent=15,
        verbose=True,
    )

    goal = MONEY_MAKER_GOAL_TEMPLATE.format(skills=skills)
    result = await engine.run(goal)
    return result


if __name__ == "__main__":
    skills = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Python programming and data analysis"
    anyio.run(run_money_maker, skills)
