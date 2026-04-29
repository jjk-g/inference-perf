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
Before ending your session, you MUST push your changes and update the issue status.

1. **File follow-up issues**: `bd create "Follow-up: <task>"` if more work is needed.
2. **Run quality gates**: Ensure tests/linters pass if you modified code.
3. **Close finished work**: `bd close <id>`
4. **Push to Remote**:
   ```bash
   git pull --rebase
   bd dolt push
   git push
   ```
5. **Verify**: Run `git status` to ensure you are "up to date with origin".
