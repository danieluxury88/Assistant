# CommitSage — TODO

## Phase 1 — MVP (DONE)

- [x] Project bootstrap (pyproject.toml, uv, hatchling)
- [x] `git_tools.py` — repo detection, branch, status, diffs, commit
- [x] `models.py` — RepositoryChangeSummary, CommitSuggestion, AppConfig
- [x] `config.py` — pydantic-settings, .env loading
- [x] `classifiers.py` — file extension → category, area, noise detection, scope inference
- [x] `diff_parser.py` — parse, compact, truncate diffs
- [x] `summarizer.py` — build compact AI-ready summary
- [x] `prompt_builder.py` — Conventional Commits prompt, JSON format
- [x] `llm_client.py` — Anthropic API call, JSON extraction
- [x] `commit_generator.py` — AI response → CommitSuggestion
- [x] `executor.py` — confirmation prompt + git commit
- [x] `cli.py` — analyze, suggest, commit commands
- [x] Prompt templates (commit_message.txt, with_body, system_rules)
- [x] Tests — 35 passing (classifiers, diff_parser, git_tools, summarizer, commit_generator)
- [x] Repo moved to /home/daniel24/Assistant root

---

## Phase 1 — Gaps (still needed)

- [ ] **Regenerate loop** — offer "try again" in addition to yes/no in commit flow
- [ ] **Inline edit** — let user edit the suggestion before committing
- [ ] **`suggest --json`** — raw JSON output for scripting
- [ ] **Suggestion alternatives** — return 2-3 options and let user pick

---

## Phase 2 — Better Heuristics (IN PROGRESS)

### Unrelated changes handling
- [x] Detect when staged changes span unrelated areas (backend + frontend + docs, etc.)
- [x] Warn the user when mixed/unrelated changes are detected
- [x] Offer to proceed with all, or select file groups to include
- [x] If user wants to exclude staged files → ask for confirmation before unstaging
- [x] Never silently discard or unstage anything

### Improved classification
- [ ] Detect test files vs source files (test_*.py, *.spec.ts, etc.)
- [ ] Detect framework patterns (Drupal, Symfony, Django, Next.js)
- [ ] Better monorepo scope inference (packages/, apps/ structure)

### Better summarization
- [ ] Deprioritize whitespace-only diff hunks
- [ ] Highlight renamed/moved files separately
- [ ] Show deleted file summary distinct from modified

### Suggestion alternatives
- [ ] Ask AI for 2-3 alternatives in one call
- [ ] Display alternatives and let user pick

---

## Phase 2 — Commands

- [ ] **`commit-sage config`** — view/set model, provider, commit style, ignored patterns
- [ ] **`commit-sage group`** — suggest splitting staged changes into logical commit groups

---

## GitMan Integration (DONE)

- [x] Document integration strategy in `docs/gitman-integration.md`
- [x] Add `--yes` flag to `commit` command (skip all interactive prompts)
- [x] Add `--all` flag to `commit` command (auto-stage unstaged/untracked files without prompting)
- [x] When `--yes` is set, bypass mixed-change interactive menu (commit all as one)
- [x] Update `gitman perform_git_push()`: stage with `git add .`, then call `commit-sage commit --yes` with fallback to "Automatic commit"

---

## Phase 3 — Local AI

- [ ] `llama.cpp` HTTP inference client (same interface as Anthropic client)
- [ ] Local model config (endpoint, model name)
- [ ] Provider switcher in config
- [ ] Performance comparison notes

---

## Phase 4 — Smarter Workflow

- [ ] Commit body generation (richer prompt)
- [ ] Project-aware rules (read CLAUDE.md / .commitsage.toml)
- [ ] Better scope inference using git history patterns
- [ ] `commit-sage learn` — analyze past commits to infer preferred style

---

## Phase 5 — Advanced

- [ ] Commit style learning from history
- [ ] Repository profile presets
- [ ] Multi-commit planning

---

## Infrastructure

- [ ] `docs/architecture.md` — fill in
- [ ] `docs/roadmap.md` — fill in
- [ ] `docs/prompts.md` — document prompt design
- [ ] Install as global uv tool (`uv tool install .`)
- [ ] README.md
