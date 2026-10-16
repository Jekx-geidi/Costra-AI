from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
import app.models  # noqa: F401 — ensures all models are registered with Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.routers import auth, accounts, imports, records, sync, reconciliation, reporting, assistant
    application.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    application.include_router(accounts.router, prefix="/api/ai-billing/accounts", tags=["accounts"])
    application.include_router(imports.router, prefix="/api/ai-billing/imports", tags=["imports"])
    application.include_router(records.router, prefix="/api/ai-billing/records", tags=["records"])
    application.include_router(sync.router, prefix="/api/ai-billing/sync", tags=["sync"])
    application.include_router(reconciliation.router, prefix="/api/ai-billing/reconciliation", tags=["reconciliation"])
    application.include_router(reporting.router, prefix="/api/ai-billing", tags=["reporting"])
    application.include_router(assistant.router, prefix="/api/assistant", tags=["assistant"])

    @application.get("/health", tags=["health"])
    async def health():
        return {"status": "ok", "app": settings.app_name}

    return application


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.api_host, port=settings.api_port, reload=True)
