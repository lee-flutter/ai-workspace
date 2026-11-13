import argparse
import json
import sys
from pathlib import Path


class WorkspaceError(ValueError):
    pass


def load_workspace(path):
    try:
        with Path(path).open(encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise WorkspaceError(f"Cannot load workspace: {error}") from error

    if not isinstance(data, dict):
        raise WorkspaceError("Workspace must be a JSON object")

    workspace = {}
    for kind in ("agents", "skills", "contexts"):
        entries = data.get(kind)
        if not isinstance(entries, list):
            raise WorkspaceError(f"'{kind}' must be a list")
        workspace[kind] = {}
        for entry in entries:
            if not isinstance(entry, dict):
                raise WorkspaceError(f"Each entry in '{kind}' must be an object")
            name = entry.get("name")
            instructions = entry.get("instructions")
            if not isinstance(name, str) or not name.strip():
                raise WorkspaceError(f"Each entry in '{kind}' needs a non-empty name")
            if not isinstance(instructions, str) or not instructions.strip():
                raise WorkspaceError(f"'{name}' needs non-empty instructions")
            if name in workspace[kind]:
                raise WorkspaceError(f"Duplicate {kind} name: {name}")
            if kind == "agents":
                for reference_kind in ("skills", "contexts"):
                    references = entry.get(reference_kind, [])
                    if not isinstance(references, list) or not all(
                        isinstance(reference, str) and reference.strip()
                        for reference in references
                    ):
                        raise WorkspaceError(
                            f"'{name}' {reference_kind} must be a list of names"
                        )
            workspace[kind][name] = entry

    for name, agent in workspace["agents"].items():
        for kind in ("skills", "contexts"):
            for reference in agent.get(kind, []):
                if reference not in workspace[kind]:
                    raise WorkspaceError(f"Agent '{name}' references unknown {kind}: {reference}")
    return workspace


def render(workspace, agent_name, skills=(), contexts=(), task=None):
    if agent_name not in workspace["agents"]:
        raise WorkspaceError(f"Unknown agent: {agent_name}")
    agent = workspace["agents"][agent_name]
    sections = [f"# Agent: {agent_name}\n\n{agent['instructions']}"]
    for kind, extras in (("skills", skills), ("contexts", contexts)):
        names = dict.fromkeys([*agent.get(kind, []), *extras])
        for name in names:
            if name not in workspace[kind]:
                raise WorkspaceError(f"Unknown {kind}: {name}")
            label = "Skill" if kind == "skills" else "Context"
            sections.append(f"# {label}: {name}\n\n{workspace[kind][name]['instructions']}")
    if task:
        sections.append(f"# Task\n\n{task}")
    return "\n\n".join(sections)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Compose instructions from an AI workspace")
    parser.add_argument("--workspace", default="workspace.json", help="path to workspace JSON")
    commands = parser.add_subparsers(dest="command", required=True)

    list_parser = commands.add_parser("list", help="list available definitions")
    list_parser.add_argument("kind", choices=("agents", "skills", "contexts"))

    render_parser = commands.add_parser("render", help="compose instructions for an agent")
    render_parser.add_argument("agent")
    render_parser.add_argument("--skill", action="append", default=[], help="add a skill")
    render_parser.add_argument("--context", action="append", default=[], help="add a context")
    render_parser.add_argument("--task", help="append the current task")

    args = parser.parse_args(argv)
    try:
        workspace = load_workspace(args.workspace)
        if args.command == "list":
            print("\n".join(workspace[args.kind]))
        else:
            print(render(workspace, args.agent, args.skill, args.context, args.task))
    except WorkspaceError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
