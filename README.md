# Hospital Device Remediation & Compliance API

MVP backend: a persistent, hospital-owned system of record for medical device
inventory, patch/remediation history, and lifecycle tracking — independent of
whichever biomedical engineering vendor (TriMedx, Renovo, etc.) currently
manages the devices.

This is the "system of record" layer, not network visibility (that's what
Ordr/Asimily/Palo Alto already do). This tool tracks what SHOULD be true and
what's been done about it, and keeps that history even if the hospital fires
its biomed vendor.

## What's built

- **Device inventory**: manufacturer, model, serial, department, location,
  status (in-service / in-repair / quarantined / retired), which vendor
  currently manages it
- **Lifecycle event log**: append-only audit trail per device — patches
  applied, status changes, reconciliation flags, notes. This table is the
  core IP: it's what survives a vendor transition.
- **Role-based auth**: `security_admin` (read/write) vs `viewer` (read-only),
  JWT bearer tokens
- **REST API** with auto-generated docs at `/docs`

## What's NOT built yet (by design — this is the MVP)

- Reconciliation logic against network-tool data (Ordr/Asimily API ingestion)
- CSV/bulk import for existing biomed vendor exports
- Frontend (this is API-only right now)
- Production-grade auth (rate limiting, refresh tokens, MFA)
- Postgres/RDS — currently SQLite for local dev

## Running it locally

```bash
cd hospital-device-saas
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open http://localhost:8000/docs for interactive API docs (Swagger UI) —
you can register a user, log in, and hit every endpoint right from the browser.

## Quick smoke test

```bash
# Register an admin user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@hospital.org","password":"changeme123","role":"security_admin"}'

# Log in (form-encoded, not JSON — OAuth2 password flow)
curl -X POST http://localhost:8000/auth/login \
  -d "username=admin@hospital.org&password=changeme123"

# Use the returned access_token as a Bearer token for everything else
```

## Environment variables (set before real deployment)

- `SECRET_KEY` — JWT signing secret. The default in `app/auth.py` is dev-only.
- `DATABASE_URL` — defaults to local SQLite. Point this at a Postgres/RDS
  instance for anything beyond local dev, e.g.
  `postgresql://user:pass@host:5432/dbname`

## Deploying to AWS (when you're ready)

A reasonable, cheap path for an early MVP demo://
- **RDS Postgres** (smallest instance) for the database
- **Elastic Beanstalk** or a single **EC2** instance running this app behind
  nginx — fastest way to get a public URL for a funding demo
- Once you have real traction: move to **ECS/Fargate** for the API so you're
  not managing a server directly

Don't over-build the infra before you have a customer. A single EC2 box
running this is completely fine for a pitch demo.

## Next build priorities, in order

1. **Frontend dashboard** — device list, filters, add/edit forms, event
   timeline per device. This is what you'll actually demo to investors/CISOs.
2. **CSV import** — let a hospital upload their existing biomed vendor's
   asset export and map it into this schema. Proves the "independent record"
   value prop without needing any vendor API integration.
3. **Reconciliation MVP** — even a simple version: compare an uploaded
   network-scan export (IP + MAC list) against the device table and flag
   devices that are missing from one side or the other. This is your
   differentiator — don't build it last, but don't build it first either;
   prove inventory + lifecycle tracking has legs before adding this
   complexity.

## Compliance note

This system stores device metadata (make, model, serial, network location,
department) which is device data, not patient data — but department/location
fields can be PHI-adjacent depending on how granular you get (e.g. "Dr.
Smith's ICU room 4" ties a device to a care context). Keep this in mind as
you scale: encryption at rest/in transit, audit logging (already partially
in place via the lifecycle event log), and a BAA-ready hosting posture will
matter once you're talking to a real hospital's security/compliance team.
