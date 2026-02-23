from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import subprocess, os, asyncio

server = Server("dev-tools")

# ── CONFIGURE THIS ───────────────────────────────────────────────────────────
PROJECTS_DIR = "/Users/namitpatel/D drive/Projects"
# ─────────────────────────────────────────────────────────────────────────────

# Tracks the currently active project across tool calls
active_project = None


def get_all_projects() -> dict[str, str]:
    """Returns a dict of {project_name: full_path} for all git repos in PROJECTS_DIR."""
    result = {}
    try:
        for name in os.listdir(PROJECTS_DIR):
            full_path = os.path.join(PROJECTS_DIR, name)
            if os.path.isdir(full_path) and os.path.isdir(os.path.join(full_path, ".git")):
                result[name.lower()] = full_path  # lowercase for fuzzy matching
    except Exception as e:
        pass
    return result


def resolve_project(name: str | None) -> tuple[str | None, str | None]:
    """
    Resolves a project name to its full path.
    - If name is given, fuzzy-matches against known projects.
    - If name is None, returns the currently active project.
    Returns (full_path, error_message).
    """
    global active_project

    projects = get_all_projects()

    if not projects:
        return None, f"No git projects found in {PROJECTS_DIR}"

    if name is None:
        if active_project:
            return active_project, None
        # Default to first project alphabetically if none set
        first = sorted(projects.values())[0]
        active_project = first
        return first, None

    # Fuzzy match: check if the given name is a substring of any project name
    name_lower = name.lower()
    matches = {k: v for k, v in projects.items() if name_lower in k}

    if not matches:
        available = ", ".join(sorted(projects.keys()))
        return None, f"No project matching '{name}' found. Available: {available}"

    if len(matches) == 1:
        path = list(matches.values())[0]
        active_project = path
        return path, None

    # Multiple matches — pick the closest (exact match wins, else first alphabetically)
    if name_lower in matches:
        path = matches[name_lower]
    else:
        path = sorted(matches.values())[0]

    active_project = path
    return path, None


def run(cmd: list, cwd: str) -> str:
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=60)
        return r.stdout or r.stderr or "Done."
    except subprocess.TimeoutExpired:
        return "Command timed out after 60 seconds."
    except Exception as e:
        return f"Error: {str(e)}"


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="list_projects",
            description="List all available git projects",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="git_status",
            description="Get git status of a project. If no project name given, uses the active project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "Project name (optional)"}
                }
            }
        ),
        Tool(
            name="git_log",
            description="Show last 10 commits of a project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "Project name (optional)"}
                }
            }
        ),
        Tool(
            name="git_pull",
            description="Pull latest changes for a project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "Project name (optional)"}
                }
            }
        ),
        Tool(
            name="create_branch",
            description="Create and switch to a new git branch.",
            inputSchema={
                "type": "object",
                "properties": {
                    "branch": {"type": "string", "description": "Name of the new branch"},
                    "project": {"type": "string", "description": "Project name (optional)"}
                },
                "required": ["branch"]
            }
        ),
        Tool(
            name="run_tests",
            description="Run the pytest test suite for a project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "Project name (optional)"}
                }
            }
        ),
        Tool(
            name="git_commit",
            description="Stage all changes and commit with a message.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Commit message"},
                    "project": {"type": "string", "description": "Project name (optional)"}
                },
                "required": ["message"]
            }
        ),
        Tool(
            name="git_push",
            description="Push committed changes to the remote repository.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "Project name (optional)"}
                }
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    global active_project

    # list_projects doesn't need a project path
    if name == "list_projects":
        projects = get_all_projects()
        if not projects:
            return [TextContent(type="text", text=f"No git projects found in {PROJECTS_DIR}")]
        lines = []
        for proj_name, path in sorted(projects.items()):
            marker = " ← active" if path == active_project else ""
            lines.append(f"{proj_name}{marker}")
        return [TextContent(type="text", text="\n".join(lines))]

    # All other tools need a resolved project path
    project_name = arguments.get("project", None)
    path, error = resolve_project(project_name)

    if error:
        return [TextContent(type="text", text=error)]

    project_label = os.path.basename(path)

    if name == "git_status":
        return [TextContent(type="text", text=f"[{project_label}]\n{run(['git', 'status'], path)}")]

    elif name == "git_log":
        return [TextContent(type="text", text=f"[{project_label}]\n{run(['git', 'log', '--oneline', '-10'], path)}")]

    elif name == "git_pull":
        return [TextContent(type="text", text=f"[{project_label}]\n{run(['git', 'pull'], path)}")]

    elif name == "create_branch":
        branch = arguments.get("branch")
        if not branch:
            return [TextContent(type="text", text="Please provide a branch name.")]
        return [TextContent(type="text", text=f"[{project_label}]\n{run(['git', 'checkout', '-b', branch], path)}")]

    elif name == "run_tests":
        return [TextContent(type="text", text=f"[{project_label}]\n{run(['python', '-m', 'pytest', '--tb=short', '-q'], path)}")]

    elif name == "git_commit":
        message = arguments.get("message")
        if not message:
            return [TextContent(type="text", text="Please provide a commit message.")]
        # Stage all changes first, then commit
        stage = run(["git", "add", "-A"], path)
        commit = run(["git", "commit", "-m", message], path)
        return [TextContent(type="text", text=f"[{project_label}]\n{stage}\n{commit}")]

    elif name == "git_push":
        # Get current branch name first, then push
        branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], path).strip()
        result = run(["git", "push", "origin", branch], path)
        return [TextContent(type="text", text=f"[{project_label}] → pushing branch '{branch}'\n{result}")]


async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())