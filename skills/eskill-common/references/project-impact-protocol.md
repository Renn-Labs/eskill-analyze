# Project Impact Protocol

How execution skills evaluate and log project-level impact after each task.

## After Each Task

1. Check if task aligns with a priority in `{project}/.omc/project-context.json`
2. If aligned, note which priority was served
3. Check if task resolves a tech debt item
4. Log to impact log (workstream or project-level)

## After Sprint/Overnight Completion

Update `project-context.json`:
- Increment `velocity.tasks_last_7d` by tasks completed
- Update `tech_debt` if debt items were addressed
- Update `priorities` status if priority items were completed
- Append to `recent_completions` (keep last 10)
- Update `header.last_build` based on final quality gate
- Update `header.last_updated` to now

## Checkpoint Reports (Every 5 Tasks)

Include project-level summary:
```
=== CHECKPOINT {N} ({completed}/{total} tasks) ===
- Workstream: {ws-id or "none"}
- Project health: {before} → {after}
- Priorities addressed: #{N} ({priority_name})
- Tech debt resolved: {count} items
- Follow-up: "{recommendation}"
```
