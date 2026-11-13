# AI workspace

A local, file-based hub for reusable agent instructions, skills, and project
contexts. It composes a prompt that you can paste into your AI assistant; it
does not connect to a model or execute the instructions.

## Get started

Python 3 is the only requirement. From this directory:

```sh
python3 ai_hub.py list agents
python3 ai_hub.py list skills
python3 ai_hub.py list contexts
python3 ai_hub.py render developer --task "Implement the next feature"
```

Edit `workspace.json` to make the starter definitions your own. Each agent,
skill, and context has a unique `name` within its category and a non-empty
`instructions` string. Agents can also specify lists of `skills` and `contexts`
by name. The included `project` context is a placeholder: replace it with the
relevant conventions and commands for your project.

For a particular task, add extra definitions without changing the agent:

```sh
python3 ai_hub.py render developer --skill code-review --context project --task "Review my changes"
```

Repeat `--skill` or `--context` to add more. Definitions already attached to
the agent are included only once. The output contains the agent, skills,
contexts, and optional task, in that order. Copy it into your assistant along
with any code or other information it needs.

To keep separate workspaces, copy `workspace.json` and pass its path before the
command:

```sh
python3 ai_hub.py --workspace /path/to/workspace.json render developer
```

Names are case-sensitive. Invalid definitions, duplicate names, and missing
references are reported as errors.