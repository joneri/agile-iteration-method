# Contributing to Fire Win

This document describes how to contribute to the project and the rules that apply.

## Agile Iteration Method

This project uses the “Agile Iteration Method” defined in `AGENTS.md`.

Before starting implementation:
- Ensure there is a clear Epic (often defined in a runbook).
- Ensure work is defined as a Done Increment that delivers end-to-end user value.

PRs should normally correspond to **one Done Increment**.
Small PRs mean *cohesive increments*, not micro-changes.

When in doubt:
- Check `AGENTS.md`
- Check relevant runbook in `docs/runbooks/`

## Quick Start

### Prerequisites

- Node.js (latest LTS recommended)
- MongoDB instance (local or remote)

### Installation

```bash
npm install
```

### Running Development Server

```bash
npm run dev
```

Application runs on http://localhost:3000 (But sometimes becomes 3001 or 3002)

### Build

```bash
npm run build
```

### Testing

```bash
# Unit tests
npm test

# End-to-end tests
npm run test:e2e

# Lint
npm run lint
```

## Branch and Commits

### Branch Naming

Use descriptive branch names with a prefix:
- `fix/value-series-thursday` - Bug fixes
- `feat/calendar-symbol-fallback` - New features
- `refactor/portfolio-mapping` - Code refactoring
- `docs/contributing-guide` - Documentation

### Commit Style

- Use imperative mood ("Add feature" not "Added feature")
- Keep first line short (50 chars or less)
- Add details in body if needed
- Reference issues when relevant

Examples:
```
Fix 0 datapunkter in 1w view

Add fallback to portfolio union when calendar symbol returns no candles.
Ensures endpoint never returns empty series if portfolio has data.
```

## Pull Request Rules

- **Small PRs** – One Done Increment (one cohesive user-visible feature or fix)
- **No unrelated refactors** - Keep scope focused
- **No new dependencies without justification** - Explain why it's needed
- **Update types** - If API contracts change, update TypeScript types in shared/types
- **Remove temporary logs** - Or hide them behind debug flags (`process.env.DEBUG_VALUE_SERIES`)
- **Test edge cases** - Especially for value-series: test 1w, 1y, 2y ranges

## Definition of Done

A PR is considered done only if it represents a **Done Increment**
as defined in `AGENTS.md`:
- end-to-end user-visible behavior
- safe to evaluate and give feedback on

Before submitting a PR, verify:

- [ ] Builds locally without errors (`npm run build`)
- [ ] Lint passes (`npm run lint`) or clear justification if repo has known lint issues
- [ ] Functionality tested manually with clear reproduction steps
- [ ] Edge cases tested (for graphs/value-series: test 1w, 1m, 1y, 2y ranges)
- [ ] No new console warnings in browser
- [ ] API contract is backwards compatible OR frontend updated in same PR
- [ ] Types updated if API contract changed
- [ ] Tests pass (`npm test`)

## Debug and Logging Policy

### When to Log

- Only during debugging/troubleshooting
- Never in production without guard

### Log Format

Use clear prefixes:
```typescript
console.log("[value-series]", { pointsCount, firstDate, lastDate });
console.log("[vs-calendar]", { calendarSymbol, candlesCount });
```

### Before Merge

- Remove temporary diagnostic logs
- OR protect with environment flag:
```typescript
if (process.env.DEBUG_VALUE_SERIES) {
  console.log("[debug]", data);
}
```

## Security and Secrets

### Never Commit Secrets

- No API keys, tokens, or passwords in code
- Use `.env.local` for local development
- Use environment variables for production

### If a Secret is Committed

1. **Rotate immediately** - Generate new secret
2. **Update deployment** - Update production environment variables
3. **Remove from history** - Use `git filter-branch` or BFG Repo-Cleaner if needed
4. **Notify team** - Inform maintainers

### Environment Files

- `.env.local` - Local development (gitignored)
- `.env.example` - Template without real values (committed)
- `CRON_SECRET` - Required for internal job authentication

## Code Style

### General Principles

- Follow existing code style in the file you're editing
- TypeScript strict mode enabled - respect type safety
- Use Prettier for formatting (if configured)

### TypeScript

- Prefer explicit types over `any`
- Use shared types from `src/shared/types/`
- Update type definitions when API contracts change

### React/Next.js

- Server components by default
- Use `"use client"` directive only when needed
- Follow Next.js App Router conventions

### File Organization

```
src/
  app/           # Next.js app routes and pages
  server/        # Backend logic and database access
  shared/        # Shared types and utilities
  ui/            # Reusable UI components
```

## Common Commands

```bash
# Development
npm run dev                 # Start dev server
npm run build              # Production build
npm test                   # Run unit tests
npm run test:e2e          # Run Playwright e2e tests
npm run lint              # Run linter + guardrails

# Migrations
npm run migrate:ledger    # Migrate holdings to transactions
npm run migrate:fees      # Migrate fees

# Verification
npm run verify:increment6 # Verify increment 6
npm run verify:avanza     # Verify Avanza integration
MARKET_PROVIDER=avanza npm run verify:autopost   # Verify auto-post functionality

# Optional verify overrides
# - VERIFY_BASE_URL=http://127.0.0.1:3001
# - VERIFY_MIN_SUGGESTIONS=1
# - VERIFY_MAX_SUGGESTIONS=5
```

## Getting Help

- Check existing issues and PRs first
- Review `AGENTS.md` for development workflow
- Ask questions in PR comments

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

By contributing documentation to this repository, you agree that your contributions will be licensed under CC BY 4.0 (see LICENSE-DOCS).
