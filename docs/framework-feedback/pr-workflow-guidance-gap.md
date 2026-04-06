# Framework Feedback: Agent Must Guide Orchestrator Through PR Workflow

**Project:** meshscope
**Session:** 2026-04-05
**Category:** Missing agent instruction

---

## What happened

After committing framework fixes to a feature branch, the agent created PR #1 and reported the URL. But the agent did not:
1. Explain that the Orchestrator needs to review and merge the PR before work can continue
2. Explain what "CI passes" means or how to check it
3. Explain where to find the merge button or what it does
4. Pause and wait for confirmation that the merge was complete before proceeding

The Orchestrator had to ask "Does this mean I need to accept the pull request?" — indicating the handoff was unclear.

## Why it matters

The Solo Orchestrator Framework targets experienced technologists who may not have daily Git/GitHub PR workflow experience. The Orchestrator's Competency Matrix (Intake Section 6.2) explicitly identifies domains where the Orchestrator needs more support. DevOps is marked "Yes" but PR-based branching workflow is a specific sub-skill that shouldn't be assumed.

More broadly: every time the agent creates a PR, there is a mandatory human action (review + merge) before development can continue. If the agent doesn't clearly communicate this, the Orchestrator may not realize work is blocked on them.

## Recommended fix

**In the Builder's Guide, Phase 2 (The Build Loop):** Add a standard PR handoff instruction that the agent must follow every time a PR is created:

```markdown
### PR Handoff Protocol

When the agent creates a pull request, it MUST:
1. Report the PR URL
2. State what the PR contains (1-2 sentence summary)
3. Explain what the Orchestrator needs to do:
   "This PR needs your review and merge before we can continue.
   Go to [URL], verify CI checks pass (green checkmarks), then
   click 'Merge pull request'."
4. Wait for the Orchestrator to confirm the merge is complete
5. Only then: switch to main, pull, and create the next branch

Do not continue development until the Orchestrator confirms the
merge. The agent cannot merge PRs — this is a human gate.
```

**In CLAUDE.md (agent instructions):** Add to the "When to Ask the Orchestrator" section:

```markdown
- After creating a PR: always explain that the Orchestrator must
  review and merge it before work continues. Do not assume familiarity
  with PR workflow. State the specific action needed and wait for
  confirmation.
```

## Additional observation

The agent should also explain the PR workflow once (early in Phase 2) as part of establishing the development rhythm:

```
"From this point forward, all changes go through pull requests.
The workflow is:
1. I work on a feature branch
2. When ready, I push and create a PR
3. GitHub runs automated checks (CI) — takes 2-5 minutes
4. You review the PR at the GitHub URL I provide
5. If checks pass (green), you click 'Merge pull request'
6. I pull the changes and start the next feature

I'll remind you each time a PR needs your action."
```

This one-time explanation at the start of Phase 2 sets expectations for the entire construction phase.
