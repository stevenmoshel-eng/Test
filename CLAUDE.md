# CLAUDE.md

This file provides guidance to AI assistants (Claude and others) working in this repository.

---

## Repository Status

This is a **newly initialized, empty repository**. No source code, dependencies, tests, or CI/CD
configuration have been added yet. The sections below serve as a living document — update them as
the project takes shape.

---

## Repository Overview

| Field         | Value                                     |
|---------------|-------------------------------------------|
| Remote origin | `http://local_proxy@127.0.0.1:31173/git/stevenmoshel-eng/Test` |
| Default branch | `main` (to be created on first push)   |
| Language / stack | _Not yet determined_                 |
| Package manager | _Not yet determined_                  |

---

## Project Structure

_No structure exists yet. Update this section once files are added._

A suggested baseline layout (adapt to the chosen stack):

```
/
├── src/           # Application source code
├── tests/         # Test suites
├── docs/          # Documentation
├── .github/       # GitHub Actions workflows (if using GitHub)
├── CLAUDE.md      # This file
└── README.md      # Human-facing project introduction
```

---

## Development Setup

_No environment setup is required yet. Document prerequisites here once a tech stack is chosen._

Typical steps to include:

1. **Clone the repository**
   ```bash
   git clone <remote-url>
   cd Test
   ```

2. **Install dependencies** (fill in once stack is decided)
   ```bash
   # e.g., npm install / pip install -r requirements.txt / go mod download
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Fill in required values
   ```

4. **Run the application**
   ```bash
   # e.g., npm run dev / python -m app / go run ./cmd/server
   ```

---

## Running Tests

_No test framework is configured yet._

Once tests exist, document the commands here:

```bash
# Run all tests
# e.g., npm test / pytest / go test ./...

# Run tests with coverage
# e.g., npm run test:coverage / pytest --cov

# Run a single test file
# e.g., npm test -- path/to/file.test.ts
```

---

## Code Conventions

_No linting or formatting configuration exists yet. Document conventions here once they are established._

### Recommended practices to establish early

- Add an `.editorconfig` for cross-editor consistency (indentation, line endings, charset).
- Configure a formatter (e.g., Prettier, Black, gofmt) and run it in CI.
- Configure a linter (e.g., ESLint, Ruff, golangci-lint) with project-specific rules.
- Enforce conventions via pre-commit hooks or a CI check.

### General guidelines for AI assistants

- **Read before editing.** Always read existing files before modifying them.
- **Minimal changes.** Only change what is necessary for the current task.
- **No speculative additions.** Do not add features, refactors, or "improvements" that were not requested.
- **No dead code.** Remove code that is no longer used rather than commenting it out.
- **Security first.** Never introduce SQL injection, XSS, command injection, or other OWASP Top 10 vulnerabilities.
- **No secrets in code.** Credentials, API keys, and tokens must live in environment variables or a secrets manager — never in source files.

---

## Git Workflow

### Branch naming

| Purpose        | Pattern                        | Example                          |
|----------------|--------------------------------|----------------------------------|
| Feature        | `feature/<short-description>`  | `feature/user-auth`              |
| Bug fix        | `fix/<short-description>`      | `fix/login-redirect`             |
| Chore / CI     | `chore/<short-description>`    | `chore/update-dependencies`      |
| Claude AI work | `claude/<task-id>`             | `claude/claude-md-mlych2a1c88rlnc8-5fPkP` |

### Commit style

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>

[optional body]
```

Common types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`.

Examples:
```
feat(auth): add JWT refresh token support
fix(api): return 404 when user not found
docs: add CLAUDE.md with project conventions
```

### Pull request process

1. Open a PR from your feature branch targeting `main`.
2. Fill in the PR template (summary + test plan).
3. Ensure CI passes before requesting review.
4. Squash-merge when approved.

---

## CI / CD

_No CI/CD pipeline is configured yet._

Once added, document the pipeline stages here (lint → test → build → deploy) and any required
environment secrets that must be configured in the repository settings.

---

## Environment Variables

_No environment variables are required yet._

Once the application needs configuration, maintain a `.env.example` file at the repository root
listing every required variable with a description and a safe placeholder value. Never commit
actual secrets.

---

## Key Decisions Log

Use this section to record significant architectural or tooling decisions as they are made.

| Date       | Decision                        | Rationale                       |
|------------|---------------------------------|---------------------------------|
| 2026-02-22 | Repository created (empty)      | Initial setup                   |

---

## Updating This File

Keep CLAUDE.md current as the project evolves:

- Add the tech stack details as soon as a language/framework is chosen.
- Document the test command the moment a test framework is added.
- Record environment variables in the table above whenever a new one is introduced.
- Add a new row to the Key Decisions Log for any significant architectural choice.
