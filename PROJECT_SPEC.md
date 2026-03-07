# 📘 PROJECT_SPEC.md
## 🧠 CommitSage — AI-Assisted Git Commit Helper

---

## 1. 📌 Project Overview

**CommitSage** is a local-first CLI tool that analyzes pending Git changes and helps generate clear, structured commit messages.

The tool is designed to:
- inspect staged and unstaged changes
- summarize the purpose of the changes
- suggest high-quality commit messages
- optionally create commits after user confirmation
- start with an external AI API
- later support fully local inference with `llama.cpp`

The main goal is to create a **fast, efficient, developer-friendly assistant** for daily Git workflows.

---

## 2. 🎯 Objectives

### Primary objectives
- analyze Git changes quickly
- generate useful commit messages
- support terminal-based workflows
- remain modular and extensible
- prepare architecture for future local AI inference

### Secondary objectives
- improve consistency of commit messages
- reduce friction in daily commit workflows
- support future grouping of changes into logical commits
- support project-aware commit styles

---

## 3. 👤 Target User

CommitSage is aimed at developers who:
- work locally in Git repositories
- want help writing better commit messages
- prefer CLI workflows
- want to keep increasing automation over time
- may work in Drupal, Symfony, Python, docs, or mixed repositories

Initial optimization is for:
- single-developer usage
- local repositories
- interactive terminal sessions

---

## 4. 🧩 Scope

### Included in MVP
- detect if current directory is a Git repository
- inspect staged changes
- inspect unstaged changes
- list changed files
- summarize changes
- send compact summary to AI provider
- receive commit message suggestion
- display suggestion in terminal
- optionally create commit after confirmation

### Not included in MVP
- automatic commit splitting into multiple commits
- automatic staging of files
- deep semantic repository indexing
- branch management
- PR/MR generation
- commit history learning
- background repository watching

---

## 5. 🏗️ Architecture Overview

CommitSage is composed of the following layers:

### 5.1 ⚙️ CLI Layer
Handles:
- user commands
- user options
- displaying results
- confirmation prompts

**Language:** Python

---

### 5.2 🔍 Git Inspection Layer
Handles:
- repository detection
- reading Git status
- reading staged and unstaged diff
- listing changed files
- identifying file states

**Language:** Python
**Integration:** Git CLI through subprocess

---

### 5.3 🧠 Change Analysis Layer
Handles:
- classifying changed files
- grouping by file type or area
- identifying likely scope
- filtering low-value noise
- building a compact AI-ready summary

**Language:** Python

---

### 5.4 ✨ AI Provider Layer
Handles:
- building prompt input
- calling AI backend
- parsing structured responses
- returning commit suggestions

**Phase 1:** external AI API
**Phase 2:** local `llama.cpp` server

---

### 5.5 ✅ Commit Execution Layer
Handles:
- showing final suggestion
- asking for approval
- running `git commit`

**Language:** Python

---

## 6. 🛠️ Technology Stack

### Core stack
- **Python 3.11+**
- **Typer** for CLI commands
- **Rich** for terminal output
- **Pydantic** for structured models
- **subprocess** for Git command execution
- **pathlib** for path handling

### AI integration
#### Phase 1
- external AI API

#### Phase 2
- `llama.cpp` local server
- HTTP-based inference client

---

## 7. 📚 Language Choice by Stage

### Stage A — Repository inspection
**Python**
- run Git commands
- collect file lists
- identify staged and unstaged state

### Stage B — Diff preprocessing
**Python**
- parse diff output
- compact diff data
- trim excessive payload
- prioritize important hunks

### Stage C — Heuristic analysis
**Python**
- detect change type
- infer likely commit scope
- remove noisy/generated files

### Stage D — Commit suggestion generation
**AI provider**
- summarize intent
- generate commit message
- optionally generate body

### Stage E — User interaction
**Python**
- display analysis
- show suggestions
- accept/edit/regenerate

