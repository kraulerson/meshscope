# Module: Mobile Application
# Covers: iOS native, Android native, cross-platform (React Native, Flutter, KMP)

<!-- ENGINEER:CONTEXT -->
This project is a mobile application. Evaluate it with the expectations of production mobile software — platform guidelines compliance, lifecycle management, offline behavior, performance on constrained devices, app store readiness, and the specific challenges of mobile development (signing, provisioning, build variants, deep linking).
<!-- /ENGINEER:CONTEXT -->

<!-- ENGINEER:CATEGORIES -->
8. **Platform Compliance**
   - Does the app follow platform-specific design guidelines? (Material Design for Android, Human Interface Guidelines for iOS)
   - Are platform-specific APIs used correctly? (permissions, background processing, notifications, storage)
   - Is the app prepared for app store review? (privacy labels, entitlements, content ratings, required metadata)
   - If cross-platform, are platform differences handled or are they papered over with a lowest-common-denominator approach?

9. **Mobile Lifecycle and State Management**
   - Is the app lifecycle handled correctly? (background, foreground, process death, orientation changes)
   - Is state persisted across process death and configuration changes?
   - Are background tasks managed correctly (not draining battery, respecting OS limits)?
   - Is navigation implemented correctly, including deep linking and back stack management?
   - Is data persistence appropriate? (local database vs. shared preferences vs. keychain vs. file storage)

10. **Performance on Constrained Devices**
    - Is memory usage reasonable? Are there leaks?
    - Does the app perform well on older/lower-end devices, or only on current flagships?
    - Are images and assets sized appropriately? Is there lazy loading?
    - Are network calls efficient? (caching, pagination, compression, minimal payload)
    - Is the app responsive during data loading? (no ANR on Android, no main thread blocking on iOS)

11. **Offline Capability and Data Sync**
    - What happens when the device loses connectivity?
    - Is there meaningful offline functionality, or does the app become unusable?
    - If offline changes are possible, how are conflicts resolved on sync?
    - Is the sync mechanism robust against partial failures?

12. **Build and Release Pipeline**
    - Is the build system configured correctly? (Gradle for Android, Xcode project/SPM for iOS, platform build tools for cross-platform)
    - Are signing configurations, provisioning profiles, and build variants handled properly?
    - Is there a path to CI/CD for automated builds and deployment?
    - Are multiple environments supported? (development, staging, production)
    - Is the app versioning and update strategy sound?

13. **Security (Mobile-Specific)**
    - Is sensitive data stored securely? (Keychain on iOS, EncryptedSharedPreferences/Keystore on Android, not plain SharedPreferences or UserDefaults)
    - Is certificate pinning implemented for sensitive API calls?
    - Is the app protected against reverse engineering? (ProGuard/R8 for Android, no secrets in client code)
    - Are biometric authentication APIs used correctly if applicable?
    - Is the app vulnerable to tapjacking, task hijacking, or intent/URL scheme abuse?
<!-- /ENGINEER:CATEGORIES -->

<!-- ENGINEER:OUTPUT -->
- A "Store Readiness Checklist" for both Google Play and Apple App Store identifying blockers
<!-- /ENGINEER:OUTPUT -->

<!-- CIO:CONTEXT -->
This project is a mobile application intended for distribution via app stores or enterprise deployment. Evaluate it considering distribution costs, device management, update cycles, support burden across device fragmentation, and app store compliance requirements.
<!-- /CIO:CONTEXT -->

<!-- CIO:CATEGORIES -->
9. **Distribution and Update Strategy**
   - What is the app store submission and review process? What is the timeline for updates reaching users?
   - Is there an enterprise distribution option (MDM, private app catalog)?
   - How are critical bug fixes delivered? Can the app be updated without a store release? (CodePush, feature flags)
   - What is the user migration strategy for major version changes?

10. **Device Fragmentation and Support Cost**
    - What OS versions are supported? What devices are targeted?
    - What is the testing burden across the device/OS matrix?
    - What is the expected support cost for device-specific issues?
    - Is there a clear deprecation policy for old OS versions?

11. **App Store Compliance and Monetization**
    - Does the app comply with Apple App Store and Google Play policies?
    - If there are in-app purchases or subscriptions, are they implemented per store requirements?
    - Are the app store commission and payment processing fees factored into the business model?
    - Is the app at risk of store rejection for any reason?
<!-- /CIO:CATEGORIES -->

<!-- CIO:OUTPUT -->
- A "Distribution Cost Model" covering developer account fees, store commissions, testing infrastructure, and support estimates
<!-- /CIO:OUTPUT -->

<!-- SECURITY:CONTEXT -->
This project is a mobile application that runs on user devices. Evaluate it with the expectation that the device may be compromised, the network is untrusted, the binary can be reverse-engineered, and data at rest must be protected. Pay particular attention to local data storage, network communication security, and client-side secrets.
<!-- /SECURITY:CONTEXT -->

<!-- SECURITY:CATEGORIES -->
10. **Mobile Data Storage Security**
    - Is sensitive data stored using platform-secure mechanisms? (iOS Keychain, Android Keystore/EncryptedSharedPreferences)
    - Are database files encrypted? (SQLCipher, Realm encryption, or equivalent)
    - Is app backup configured correctly? (sensitive data excluded from cloud backups)
    - Is the app vulnerable to data extraction on rooted/jailbroken devices?
    - Are temporary files and caches cleaned appropriately?

