from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from utilities.help_func import LOGS
from services.x_twitter.routes import router as x_routes



app = FastAPI(    
    title="Bengaluru Feeds API",
    description="API to fetch crime, local news, weather, civic, potholes, and traffic feeds for Bengaluru from X (formerly Twitter) API v2.",
    version="1.0.0"
    )

# --- Add Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(x_routes, prefix="/x", tags=["X_twitter"])


# --- Root Endpoint ---
@app.get("/")
async def root():
    """Provides a simple welcome message."""
    await LOGS.alog_info("Root endpoint accessed.")
    return JSONResponse({"message": "Root route for Agentic AI day"})