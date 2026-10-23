# CommitSage

> Your AI-powered companion for crafting perfect Git commit messages

CommitSage is a smart CLI tool that analyzes your Git changes and helps you write clear, consistent, and meaningful commit messages. Say goodbye to "fix stuff" and "wip" commits!

## Features

- **Smart Change Analysis** — Inspects staged and unstaged changes automatically
- **AI-Powered Suggestions** — Uses Claude or OpenAI models to generate high-quality conventional commit messages
- **Beautiful Terminal UI** — Powered by Rich for a delightful command-line experience
- **Mixed Change Detection** — Identifies unrelated changes and suggests splitting them into separate commits
- **Configurable** — Customize AI model, commit style, and ignore patterns
- **Fast & Local-First** — Designed for efficient daily Git workflows
- **Zero Configuration** — Works out of the box with sensible defaults

## Installation

### Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- Git repository
- Anthropic or OpenAI API key

### Install from source

```bash
# Clone the repository
git clone <repository-url>
cd commit-sage

# Install dependencies
uv sync

# Install dev dependencies (for testing)
uv sync --dev
```

### Install as a global tool

```bash
# Install commit-sage as a globally available command
uv tool install .

# Verify installation
commit-sage --version
```

### Choose a model profile

CommitSage talks to a model through a **profile**. Out of the box there are two, `claude` (Anthropic API) and `openai` (OpenAI API), both billed per token. Add your own in `~/.config/commit-sage/config.toml`; [config/profiles.example.toml](config/profiles.example.toml) shows every kind:

| Kind | `provider` | Example |
| --- | --- | --- |
| Per token (API key) | `anthropic` or `openai` | Anthropic, OpenAI, or any hosted OpenAI-compatible API via `base_url` (OpenRouter, Groq, ...) |
| Local | `openai` with `base_url` | llama.cpp / llama-swap, Ollama, LM Studio on `127.0.0.1` |
| Subscription | `command` | A logged-in CLI that reads the prompt on stdin: `claude -p` (Claude Code), `codex exec` (ChatGPT) |

```bash
mkdir -p ~/.config/commit-sage
cp config/profiles.example.toml ~/.config/commit-sage/config.toml   # then edit default_profile
commit-sage profiles                                                # list profiles, * marks the active one
```

API keys never go in the profile file. A profile names the variable (`api_key_env = "ANTHROPIC_API_KEY"`), and CommitSage reads it from the environment, from `~/.config/commit-sage/.env`, or from a `.env` in the current directory:

```bash
echo 'ANTHROPIC_API_KEY=your-api-key-here' >> ~/.config/commit-sage/.env
```

## Quick Start

```bash
# Stage your changes
git add .

# Generate a commit message
commit-sage suggest

# Review the suggestion and commit
commit-sage commit
```

That's it! CommitSage will analyze your changes and suggest a well-structured commit message.

## Usage

### Basic Commands

```bash
# Get a commit message suggestion for staged changes
commit-sage suggest

# Generate and create a commit in one step
commit-sage commit

# Skip confirmation prompt (useful for scripts)
commit-sage commit --yes

# Auto-stage all unstaged/untracked files, then commit
commit-sage commit --all

# Analyze staged and unstaged changes without committing
commit-sage analyze

# Use another model profile for one run (local, per token, subscription)
commit-sage suggest --profile claude-code

# List profiles; * marks the active one
commit-sage profiles

# Display version
commit-sage --version
```

### Example Output

```
Analyzing changes...

 Suggested Commit
 feat(cli): add interactive commit confirmation

 Body
 Adds user confirmation prompt before creating commits to
 prevent accidental commits

Confidence: ████████░░ 82%

Create this commit? [Y/n]:
```

### Mixed Changes

When staged files span unrelated areas (e.g. backend + docs + frontend), CommitSage detects this and offers to split them into separate commits:

```
Mixed changes detected — your staged changes span multiple unrelated areas.

 #   Area       Files
 1   backend    src/auth.py, src/models.py
 2   docs       README.md
 3   frontend   app.css

Options:
  a   Proceed with all changes (one commit)
  1   Include only backend files
  2   Include only docs files
  3   Include only frontend files
  d   Discard specific staged files (will confirm before any change)
  q   Quit

Your choice [a]:
```

## Configuration