### Stage F — Commit execution
**Python**
- create commit
- handle errors
- report result

---

## 8. 🔌 AI Strategy

### Phase 1 — External API
Purpose:
- validate workflow quickly
- refine prompts
- measure usefulness
- avoid local model setup complexity initially

Used for:
- commit message generation
- optional body generation
- suggestion alternatives

---

### Phase 2 — Local AI with `llama.cpp`
Purpose:
- support privacy-first execution
- reduce recurring API cost
- enable local-only workflows
- improve long-term control

Used for:
- same inference contract as API mode
- local model serving through HTTP endpoint

---

## 9. ⚡ Core Workflow

### MVP flow
1. user runs CommitSage in a repository
2. tool verifies Git repository
3. tool reads Git status
4. tool collects changed files
5. tool reads staged and/or unstaged diff
6. tool builds compact summary
7. tool sends summary to AI provider
8. AI provider returns commit suggestion
9. tool displays suggestion
10. user approves, regenerates, or exits
11. tool optionally creates commit

---

## 10. 💬 Commit Style

Initial commit style:
- **Conventional Commits**
- concise subject line
- optional body

Examples:
- `feat: add route filtering for admin dashboard`
- `fix: handle empty reservation type selection`
- `docs: update WSL setup instructions`

Future support:
- custom team styles
- learned preferences
- project-specific scopes

---

## 11. 📦 CLI Command Design

### MVP commands

#### `commit-sage analyze`
Displays:
- repository state
- changed files
- file classification
- staged and unstaged summary

#### `commit-sage suggest`
Generates:
- commit message suggestion
- optional alternatives
- optional body

#### `commit-sage commit`
Runs:
- analysis
- suggestion
- confirmation
- `git commit`

---

### Future commands

#### `commit-sage group`
Suggest logical commit groups.

#### `commit-sage config`
Manage:
- AI provider
- model name
- endpoint
- commit style
- ignored paths

#### `commit-sage learn`
Analyze previous commits and infer preferred style.

---

## 12. 🧾 Data Models

### RepositoryChangeSummary
Contains:
- staged files
- unstaged files
- file type breakdown
- inferred scope
- diff summary
- ignored/noisy files

### CommitSuggestion
Contains:
- type
- scope
- subject
- body
- confidence
- alternatives

### AppConfig
Contains:
- AI provider
- API model
- local endpoint
- commit style
- ignored patterns
- diff size limits

---

## 13. ✅ Functional Requirements

### FR-01
The system must detect whether the current folder is a Git repository.

### FR-02
The system must read staged and unstaged changes.

### FR-03
The system must list changed files.

### FR-04
The system must classify files by type.

### FR-05
The system must generate a compact summary for AI input.

### FR-06
The system must request a commit suggestion from the configured AI provider.

### FR-07
The system must display the generated commit suggestion clearly.

### FR-08
The system must allow regeneration of the suggestion.

### FR-09
The system must optionally create a Git commit after user confirmation.

### FR-10
The system must support future replacement of AI provider without redesigning the core workflow.

---

## 14. 🛡️ Non-Functional Requirements

### NFR-01 Performance
The tool should feel fast enough for frequent daily use.

### NFR-02 Maintainability
The architecture should remain modular and testable.

### NFR-03 Portability
The tool should run on:
- WSL Ubuntu
- Linux
- macOS

### NFR-04 Extensibility
The design should allow additional providers, rules, and commands.

### NFR-05 Safety
The tool must never create a commit without clear user intent.

---

## 15. 🧱 Design Principles

### Heuristics before AI 🪶
Use deterministic logic first. Use AI only where semantic judgment is helpful.

### Fast first ⚡
Avoid sending full repository context. Send compact summaries.

### Modular providers 🔌
AI provider logic must be isolated from the rest of the application.

### Human in the loop 👤
The tool assists; it does not silently automate commit creation.

