# Module: Desktop Application
# Covers: Electron, Tauri, native desktop (WPF, SwiftUI/AppKit, GTK), cross-platform desktop

<!-- ENGINEER:CONTEXT -->
This project is a desktop application. Evaluate it with the expectations of production desktop software — platform integration, window/process management, file system access, OS-level permissions, installer/updater mechanics, and performance on user hardware rather than managed infrastructure.
<!-- /ENGINEER:CONTEXT -->

<!-- ENGINEER:CATEGORIES -->
8. **Platform Integration**
   - Does the app integrate with OS-native features appropriately? (system tray, notifications, file associations, drag-and-drop, clipboard)
   - Does it respect OS conventions? (menu bar on macOS, taskbar on Windows, keyboard shortcuts)
   - Is the app DPI-aware and does it handle multi-monitor setups correctly?
   - Does it integrate with OS accessibility APIs? (screen readers, high contrast, reduced motion)

9. **Resource Management**
   - Is memory usage reasonable at idle and under load?
   - Does the app clean up resources on exit? (temp files, sockets, child processes)
   - If Electron/Tauri, is the bundle size appropriate? Are unnecessary Chromium features disabled?
   - Is CPU usage reasonable at idle? (no polling loops, no unnecessary wake-ups)
   - Is disk I/O managed? (not constantly writing to disk, respecting SSDs)

10. **Installer, Updater, and Lifecycle**
    - Is there a proper installer for each target platform? (MSI/NSIS for Windows, DMG for macOS, AppImage/deb/rpm for Linux)
    - Is there an auto-update mechanism? Is it secure? (signed updates, HTTPS, rollback capability)
    - Does the app handle first-run setup gracefully?
    - Is uninstallation clean? (no leftover files, registry entries, or services)
    - How are settings migrated between versions?

11. **Offline and Local-First**
    - Does the app function fully offline, or does it depend on network services?
    - If it requires a network connection, does it fail gracefully when offline?
    - Is user data stored locally in a standard, portable format?
    - Can the user export/backup their data without special tools?

12. **Security (Desktop-Specific)**
    - Does the app request minimum necessary OS permissions?
    - If Electron, is the renderer process sandboxed? Is `nodeIntegration` disabled? Is `contextIsolation` enabled?
    - Are IPC channels between processes validated and scoped?
    - Does the app handle file paths safely? (no path traversal, no symlink attacks)
    - If the app auto-updates, are updates verified before installation?
<!-- /ENGINEER:CATEGORIES -->

<!-- ENGINEER:OUTPUT -->
- A "Platform Readiness Matrix" showing feature completeness and compliance per OS (Windows, macOS, Linux)
<!-- /ENGINEER:OUTPUT -->

<!-- CIO:CONTEXT -->
This project is a desktop application intended for deployment on end-user machines. Evaluate it considering deployment at scale, endpoint management integration, update distribution, support burden across hardware diversity, and the security implications of software running with user-level (or elevated) OS privileges.
<!-- /CIO:CONTEXT -->

<!-- CIO:CATEGORIES -->
9. **Enterprise Deployment and Management**
   - Can the app be deployed via enterprise tools? (SCCM, Intune, Munki, Jamf, Ansible)
   - Can the app be configured via group policy, MDM profiles, or managed configuration files?
   - Is silent installation supported for mass deployment?
   - Can updates be staged, tested, and rolled out gradually across an organization?

10. **Hardware and OS Compatibility**
    - What are the minimum hardware requirements? Are they documented?
    - What OS versions are supported? Is there a lifecycle/deprecation policy?
    - What happens on unsupported hardware or OS versions?
    - What is the testing burden for the hardware/OS matrix?
<!-- /CIO:CATEGORIES -->

<!-- CIO:OUTPUT -->
- An "Enterprise Deployment Feasibility" assessment covering deployment methods, configuration management, and update logistics
<!-- /CIO:OUTPUT -->