| Setting | Where | Default |
| --- | --- | --- |
| Profile file | `~/.config/commit-sage/config.toml`, or the path in `COMMIT_SAGE_CONFIG` | built-in `claude` and `openai` profiles only |
| Active profile | `--profile NAME`, then `COMMIT_SAGE_PROFILE`, then `default_profile` in the file | `claude` |
| Model | `--model`, then `COMMIT_SAGE_MODEL`, then the profile's `model`, then the provider default | `claude-haiku-4-5-20251001` / `gpt-5-mini` |
| Max diff lines | `COMMIT_SAGE_MAX_DIFF_LINES` | `300` |
| Commit style | `COMMIT_SAGE_COMMIT_STYLE` | `conventional` |

Environment variables can also live in `~/.config/commit-sage/.env` or a `.env` in the current directory (the latter wins).

Profile fields:

| Field | Used by | Meaning |
| --- | --- | --- |
| `provider` | all | `anthropic`, `openai` (any OpenAI-compatible Responses API) or `command` |
| `model` | all | Model name; for `command`, substituted into `{model}` in the argv |
| `api_key_env` | `anthropic`, `openai` | Name of the variable holding the key |
| `api_key` | `openai` | Literal key, only for local servers that ignore it |
| `base_url` | `openai` | Endpoint; empty means api.openai.com |
| `command` | `command` | Argv that reads the prompt on stdin and prints the reply on stdout |
| `description` | all | Shown by `commit-sage profiles` |

## Architecture

CommitSage is built with a modular architecture:

- **CLI Layer** (`cli.py`) — Handles user commands and terminal UI
- **Git Tools** (`git_tools.py`) — Interfaces with Git repositories
- **Summarizer** (`summarizer.py`) — Analyzes and summarizes changes
- **Classifiers** (`classifiers.py`) — Detects change patterns and categories
- **LLM Client** (`llm_client.py`) — Communicates with AI providers
- **Commit Generator** (`commit_generator.py`) — Creates structured commit messages
- **Prompt Builder** (`prompt_builder.py`) — Crafts effective AI prompts
- **Executor** (`executor.py`) — Handles confirmation and git commit execution

## Commit Message Format

CommitSage generates **Conventional Commits** following this format:

```
<type>(<scope>): <subject>

<body>
```

### Types

- `feat` — New feature
- `fix` — Bug fix
- `docs` — Documentation changes
- `style` — Code style changes (formatting, etc.)
- `refactor` — Code refactoring
- `perf` — Performance improvements
- `test` — Adding or updating tests
- `build` — Build system changes
- `ci` — CI/CD changes
- `chore` — Other changes (maintenance, etc.)
- `revert` — Revert a previous commit

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=commit_sage

# Run specific test file
uv run pytest tests/test_commit_generator.py
```

## GitMan Integration

CommitSage integrates with GitMan to replace generic "Automatic commit" messages with AI-generated ones. When `gitman push` runs on owned repositories, it calls `commit-sage commit --yes` to generate a meaningful commit message automatically.

It uses the active profile (see [Configuration](#configuration)); set `COMMIT_SAGE_PROFILE` in GitMan's environment to choose another one.

See [docs/gitman-integration.md](docs/gitman-integration.md) for full details.

## Roadmap

- [x] Local inference through any OpenAI-compatible server (llama.cpp / llama-swap, Ollama), via profiles
- [ ] Commit history learning for project-aware messages
- [ ] Multi-language support
- [ ] Custom commit templates
- [ ] `commit-sage config` command
- [ ] `commit-sage group` command — suggest logical commit splits
- [ ] Suggestion alternatives (pick from 2-3 options)
- [ ] Regenerate loop (try again without re-running)
- [ ] Inline message editing before commit

## Contributing

Contributions are welcome! This is a local-first tool designed for developer productivity.

### Development Setup

```bash
# Clone the repo
git clone <repository-url>
cd commit-sage

# Install in development mode with dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Run the CLI locally
uv run commit-sage --help
```

## License

See the LICENSE file for details.

## Acknowledgments

- Built with [Typer](https://typer.tiangolo.com/) for the CLI
- Styled with [Rich](https://rich.readthedocs.io/) for beautiful terminal output
- Powered by [Anthropic's Claude](https://www.anthropic.com/) for AI capabilities
- Follows [Conventional Commits](https://www.conventionalcommits.org/) specification
- Package management by [uv](https://docs.astral.sh/uv/)

---

Made with care for developers who value clean Git history. Happy Committing!
