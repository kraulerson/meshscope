# Module: Framework / Meta-Tool / Development Orchestrator
# Covers: Dev frameworks, build systems, compliance enforcement tools, LLM orchestrators,
#         code generation frameworks, linters, CI/CD tools, project scaffolders

<!-- ENGINEER:CONTEXT -->
This project is a framework or meta-tool — software that governs, scaffolds, or orchestrates other software development. Evaluate it with the understanding that the project's failures do not just affect itself but propagate into every project built with it. The stakes are higher than a standalone application: a flawed rule or broken hook silently corrupts downstream output.
<!-- /ENGINEER:CONTEXT -->

<!-- ENGINEER:CATEGORIES -->
8. **Enforcement Integrity**
   - What percentage of the framework's rules are mechanically enforced (hooks, scripts, checks, pre-commit gates) vs. relying on downstream compliance (LLM following instructions, developer reading docs)?
   - Where enforcement relies on an external actor following instructions, how robust is that reliance? What happens when instructions are ignored or misinterpreted?
   - If the framework claims a layered defense model, is it actually implemented? Trace each enforcement concern through all layers and identify where redundant coverage exists vs. single points of failure.
   - What happens if a hook fails silently? What happens if a config is misconfigured? Does the framework fail open (dangerous) or fail closed (safe)?

9. **Extensibility and Modularity**
   - Can new platforms, languages, or tooling be added without modifying core files?
   - Is there a clean plugin or profile interface, or does extending require forking?
   - Are extension points documented with examples?
   - What is the coupling between core and extensions? Could an extension break the core?

10. **Template and Sync Mechanism**
    - If the framework uses a template/sync model, how are updates propagated to downstream projects?
    - What happens when a downstream project diverges from the template?
    - Is there merge conflict resolution, or does sync clobber local changes?
    - Can projects selectively adopt template updates?

11. **Cross-Platform Credibility**
    - Does the framework genuinely handle platform-specific concerns, or does it operate at a layer above where real platform problems live?
    - Are platform-specific profiles substantively different, or are they cosmetic variations?
    - Would a platform specialist (iOS dev, Android dev, DevOps engineer) find the platform-specific rules useful or naive?

12. **Context and Scale Limits**
    - How does the framework perform on projects with 100+ files? 500+?
    - If the framework feeds context to an LLM, what happens when the context window fills?
    - Does the framework degrade gracefully under scale, or does it break silently?
    - Can it handle monorepo structures, multi-service architectures, or polyglot codebases?

13. **Comparison to Simpler Approaches**
    - What does this framework provide that a well-written README, a .cursorrules file, a CLAUDE.md, pre-commit hooks, or standard linters do not?
    - Is the added complexity justified by added capability?
    - At what project size or team size does this framework start providing net value over simpler alternatives?
<!-- /ENGINEER:CATEGORIES -->

<!-- ENGINEER:OUTPUT -->
- An "Enforcement Map" showing each rule/concern and the layers that enforce it (mechanical, advisory, not enforced)
- A "Complexity vs. Value" analysis comparing this to at least 3 simpler alternative approaches
<!-- /ENGINEER:OUTPUT -->

<!-- CIO:CONTEXT -->
This project is a framework or meta-tool that governs how software is developed. Evaluate it as a development governance layer — considering whether it creates or reduces risk, whether it can be standardized across teams, and whether it introduces vendor lock-in or single points of failure in the development process itself.
<!-- /CIO:CONTEXT -->

<!-- CIO:CATEGORIES -->
9. **Development Governance Model**
   - Does the framework enable centralized governance of development standards?
   - Can rules and policies be updated centrally and propagated to all teams?
   - Is there separation between who defines rules and who is governed by them?
   - Does the framework produce compliance evidence that auditors would accept?

10. **Lock-In and Exit Strategy**
    - If the framework is abandoned or becomes unsuitable, what is the migration path?
    - Do projects built with the framework have any dependency on it at runtime, or only at development time?
    - What intellectual property, configurations, or processes are locked inside the framework's ecosystem?
    - How much rework is required to replace this with an alternative approach?

11. **LLM Dependency Risk** (if applicable)
    - If the framework depends on an LLM service, what happens when the API changes, pricing changes, or the service is unavailable?
    - Is there a fallback for LLM-dependent functionality?
    - What is the per-project or per-developer cost of LLM API usage?
    - Does the framework's reliance on a specific LLM vendor create unacceptable vendor concentration risk?
<!-- /CIO:CATEGORIES -->

<!-- CIO:OUTPUT -->
- A "Governance Maturity Assessment" evaluating the framework's readiness for enterprise-scale governance
<!-- /CIO:OUTPUT -->

<!-- SECURITY:CONTEXT -->
This project is a framework or meta-tool that sits between developers (or an LLM) and the code that gets produced. Evaluate it as a supply chain component — a compromised or flawed framework silently injects vulnerabilities into every downstream project. Also evaluate any LLM integration as a trust boundary where adversarial input can influence code generation.
<!-- /SECURITY:CONTEXT -->

<!-- SECURITY:CATEGORIES -->
10. **Supply Chain Position Risk**
    - The framework is a supply chain component for every project that uses it. What happens if the framework's source repository is compromised?
    - Is there integrity verification (checksums, signatures) on framework components?
    - Can a malicious rule, hook, or template update inject code into downstream projects?
    - What is the blast radius of a compromised framework update?

