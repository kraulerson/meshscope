# Module: Web Application
# Covers: SPAs, full-stack web apps, server-rendered apps, progressive web apps

<!-- ENGINEER:CONTEXT -->
This project is a web application. Evaluate it with the expectations of production web software — browser compatibility, responsive design, accessibility, state management, API integration, build tooling, and deployment readiness.
<!-- /ENGINEER:CONTEXT -->

<!-- ENGINEER:CATEGORIES -->
8. **Frontend Architecture**
   - Is state management appropriate for the application's complexity? (local state vs. global store vs. server state)
   - Is the component structure logical and reusable, or are components monolithic?
   - Are there unnecessary re-renders, memory leaks, or performance antipatterns?
   - Is routing implemented correctly, including deep linking and browser history?
   - Is the build pipeline configured correctly? (bundling, tree-shaking, code splitting, minification)

9. **API Design and Integration**
   - Are API calls centralized or scattered throughout components?
   - Is there proper error handling for network failures, timeouts, and non-2xx responses?
   - Are loading and error states handled in the UI?
   - Is there request caching, deduplication, or optimistic updates where appropriate?
   - Are API contracts documented or typed?

10. **Accessibility and Standards Compliance**
    - Does the application meet WCAG 2.1 AA standards?
    - Are semantic HTML elements used correctly?
    - Is keyboard navigation functional throughout?
    - Are ARIA attributes used appropriately (not just sprinkled on for appearance)?
    - Has color contrast been verified? Are there color-only indicators that would fail for colorblind users?

11. **Security Posture (Web-Specific)**
    - Is Content Security Policy (CSP) configured?
    - Are cookies configured with appropriate flags (HttpOnly, Secure, SameSite)?
    - Is CORS configured correctly (not wildcard in production)?
    - Is there protection against CSRF?
    - Are user inputs sanitized before rendering (XSS prevention)?

12. **Deployment and DevOps Readiness**
    - Is there a clear path from development to production deployment?
    - Are environment-specific configurations handled correctly?
    - Is there a CI/CD pipeline or at minimum documented deployment steps?
    - Are static assets configured for CDN delivery and caching?
    - Is there health checking, monitoring, or observability built in?
<!-- /ENGINEER:CATEGORIES -->

<!-- ENGINEER:OUTPUT -->
- A "Production Readiness Checklist" identifying what must be addressed before this goes live
<!-- /ENGINEER:OUTPUT -->

<!-- CIO:CONTEXT -->
This project is a web application intended for browser-based access. Evaluate it as a product or internal tool that will be accessed by end users, considering hosting costs, maintenance burden, security exposure, and user experience quality.
<!-- /CIO:CONTEXT -->

<!-- CIO:CATEGORIES -->
9. **User Experience and Adoption Risk**
   - Is the application usable enough that end users will actually adopt it, or will they resist?
   - What is the support burden likely to be? (training, help desk, user complaints)
   - Is the application accessible to users with disabilities? (legal obligation, not optional)
   - Does the application work across the devices and browsers your organization supports?

10. **Hosting and Infrastructure Model**
    - What hosting infrastructure is required? (static hosting, application server, database, CDN)
    - What are the estimated monthly hosting costs at expected user volumes?
    - Is the architecture cloud-provider-agnostic or locked to a specific platform?
    - What is the disaster recovery and business continuity plan?
<!-- /CIO:CATEGORIES -->

<!-- CIO:OUTPUT -->
- A "Build vs. Buy" comparison — would an off-the-shelf SaaS product serve the same need at lower TCO?
<!-- /CIO:OUTPUT -->

<!-- SECURITY:CONTEXT -->
This project is a web application accessible via browser. Evaluate it as a customer-facing or employee-facing application with all the security expectations that entails — OWASP Top 10 coverage, authentication, session management, data protection, and compliance readiness.
<!-- /SECURITY:CONTEXT -->

<!-- SECURITY:CATEGORIES -->
10. **OWASP Top 10 Coverage**
    - Systematically evaluate the application against each current OWASP Top 10 category
    - For each category, identify whether the application is vulnerable, protected, or not applicable
    - Pay special attention to: Injection, Broken Authentication, Sensitive Data Exposure, XSS, and Security Misconfiguration

