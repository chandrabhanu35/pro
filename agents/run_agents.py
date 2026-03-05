#!/usr/bin/env python3
"""
Autonomous Task Agents - Main CLI Runner

Run any autonomous agent from the command line or use the interactive menu.

Usage:
    python run_agents.py                         # Interactive menu
    python run_agents.py social "My bakery"      # Social media agent
    python run_agents.py app "Todo app"          # App builder agent
    python run_agents.py money "Python skills"   # Money maker agent
    python run_agents.py website "Portfolio"      # Website builder agent
    python run_agents.py custom "Any goal here"  # Custom goal agent
"""

import sys
import anyio

from task_engine import AutonomousTaskEngine
from social_media_agent import run_social_media_agent
from app_builder_agent import run_app_builder
from money_maker_agent import run_money_maker
from website_builder_agent import run_website_builder


BANNER = """
╔══════════════════════════════════════════════════════════════╗
║             AUTONOMOUS TASK AGENTS                          ║
║                                                              ║
║  Give me a goal. I'll plan, execute, and deliver.            ║
║  Agents work autonomously until your task is complete.       ║
╚══════════════════════════════════════════════════════════════╝
"""

MENU = """
Available Agents:
─────────────────────────────────────────
  [1] Social Media Manager
      → Creates content calendars, posts, growth strategies

  [2] App Builder
      → Builds complete web/mobile applications

  [3] Money Maker
      → Finds income opportunities and sets them up

  [4] Website Builder
      → Builds complete, deployable websites

  [5] Custom Goal
      → Tell me anything - I'll figure out how to do it

  [0] Exit
─────────────────────────────────────────
"""


async def run_custom_goal(goal: str):
    """Run any arbitrary goal through the autonomous engine."""
    print("=" * 60)
    print("  AUTONOMOUS CUSTOM AGENT")
    print("=" * 60)
    print(f"\n  Goal: {goal}\n")

    engine = AutonomousTaskEngine(
        work_dir=".",
        max_turns_per_agent=15,
        verbose=True,
    )
    result = await engine.run(goal)
    return result


async def interactive_menu():
    """Show interactive menu and run selected agent."""
    print(BANNER)
    print(MENU)

    choice = input("Select an agent [1-5]: ").strip()

    if choice == "0":
        print("Goodbye!")
        return

    prompts = {
        "1": ("Social Media", "Describe your business/brand: "),
        "2": ("App Builder", "Describe the app you want to build: "),
        "3": ("Money Maker", "Describe your skills and interests: "),
        "4": ("Website Builder", "Describe the website you want: "),
        "5": ("Custom Goal", "What do you want to achieve? "),
    }

    if choice not in prompts:
        print("Invalid choice. Please select 1-5.")
        return

    name, prompt_text = prompts[choice]
    user_input = input(f"\n{prompt_text}").strip()

    if not user_input:
        print("No input provided. Exiting.")
        return

    print(f"\nStarting {name} Agent...\n")

    runners = {
        "1": lambda: run_social_media_agent(user_input),
        "2": lambda: run_app_builder(user_input),
        "3": lambda: run_money_maker(user_input),
        "4": lambda: run_website_builder(user_input),
        "5": lambda: run_custom_goal(user_input),
    }

    await runners[choice]()


async def main():
    args = sys.argv[1:]

    if not args:
        await interactive_menu()
        return

    command = args[0].lower()
    description = " ".join(args[1:]) if len(args) > 1 else ""

    if command == "social":
        desc = description or "A tech startup"
        await run_social_media_agent(desc)
    elif command == "app":
        desc = description or "A task management app"
        await run_app_builder(desc)
    elif command == "money":
        desc = description or "Programming and web development"
        await run_money_maker(desc)
    elif command == "website":
        desc = description or "A modern portfolio website"
        await run_website_builder(desc)
    elif command == "custom":
        if not description:
            description = input("What's your goal? ").strip()
        await run_custom_goal(description)
    else:
        # Treat the entire input as a custom goal
        full_goal = " ".join(args)
        await run_custom_goal(full_goal)


if __name__ == "__main__":
    anyio.run(main)
