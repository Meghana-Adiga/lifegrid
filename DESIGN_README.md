# LIFEGRID Phase 1 — Core

A small local-development modular monolith for community resource coordination. The backend provides working REST endpoints for registration/login, profiles, categories, resource listing/creation/update, requests, manual assignments, assignment status, dashboard counts and basic audit events. The React page provides sign-in and dashboard summary; remaining operations are available through the interactive API docs.

## Run locally

Requirements: Docker Desktop / Docker Engine with Compose.

```sh
docker compose up --build
```

- Web: http://localhost:5173
- API and OpenAPI docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

Create the first account with `POST /auth/register` in `/docs`. Roles default to `member`; coordinator/admin roles require a trusted operator to update the user record directly for this MVP. The sample compose credentials and JWT secret are for local development only. Do not expose this configuration publicly.

## Tests

With Python dependencies installed in a virtual environment: `cd backend && pytest -q`. These are smoke tests only; they do not cover all authorization and business rules. The frontend can be production-built with `cd frontend && npm install && npm run build`.

## Scope and limitations

Modular monolith, PostgreSQL-backed in Compose. Assignment selection is manual. No AI agents, automated allocation, simulation, routing optimization, payments or real-time tracking. No password reset, email verification, migrations, rate limits, deployment security hardening, or full CRUD UI. Basic audit records are created for selected write operations; this is not a tamper-proof compliance log. JWT secret must be replaced and first-admin provisioning improved before any hosted deployment.
