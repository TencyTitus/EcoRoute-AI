from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine

# Import all models from consolidated models.py
from app import models

from app.routers import vehicles, routes, emissions
from app.routers import auth, optimization, delivery_points, analytics, driver, admin, manager

import logging

# Configure logging to file
logging.basicConfig(
    filename='backend.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="EcoRoute AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost",
        "http://127.0.0.1",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from starlette.requests import Request
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Request Error: {str(e)}")
        raise e

# Create all tables using Base from models.py
models.Base.metadata.create_all(bind=engine)

# Register routers
app.include_router(auth.router)
app.include_router(vehicles.router)
app.include_router(routes.router)
app.include_router(emissions.router)
app.include_router(optimization.router)
app.include_router(delivery_points.router)
app.include_router(analytics.router)
app.include_router(driver.router)
app.include_router(admin.router)
app.include_router(manager.router)

@app.get("/")
def root():
    return {"status": "EcoRoute AI Backend Running"}
