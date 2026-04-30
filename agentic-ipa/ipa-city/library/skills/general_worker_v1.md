# General Worker Skill

This skill describes the standard workflow for any worker agent in the Gas City workspace using the `bd` (beads) issue tracker.

## Workflow Phases

### 1. Finding & Claiming Work
Identify available tasks and mark them as yours to avoid duplicate efforts.

```bash
bd ready              # List available work items
bd show <id>          # View details for a specific issue
bd update <id> --claim  # Claim the issue atomically
```

### 2. Execution
Perform the task as described in the issue. Follow any specific skills or knowledge relevant to the task.

### 3. Session Completion (MANDATORY)
Before ending your session, you MUST complete all steps below. Work is NOT complete until `git push` succeeds.

1. **File follow-up issues**: Create issues for anything that needs follow-up using `bd create`.
2. **Run quality gates**: If code changed, run tests, linters, and builds.
3. **Update issue status**: Close finished work (`bd close <id>`), update in-progress items.
4. **PUSH TO REMOTE**:
   ```bash
   git pull --rebase
   bd dolt push
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up**: Clear stashes, prune remote branches.
6. **Verify**: All changes committed AND pushed.
7. **Hand off**: Provide context for the next session.
