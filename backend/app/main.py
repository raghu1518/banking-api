from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.bootstrap import bootstrap_defaults
from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.exceptions import register_exception_handlers
from app.core.logger import configure_logging
from app.core.response import api_response
from app.core.schema import apply_schema_compatibility
from app.routers import accounts, audit_logs, auth, debit_cards, deposits, mutual_funds, transactions, users

configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    apply_schema_compatibility(engine)
    with SessionLocal() as session:
        bootstrap_defaults(session)
    yield


app = FastAPI(
    title=settings.app_name,
    docs_url="/docs" if settings.enable_swagger else None,
    redoc_url="/redoc" if settings.enable_swagger else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.get("/")
def health():
    return api_response("success", "Banking API is running", {"version": "1.0.0"})


app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(accounts.router, prefix=settings.api_prefix)
app.include_router(transactions.router, prefix=settings.api_prefix)
app.include_router(debit_cards.router, prefix=settings.api_prefix)
app.include_router(mutual_funds.router, prefix=settings.api_prefix)
app.include_router(deposits.router, prefix=settings.api_prefix)
app.include_router(audit_logs.router, prefix=settings.api_prefix)
