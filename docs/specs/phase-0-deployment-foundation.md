# Phase 0: OCI ARM64 Deployment Foundation

## Problem Statement

The Owner needs a reproducible, private, and recoverable foundation on OCI ARM64 before Personal Asset OS can store or calculate financial data. The current repository contains approved governance and system specifications but no executable product, deployment stack, security boundary, backup workflow, or verified ARM64 release path.

Without this foundation, a development Agent could produce code that works only on AMD64, exposes services publicly, mixes AI control-plane privileges with the product runtime, stores secrets in Git, performs uncontrolled database changes, or claims completion without a reproducible system-level test.

## Solution

Build the Phase 0 deployment foundation as ten independently reviewable tasks. The resulting system will run four product services—web, backend, PostgreSQL, and Redis—on Ubuntu 24.04 ARM64. It will be reachable only through Tailscale Serve, keep AI-PM and Agent privileges outside the product runtime, load secrets from protected files, provide distinct liveness and readiness behavior, support encrypted PostgreSQL backup and isolated restore, and expose a single black-box candidate-verification seam.

The Phase is complete only after the same committed candidate passes the full gate on the actual OCI ARM64 host. Phase 0 does not implement Owner login, Financial Accounts, Assets, Holdings, Quotes, Portfolio calculations, or any other Phase 1 behavior.

## User Stories

1. As the Owner, I want the system to run on OCI Ampere ARM64, so that it uses the selected production environment.
2. As the Owner, I want a documented 2 OCPU, 12 GB RAM, and 100 GB disk baseline, so that resource expectations are explicit.
3. As the Owner, I want the product runtime separated from AI-PM and development Agents, so that a control-plane failure does not stop the product.
4. As the Owner, I want development Agents denied direct Docker and production-data access, so that delegated work cannot silently become host administration.
5. As the Owner, I want only one private HTTPS entry point, so that PostgreSQL, Redis, and Backend internals are not exposed.
6. As the Owner, I want Tailscale-only access with Funnel disabled, so that Internet scanners cannot reach the application.
7. As the Owner, I want the React application served as static production assets, so that no development server runs in production.
8. As the Owner, I want one web service to serve the frontend and proxy the API, so that the deployment has fewer runtime failure points.
9. As the Owner, I want Backend liveness to remain available during dependency failure, so that process health can be distinguished from readiness.
10. As the Owner, I want readiness to fail when PostgreSQL, Redis, or the schema revision is unavailable, so that traffic is not sent to an unusable Backend.
11. As the Owner, I want PostgreSQL data to survive container and Compose restarts, so that runtime replacement does not erase data.
12. As the Owner, I want secrets stored outside the public repository, so that publishing source code cannot publish credentials.
13. As the Owner, I want unsafe default or missing secrets to prevent startup, so that an insecure configuration cannot appear healthy.
14. As the Owner, I want repeatable Backend and Frontend dependency installation, so that later builds use the reviewed dependency graph.
15. As the Owner, I want every production image to have native Linux ARM64 support, so that production does not depend on emulation.
16. As the Owner, I want image and tool versions pinned, so that a rebuild does not silently change its inputs.
17. As the Owner, I want a manual PostgreSQL backup command in Phase 0, so that recoverability exists before financial features are added.
18. As the Owner, I want each backup encrypted before it leaves the host, so that storage access alone cannot reveal its contents.
19. As the Owner, I want backup checksums verified, so that a corrupt file is not reported as successful.
20. As the Owner, I want restores to use an isolated PostgreSQL instance, so that verification cannot overwrite production data.
21. As the Owner, I want a candidate-verification wrapper that accepts only a commit SHA, so that AI-PM cannot inject arbitrary Docker commands.
22. As the Owner, I want candidate tests to use separate secrets, volumes, ports, and a Compose project, so that tests cannot touch production.
23. As the Owner, I want formal deployment to use a different approved-release wrapper, so that passing tests does not grant deployment authority.
24. As the Owner, I want GitHub CI to run lint, type checking, tests, builds, and security scans, so that obvious failures are caught before OCI verification.
25. As the Owner, I want the actual ARM64 host to run the final smoke test, so that AMD64 CI cannot falsely prove production compatibility.
26. As the Owner, I want logs rotated and bounded, so that diagnostics cannot fill the system disk.
27. As the Owner, I want disk warnings at 80% and protective behavior at 90%, so that PostgreSQL remains the priority during storage pressure.
28. As the Owner, I want the homepage and API reachable through one black-box seam, so that tests verify the deployed system rather than internal implementation details.
29. As AI-PM, I want each Phase 0 task to produce one reviewable commit, so that failures can be isolated and reverted.
30. As AI-PM, I want machine-readable test evidence tied to a commit SHA, so that a task cannot be marked complete based on an assertion alone.
31. As a development Agent, I want explicit exclusions for every task, so that I do not implement Phase 1 behavior early.
32. As a public contributor, I want clear setup and security documentation, so that I can work without learning private deployment details.
33. As a public contributor, I want synthetic test data only, so that tests and artifacts are safe to publish.
34. As the Owner, I want no automated database migration during Backend startup, so that container restarts cannot modify the schema.
35. As the Owner, I want the Phase Gate to include dependency failure and recovery, so that health behavior is proven rather than inferred.
36. As the Owner, I want the Phase Gate to include restart persistence, so that a healthy fresh start does not hide volume mistakes.
37. As the Owner, I want no product Worker or Scheduler in Phase 0, so that unused infrastructure is not deployed.
38. As the Owner, I want the finished Phase documented without invented commands, so that README operations match verified scripts.

## Implementation Decisions

