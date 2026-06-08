from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .routers import (
    admin,
    auth,
    diagnostic,
    problems,
    recommendations,
    skills,
    submissions,
)

app = FastAPI(
    title="SmartCode API",
    version="0.2.0",
    description="Backend API for SmartCode -- adaptive Python practice with AI grading (LAU COE 416 group 11).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}


# Auth
app.include_router(auth.router, prefix="/api")

# Student
app.include_router(skills.router, prefix="/api")
app.include_router(skills.catalog_router, prefix="/api")
app.include_router(problems.router, prefix="/api")
app.include_router(submissions.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
app.include_router(diagnostic.router, prefix="/api")

# Admin
app.include_router(admin.router, prefix="/api")


# ---------------------------------------------------------------------------
# Production: serve the React SPA from the same origin so we ship one process.
# Set FRONTEND_DIST to the absolute path of the Vite `dist/` folder.
# Leave it empty in dev — Vite's dev server hosts the frontend on :5173.
# ---------------------------------------------------------------------------
_frontend_dist = (
    Path(settings.frontend_dist).expanduser().resolve()
    if settings.frontend_dist
    else None
)
if _frontend_dist and _frontend_dist.is_dir():
    # Hashed bundles (JS/CSS/images) live under dist/assets — serve them as static.
    assets_dir = _frontend_dist / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # index.html must NOT be cached by browsers -- otherwise users keep seeing
    # the previous build's JS reference after a redeploy. Hashed asset files
    # under /assets/* are still freely cacheable (their hash changes per build),
    # so we only force no-store on the HTML shell.
    _NO_STORE = {"Cache-Control": "no-store, max-age=0, must-revalidate"}

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        # Don't let the SPA swallow API errors — let unknown /api/* return 404 JSON.
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        # Serve an exact asset if it exists (favicon, vite.svg, etc.)
        candidate = _frontend_dist / full_path
        if full_path and candidate.is_file():
            return FileResponse(str(candidate))
        # Otherwise hand back index.html so the React router can take over.
        index = _frontend_dist / "index.html"
        if not index.is_file():
            raise HTTPException(
                status_code=500, detail="index.html missing from frontend build"
            )
        return FileResponse(str(index), headers=_NO_STORE)
