"""
FastAPI main application for tank simulation system.

This module implements the main FastAPI application with endpoints for
serving the synoptic interface and handling simulation requests.
"""

from typing import Dict
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.src.models.simulation_models import SimulationRequest, SimulationResponse
from app.src.services.simulation_services import SimulationService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Tank Simulation API",
    description="API for simulating a 5-tank process control system with level and concentration control",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Initialize simulation service
simulation_service = SimulationService()


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """
    Root endpoint redirecting to synoptic interface.

    Returns:
        HTMLResponse: Redirect message to synoptic endpoint.
    """
    return HTMLResponse(
        content="<h1>Tank Simulation API</h1><p>Navigate to <a href='/synoptic'>/synoptic</a> for the interface.</p>"
    )


@app.get("/synoptic", response_class=HTMLResponse)
async def get_synoptic() -> FileResponse:
    """
    Serve the synoptic HTML interface.

    This endpoint serves the main HTML page that displays the SVG-based
    synoptic diagram and handles user interactions for simulation control.

    Returns:
        FileResponse: The index.html file containing the synoptic interface.

    Raises:
        HTTPException: If the HTML file is not found.
    """
    try:
        return FileResponse("app/static/index.html")
    except FileNotFoundError:
        logger.error("index.html file not found")
        raise HTTPException(status_code=404, detail="Synoptic interface file not found")


@app.post("/simulation", response_model=SimulationResponse)
async def run_simulation(request: SimulationRequest) -> SimulationResponse:
    """
    Execute simulation with provided parameters.

    This endpoint receives simulation parameters including initial conditions,
    control inputs, and simulation time settings, then executes the simulation
    and returns the time-series data for all process variables.

    Args:
        request (SimulationRequest): Simulation parameters including:
            - initial_conditions: Initial states for all tanks
            - control_inputs: Control signals for pumps and valves
            - simulation_config: Time step, duration, and solver settings

    Returns:
        SimulationResponse: Simulation results including:
            - time_series: Arrays of time-stamped data for all variables
            - metadata: Simulation statistics and performance metrics
            - status: Execution status and any warnings

    Raises:
        HTTPException: If simulation parameters are invalid or execution fails.
    """
    try:
        logger.info(
            f"Received simulation request: {request.simulation_config.simulation_id}"
        )

        # Execute simulation
        response = simulation_service.execute_simulation(request)

        logger.info(
            f"Simulation completed successfully: {request.simulation_config.simulation_id}"
        )
        return response

    except ValueError as e:
        logger.error(f"Invalid simulation parameters: {str(e)}")
        raise HTTPException(
            status_code=400, detail=f"Invalid simulation parameters: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Simulation execution error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Simulation execution failed: {str(e)}"
        )


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for monitoring service availability.

    Returns:
        Dict[str, str]: Status message indicating service health.
    """
    return {"status": "healthy", "service": "Tank Simulation API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