11. **Network Security (Mobile-Specific)**
    - Is all traffic encrypted via TLS?
    - Is certificate pinning implemented? What happens when pins expire?
    - Is the app configured for Network Security Configuration (Android) / App Transport Security (iOS)?
    - Are API tokens stored and transmitted securely?
    - Is the app vulnerable to man-in-the-middle attacks on untrusted networks?

12. **Binary Protection and Reverse Engineering**
    - Is code obfuscation enabled? (ProGuard/R8 for Android, Swift compilation for iOS)
    - Are there secrets, API keys, or encryption keys embedded in the binary?
    - Is anti-tampering or integrity verification implemented?
    - Can the app detect rooted/jailbroken devices where relevant to security posture?

13. **Platform Permission Model**
    - Are only necessary permissions requested?
    - Are runtime permissions handled correctly with graceful degradation?
    - Are permission rationale messages clear and honest?
    - Are there permissions requested that are disproportionate to the app's stated functionality?
<!-- /SECURITY:CATEGORIES -->

<!-- SECURITY:OUTPUT -->
- A **Mobile OWASP Top 10 Assessment** covering each category from the OWASP Mobile Application Security standard
<!-- /SECURITY:OUTPUT -->

<!-- LEGAL:CONTEXT -->
This project is a mobile application intended for app store distribution. Evaluate legal risks specific to mobile distribution — app store terms compliance, in-app purchase regulations, children's privacy (COPPA), data collection transparency requirements, and the specific privacy disclosure requirements of iOS and Android platforms.
<!-- /LEGAL:CONTEXT -->

<!-- LEGAL:CATEGORIES -->
9. **App Store Terms Compliance**
   - Does the app comply with Apple's App Store Review Guidelines and Google's Developer Program Policies?
   - Are subscription terms presented correctly per each store's requirements?
   - Is the app at risk of removal for policy violations?
   - Are required privacy disclosures (Apple privacy nutrition labels, Google data safety) accurate and complete?

10. **Mobile-Specific Privacy**
    - Does the app comply with Apple's ATT (App Tracking Transparency) requirements?
    - Is the Google Play data safety section accurately filled?
    - Does the app collect device identifiers? Are users informed?
    - If the app is usable by children under 13, does it comply with COPPA and similar laws?
    - Are push notification permissions used appropriately and disclosed?

11. **In-App Purchase and Subscription Law**
    - Are subscription auto-renewal terms clearly disclosed per FTC and EU consumer protection rules?
    - Is the cancellation process clear and accessible?
    - Are free trial terms transparent and non-deceptive?
    - Do in-app purchases comply with consumer protection laws in target markets?
<!-- /LEGAL:CATEGORIES -->

<!-- LEGAL:OUTPUT -->
- An "App Store Compliance Checklist" covering both Apple and Google policy requirements
<!-- /LEGAL:OUTPUT -->

<!-- TECHUSER:CONTEXT -->
This project is a mobile application. You are evaluating whether a technically literate non-coder could build, test, customize, and publish this application — recognizing that mobile development has some of the highest tooling complexity in software (Xcode, Android Studio, signing certificates, provisioning profiles, emulators).
<!-- /TECHUSER:CONTEXT -->

<!-- TECHUSER:CATEGORIES -->
11. **Build Environment Setup**
    - Is the mobile development environment setup documented? (Xcode version, Android Studio version, SDK levels, emulator configuration)
    - Is the setup achievable by someone who has never built a mobile app before?
    - Are platform-specific gotchas documented? (Apple Developer account, code signing, Gradle issues)
    - Is there a clear path to running the app on a physical device for testing?

12. **App Store Publishing Path**
    - Is the app store submission process documented?
    - Can a non-developer handle the app store listing, screenshots, descriptions, and metadata?
    - Are signing, provisioning, and release build steps documented?
    - What ongoing maintenance is required after initial publication? (certificate renewal, SDK updates, policy compliance)

13. **Testing Without Code**
    - Can the app be tested manually without writing automated tests?
    - Is there guidance on what to test and how to identify common issues?
    - Are TestFlight (iOS) and internal testing (Android) processes documented?
    - Can a non-coder recruit and manage beta testers?
<!-- /TECHUSER:CATEGORIES -->

<!-- TECHUSER:OUTPUT -->
- A "Publishing Roadmap" estimating time and steps from working app to live store listing for someone who has never published a mobile app
<!-- /TECHUSER:OUTPUT -->

<!-- REDTEAM:CONTEXT -->
This project is a mobile application running on iOS, Android, or both. Prioritize mobile-specific attack vectors: insecure local data storage (Keychain/Keystore misuse, plaintext SQLite, shared preferences), certificate pinning bypass, intent/URL scheme hijacking, WebView JavaScript bridge exploitation, binary reverse engineering and tampering, jailbreak/root detection bypass, insecure IPC, and clipboard data leakage.
<!-- /REDTEAM:CONTEXT -->

<!-- REDTEAM:CATEGORIES -->
<!-- /REDTEAM:CATEGORIES -->

<!-- REDTEAM:OUTPUT -->
<!-- /REDTEAM:OUTPUT -->
