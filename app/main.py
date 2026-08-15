from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import devices, auth_router

# Creates tables if they don't exist. For production, switch to Alembic migrations.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Hospital Device Remediation & Compliance API",
    description=(
        "Persistent, hospital-owned system of record for medical device inventory, "
        "patch/remediation history, and lifecycle tracking — independent of whichever "
        "biomedical engineering vendor currently manages the devices."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this before production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(devices.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "hospital-device-saas"}


@app.get("/health")
def health():
    return {"status": "healthy"}