11. **LLM Security Boundary** (if applicable)
    - If the framework sends instructions to an LLM, what prevents prompt injection through project files, user input, or dependency contents?
    - If a developer opens a file containing adversarial content, can it influence the LLM's behavior within the framework?
    - Does the framework leak sensitive project information (API keys, credentials, internal architecture) to external APIs?
    - What data residency and retention implications exist from sending project context to external services?

12. **Defense-in-Depth Chain Analysis** (if the framework claims layered enforcement)
    - For each security-relevant concern, trace the FULL enforcement chain — from rules (instruction layer) through hooks (mechanical layer) through any post-hoc validation.
    - Map which layers cover which concerns and identify: (a) concerns with redundant multi-layer coverage where mechanical enforcement catches instruction non-compliance, (b) concerns with only single-layer coverage and no backup, (c) concerns where all layers ultimately depend on instruction compliance with no mechanical fallback.
    - Read hook/script source code, not just descriptions, to verify what each enforcement mechanism concretely does.
    - Produce a **Defense Chain Map** showing each security concern and which layers actually cover it.
    - Evaluate whether mechanical enforcement layers (hooks, scripts) can themselves be bypassed, fail silently, or have coverage gaps.

13. **Framework Configuration Security**
    - Can a misconfigured framework weaken the security posture of downstream projects without warning?
    - Are there secure defaults, or does misconfiguration fail open?
    - Is there validation that detects insecure configurations?
<!-- /SECURITY:CATEGORIES -->

<!-- SECURITY:OUTPUT -->
- A **Defense Chain Map** showing each security concern mapped to its enforcement layers with gap identification
- A **Supply Chain Risk Assessment** evaluating the framework's position as a transitive dependency of all downstream projects
<!-- /SECURITY:OUTPUT -->

<!-- LEGAL:CONTEXT -->
This project is a framework or meta-tool used to build other software. Evaluate legal risks considering that the framework's license, dependencies, and operational behavior affect not just itself but every project built with it. Also evaluate any AI/LLM integration for IP ownership implications of generated output.
<!-- /LEGAL:CONTEXT -->

<!-- LEGAL:CATEGORIES -->
9. **Downstream License Propagation**
   - Does the framework's license impose obligations on projects built with it?
   - If the framework generates files, templates, or boilerplate, what license applies to the generated output?
   - Could using this framework create license obligations that surprise downstream users?

10. **AI-Generated Code Ownership and IP** (if applicable)
    - Code produced under this framework may be generated or influenced by an LLM. What is the IP status of that code?
    - Does the framework address the legal ambiguity around AI-generated code ownership?
    - If the LLM produces code that infringes on existing patents or copyrights, who is liable?
    - Does the framework have any mechanism to check for or flag potential IP infringement?
    - How does this interact with the LLM provider's terms of service regarding output ownership?
    - Are there export control implications for AI-generated code?

11. **Contractual Implications for Users**
    - If an employee uses this framework, does it affect their employment IP assignment agreements?
    - If a contractor or consulting firm uses this framework for client work, what are the implications?
    - Could use of this framework violate non-disclosure agreements through data sent to external APIs?
<!-- /LEGAL:CATEGORIES -->

<!-- LEGAL:OUTPUT -->
- An "AI-Generated Code IP Risk Assessment" covering ownership, infringement, and provider ToS implications (if applicable)
- A "Downstream License Impact" analysis showing how the framework's license affects projects built with it
<!-- /LEGAL:OUTPUT -->

<!-- TECHUSER:CONTEXT -->
This project is a framework or meta-tool designed to help you build software more effectively. You are evaluating whether a technically literate non-coder can set this up, configure it for a project, and benefit from its enforcement and guidance without understanding the framework's internals.
<!-- /TECHUSER:CONTEXT -->

<!-- TECHUSER:CATEGORIES -->
11. **Framework Mental Model**
    - Can you understand HOW this framework works (not just what it does) without reading source code?
    - Is the conceptual model (rules, hooks, profiles, templates, etc.) explained clearly?
    - Can you predict what the framework will do in a given situation, or is its behavior opaque?
    - Is there a diagram, flowchart, or visual explanation of how the pieces fit together?

12. **Configuration for New Projects**
    - How do you apply this framework to a brand new project? Is the process documented step-by-step?
    - Can you select a pre-built profile for your project type, or must you configure from scratch?
    - What decisions do you need to make during setup, and are they explained well enough to choose correctly?
    - If you choose wrong, can you change course without starting over?

13. **Comparison to Going Without**
    - What is the concrete benefit of using this framework vs. the tool it wraps with a well-written instruction file?
    - Does the framework solve problems you actually have, or problems you did not know existed?
    - Is the complexity justified by the benefit for a non-coder user?
    - Would a simpler approach (a checklist, a template, a set of custom instructions) achieve 80% of the benefit at 20% of the complexity?
<!-- /TECHUSER:CATEGORIES -->

<!-- TECHUSER:OUTPUT -->
- A "Framework Value Justification" comparing concrete benefits against the setup and learning investment for a non-coder user
<!-- /TECHUSER:OUTPUT -->

<!-- REDTEAM:CONTEXT -->
This project is a framework or meta-tool that governs other software development. Prioritize supply chain and propagation attack vectors: can a compromised framework component inject malicious code into downstream projects? Can template files, hooks, or scaffolded configurations be manipulated to weaken the security posture of projects built with this framework? Test for: template injection, hook bypass paths, integrity verification gaps, and whether the framework's own update mechanism can be hijacked.
<!-- /REDTEAM:CONTEXT -->

<!-- REDTEAM:CATEGORIES -->
<!-- /REDTEAM:CATEGORIES -->

<!-- REDTEAM:OUTPUT -->
<!-- /REDTEAM:OUTPUT -->