### Local-first future 🏠
Even during API phase, architecture must be ready for local-only execution.

---

## 16. 🪜 Roadmap

### Phase 1 — MVP with external AI API 🔌
- Git repository detection
- Git status reading
- staged/unstaged diff reading
- compact summary generation
- commit suggestion
- optional commit execution

### Phase 2 — Better heuristics 🧠
- improved file classification
- noisy file filtering
- better summarization
- suggestion alternatives

### Phase 3 — Local AI with `llama.cpp` 🖥️
- local inference client
- local model configuration
- local HTTP integration
- performance comparison

### Phase 4 — Smarter workflow 🚀
- commit body generation
- commit grouping suggestions
- project-aware rules
- better scope inference

### Phase 5 — Advanced personalization ✨
- commit style learning
- repository profile presets
- multi-commit planning

---

## 17. ⚠️ Risks

### Poor suggestions
Mitigation:
- strict prompt structure
- compact input summaries
- alternatives and regeneration

### Slow inference
Mitigation:
- use heuristics first
- keep prompts small
- move to local optimized runtime later

### Over-automation
Mitigation:
- require confirmation
- show decisions clearly
- do not stage or commit silently

### Large diffs
Mitigation:
- truncate or summarize large patches
- prioritize important hunks
- exclude generated files

---

## 18. 🏁 Success Criteria

CommitSage is successful if:
- it saves time during commit creation
- it improves commit message consistency
- it feels easy to use daily
- users trust the output enough to keep using it
- migration from API mode to local mode is smooth

---

## 19. 🎯 Recommended First Milestone

### MVP Commit Suggestion
Build a CLI that:
- detects the repository
- reads staged diff
- summarizes changes
- calls external AI API
- shows one commit suggestion
- optionally commits after approval

This milestone proves the core value with minimum complexity.
```

---

# 📁 Suggested Folder Structure

```text
commit-sage/
├── README.md
├── PROJECT_SPEC.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── config/
│   └── default.toml
├── prompts/
│   ├── commit_message.txt
│   ├── commit_message_with_body.txt
│   └── system_rules.txt
├── src/
│   └── commit_sage/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── models.py
│       ├── git_tools.py
│       ├── diff_parser.py
│       ├── classifiers.py
│       ├── summarizer.py
│       ├── prompt_builder.py
│       ├── llm_client.py
│       ├── commit_generator.py
│       ├── executor.py
│       └── utils.py
├── tests/
│   ├── test_git_tools.py
│   ├── test_diff_parser.py
│   ├── test_classifiers.py
│   ├── test_summarizer.py
│   └── test_commit_generator.py
└── docs/
    ├── architecture.md
    ├── roadmap.md
    └── prompts.md
