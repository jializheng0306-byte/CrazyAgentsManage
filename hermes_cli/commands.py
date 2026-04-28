# -*- coding: utf-8 -*-
"""
Hermes CLI Commands -- Team memory and agent management CLI.

Provides command-line interface for:
- Team memory management (list, show, create, update)
- Role memory management
- Agent role inspection
- Task orchestration control
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


def cmd_team_list(args: argparse.Namespace) -> int:
    """List all teams and their memory stats."""
    from src.memory.team_memory import TeamMemoryManager

    manager = TeamMemoryManager()
    teams = manager.list_teams()

    if not teams:
        print("No teams found.")
        return 0

    print(f"{'Team':<20} {'Roles':<8} {'Docs':<8} {'Total Memory':<12}")
    print("-" * 52)
    for team in teams:
        print(
            f"{team['name']:<20} "
            f"{len(team.get('roles', [])):<8} "
            f"{len(team.get('docs', [])):<8} "
            f"{team.get('memory_count', 0):<12}"
        )

    return 0


def cmd_team_show(args: argparse.Namespace) -> int:
    """Show details of a specific team."""
    from src.memory.team_memory import TeamMemoryManager

    manager = TeamMemoryManager()
    team = manager.get_team(args.name)

    if not team:
        print(f"Team '{args.name}' not found.")
        return 1

    print(f"Team: {team['name']}")
    print(f"Path: {team['path']}")
    print()

    if team.get("memory"):
        print("=== Team Memory ===")
        print(team["memory"][:2000])
        if len(team["memory"]) > 2000:
            print(f"... ({len(team['memory'])} chars total)")
        print()

    if team.get("roles"):
        print("=== Roles ===")
        for role_name, content in team["roles"].items():
            lines = content.split("\n")
            preview = "\n".join(lines[:5])
            print(f"  {role_name}: {len(content)} chars")
            if len(lines) > 5:
                print(f"    Preview: {preview}...")
            else:
                print(f"    {preview}")
        print()

    if team.get("docs"):
        print("=== Documents ===")
        for doc_name, content in team["docs"].items():
            print(f"  {doc_name}: {len(content)} chars")
        print()

    return 0


def cmd_team_create(args: argparse.Namespace) -> int:
    """Create a new team with optional role memories."""
    from src.memory.team_memory import TeamMemoryManager

    manager = TeamMemoryManager()
    team_dir = manager._ensure_team(args.name)

    if args.roles:
        for role_name in args.roles.split(","):
            role_name = role_name.strip()
            manager.create_role_memory(args.name, role_name)
            print(f"Created role memory: {role_name}")

    if args.charter:
        manager.create_team_doc(args.name, "team-charter", args.charter)
        print("Created team charter.")

    print(f"Team '{args.name}' created at {team_dir}")
    return 0


def cmd_team_memory_update(args: argparse.Namespace) -> int:
    """Append content to a team's shared memory."""
    from src.memory.team_memory import TeamMemoryManager

    manager = TeamMemoryManager()

    if args.file:
        content = Path(args.file).read_text(encoding="utf-8")
    elif args.content:
        content = args.content
    else:
        print("Error: --file or --content required")
        return 1

    path = manager.append_to_team_memory(args.name, content)
    print(f"Updated team memory for '{args.name}' at {path}")
    return 0


def cmd_role_memory(args: argparse.Namespace) -> int:
    """Manage role memory within a team."""
    from src.memory.team_memory import TeamMemoryManager

    manager = TeamMemoryManager()

    if args.action == "show":
        content = manager.get_role_memory(args.team, args.role)
        if content:
            print(content)
        else:
            print(f"No memory found for role '{args.role}' in team '{args.team}'")
            return 1

    elif args.action == "append":
        if not args.content:
            print("Error: --content required for append")
            return 1
        path = manager.create_role_memory(args.team, args.role, args.content)
        print(f"Appended to role memory: {path}")

    elif args.action == "list":
        team = manager.get_team(args.team)
        if team and team.get("roles"):
            for role_name in team["roles"]:
                print(role_name)
        else:
            print(f"No roles found in team '{args.team}'")

    return 0


