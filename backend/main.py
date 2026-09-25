from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import time

from .routers import alerts, entities, transactions, search, system, upload
from .services import data_service

app = FastAPI(
    title='BTC-TRACE API',
    description='AI-Powered Bitcoin Transaction Monitoring & Analysis',
    version='1.0.0',
    docs_url='/api/docs',
    openapi_url='/api/openapi.json'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles

api_router = APIRouter(prefix="/api")
api_router.include_router(alerts.router)
api_router.include_router(entities.router)
api_router.include_router(transactions.router)
api_router.include_router(search.router)
api_router.include_router(system.router)
api_router.include_router(upload.router)

@api_router.get("/health", tags=["Health"])
def health_check():
    ds = data_service.data_service
    return {
        "status": "healthy",
        "version": app.version,
        "uptime_seconds": time.time() - startup_time,
        "data_loaded": ds.data_loaded if ds else False,
        "model_loaded": ds.model_loaded if ds else False
    }

app.include_router(api_router)

startup_time = time.time()

@app.on_event("startup")
async def startup_event():
    data_dir = Path(__file__).parent.parent / "data"
    data_service.data_service = data_service.DataService(data_dir)

# Mount frontend
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {"message": "Frontend not built. Run 'npm run build' in the frontend directory."}
