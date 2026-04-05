# Project Review Suite

A modular evaluation system that critically reviews any software project from six independent professional perspectives. Each review runs in its own Claude Code CLI instance with full project access.

## Architecture

```
Projects/
├── README.md
├── compose.sh              # Assembles base + module into a runnable prompt
├── run-reviews.sh          # Orchestrates review execution
├── bases/                  # Reviewer personas — project-agnostic scaffolds
│   ├── 01-senior-engineer.md
│   ├── 02-cio.md
│   ├── 03-security.md
│   ├── 04-legal.md
│   ├── 05-technical-user.md
│   └── 06-red-team-review.md
└── modules/                # Project-type domain categories — swappable
    ├── web-app.md
    ├── mobile-app.md
    ├── api-service.md
    ├── cli-tool.md
    ├── framework.md
    └── desktop-app.md
```

**Bases** contain the reviewer persona, evaluation methodology, universal categories (architecture, code quality, dependencies, testing, documentation, error handling, performance), output format, and constraints. These never change between project types.

**Modules** contain project-type-specific categories injected into each base via placeholder substitution. Each module has sections for all six reviewers, delimited by HTML comment tags. The red team module sections provide domain-specific attack vector context (e.g., web-specific XSS vectors, mobile-specific local storage attacks) while the red team base template contains the universal offensive testing methodology.

**compose.sh** extracts the reviewer-specific section from a module and injects it into the corresponding base template, producing a complete prompt ready for Claude Code.

## Reviewers

| # | Reviewer | Focus |
|---|----------|-------|
| 1 | Senior Software Engineer (20+ yr) | Architecture, code quality, enforcement, scalability |
| 2 | CIO (startup to Fortune 500) | TCO, vendor risk, governance, strategic positioning |
| 3 | SVP IT Security | Attack surfaces, data protection, compliance, enforcement vs. theater |
| 4 | Corporate Legal | Licensing, IP, privacy, regulatory, liability |
| 5 | Technical User (non-coder) | Onboarding, usability, documentation, personal/enterprise viability |
| 6 | Red Team / Offensive Security | Exploitable vulnerabilities, attack chains, proof-of-concept exploits |

## Modules

| Module | Use For |
|--------|---------|
| `web-app` | SPAs, full-stack web apps, server-rendered apps, PWAs |
| `mobile-app` | iOS native, Android native, cross-platform (React Native, Flutter, KMP) |
| `api-service` | REST APIs, GraphQL, gRPC, microservices, serverless |
| `cli-tool` | Command-line tools, build tools, automation utilities |
| `framework` | Dev frameworks, LLM orchestrators, build systems, compliance tools |
| `desktop-app` | Electron, Tauri, native desktop (WPF, SwiftUI, GTK) |

## Usage

### Run all 6 reviews for a project

```bash
cd /path/to/your-project
/path/to/evaluation-prompts/Projects/run-reviews.sh web-app
```

### Run specific reviewers

```bash
# Engineer + Security only
/path/to/evaluation-prompts/Projects/run-reviews.sh mobile-app 1 3

# CIO + Legal + TechUser
/path/to/evaluation-prompts/Projects/run-reviews.sh api-service 2 4 5

# Red team only
/path/to/evaluation-prompts/Projects/run-reviews.sh web-app 6
```

### Set project path externally

```bash
PROJECT_DIR=/path/to/project /path/to/evaluation-prompts/Projects/run-reviews.sh cli-tool
```

### Compose a prompt without running it

```bash
# Print to stdout (inspect before running)
/path/to/evaluation-prompts/Projects/compose.sh engineer web-app

# Write to file
/path/to/evaluation-prompts/Projects/compose.sh security mobile-app ./security-prompt.md

# Then run manually
cd /path/to/project
claude -p "$(cat ./security-prompt.md)"
```

## Output

Each review writes a markdown file to the project root:

| File | Reviewer |
|------|----------|
| `senior-engineer-review-v1.md` | Senior Software Engineer |
| `cio-review-v1.md` | CIO |
| `security-review-v1.md` | SVP IT Security |
| `legal-review-v1.md` | Corporate Legal |
| `technical-user-review-v1.md` | Technical User |
| `red-team-review-v1.md` | Red Team / Offensive Security |

## Adding a New Module

1. Create `modules/your-type.md`
2. Add sections for each reviewer using the tag format:

```markdown
<!-- ENGINEER:CONTEXT -->
Project-type context for the engineer reviewer.
<!-- /ENGINEER:CONTEXT -->

<!-- ENGINEER:CATEGORIES -->
8. **Domain-Specific Category**
   - Evaluation criteria...
<!-- /ENGINEER:CATEGORIES -->

<!-- ENGINEER:OUTPUT -->
- Additional output requirements for this project type
<!-- /ENGINEER:OUTPUT -->
```

Required sections per reviewer: `CONTEXT`, `CATEGORIES`, `OUTPUT`
Reviewer tags: `ENGINEER`, `CIO`, `SECURITY`, `LEGAL`, `TECHUSER`, `REDTEAM`

Categories should start numbering at 8+ (universal categories are 1-7).
`OUTPUT` sections can be empty (just the tags with nothing between) if no extra output is needed.

3. Test composition: `./compose.sh engineer your-type`

## Design Decisions

**Why separate bases and modules?** A reviewer's evaluation methodology, persona depth, and output structure are stable across project types. Only the domain-specific categories change. This prevents duplicating ~70% of each prompt across every project type.

**Why HTML comment tags?** They are invisible in rendered markdown, parseable with simple tools, and do not conflict with the prompt content itself.

**Why not a single config file?** Each module's content is substantial (500-1000 words per reviewer section). YAML or JSON would make the domain-specific evaluation criteria unreadable and uneditable.

**Why sequential execution?** Each review takes 5-15 minutes and produces substantial output. Reading each review before running the next lets you catch patterns and decide if you want to adjust subsequent reviews.

## Notes

- All reviews are **read-only** — no project files are modified
- Each review runs in a separate Claude Code instance with no shared context
- Prompts instruct Claude to cite specific files and line numbers
- Reviews are intentionally critical — if something is weak, they will say so
- The legal review includes a disclaimer that it is risk analysis, not legal advice
- The security review evaluates controls assuming worst-case non-compliance