def cmd_roles_list(args: argparse.Namespace) -> int:
    """List all available agent roles."""
    from src.agent.agent_factory import available_roles

    roles = available_roles()
    print(f"{'Role':<15} {'Toolsets':<30} Description")
    print("-" * 80)
    for role in roles:
        toolsets = ", ".join(role["toolsets"])
        print(f"{role['name']:<15} {toolsets:<30} {role['description']}")

    return 0


def cmd_memory_summary(args: argparse.Namespace) -> int:
    """Show memory system summary."""
    from src.memory.memory_loader import MemoryLoader

    loader = MemoryLoader()
    summary = loader.get_memory_summary()

    print("=== Memory System Summary ===")
    for layer, info in summary.items():
        print(f"\n{layer}:")
        for key, value in info.items():
            if key == "teams":
                print(f"  teams: {', '.join(value) if value else 'none'}")
            else:
                print(f"  {key}: {value}")

    return 0


def cmd_experiences(args: argparse.Namespace) -> int:
    """List recent experience entries."""
    from src.memory.memory_improvement import SelfImprovementLoop

    loop = SelfImprovementLoop()
    experiences = loop.get_recent_experiences(
        limit=args.limit,
        experience_type=args.type,
    )

    if not experiences:
        print("No experiences found.")
        return 0

    for exp in experiences:
        print(f"[{exp['type']}] {exp['name']}")
        print(f"  Size: {exp['size']} bytes")
        if exp.get("preview"):
            preview = exp["preview"][:200].replace("\n", " ")
            print(f"  Preview: {preview}...")
        print()

    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="hermes",
        description="CrazyAgentsManage CLI -- Team memory and agent management",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # team list
    p_team_list = subparsers.add_parser("team-list", help="List all teams")
    p_team_list.set_defaults(func=cmd_team_list)

    # team show
    p_team_show = subparsers.add_parser("team-show", help="Show team details")
    p_team_show.add_argument("name", help="Team name")
    p_team_show.set_defaults(func=cmd_team_show)

    # team create
    p_team_create = subparsers.add_parser("team-create", help="Create a new team")
    p_team_create.add_argument("name", help="Team name")
    p_team_create.add_argument("--roles", help="Comma-separated role names")
    p_team_create.add_argument("--charter", help="Team charter content")
    p_team_create.set_defaults(func=cmd_team_create)

    # team memory update
    p_team_update = subparsers.add_parser("team-memory", help="Update team memory")
    p_team_update.add_argument("name", help="Team name")
    p_team_update.add_argument("--content", help="Content to append")
    p_team_update.add_argument("--file", help="File to append from")
    p_team_update.set_defaults(func=cmd_team_memory_update)

    # role memory
    p_role = subparsers.add_parser("role-memory", help="Manage role memory")
    p_role.add_argument("action", choices=["show", "append", "list"], help="Action")
    p_role.add_argument("--team", required=True, help="Team name")
    p_role.add_argument("--role", help="Role name")
    p_role.add_argument("--content", help="Content to append")
    p_role.set_defaults(func=cmd_role_memory)

    # roles list
    p_roles = subparsers.add_parser("roles", help="List available agent roles")
    p_roles.set_defaults(func=cmd_roles_list)

    # memory summary
    p_summary = subparsers.add_parser("memory-summary", help="Show memory system summary")
    p_summary.set_defaults(func=cmd_memory_summary)

    # experiences
    p_exp = subparsers.add_parser("experiences", help="List recent experiences")
    p_exp.add_argument("--limit", type=int, default=10, help="Max results")
    p_exp.add_argument("--type", choices=["pattern", "lesson"], help="Filter by type")
    p_exp.set_defaults(func=cmd_experiences)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if hasattr(args, "func"):
        return args.func(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
