# app/main.py
import os
import atexit
import asyncio
from typing import AsyncGenerator

from fastapi import FastAPI, Depends, Request
from app.logging_setup import setup_cloud_logging

from app.books import (
    add_book_router,
    get_recommendation_router,
    mark_read_router,
    remove_book_router,
    get_all_books_router,
    clear_and_seed_db_router
)

# --- Replace these with your real init/close functions ---
async def create_db_pool():
    # example: await some_db_lib.connect_pool(...)
    class DB:
        async def close(self):
            pass
    await asyncio.sleep(0)  # placeholder for async init
    return DB()

async def close_db_pool(db):
    await db.close()
# -------------------------------------------------------

async def get_db(request: Request) -> AsyncGenerator:
    """
    Dependency that returns a shared, lazily-initialized DB/client stored on app.state.
    The resource is created once and reused for subsequent requests.
    """
    app = request.app
    if not hasattr(app.state, "db") or app.state.db is None:
        # create and store singleton
        app.state.db = await create_db_pool()

        # register synchronous cleanup on process exit
        def _sync_close():
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                # schedule async close if event loop active
                loop.create_task(close_db_pool(app.state.db))
            else:
                # run a new loop to close
                asyncio.run(close_db_pool(app.state.db))
        atexit.register(_sync_close)

    yield app.state.db

def create_app() -> FastAPI:
    app = FastAPI(title="StorySpark API", version="0.1")
    app.state.cloud_logging_client = setup_cloud_logging()

    # include routers (each router can use Depends(get_db) on endpoints)
    app.include_router(add_book_router)
    app.include_router(get_recommendation_router)
    app.include_router(mark_read_router)
    app.include_router(remove_book_router)
    app.include_router(get_all_books_router)
    app.include_router(clear_and_seed_db_router)

    @app.get("/healthz", tags=["health"])
    async def healthz():
        return {"status": "ok"}

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
