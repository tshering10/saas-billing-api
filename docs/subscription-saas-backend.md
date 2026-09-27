# Subscription SaaS Backend — Project Roadmap

**Tech stack:** FastAPI · PostgreSQL · Docker · Stripe + eSewa
**Goal:** Learning portfolio project demonstrating real-world subscription billing, multi-tenancy, and payment gateway abstraction.

---

## Architecture Decisions

### Multi-tenancy: Shared database, row-level tenancy
Every tenant-scoped table carries an `organization_id` foreign key; all queries filter by it (enforced in the service layer, optionally backed by Postgres Row-Level Security as a stretch goal). This is the industry-standard approach for SaaS and is what most companies actually use — unlike per-tenant databases or per-tenant schemas, which don't scale operationally and don't teach the actual hard problem (safe row-level isolation).

```
Organization (id, name, ...)
User (id, organization_id → FK, email, role, ...)
Subscription (id, organization_id → FK, plan_id, status, ...)
Invoice (id, organization_id → FK, ...)
```

- `Organization` owns one `Subscription` (seat-based / team billing)
- `User` belongs to an `Organization` with a `role`: `owner`, `admin`, `member`
- Only `owner`/`admin` can manage billing; `member` just uses the product

### Dashboards: thin admin + customer views, not a separate frontend project
- **Customer-facing**: current plan, usage/limits, invoice history, manage subscription (can lean on Stripe's hosted Customer Portal for the Stripe side)
- **Admin-facing**: list of orgs/subscriptions, basic metrics (active subs, churn, revenue by plan), manual override actions (refund, force-cancel)
- Server-rendered pages (Jinja2) or a minimal frontend (Next.js/htmx) hitting the API is enough to make the project demo-able — no need for a full SPA if the focus is backend.

---

## Phase 0 — Setup & Foundations
- FastAPI project structure: `app/{core,models,schemas,api,services,workers}`
- PostgreSQL via SQLAlchemy 2.0 (async) + Alembic for migrations
- Docker Compose: `api`, `postgres`, `redis` (background jobs/caching), optionally `worker`
- Settings via `pydantic-settings` (`.env` for secrets/keys)
- Auth: JWT-based (access + refresh tokens), password hashing with `passlib`/`argon2`

## Phase 1 — Core Domain Models
- `Organization` — name, owner, created_at
- `User` — account, email, auth, `organization_id`, `role`
- `Plan` — name, price, billing interval (monthly/yearly), features/limits (JSON or separate table)
- `Subscription` — `organization_id`, plan, status (`trialing`, `active`, `past_due`, `canceled`, `unpaid`), `current_period_start/end`, `cancel_at_period_end`
- `Invoice` — amount, currency, status, linked subscription
- `PaymentMethod` — stored token/reference (never raw card data — rely on Stripe's tokenization; eSewa is redirect-based so less relevant here)
- `Transaction` / `PaymentAttempt` — gateway, external reference ID, status, raw payload (for auditing)

## Phase 2 — Gateway Abstraction Layer
The most valuable learning piece — core logic never talks to Stripe/eSewa SDKs directly.
- Define a `PaymentGateway` interface/protocol: `create_checkout_session()`, `verify_payment()`, `create_subscription()`, `cancel_subscription()`, `handle_webhook()`
- Implement `StripeGateway` and `EsewaGateway` against that interface
- A `gateway` field on `Subscription`/`Transaction` so business logic never branches on provider

## Phase 3 — Checkout & Subscription Lifecycle
- Endpoint to create checkout session (Stripe Checkout, or eSewa's redirect flow)
- Webhook endpoints per gateway (`/webhooks/stripe`, `/webhooks/esewa`):
  - Signature verification (Stripe: `stripe-signature` header + webhook secret)
  - Idempotency: store processed event IDs so retried webhooks don't double-process
  - Handle events: `checkout.session.completed`, `invoice.paid`, `invoice.payment_failed`, `customer.subscription.updated/deleted`
- State machine for subscription status transitions, with clear rules (e.g., grace period on `past_due` before `canceled`)

## Phase 4 — Billing Logic
- Prorated upgrades/downgrades between plans
- Trial periods
- Renewal logic — eSewa has no native recurring billing like Stripe, so a scheduled job (Celery beat / APScheduler) creates a new payment request each cycle and marks the subscription `past_due` if unpaid after N days
- Dunning: retry failed payments, email reminders

## Phase 5 — Multi-tenancy & Access Control
- `Organization` and `role`-based permissions wired through all endpoints
- Seat limits per plan (e.g., "up to 5 users")
- Dependency/middleware that scopes every query to `current_org_id`
- (Stretch) Postgres Row-Level Security policies as a defense-in-depth layer

## Phase 6 — Dashboards
- Customer: plan, usage/limits, invoice history, manage subscription
- Admin: orgs/subscriptions list, active subs / churn / revenue-by-plan metrics, manual refund/cancel actions
- Thin server-rendered or minimal frontend implementation

## Phase 7 — Production-Readiness (portfolio polish)
- Background worker (Celery or `arq`) for webhook processing off the request path
- Rate limiting on public endpoints
- Structured logging + request IDs
- Tests: unit tests for gateway logic with mocked Stripe/eSewa responses, integration tests with Stripe's test mode
- Clean, well-organized OpenAPI docs
- CI (GitHub Actions): lint, test, build Docker image

---

## Additional Features (priority order)
1. **Multi-currency support** — Stripe handles USD/etc., eSewa is NPR-only; store currency per transaction, don't assume one currency globally
2. **Webhook replay/dead-letter handling** — log failed webhook processing for manual replay
3. **Coupon/discount codes**
4. **Metered billing** (pay-per-use on top of subscription)
5. **Soft-delete + data retention** for canceled accounts/orgs
6. **Feature flag / entitlement service** — plan determines unlocked features/limits, exposed via `/me/entitlements`
7. **Postgres Row-Level Security** (stretch goal, ties into Phase 5)

---

## Suggested Build Order

```
Auth & Users & Organizations (roles)
        │
        ▼
Plans → Subscriptions (manual/no payment yet)
        │
        ▼
Stripe integration + webhooks
        │
        ▼
eSewa integration + webhooks
        │
        ▼
Billing cycle automation (worker)
        │
        ▼
Usage limits / entitlements
        │
        ▼
Dashboards (customer + admin)
        │
        ▼
Polish: tests, CI, docs
```

**Portfolio narrative tip:** get Stripe fully working first (proper recurring billing, sandbox, great docs), then layer in eSewa. Since eSewa forces you to simulate recurring billing yourself, it highlights *why* the gateway abstraction layer earns its keep.
