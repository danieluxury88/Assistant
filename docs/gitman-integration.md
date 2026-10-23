# 🔗 GitMan Integration Guide

> Integrating CommitSage with GitMan for intelligent automated commits

## 📋 Overview

GitMan is a repository management tool that automates Git operations across multiple repositories. Currently, the `gitman push` command uses a generic "Automatic commit" message for all changes. By integrating CommitSage, we can replace this with AI-generated, context-aware commit messages that follow best practices.

## 🎯 Current Behavior

The `gitman push` command currently does the following for each repository with `ownership = "own"`:

```bash
git -C "$repo" add .
git -C "$repo" commit -m "Automatic commit"
git -C "$repo" push
```

**Problems with this approach:**
- ❌ Generic commit message provides no context
- ❌ All changes are lumped into a single commit
- ❌ No distinction between feature changes, fixes, or different logical areas
- ❌ Poor Git history makes debugging and code review difficult
- ❌ Violates conventional commit standards

## ✨ Proposed Integration

Replace the generic commit message with CommitSage-generated intelligent commit messages.

### Option 1: Simple Integration (Single Commit)

This approach generates one AI-powered commit per repository, replacing "Automatic commit" with a meaningful message.

#### Modified `perform_git_push()` Function

```bash
perform_git_push() {
    echo "Performing git push in owned repositories..."
    while read -r repo type ownership extra; do
        if [[ -z "$repo" || "$repo" == \#* ]]; then
            continue
        fi

        if [[ -n "$extra" ]]; then
            echo "Skipping malformed repo entry: $repo $type $ownership $extra"
            continue
        fi

        # Default to external if no ownership specified
        [[ -z "$ownership" ]] && ownership="external"

        if [[ "$ownership" != "own" ]]; then
            print_repo_operation_header "⏭ Skip push" "$repo" "$type" "$ownership"
            echo "Skipping repository because ownership is '$ownership'."
            continue
        fi

        print_repo_operation_header "⬆ Push" "$repo" "$type" "$ownership"

        if ! is_git_repo "$repo"; then
            echo "Repository not found or not a git repo."
            continue
        fi

        # Stage all changes
        git -C "$repo" add .

        # Check if there are changes to commit
        if git -C "$repo" diff --cached --quiet; then
            echo "No changes to commit in $repo"
            continue
        fi

        # Use CommitSage to generate and create the commit
        echo "🧙 Generating intelligent commit message with CommitSage..."

        # Navigate to repo and run CommitSage
        (
            cd "$repo" || exit 1

            # Check if CommitSage is available
            if ! command -v commit-sage >/dev/null 2>&1; then
                echo "⚠️  CommitSage not found, falling back to automatic commit"
                git commit -m "Automatic commit"
            else
                # Use CommitSage commit command with auto-confirm flag (if available)
                # Or use suggest + manual creation
                commit-sage commit --yes 2>/dev/null || {
                    echo "⚠️  CommitSage failed, falling back to automatic commit"
                    git commit -m "Automatic commit"
                }
            fi
        )

        # Push the changes
        git -C "$repo" push
    done < "$REPO_LIST"
}
```

### Option 2: Interactive Integration (Review Before Commit)

For more control, allow reviewing the suggested commit message before pushing.

```bash
perform_git_push() {
    echo "Performing git push in owned repositories..."
    while read -r repo type ownership extra; do
        if [[ -z "$repo" || "$repo" == \#* ]]; then
            continue
        fi

        if [[ -n "$extra" ]]; then
            echo "Skipping malformed repo entry: $repo $type $ownership $extra"
            continue
        fi

        [[ -z "$ownership" ]] && ownership="external"

        if [[ "$ownership" != "own" ]]; then
            print_repo_operation_header "⏭ Skip push" "$repo" "$type" "$ownership"
            echo "Skipping repository because ownership is '$ownership'."
            continue
        fi

        print_repo_operation_header "⬆ Push" "$repo" "$type" "$ownership"

        if ! is_git_repo "$repo"; then
            echo "Repository not found or not a git repo."
            continue
        fi

        git -C "$repo" add .

        if git -C "$repo" diff --cached --quiet; then
            echo "No changes to commit in $repo"
            continue
        fi

        # Show what will be committed
        echo "📝 Changes to be committed:"
        git -C "$repo" status --short
        echo ""

        # Generate commit message suggestion
        echo "🧙 Generating commit message..."
        (
            cd "$repo" || exit 1

            if ! command -v commit-sage >/dev/null 2>&1; then
                echo "⚠️  CommitSage not found"
                git commit -m "Automatic commit"
            else
                # Use interactive mode
                commit-sage commit
            fi
        )

        # Ask if user wants to push
        echo ""
        read -p "Push to remote? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git -C "$repo" push
        else
            echo "Skipping push for $repo"
        fi
    done < "$REPO_LIST"
}
```