11. **Client-Side Security**
    - Is sensitive data stored in localStorage, sessionStorage, or cookies without encryption?
    - Are there exposed API keys, tokens, or secrets in client-side code or source maps?
    - Is the Content Security Policy restrictive enough to prevent common attacks?
    - Are third-party scripts loaded from trusted sources with integrity checks (SRI)?
    - Is there client-side input validation that is NOT duplicated server-side? (validation must exist server-side)

12. **Session and Authentication Security**
    - How are sessions created, maintained, and terminated?
    - Is session fixation possible?
    - Are tokens stored securely and transmitted safely?
    - Is there account lockout, rate limiting, or brute-force protection?
    - Is multi-factor authentication supported or available?
    - How does password reset work? Is it secure?
<!-- /SECURITY:CATEGORIES -->

<!-- SECURITY:OUTPUT -->
- An **OWASP Top 10 Assessment Table** with pass/fail/partial/N/A for each category
<!-- /SECURITY:OUTPUT -->

<!-- LEGAL:CONTEXT -->
This project is a web application that may be deployed publicly or within an organization. Evaluate legal risks associated with web-accessible software — data privacy obligations, accessibility requirements, cookie/tracking compliance, terms of service needs, and content liability.
<!-- /LEGAL:CONTEXT -->

<!-- LEGAL:CATEGORIES -->
9. **Web-Specific Privacy Obligations**
   - Does the application use cookies, tracking pixels, analytics, or fingerprinting?
   - Is there a cookie consent mechanism compliant with ePrivacy Directive and GDPR?
   - Is a privacy policy published and accessible? Does it accurately describe data practices?
   - Are third-party analytics or advertising SDKs present? What data do they collect?
   - Does the application support GDPR data subject rights (right to access, delete, port)?

10. **Accessibility Legal Requirements**
    - Does the application meet ADA (US), EAA (EU), or equivalent accessibility standards?
    - Has accessibility testing been conducted?
    - Is there litigation risk from accessibility non-compliance?
    - Are there accessibility statements or conformance claims?

11. **Terms of Service and User Agreements**
    - If user-facing, are there Terms of Service? Are they enforceable?
    - Are there acceptable use policies?
    - Is there a DMCA or content takedown process if the application hosts user content?
    - How are user accounts terminated? Is data handled per privacy obligations upon termination?
<!-- /LEGAL:CATEGORIES -->

<!-- LEGAL:OUTPUT -->
- A "Privacy Compliance Checklist" covering GDPR, CCPA, ePrivacy, and cookie consent requirements
<!-- /LEGAL:OUTPUT -->

<!-- TECHUSER:CONTEXT -->
This project is a web application. You are evaluating whether a technically literate non-coder could set this up, deploy it, maintain it, and potentially customize it for personal or organizational use.
<!-- /TECHUSER:CONTEXT -->

<!-- TECHUSER:CATEGORIES -->
11. **Deployment Accessibility**
    - Can you deploy this application without understanding server administration?
    - Are there one-click or simplified deployment options (Vercel, Netlify, Railway, Docker)?
    - Is the deployment process documented step-by-step?
    - What happens when you need to update the deployed version?

12. **Customization Without Coding**
    - Can you change branding, colors, text, and layout without modifying source code?
    - Are there configuration files or environment variables for common customizations?
    - Is there a theming system or admin panel?
    - What percentage of common customization needs require code changes?
<!-- /TECHUSER:CATEGORIES -->

<!-- TECHUSER:OUTPUT -->
- A "Deployment Options" section rating each deployment method by difficulty for non-coders
<!-- /TECHUSER:OUTPUT -->

<!-- REDTEAM:CONTEXT -->
This project is a web application accessible via browser. Prioritize web-specific attack vectors: XSS (reflected, stored, DOM-based), CSRF, CORS misconfiguration, cookie/session attacks, client-side prototype pollution, CSP bypass, clickjacking, open redirects, and server-side request forgery. Check for exposed source maps, debug endpoints, and development artifacts in the build output.
<!-- /REDTEAM:CONTEXT -->

<!-- REDTEAM:CATEGORIES -->
<!-- /REDTEAM:CATEGORIES -->

<!-- REDTEAM:OUTPUT -->
<!-- /REDTEAM:OUTPUT -->