- The repository is a single-context project. Domain vocabulary comes from the root glossary, and architecture decisions come from the accepted ADRs.
- AI-PM is the only dispatcher and verifier. Development Agents prepare candidates but cannot approve tasks, merge the protected branch, or deploy.
- The OCI host uses separate administrative, AI-PM, and non-interactive deployment identities. AI-PM is not a Docker-group member.
- The product Compose project contains exactly four runtime services: web, backend, PostgreSQL, and Redis.
- The web image builds the React application in a build stage and serves the resulting static assets through Nginx. It also proxies the versioned API path to Backend.
- Tailscale Serve runs on the host outside Compose and forwards private HTTPS traffic to the locally bound web service. Funnel and public web ingress remain disabled.
- PostgreSQL and Redis are reachable only on the internal Compose network. Backend is not published to a host port.
- PostgreSQL uses a persistent named volume. Redis contains reconstructable session or cache data and is not part of the database backup.
- Backend exposes separate liveness and readiness endpoints. Liveness checks the process only; readiness checks PostgreSQL, Redis, and the expected migration revision.
- Backend never runs database migrations automatically at process startup.
- Non-sensitive configuration may use environment variables. Secrets use read-only files mounted from a protected directory outside the repository.
- Backend dependencies are managed with uv and a committed lock file. Frontend dependencies use npm and a committed package lock.
- Production images and tools use explicit versions. A release records multi-architecture image digests and rejects dependencies without native Linux ARM64 support.
- Phase 0 backup uses PostgreSQL custom-format dump, age public-key encryption, checksum validation, and isolated restore.
- The long-term backup target is private OCI Object Storage through Instance Principal. Phase 0 must establish and verify the manual foundation; Phase 1 enables the daily systemd timer and retention policy.
- The host retains no long-lived backup decryption private key. The Owner supplies it temporarily for a restore exercise.
- Application logs are structured, redacted, and emitted to standard output/error. Product-container logs are bounded to approximately 100 MB each; the host journal is bounded separately.
- Candidate verification and formal deployment are different wrappers. Both accept constrained inputs; neither accepts arbitrary commands, paths, volumes, or secret locations.
- The candidate wrapper deploys an isolated test Compose project from a committed SHA, runs the gate, returns redacted evidence, and tears down test services without touching production resources.
- GitHub is the public source and Issue Tracker. The protected default branch accepts only reviewed, tested work. Public artifacts contain no real Financial Accounts, Holdings, secrets, deployment identifiers, backups, logs, or traces.
- Phase 0 is implemented as tasks P0-001 through P0-010. Each task has one owner, one branch, one semantic commit, explicit dependencies, and external acceptance evidence.

## Testing Decisions

- The primary testing seam is the deployed candidate's web/API boundary, invoked through the constrained candidate-verification workflow. This is the highest seam that observes the product as the Owner will reach it while still remaining isolated from production.
- Black-box acceptance verifies the homepage, API proxy, liveness, readiness, service health, dependency failure and recovery, restart persistence, backup encryption, checksum validation, isolated restore, and absence of production secrets or volumes.
- PostgreSQL failure must leave liveness at HTTP 200 and change readiness to HTTP 503. Restoring PostgreSQL must return readiness to HTTP 200 without rebuilding the candidate.
- A marker written to the test PostgreSQL volume must survive a Compose restart.
- Backup verification must prove that the dump is readable, encrypted output exists, the recorded checksum matches, and an isolated restore succeeds.
- Candidate evidence must identify the commit SHA, host architecture, image architectures, Compose health, endpoint outcomes, and backup/restore result without exposing secrets.
- GitHub CI runs the same language-level quality commands and an AMD64 container integration build, but it does not replace the OCI ARM64 gate.
- Unit tests are reserved for pure behavior that cannot be asserted precisely through the system seam, such as configuration validation or deterministic parsing. Tests must not mirror private function structure.
- No test may require real Financial Account or Holding data. Synthetic fixtures and redacted artifacts are mandatory.
- Playwright is not required for the Phase 0 browser matrix; a minimal homepage smoke test is sufficient. The isolated Playwright environment becomes mandatory for the Phase 1 Owner and Holding journey.
- Existing prior art consists of the approved health semantics, Phase Gate, backup contract, Agent boundary, and fixed task workflow in the governance documents. There is no pre-existing product code or lower-level test suite to preserve.

## Out of Scope

- Owner authentication, password hashing, browser sessions, CSRF, and login rate limiting.
- Financial Account, Asset, Holding, Audit Log, and Backup Run domain models.
- Holding create, edit, archive, or restore behavior.
- Mock or real Quotes, market-price persistence, and refresh APIs.
- Portfolio cost, Market Value, unrealized profit, return, or Summary calculations.
- Buy or sell Transactions, dividends, fees, taxes, and realized profit.
- Portfolio allocation, ranking, history, snapshots, cash flow, liabilities, goals, risk, and rebalancing.
- Telegram notifications and the AI asset assistant.
- Multi-user, multi-tenant, public SaaS, OAuth, MFA, and public registration.
- Kubernetes, Vault, a service mesh, a permanent browser-testing service, or unused Worker/Scheduler containers.
- Public Internet access to the application.

## Further Notes

- Phase 0 is not a financial application release. It is the verified deployment and recovery foundation on which Phase 1 can be built.
- The first implementation task after governance approval is the minimal Backend skeleton and liveness endpoint.
- The public GitHub repository is the authoritative source and Issue Tracker. The initial governance baseline is bootstrapped before normal protected-branch task flow begins.
- The `ready-for-agent` label means the spec is sufficiently decided for task execution; it does not grant production deployment authority.
