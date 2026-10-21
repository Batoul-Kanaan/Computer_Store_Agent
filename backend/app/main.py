from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.database import connect, ensure_indexes
from backend.app.routes import router


def create_app(db=None, agent_runner=None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        client = None
        if db is None:
            client, live_db = connect()
            app.state.db = live_db
        else:
            app.state.db = db
            ensure_indexes(db)
        app.state.agent_runner = agent_runner
        yield
        if client is not None:
            client.close()

    app = FastAPI(title="Computer Store AI API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
    )
    app.include_router(router)
    return app


app = create_app()