```

---

# 🪜 Phase 1 Implementation Plan

## Phase 1 Goal 🔌

Create the first working version using an external AI API.

The tool should:

* inspect repository changes
* summarize them
* ask an AI model for a commit suggestion
* show the suggestion clearly
* optionally create the commit

---

## 1. MVP Features

### 1.1 `commit-sage analyze`

Shows:

* current branch
* staged files
* unstaged files
* file categories
* basic summary

### 1.2 `commit-sage suggest`

Runs:

* analyze
* summarize
* call AI
* show suggestion

### 1.3 `commit-sage commit`

Runs:

* suggest
* ask for confirmation
* execute `git commit`

---

## 2. Phase 1 Modules

### `cli.py`

Responsible for:

* Typer commands
* user input/output
* command routing

### `git_tools.py`

Responsible for:

* repository detection
* git status
* diff retrieval
* current branch
* changed file listing

### `models.py`

Responsible for:

* Pydantic models
* typed app contracts

### `classifiers.py`

Responsible for:

* file extension/type grouping
* basic change categorization

### `summarizer.py`

Responsible for:

* compact text summary for AI input
* diff truncation rules
* file grouping summary

### `prompt_builder.py`

Responsible for:

* generating AI prompt payload
* commit style instructions

### `llm_client.py`

Responsible for:

* external AI API calls
* response parsing
* provider abstraction start

### `commit_generator.py`

Responsible for:

* transforming AI output into `CommitSuggestion`
* fallback handling
* alternatives

### `executor.py`

Responsible for:

* confirmation prompt
* git commit execution

---

## 3. Phase 1 Detailed Steps

## Step 1 — Project bootstrap 🏗️

Create:

* Python project
* Typer CLI
* base package structure
* config loading
* `.env.example`

Deliverable:

* `commit-sage --help` works

---

## Step 2 — Git inspection core 🔍

Implement:

* `is_git_repo()`
* `get_current_branch()`
* `get_status_porcelain()`
* `get_staged_diff()`
* `get_unstaged_diff()`
* `get_changed_files()`

Deliverable:

* `commit-sage analyze` shows repository info

---

## Step 3 — File classification 🧩

Implement simple categories:

* Python
* PHP
* JS/TS
* CSS/SCSS
* YAML
* Markdown
* JSON
* config
* assets
* unknown

Add high-level labels:

* docs
* backend
* frontend
* config
* mixed

Deliverable:

* analyze command shows file breakdown

---

## Step 4 — Diff summarization ✂️

Implement:

* file count summary
* changed file list
* diff truncation
* top relevant hunks
* total lines added/removed

Deliverable:

* AI input summary is compact and readable

---

## Step 5 — Prompt builder ✨

Create prompt templates that ask AI to return:

* conventional commit type
* optional scope
* concise subject
* optional body
* strict JSON if possible

Deliverable:

* repeatable prompt format

---

## Step 6 — API client 🔌

Implement:

* external AI API call
* environment-based key loading
* timeout/error handling
* response parsing

Deliverable:

* `commit-sage suggest` returns an AI-generated suggestion

---

## Step 7 — Suggestion rendering 💬

Display:

* detected scope
* suggested commit
* optional body
* alternatives if available

Deliverable:

* polished terminal output using `rich`

---

## Step 8 — Commit execution ✅

Implement:

* confirmation prompt
* `git commit -m`
* optional body support
* clean error messages

Deliverable:

* `commit-sage commit` can create a commit after approval

---

## 4. Suggested Phase 1 Data Contracts

### RepositoryChangeSummary

```python
class RepositoryChangeSummary(BaseModel):
    branch: str
    staged_files: list[str]
    unstaged_files: list[str]
    file_categories: dict[str, int]
    inferred_scope: str | None = None
    summary_text: str
```

### CommitSuggestion

```python
class CommitSuggestion(BaseModel):
    commit_type: str
    scope: str | None = None
    subject: str
    body: str | None = None
    confidence: float | None = None
```

---

## 5. Suggested Initial Commands

```bash
commit-sage analyze
commit-sage suggest
commit-sage commit
```

Optional flags later:

```bash
commit-sage suggest --staged-only
commit-sage suggest --unstaged-only
commit-sage commit --yes
commit-sage suggest --json
```

---

## 6. Phase 1 Success Definition ✅

Phase 1 is complete when:

* tool runs locally from terminal
* it detects Git changes correctly
* it sends a compact summary to the AI API
* it produces a good commit suggestion
* it can create a commit after approval

---

## 7. Recommended Immediate Next Tasks 🚀

### Task 1

Create the repository and Python package skeleton

### Task 2

Implement `git_tools.py`

### Task 3

Implement `models.py`

### Task 4

Implement `analyze` command

### Task 5

Add AI API integration

### Task 6

Implement `suggest`

### Task 7

Implement `commit`

---

## 8. Practical Build Order 🧭

Best order to move fast:

1. project bootstrap
2. git inspection
3. analyze command
4. summarizer
5. API prompt + client
6. suggest command
7. commit execution
8. cleanup and tests