### Option 3: Advanced Integration (Smart Commit Splitting)

For repositories with mixed changes, use CommitSage's mixed-change detection to create multiple logical commits.

```bash
perform_git_push_smart() {
    echo "Performing smart git push in owned repositories..."
    while read -r repo type ownership extra; do
        if [[ -z "$repo" || "$repo" == \#* ]]; then
            continue
        fi

        if [[ -n "$extra" ]]; then
            echo "Skipping malformed repo entry: $repo $type $ownership $extra"
            continue
        fi

        [[ -z "$ownership" ]] && ownership="external"

        if [[ "$ownership" != "own" ]]; then
            print_repo_operation_header "⏭ Skip push" "$repo" "$type" "$ownership"
            echo "Skipping repository because ownership is '$ownership'."
            continue
        fi

        print_repo_operation_header "⬆ Smart Push" "$repo" "$type" "$ownership"

        if ! is_git_repo "$repo"; then
            echo "Repository not found or not a git repo."
            continue
        fi

        # Check for unstaged changes
        if [[ -z "$(git -C "$repo" status --porcelain)" ]]; then
            echo "No changes to commit in $repo"
            git -C "$repo" push 2>/dev/null && echo "✓ Pushed existing commits"
            continue
        fi

        echo "🧙 Analyzing changes with CommitSage..."
        (
            cd "$repo" || exit 1

            if ! command -v commit-sage >/dev/null 2>&1; then
                echo "⚠️  CommitSage not found, using standard flow"
                git add .
                git commit -m "Automatic commit"
                git push
            else
                # CommitSage will handle staging, commit creation, and mixed-change detection
                # Use the --all flag to include unstaged changes
                commit-sage commit --all --yes 2>/dev/null || {
                    echo "⚠️  CommitSage failed, falling back to automatic commit"
                    git add .
                    git commit -m "Automatic commit"
                }
                git push
            fi
        )
    done < "$REPO_LIST"
}
```

## 🛠️ Implementation Steps

### Step 1: Install CommitSage

```bash
# Clone and install CommitSage
cd /path/to/commit-sage
pip install -e .

# Verify installation
commit-sage --version
```

### Step 2: Set Up API Key

```bash
# Add to your shell configuration (~/.bashrc or ~/.zshrc)
export ANTHROPIC_API_KEY="your-api-key-here"
# or
export OPENAI_API_KEY="your-api-key-here"

# Optional: pick a profile from ~/.config/commit-sage/config.toml
export COMMIT_SAGE_PROFILE="local"

# Reload your shell configuration
source ~/.bashrc  # or source ~/.zshrc
```

### Step 3: Modify GitMan Script

1. Back up the original gitman script:
   ```bash
   cp /home/daniel24/Scripts/gitman /home/daniel24/Scripts/gitman.backup
   ```

2. Edit `/home/daniel24/Scripts/gitman` and replace the `perform_git_push()` function with one of the options above.

3. Make the script executable (if not already):
   ```bash
   chmod +x /home/daniel24/Scripts/gitman
   ```

### Step 4: Test the Integration

Test on a single repository first:

```bash
# Edit your repos.txt to temporarily comment out all but one test repo
# Then run:
gitman push
```

### Step 5: Add Configuration (Optional)

Create a `.commitsagerc` or configure CommitSage per repository if needed.

## 🎮 Usage Examples

### Basic Usage (Option 1)

```bash
# Automatically generates intelligent commits and pushes
gitman push
```

**Output:**
```
⬆ Push myproject
   /home/user/projects/myproject
   Type: symfony
   Ownership: own

🧙 Generating intelligent commit message with CommitSage...

✨ Suggested commit:
   feat(auth): add JWT token validation middleware

✅ Commit created successfully!
```

### Interactive Mode (Option 2)

```bash
gitman push
```

**Output:**
```
📝 Changes to be committed:
 M src/Security/JwtAuthenticator.php
 M config/packages/security.yaml
 A tests/Security/JwtAuthenticatorTest.php

🧙 Generating commit message...

┌─ Suggested Commit Message ─────────────────────┐
│ feat(auth): add JWT token validation          │
│                                                 │
│ - Implements JWT authenticator for API access  │
│ - Updates security configuration               │
│ - Adds comprehensive test coverage             │
│                                                 │
│ Confidence: 92%                                │
└─────────────────────────────────────────────────┘

✅ Create this commit? [y/N]: y
✓ Commit created

Push to remote? (y/N): y
✓ Pushed to origin/main
```

