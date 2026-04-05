# Module: API / Backend Service
# Covers: REST APIs, GraphQL services, gRPC services, microservices, serverless functions

<!-- ENGINEER:CONTEXT -->
This project is a backend API or service. Evaluate it with the expectations of production server-side software — API design, data modeling, concurrency handling, observability, deployment architecture, and operational readiness.
<!-- /ENGINEER:CONTEXT -->

<!-- ENGINEER:CATEGORIES -->
8. **API Design Quality**
   - Are endpoints logically organized and consistently named?
   - Is the API versioned? Is backward compatibility considered?
   - Are request/response schemas documented (OpenAPI, GraphQL schema, protobuf definitions)?
   - Is pagination, filtering, and sorting handled for collection endpoints?
   - Are HTTP status codes used correctly and consistently?
   - Is the API idempotent where it should be?

9. **Data Layer and Persistence**
   - Is the data model well-normalized (or appropriately denormalized with justification)?
   - Are database migrations versioned and reversible?
   - Is there an ORM or query builder, and is it used correctly (no raw SQL injection vectors, no N+1)?
   - Are database connections pooled and managed correctly?
   - Is there a caching strategy? Is cache invalidation handled?

10. **Concurrency and Reliability**
    - How does the service handle concurrent requests? Are there race conditions?
    - Is there rate limiting or throttling?
    - Are long-running operations handled asynchronously?
    - Is there retry logic with backoff for external service calls?
    - What happens during partial failures? (database down, external API down, message queue unavailable)

11. **Observability and Operations**
    - Is there structured logging with correlation IDs?
    - Are metrics exposed? (request latency, error rates, queue depths, resource utilization)
    - Is there distributed tracing for multi-service architectures?
    - Are health check and readiness endpoints implemented?
    - Is there alerting configuration or documentation?

12. **Deployment Architecture**
    - Is the service containerized? Is the Dockerfile well-constructed (multi-stage, minimal base, non-root)?
    - Is infrastructure defined as code? (Terraform, Pulumi, CloudFormation, Kubernetes manifests)
    - Are environment configurations separated from application code?
    - Is there a blue-green, canary, or rolling deployment strategy?
    - Is horizontal scaling supported? What is the stateful vs. stateless boundary?
<!-- /ENGINEER:CATEGORIES -->

<!-- ENGINEER:OUTPUT -->
- An "Operational Readiness Checklist" covering logging, monitoring, alerting, deployment, and incident response
<!-- /ENGINEER:OUTPUT -->

<!-- CIO:CONTEXT -->
This project is a backend API or service that other applications depend on. Evaluate it as infrastructure — availability requirements, operational cost, maintenance burden, and the risk profile of having business processes depend on this service.
<!-- /CIO:CONTEXT -->

<!-- CIO:CATEGORIES -->
9. **Availability and SLA Viability**
   - What uptime can this service realistically deliver?
   - Is there high availability architecture? (redundancy, failover, load balancing)
   - What is the disaster recovery plan? What is the RTO/RPO?
   - What happens to dependent systems if this service goes down?

10. **Operational Cost Model**
    - What is the infrastructure cost at current and projected load?
    - What is the operational staffing requirement? (on-call, incident response, maintenance)
    - How does cost scale with usage growth?
    - Are there unexpected cost drivers? (egress fees, API call charges, storage growth)
<!-- /CIO:CATEGORIES -->

<!-- CIO:OUTPUT -->
- An "SLA Feasibility Assessment" estimating achievable availability based on current architecture
<!-- /CIO:OUTPUT -->

<!-- SECURITY:CONTEXT -->
This project is a backend API or service that processes requests, accesses data stores, and potentially handles sensitive information. Evaluate it as an attack target — API abuse, data exfiltration, privilege escalation, and injection attacks are the primary threat vectors.
<!-- /SECURITY:CONTEXT -->

<!-- SECURITY:CATEGORIES -->
10. **API Security**
    - Is authentication required for all non-public endpoints?
    - Are API keys or tokens validated on every request?
    - Is there rate limiting to prevent abuse and DDoS?
    - Are request payloads validated and size-limited?
    - Is there protection against parameter tampering, mass assignment, or IDOR?

