from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import world
from app.core.config import settings

app = FastAPI(
    title="Urban Resilience Simulator API",
    description="API for the Urban Resilience Simulation Platform",
    version="1.0.0"
)

# CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(world.router, prefix="/api/v1", tags=["world"])

@app.get("/")
async def root():
    return {"message": "Urban Resilience Simulator API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    # Run the Uvicorn server
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)