# 🧙‍♂️ CommitSage

> ✨ Your AI-powered companion for crafting perfect Git commit messages

CommitSage is a smart CLI tool that analyzes your Git changes and helps you write clear, consistent, and meaningful commit messages. Say goodbye to "fix stuff" and "wip" commits! 🎯

## 🌟 Features

- 🔍 **Smart Change Analysis** — Inspects staged and unstaged changes automatically
- 🤖 **AI-Powered Suggestions** — Uses Claude to generate high-quality conventional commit messages
- 🎨 **Beautiful Terminal UI** — Powered by Rich for a delightful command-line experience
- 🧩 **Mixed Change Detection** — Identifies unrelated changes and suggests splitting them into separate commits
- ⚙️ **Configurable** — Customize AI model, commit style, and ignore patterns
- 🚀 **Fast & Local-First** — Designed for efficient daily Git workflows
- 📦 **Zero Configuration** — Works out of the box with sensible defaults

## 📦 Installation

### Prerequisites

- Python 3.11 or higher
- Git repository
- Anthropic API key

### Install from source

```bash
# Clone the repository
git clone <repository-url>
cd commit-sage

# Install with pip
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

### Set up your API key

```bash
# Add your Anthropic API key to your environment
export ANTHROPIC_API_KEY="your-api-key-here"

# Or add it to your ~/.bashrc or ~/.zshrc for persistence
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.bashrc
```

## 🚀 Quick Start

```bash
# Stage your changes
git add .

# Generate a commit message
commit-sage suggest

# Review the suggestion and commit
commit-sage commit
```

That's it! CommitSage will analyze your changes and suggest a well-structured commit message. ✨

## 💡 Usage

### Basic Commands

```bash
# Get a commit message suggestion for staged changes
commit-sage suggest

# Include unstaged changes in the analysis
commit-sage suggest --all

# Only analyze staged changes
commit-sage suggest --staged

# Generate and create a commit in one step
commit-sage commit

# Show project information
commit-sage info

# Display version
commit-sage --version
```

### Example Output

```
🔍 Analyzing your changes...

┌─ Suggested Commit Message ─────────────────────────┐
│ feat(cli): add interactive commit confirmation     │
│                                                     │
│ Adds user confirmation prompt before creating      │
│ commits to prevent accidental commits               │
│                                                     │
│ Confidence: 95%                                    │
└─────────────────────────────────────────────────────┘

✅ Create this commit? [y/N]:
```

## ⚙️ Configuration

CommitSage looks for configuration in `config/default.toml` or you can create your own config file.

### Default Configuration

```toml
[ai]
provider = "anthropic"
model = "claude-haiku-4-5-20251001"

[commit]
style = "conventional"
max_diff_lines = 300

[ignore]
patterns = [
    "*.lock",
    "*.min.js",
    "*.min.css",
    "package-lock.json",
    "yarn.lock",
    "composer.lock",
    "*.generated.*",
    "__pycache__/",
    ".env",
]
```

### Customization Options

- **AI Provider**: Currently supports Anthropic (Claude)
- **Model**: Choose your preferred Claude model
- **Commit Style**: Conventional commits (more styles coming soon!)
- **Max Diff Lines**: Limit how much diff context to send to the AI
- **Ignore Patterns**: Files to exclude from analysis

## 🏗️ Architecture

CommitSage is built with a modular architecture:

- **CLI Layer** (`cli.py`) — Handles user commands and terminal UI
- **Git Tools** (`git_tools.py`) — Interfaces with Git repositories
- **Summarizer** (`summarizer.py`) — Analyzes and summarizes changes
- **Classifiers** (`classifiers.py`) — Detects change patterns and categories
- **LLM Client** (`llm_client.py`) — Communicates with AI providers
- **Commit Generator** (`commit_generator.py`) — Creates structured commit messages
- **Prompt Builder** (`prompt_builder.py`) — Crafts effective AI prompts

## 🎯 Commit Message Format

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

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=commit_sage

# Run specific test file
pytest tests/test_commit_generator.py
```

## 🗺️ Roadmap

- [ ] 🦙 Support for local inference with `llama.cpp`
- [ ] 🔀 Automatic commit splitting for mixed changes
- [ ] 📚 Commit history learning for project-aware messages
- [ ] 🌍 Multi-language support
- [ ] 🎨 Custom commit templates
- [ ] 📊 Commit statistics and insights
- [ ] 🔄 Git hooks integration
- [ ] 🎭 Multiple AI provider support (OpenAI, local models, etc.)

## 🤝 Contributing

Contributions are welcome! This is a local-first tool designed for developer productivity, and we'd love your input.

### Development Setup

```bash
# Clone the repo
git clone <repository-url>
cd commit-sage

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Make your changes and submit a PR!
```

## 📄 License

See the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [Typer](https://typer.tiangolo.com/) for the CLI
- Styled with [Rich](https://rich.readthedocs.io/) for beautiful terminal output
- Powered by [Anthropic's Claude](https://www.anthropic.com/) for AI capabilities
- Follows [Conventional Commits](https://www.conventionalcommits.org/) specification

---

Made with ❤️ for developers who care about clean Git history

**Happy Committing!** 🎉
