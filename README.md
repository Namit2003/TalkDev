# 🎙️ Voice-Controlled Dev Workflow Assistant

A hands-free developer assistant that lets you control your entire git workflow using natural voice commands via your Mac microphone. Speak naturally — no fixed phrases, no wake words, no cloud.

## Demo

<video src="Demo.mp4" controls width="800">
  Your browser does not support the video tag.
</video>

[Download the demo video](Demo.mp4)

---

## How It Works

```
You speak into Mac mic
        ↓
voice-mode MCP (Whisper STT, runs locally)
        ↓
Claude Desktop (processes intent via LLM)
        ↓
Dev MCP Server (executes git/CLI commands)
        ↓
Claude speaks the result back (Kokoro TTS)
```

Everything runs **fully locally** — no cloud, no internet required after setup.

---

## What You Can Say

- *"What's the git status of my project?"*
- *"Create a new branch called feature-auth"*
- *"Run my tests and tell me what failed"*
- *"Show me the last 10 commits"*
- *"Pull the latest changes"*
- *"Commit everything with message 'fix login bug'"*
- *"Push my changes"*
- *"List all my projects"*
- *"Switch to my backend project, then run tests"*

---

## Prerequisites

- Mac (tested on macOS)
- [Claude Desktop](https://claude.ai/download)
- Python 3.10+
- `uv` / `uvx` package manager
- Homebrew

---

## Setup

### 1. Install system dependencies

```bash
brew install portaudio ffmpeg
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install voice-mode (local Whisper STT + Kokoro TTS)

```bash
uvx voice-mode-install
```

### 3. Clone this repo and set up Python environment

```bash
git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name
python -m venv venv
source venv/bin/activate
pip install mcp
```

### 4. Configure your projects directory

Open `dev_mcp_server.py` and set the folder where all your projects live:

```python
PROJECTS_DIR = "/Users/yourname/path/to/projects"
```

The server will automatically discover all git repos inside this folder. No need to register projects individually.

### 5. Configure Claude Desktop

Open `~/Library/Application Support/Claude/claude_desktop_config.json` and add:

```json
{
  "mcpServers": {
    "voicemode": {
      "command": "/Users/yourname/.local/bin/uvx",
      "args": ["--refresh", "voice-mode"]
    },
    "dev-tools": {
      "command": "/full/path/to/venv/bin/python",
      "args": ["/full/path/to/dev_mcp_server.py"]
    }
  }
}
```

> **Note:** Use full absolute paths for both `command` and `args` — Claude Desktop doesn't inherit your shell PATH. Run `which uvx` and `which python` inside your venv to get the correct paths.

### 6. Set permissions (optional but recommended)

Create `~/.claude/settings.json` to avoid confirmation prompts on every voice call:

```json
{
  "permissions": {
    "allow": [
      "mcp__voicemode__converse",
      "mcp__voicemode__listen_for_speech"
    ]
  }
}
```

### 7. Restart Claude Desktop

Quit and reopen Claude Desktop. You should see both `voicemode` and `dev-tools` listed as connected MCP servers.

---

## Usage

Open Claude Desktop and type once to start:

```
Start a voice conversation with me
```

Then just speak naturally. Claude will listen, run the appropriate git command, and speak the result back. Once you mention a project it becomes the **active project** — subsequent commands without a project name will run against it automatically.

---

## Available Tools

| What you say | Tool | What happens |
|---|---|---|
| "list my projects" | `list_projects` | Shows all git repos in your projects dir, marks active one |
| "git status" | `git_status` | Shows current repo state |
| "show commits" | `git_log` | Last 10 commits, one-liner |
| "git pull" | `git_pull` | Pulls latest from remote |
| "create branch X" | `create_branch` | `git checkout -b X` |
| "run my tests" | `run_tests` | Runs `pytest --tb=short`, summarizes failures |
| "commit with message X" | `git_commit` | Stages all changes + commits with your message |
| "push my changes" | `git_push` | Detects current branch, pushes to origin |

All tools accept an optional project name. If omitted, the active project is used.

---

## Project Structure

```
.
├── dev_mcp_server.py   # MCP server exposing git/CLI tools
├── venv/               # Python virtual environment
├── Demo.mov            # Demo video
└── README.md
```

---

## Troubleshooting

**MCP server shows "disconnected" in Claude Desktop**
- Make sure you're using full absolute paths in `claude_desktop_config.json`
- Run `python dev_mcp_server.py` manually in terminal to see any import/syntax errors
- Restart Claude Desktop fully after any config change

**`uvx` command not found in Claude Desktop**
- Run `which uvx` in terminal to get the full path
- Use that full path in the config instead of just `uvx`

**"No git projects found" error**
- Double check `PROJECTS_DIR` in `dev_mcp_server.py` is the correct path
- Make sure the folders inside it contain a `.git` directory