"""
Social Media Autonomous Agent
Manages social media presence: content calendars, posts, hashtag strategies,
engagement plans, and growth tactics.

Usage:
    python social_media_agent.py "My fitness coaching business"
"""

import sys
import anyio
from task_engine import AutonomousTaskEngine


SOCIAL_MEDIA_GOAL_TEMPLATE = """
Create a COMPLETE social media management system for: {business}

Deliver these outputs:
1. RESEARCH: Analyze top competitors on social media, identify trending content formats,
   find the best posting times, and identify target audience demographics
2. STRATEGY: Create a 30-day content calendar with specific post ideas for
   Instagram, Twitter/X, LinkedIn, and TikTok
3. CONTENT: Write 10 ready-to-post social media posts with captions, hashtags,
   and engagement hooks for each platform
4. GROWTH PLAN: Create a follower growth strategy including engagement tactics,
   collaboration opportunities, and paid promotion recommendations
5. AUTOMATION: Create scripts or templates that can be reused for ongoing posting

Save all outputs as organized files in a 'social_media_output/' directory.
"""


async def run_social_media_agent(business: str):
    print("=" * 60)
    print("  AUTONOMOUS SOCIAL MEDIA AGENT")
    print("=" * 60)
    print(f"\n  Business: {business}\n")

    engine = AutonomousTaskEngine(
        work_dir=".",
        max_turns_per_agent=15,
        verbose=True,
    )

    goal = SOCIAL_MEDIA_GOAL_TEMPLATE.format(business=business)
    result = await engine.run(goal)
    return result


if __name__ == "__main__":
    business = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "A tech startup SaaS product"
    anyio.run(run_social_media_agent, business)
