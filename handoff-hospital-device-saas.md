# Handoff: Hospital Device Remediation SaaS — MVP Backend

## Project pitch (for context)
Hospitals outsource biomedical engineering to third parties (TriMedx, Renovo,
etc.). That vendor ends up owning the security-relevant data — device
inventory, patch history, which legacy devices need replacing. When the
vendor relationship changes or ends, that data doesn't stay with the
hospital. Existing tools (Ordr, Asimily, Palo Alto medical device products)
do network visibility but don't act as the hospital's own persistent system
of record. This product is that system of record: inventory + lifecycle
tracking, remediation/patch history log, and (future) a reconciliation layer
comparing vendor-reported vs. network-verified device data.

Sells to hospital CISOs/IT security leadership. Long sales cycle (hospital
procurement). Built from direct clinical cybersecurity experience.

## Decisions made this session
- **Backend**: Python / FastAPI (not Node) — user's call, comfort level
- **Hosting**: AWS, not Azure — this is Brianna's own hosted SaaS, not
  something deployed inside a hospital's tenant, so hospital's internal
  Azure usage is irrelevant to this choice. Use what she knows.
- **DB**: SQLite for local dev, swap to Postgres/RDS via `DATABASE_URL` env
  var for anything beyond local testing
- **MVP scope, in order**: (1) inventory + lifecycle tracking [DONE],
  (2) frontend dashboard [NOT STARTED], (3) CSV import from vendor exports
  [NOT STARTED], (4) reconciliation logic against network-scan data
  [NOT STARTED — this is the differentiator but riskiest to build first]

## What's built and tested (as of this session)
Location: `/mnt/user-data/outputs/hospital-device-saas/` (delivered as
`hospital-device-saas.zip`)

- FastAPI backend, fully working, smoke-tested end to end (register → login
  → create device → log patch event → list devices → pull event history —
  all verified 200 OK)
- **Data model** (`app/models.py`):
  - `Device` — manufacturer, model, serial_number, department, location,
    ip_address, status (in_service/in_repair/quarantined/retired),
    managed_by_vendor
  - `LifecycleEvent` — append-only audit log per device (patch_applied,
    status_change, reconciliation_flag, note) — this table is the core IP,
    the record that survives a vendor transition
  - `User` — role-based (security_admin read/write, viewer read-only)
- **Auth**: JWT bearer tokens, bcrypt password hashing (`app/auth.py`)
- **Routers**: `app/routers/auth_router.py` (register/login),
  `app/routers/devices.py` (CRUD + event logging)
- **Entry point**: `app/main.py` — run with
  `uvicorn app.main:app --reload`, docs at `/docs`

## Known issue fixed this session
`passlib` + newer `bcrypt` package have a version-detection conflict —
pinned `bcrypt==4.0.1` in requirements.txt to fix. Also loosened
`pydantic[email]` to `>=2.12.5` (was pinned to `2.9.2`) because it conflicted
with `google-genai` (used by her CALY project) in the same Python
environment — both projects can now share an environment if needed.

## Not built yet — next priorities in order
1. **Frontend dashboard** — device list, filters, add/edit forms, per-device
   event timeline. This is what actually gets demoed to investors/CISOs.
2. **CSV import** — let a hospital upload their existing biomed vendor's
   asset export and map it into this schema. Proves the "independent
   record" value prop with zero vendor API integration work.
3. **Reconciliation MVP** — compare an uploaded network-scan export
   (IP/MAC list) against the device table, flag what's missing from either
   side. Don't build this first — prove inventory/lifecycle has legs before
   adding this complexity.

## Compliance note flagged
Device metadata isn't PHI itself, but department/location fields can get
PHI-adjacent at fine granularity (e.g. tying a device to a specific patient
care context). Encryption at rest/in transit, audit logging (partially in
place via LifecycleEvent), and BAA-ready hosting will matter once talking to
a real hospital's compliance team — not urgent for MVP demo stage, but
don't let it slide indefinitely.

## To pick back up in a new session
1. Upload/reference the `hospital-device-saas.zip` project (or its unzipped
   contents) so the new session has the actual code
2. Say what you want next — most likely "build the frontend dashboard" or
   "build CSV import"
3. Mention this handoff doc exists if the new session doesn't already have
   it in context
