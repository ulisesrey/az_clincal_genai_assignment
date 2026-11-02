# AGENTS.md

## Agent skills

### Issue tracker

Issues are tracked as GitHub Issues on `ulisesrey/az_clincal_genai_assignment`, operated via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` at the repo root plus ADRs in `docs/adr/`. See `docs/agents/domain.md`.

## Git Workflow & Constraints

- **Branching:** Always use standard Git branches (`git checkout -b <branch-name>`) checked out from `develop`.
- **Commit Messages:** Follow Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`).