## 🔧 Advanced Configuration

### Custom Commit Message Templates

Add a CommitSage configuration per repository type:

```bash
# In your gitman script, before calling CommitSage:
case "$type" in
    drupal)
        export COMMIT_SAGE_CONFIG="$HOME/.config/commitsage/drupal.toml"
        ;;
    symfony)
        export COMMIT_SAGE_CONFIG="$HOME/.config/commit-sage/symfony.toml"
        ;;
    *)
        export COMMIT_SAGE_CONFIG="$HOME/.config/commit-sage/config.toml"
        ;;
esac
```

### Handling Failed Commits

Add error handling and logging:

```bash
# Create a log file for failed commits
GITMAN_LOG="$HOME/.gitman.log"

# In perform_git_push():
if ! commit-sage commit --yes; then
    echo "[$(date)] Failed to create commit in $repo" >> "$GITMAN_LOG"
    echo "⚠️  Falling back to manual commit"
    git commit -m "Automatic commit [CommitSage unavailable]"
fi
```

### Dry-Run Mode

Add a dry-run option to preview what would be committed:

```bash
# Add new gitman command
case "$1" in
    # ... existing commands ...
    push-preview)
        perform_git_push_preview
        ;;
esac

perform_git_push_preview() {
    echo "Preview mode: Showing what would be committed..."
    while read -r repo type ownership extra; do
        # ... filter logic ...

        (
            cd "$repo" || exit 1
            git add .

            if ! git diff --cached --quiet; then
                echo "Repository: $repo"
                commit-sage suggest --staged
                echo ""
            fi
        )
    done < "$REPO_LIST"
}
```

## 🚀 Benefits

| Feature | Before | After |
|---------|--------|-------|
| **Commit Messages** | "Automatic commit" | "feat(auth): add JWT validation middleware" |
| **Context** | None | Full description of changes |
| **Standards** | Non-existent | Conventional Commits |
| **Debugging** | Difficult | Easy with meaningful history |
| **Code Review** | Poor history | Clear, reviewable commits |
| **Mixed Changes** | Single commit | Can be split into logical commits |

## ⚠️ Considerations

### API Costs
- CommitSage uses the Anthropic API which has costs
- For frequent automated commits, consider cost monitoring
- Consider using a cheaper model (e.g., Claude Haiku) for automated flows

### Fallback Strategy
- Always include fallback to "Automatic commit" if CommitSage fails
- Log failures for troubleshooting
- Consider rate limiting or caching for frequently unchanged files

### Performance
- CommitSage adds ~2-5 seconds per commit
- For multiple repositories, this is still faster than manual commits
- Consider parallel processing for large repository lists

### Error Handling
- Network issues may cause CommitSage to fail
- Missing API keys should fall back gracefully
- Ensure push continues even if commit message generation fails

### Provider Selection
- The active profile decides the provider: `--profile`, then `COMMIT_SAGE_PROFILE`, then `default_profile` in `~/.config/commit-sage/config.toml`
- Without a profile file the built-in `claude` profile (Anthropic API) is used
- Local and subscription profiles need no API key; see the README's Configuration section

## 📝 Next Steps

1. **Test the integration** with a single repository
2. **Monitor API usage** and costs
3. **Collect feedback** on commit message quality
4. **Iterate on the integration** based on real-world usage
5. **Consider local LLM** integration for offline/cost-free operation

## 🤝 Related Improvements

### Future Enhancements

- **Auto-staging smart selection**: Stage only related files together
- **Branch awareness**: Different commit styles for main vs. feature branches
- **Commit templates per project**: Custom templates for different codebases
- **Multi-commit support**: Automatically split unrelated changes
- **Local LLM support**: Use llama.cpp for offline operation
- **Commit hooks**: Integrate with git hooks for all commits, not just gitman

### Example: Multi-Push with Parallel Processing

```bash
# Process repositories in parallel with GNU parallel
perform_git_push_parallel() {
    export -f perform_git_push_single
    export REPO_LIST

    cat "$REPO_LIST" | parallel -j 4 perform_git_push_single
}
```

## 📚 References

- [CommitSage Documentation](../README.md)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitMan Script](/home/daniel24/Scripts/gitman)
- [Anthropic API Documentation](https://docs.anthropic.com/)

---

**Happy Committing!** 🎉
