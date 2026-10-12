from fastapi import Depends, FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .routers import products, reports

app = FastAPI(title=settings.app_name, version=settings.version)
app.include_router(products.router)
app.include_router(reports.router)

Instrumentator(excluded_handlers=["/metrics", "/health", "/ready"]).instrument(app).expose(
    app, endpoint="/metrics", include_in_schema=False
)


@app.get("/", include_in_schema=False)
def root():
    return {"service": settings.app_name, "version": settings.version, "docs": "/docs"}


@app.get("/health", tags=["ops"])
def health():
    return {"status": "UP"}


@app.get("/ready", tags=["ops"])
def ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(503, "Database unavailable")
    return {"status": "READY"}
