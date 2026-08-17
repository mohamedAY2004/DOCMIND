# Campus pilot deployment

DocMind ships as four OCI workloads in `docker-compose.pilot.yml`: the web
frontend, API, evaluation worker, and retention worker. A fifth one-shot
workload applies Alembic migrations. PostgreSQL, Redis, and S3-compatible
storage are supplied through environment variables, so no cloud-vendor SDK is
used outside the storage adapter.

## Production configuration

Copy `backend/src/.env.example` into your secret/configuration system and set
at least `DATABASE_URL`, `REDIS_URL`, model credentials, and the S3 fields.
Production startup intentionally fails unless:

- `ENVIRONMENT=production`, `COOKIE_SECURE=true`, and
  `LOCAL_AUTH_ENABLED=true` while the current Flutter client still signs in
  with username/password. Disable it only after mobile SSO ships; web portal
  authentication remains controlled independently by `PORTAL_SSO`;
- JWT and portal HMAC secrets are non-default and at least 32 characters;
- Redis is configured; and
- `STORAGE_BACKEND=s3` with a configured bucket.

The frontend and API should share an HTTPS origin. The supplied Nginx config
proxies `/api`, `/health`, and `/metrics` to the API and disables buffering for
SSE responses.

## Rollout

Start with `PORTAL_SSO`, `STRUCTURED_CITATIONS`, `STREAMING_CHAT`, and
`SUBJECT_READINESS` enabled for staff infrastructure but restrict application
access at the ingress/identity layer. Expand to one subject, then a student
allowlist. Promote to the campus pilot after seven stable days of error,
latency, citation-coverage, backlog, and feedback metrics.

Run retention with `RETENTION_DELETE_ENABLED=false` for at least one week and
review the worker's `would_delete` output. Set it to `true` only after that
review. Early user deletion always removes private database rows, uploaded
objects, and private vector collections immediately.

## Commands

```sh
docker compose -f docker-compose.pilot.yml build
docker compose -f docker-compose.pilot.yml up -d
```

The migration workload must complete successfully before the other backend
workloads start. `/health` is the liveness endpoint and `/metrics` exposes the
operational counters used by the pilot dashboards.