11. **Data Access Controls**
    - Is there row-level security or tenant isolation for multi-tenant systems?
    - Are database credentials stored securely with least-privilege access?
    - Can a user access or modify another user's data through any endpoint?
    - Are administrative endpoints protected with elevated authentication?

12. **Infrastructure Security**
    - Is the service running as non-root?
    - Are container images minimal and regularly updated?
    - Is the network configuration least-privilege? (no unnecessary open ports, internal services not exposed)
    - Are secrets injected at runtime, not baked into images or configs?
<!-- /SECURITY:CATEGORIES -->

<!-- SECURITY:OUTPUT -->
- An **API Security Assessment Table** covering authentication, authorization, input validation, rate limiting, and data access controls per endpoint or endpoint group
<!-- /SECURITY:OUTPUT -->

<!-- LEGAL:CONTEXT -->
This project is a backend service that processes and stores data. Evaluate legal risks around data processing, data retention, cross-border transfer, subprocessor obligations, and the liability implications of a service that other applications depend on.
<!-- /LEGAL:CONTEXT -->

<!-- LEGAL:CATEGORIES -->
9. **Data Processing Obligations**
   - Is the service a data processor or data controller under GDPR?
   - Are data processing agreements needed with clients or upstream services?
   - Is there a data processing record (Article 30 GDPR)?
   - Are data subject access, deletion, and portability requests technically supported?

10. **Data Retention and Deletion**
    - Is there a data retention policy? Is it enforced technically?
    - Can data be fully deleted (not just soft-deleted) when required?
    - Are backups included in deletion processes?
    - Is there a legal hold mechanism for litigation or regulatory requirements?

11. **Service Level and Liability**
    - If this service is offered to clients, are SLA commitments defensible?
    - What is the contractual liability if the service experiences downtime or data loss?
    - Are force majeure and limitation of liability clauses adequate?
<!-- /LEGAL:CATEGORIES -->

<!-- LEGAL:OUTPUT -->
- A "Data Processing Compliance Checklist" covering GDPR, CCPA, and sector-specific data handling requirements
<!-- /LEGAL:OUTPUT -->

<!-- TECHUSER:CONTEXT -->
This project is a backend API or service. You are evaluating whether a technically literate non-coder could deploy, configure, monitor, and maintain this service — recognizing that backend services require ongoing operational attention beyond initial setup.
<!-- /TECHUSER:CONTEXT -->

<!-- TECHUSER:CATEGORIES -->
11. **Deployment for Non-Developers**
    - Can the service be deployed using a managed platform (Railway, Render, Fly.io, AWS App Runner)?
    - Is Docker Compose or equivalent available for simple local/self-hosted deployment?
    - Is the deployment process documented with copy-paste-ready commands?
    - Are database setup and migration documented as part of the deployment process?

12. **Monitoring and Troubleshooting**
    - Can you tell if the service is healthy without reading logs?
    - Is there a dashboard or status page?
    - When something goes wrong, can you identify the problem from error messages alone?
    - Is there documentation for common operational issues and their fixes?
<!-- /TECHUSER:CATEGORIES -->

<!-- TECHUSER:OUTPUT -->
- A "Deployment Difficulty Matrix" comparing self-hosted, PaaS, and managed options by complexity level
<!-- /TECHUSER:OUTPUT -->

<!-- REDTEAM:CONTEXT -->
This project is a backend API or service. Prioritize server-side attack vectors: authentication bypass, broken object-level authorization (BOLA/IDOR), mass assignment, rate limiting gaps, GraphQL introspection and query depth abuse, SSRF through API integrations, deserialization attacks, and race conditions in stateful operations. If the API handles file uploads, webhooks, or background jobs, test those paths for injection and abuse.
<!-- /REDTEAM:CONTEXT -->

<!-- REDTEAM:CATEGORIES -->
<!-- /REDTEAM:CATEGORIES -->

<!-- REDTEAM:OUTPUT -->
<!-- /REDTEAM:OUTPUT -->