<!-- SECURITY:CONTEXT -->
This project is a desktop application running on end-user machines with local OS access. Evaluate it understanding that desktop apps have broad attack surface — file system access, process execution, network communication, and potential privilege escalation. If Electron-based, evaluate the web-to-native bridge as a critical security boundary.
<!-- /SECURITY:CONTEXT -->

<!-- SECURITY:CATEGORIES -->
10. **Local Privilege and Sandbox**
    - What OS-level permissions does the app require? Is each justified?
    - If Electron/Tauri, is the renderer properly sandboxed from native APIs?
    - Can a vulnerability in the UI layer escalate to OS-level access?
    - Does the app follow principle of least privilege?

11. **IPC and Process Security**
    - If the app uses multiple processes, are IPC channels authenticated and validated?
    - Can a malicious local process communicate with the app's IPC channels?
    - Are child processes spawned with minimal permissions?

12. **Update Channel Security**
    - Are updates delivered over HTTPS with certificate verification?
    - Are update packages signed and verified before installation?
    - Can the update channel be hijacked via DNS spoofing or MITM?
    - Is there a rollback mechanism if an update introduces issues?
<!-- /SECURITY:CATEGORIES -->

<!-- SECURITY:OUTPUT -->
- A "Desktop Threat Model" mapping attack vectors specific to desktop deployment (local attackers, malicious files, update hijacking, IPC abuse)
<!-- /SECURITY:OUTPUT -->

<!-- LEGAL:CONTEXT -->
This project is a desktop application distributed to end users. Evaluate legal risks around software distribution, OS-specific compliance requirements, telemetry/data collection on user devices, and the licensing implications of bundling runtime dependencies.
<!-- /LEGAL:CONTEXT -->

<!-- LEGAL:CATEGORIES -->
9. **Desktop Distribution Licensing**
   - If the app bundles a runtime (Electron/Chromium, .NET, JVM), are all bundled component licenses satisfied?
   - Does distribution via platform-specific channels (Microsoft Store, Mac App Store) impose additional requirements?
   - Are code signing certificates from a recognized CA? Are they valid and unexpired?

10. **On-Device Data and Privacy**
    - Does the app collect telemetry, crash reports, or usage analytics from user devices?
    - Is data collection disclosed and consented to?
    - Does the app access user files, clipboard, or other local data beyond its stated purpose?
    - Is there compliance with platform-specific privacy requirements? (macOS privacy permissions, Windows privacy settings)
<!-- /LEGAL:CATEGORIES -->

<!-- LEGAL:OUTPUT -->
<!-- /LEGAL:OUTPUT -->

<!-- TECHUSER:CONTEXT -->
This project is a desktop application. You are evaluating whether a technically literate non-coder could install, configure, and use this application on their own machine, and potentially distribute it within their organization.
<!-- /TECHUSER:CONTEXT -->

<!-- TECHUSER:CATEGORIES -->
11. **Installation Experience**
    - Is there a one-click installer, or does setup require technical steps?
    - Does the installer handle prerequisites automatically?
    - Is the app signed and trusted by the OS? (no security warnings during installation)
    - Does it work immediately after installation, or is additional configuration required?

12. **Building and Customization**
    - If you wanted to build this app from source, is the process documented?
    - Can you customize the app's behavior through settings/preferences without touching code?
    - If the app needs to be rebuilt after customization, is the build process approachable?
<!-- /TECHUSER:CATEGORIES -->

<!-- TECHUSER:OUTPUT -->
<!-- /TECHUSER:OUTPUT -->

<!-- REDTEAM:CONTEXT -->
This project is a desktop application running on user hardware. Prioritize desktop-specific attack vectors: local privilege escalation, IPC channel abuse, file system path traversal, DLL/dylib hijacking, unsigned or weakly signed binaries, auto-updater man-in-the-middle, insecure local storage of credentials, and abuse of OS-level permissions granted to the application.
<!-- /REDTEAM:CONTEXT -->

<!-- REDTEAM:CATEGORIES -->
<!-- /REDTEAM:CATEGORIES -->

<!-- REDTEAM:OUTPUT -->
<!-- /REDTEAM:OUTPUT -->
