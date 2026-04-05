# Module: CLI Tool / Utility
# Covers: Command-line tools, build tools, automation scripts, developer utilities

<!-- ENGINEER:CONTEXT -->
This project is a command-line tool or utility. Evaluate it with the expectations of production CLI software — argument parsing, input/output handling, exit codes, composability with other tools, cross-platform behavior, and the Unix philosophy where applicable.
<!-- /ENGINEER:CONTEXT -->

<!-- ENGINEER:CATEGORIES -->
8. **CLI Design and UX**
   - Is the argument/flag interface intuitive and consistent?
   - Does the tool provide useful help text (`--help`, man page, usage examples)?
   - Are exit codes meaningful and documented? (0 for success, non-zero for specific failure types)
   - Is output structured for both human readability and machine parsing? (quiet mode, JSON output, verbose mode)
   - Does the tool follow platform conventions? (GNU long/short flags on Linux, standard patterns on the target platform)

9. **Composability and Piping**
   - Can the tool read from stdin and write to stdout for use in pipelines?
   - Does it handle large inputs via streaming, or does it load everything into memory?
   - Are error messages written to stderr (not stdout)?
   - Can the tool's output be consumed by other common tools? (jq, awk, grep)

10. **Configuration and Defaults**
    - Is there a config file format? Is it documented?
    - Is the config file location predictable? (XDG base dirs, home directory, project-local)
    - Do sensible defaults exist so the tool works without a config file?
    - Is the precedence order clear? (CLI flags > env vars > config file > defaults)
    - Are environment variable overrides supported and documented?

11. **Cross-Platform Behavior**
    - Does the tool work on Linux, macOS, and Windows? If not, is this documented?
    - Are file path separators, line endings, and shell differences handled?
    - Are there platform-specific dependencies that limit portability?
    - Is the installation method available on all target platforms?

12. **Installation and Distribution**
    - Is the tool distributed via standard package managers? (npm, pip, brew, apt, cargo, go install)
    - Can it be installed as a single binary without runtime dependencies?
    - Is the installation process a single command?
    - Is the version easily discoverable? (`--version`)
<!-- /ENGINEER:CATEGORIES -->

<!-- ENGINEER:OUTPUT -->
- A "CLI Standards Compliance" section evaluating adherence to platform CLI conventions
<!-- /ENGINEER:OUTPUT -->

<!-- CIO:CONTEXT -->
This project is a command-line tool or utility. Evaluate it as a tool that may be adopted by developers or operations staff — considering standardization, support burden, security review requirements, and whether it solves a problem worth tooling for.
<!-- /CIO:CONTEXT -->

<!-- CIO:CATEGORIES -->
9. **Standardization and Control**
   - If deployed across a team, how do you ensure everyone uses the same version?
   - Can the tool be distributed via internal package repositories?
   - Is usage auditable? Can you tell who ran what and when?
   - Does the tool phone home or send telemetry? Is it configurable?

10. **Alternatives Assessment**
    - Does this tool duplicate functionality available in existing system tools or established alternatives?
    - What is the marginal value over shell scripts, makefiles, or existing CLI tools?
    - Is the maintenance burden of another tool in the chain justified?
<!-- /CIO:CATEGORIES -->

<!-- CIO:OUTPUT -->
<!-- /CIO:OUTPUT -->

<!-- SECURITY:CONTEXT -->
This project is a command-line tool that executes on developer or operator machines. Evaluate it as software that may have elevated privileges, access to credentials, and the ability to modify files and execute commands on the local system.
<!-- /SECURITY:CONTEXT -->

<!-- SECURITY:CATEGORIES -->
10. **Local System Security**
    - Does the tool require elevated privileges (root/admin)? Is that necessary?
    - Does the tool write to or read from sensitive system locations?
    - Is file access scoped to intended directories, or could path traversal reach unintended locations?
    - Does the tool execute shell commands? If so, are inputs sanitized against command injection?

11. **Credential Handling**
    - If the tool handles credentials, are they stored securely? (system keychain, not plaintext files)
    - Are credentials transmitted securely?
    - Is the credential scope minimal? (principle of least privilege)
    - Are credentials cleared from memory after use?

12. **Update and Integrity**
    - Is the tool's update mechanism secure? (signed releases, checksum verification, HTTPS only)
    - Can a malicious update be pushed to users?
    - Are release artifacts reproducible or at minimum verifiable?
<!-- /SECURITY:CATEGORIES -->

<!-- SECURITY:OUTPUT -->
- A "Local Privilege Assessment" documenting every elevated access the tool requires and whether each is justified
<!-- /SECURITY:OUTPUT -->

<!-- LEGAL:CONTEXT -->
This project is a command-line tool intended for distribution. Evaluate legal risks around distribution method, dependency bundling, license compliance for statically linked libraries, and any data the tool collects or transmits.
<!-- /LEGAL:CONTEXT -->

<!-- LEGAL:CATEGORIES -->
9. **Distribution-Specific Licensing**
   - If the tool bundles or statically links dependencies, are all license obligations met for that distribution method?
   - Does distribution via specific package managers impose additional obligations?
   - Is source code availability required by any dependency license?

10. **Telemetry and Data Collection**
    - Does the tool collect or transmit any data? (usage analytics, crash reports, version checks)
    - If so, is the user informed and given the ability to opt out?
    - Does any data collection comply with privacy regulations in target markets?
<!-- /LEGAL:CATEGORIES -->

<!-- LEGAL:OUTPUT -->
<!-- /LEGAL:OUTPUT -->

<!-- TECHUSER:CONTEXT -->
This project is a command-line tool. You are evaluating whether a technically literate non-coder comfortable with the terminal could install, configure, and use this tool effectively for its intended purpose.
<!-- /TECHUSER:CONTEXT -->

<!-- TECHUSER:CATEGORIES -->
11. **Installation Simplicity**
    - Is the installation a single command?
    - Are there prerequisites beyond a standard OS installation?
    - What happens if installation fails? Is there a fallback method?
    - Is uninstallation clean and documented?

12. **Discoverability and Help**
    - Can you figure out how to use the tool from `--help` alone?
    - Are common use cases shown with examples?
    - Is there a cheat sheet or quick reference?
    - Are error messages actionable? (do they tell you what to do, not just what went wrong)
<!-- /TECHUSER:CATEGORIES -->

<!-- TECHUSER:OUTPUT -->
<!-- /TECHUSER:OUTPUT -->

<!-- REDTEAM:CONTEXT -->
This project is a command-line tool or utility. Prioritize CLI-specific attack vectors: command injection through argument parsing, path traversal in file operations, symlink following, unsafe temporary file handling, shell expansion abuse, privilege escalation if the tool runs as root or with elevated permissions, and insecure handling of credentials passed via arguments, environment variables, or config files.
<!-- /REDTEAM:CONTEXT -->

<!-- REDTEAM:CATEGORIES -->
<!-- /REDTEAM:CATEGORIES -->

<!-- REDTEAM:OUTPUT -->
<!-- /REDTEAM:OUTPUT -->
