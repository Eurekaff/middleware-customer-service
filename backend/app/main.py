from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.db.session import Base, engine
from app import models  # noqa: F401


def create_app() -> FastAPI:
    Base.metadata.create_all(bind=engine)

    fastapi_app = FastAPI(title="Middleware Customer Service")
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    fastapi_app.include_router(router, prefix="/api")
    return fastapi_app


app = create_app()
