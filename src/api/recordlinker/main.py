import os.path

import fastapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import FileResponse

from recordlinker import middleware
from recordlinker._version import __version__
from recordlinker.config import settings
from recordlinker.routes.algorithm_router import router as algorithm_router
from recordlinker.routes.demo_router import router as demo_router
from recordlinker.routes.health_router import router as health_router
from recordlinker.routes.link_router import router as link_router
from recordlinker.routes.patient_router import router as patient_router
from recordlinker.routes.person_router import router as person_router
from recordlinker.routes.seed_router import router as seed_router

app = fastapi.FastAPI(title="Record Linker", version=__version__)
api = fastapi.FastAPI(
    title="Record Linker API",
    version=__version__,
    contact={
        "name": "CDC Public Health Data Infrastructure",
        "url": "https://github.com/CDCgov/RecordLinker",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0",
    },
    summary="""
        The RecordLinker is a service that links records from two datasets based on a set
        of common attributes. The service is designed to be used in a variety of public
        health contexts, such as linking patient records from different sources or linking
        records from different public health surveillance systems. The service uses a
        probabilistic record linkage algorithm to determine the likelihood that two
        records refer to the same entity. The service is implemented as a RESTful API that
        can be accessed over HTTP. The API provides endpoints for uploading datasets,
        configuring the record linkage process, and retrieving the results of the record
        linkage process.
    """.strip(),
)

api.add_middleware(middleware.CorrelationIdMiddleware)
api.add_middleware(middleware.AccessLogMiddleware)
if settings.ui_host:
    # Add CORS for local development
    api.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.ui_host],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(GZipMiddleware, minimum_size=500, compresslevel=5)


# FIXME: Change health check endpoint to /api/health
api.include_router(health_router)
app.include_router(link_router, tags=["link"])
app.include_router(algorithm_router, prefix="/algorithm", tags=["algorithm"])
app.include_router(person_router, prefix="/person", tags=["mpi"])
app.include_router(patient_router, prefix="/patient", tags=["mpi"])
app.include_router(seed_router, prefix="/seed", tags=["mpi"])
api.include_router(demo_router, prefix="/demo", tags=["demo"])

app.mount(settings.api_root_path, api)

if settings.ui_static_dir:

    @app.exception_handler(StarletteHTTPException)
    async def not_found_handler(request, exc):
        """
        Custom 404 page
        """
        if exc.status_code == fastapi.status.HTTP_404_NOT_FOUND:
            return FileResponse(os.path.join(settings.ui_static_dir, "404.html"), status_code=404)
        raise exc

    # page routes
    @app.get("/match-queue")
    @app.get("/match-review")
    async def page(request: fastapi.Request):
        """
        Route to handle custom HTML pages for the UI
        """
        path: str = request.url.path.strip("/") or "index"
        view: str = path if path.endswith(".ico") else f"{path}.html"
        return FileResponse(os.path.join(settings.ui_static_dir, view))

    # Other static files of NextJS app (includes index.html)
    # [page-rehydration].txt files, images and js/css bundles in _next
    app.mount(
        "/",
        StaticFiles(directory=os.path.join(settings.ui_static_dir), html=True),
        name="SpaStatic",
    )
