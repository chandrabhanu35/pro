"""
Website Builder Autonomous Agent
Builds complete, deployable websites from a description.
Handles design, code, content, and deployment config.

Usage:
    python website_builder_agent.py "A portfolio site for a photographer"
"""

import sys
import anyio
from task_engine import AutonomousTaskEngine


WEBSITE_GOAL_TEMPLATE = """
Build a COMPLETE, production-ready website: {site_description}

Deliver:
1. RESEARCH: Research best design patterns, competitor sites, and modern trends
   for this type of website
2. DESIGN: Create a complete design system - color palette, typography, spacing,
   component styles as CSS variables
3. BUILD: Create the full website with:
   - Responsive HTML/CSS (mobile-first)
   - JavaScript for interactivity
   - All pages fully built out with placeholder content
   - SEO meta tags, Open Graph tags
   - Accessibility (ARIA labels, semantic HTML)
   - Performance optimizations (lazy loading, minified assets)
4. CONTENT: Write compelling copy for all sections - headlines, descriptions,
   CTAs, about text, etc.
5. DEPLOY: Create deployment configs for Vercel/Netlify/GitHub Pages with
   a proper README and setup instructions

Save everything in a 'website_output/' directory with proper structure.
"""


async def run_website_builder(site_description: str):
    print("=" * 60)
    print("  AUTONOMOUS WEBSITE BUILDER AGENT")
    print("=" * 60)
    print(f"\n  Site: {site_description}\n")

    engine = AutonomousTaskEngine(
        work_dir=".",
        max_turns_per_agent=20,
        verbose=True,
    )

    goal = WEBSITE_GOAL_TEMPLATE.format(site_description=site_description)
    result = await engine.run(goal)
    return result


if __name__ == "__main__":
    desc = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "A modern portfolio website for a developer"
    anyio.run(run_website_builder, desc)
