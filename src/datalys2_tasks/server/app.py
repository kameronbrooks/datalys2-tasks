from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from .database import init_db
from contextlib import asynccontextmanager
from .scheduler_router import router as scheduler_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown (if needed)

app = FastAPI(title="Datalys2 SERVER", lifespan=lifespan)
app.include_router(scheduler_router)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/dashboard", StaticFiles(directory=static_dir, html=True), name="static")

@app.get("/")
def read_root():
    # Redirect root to dashboard
    return RedirectResponse(url="/dashboard/")

def start_server():
    import uvicorn
    from ..core.config import settings
    uvicorn.run(app, host=settings.server_host, port=settings.server_port)

if __name__ == "__main__":
    start_server()

