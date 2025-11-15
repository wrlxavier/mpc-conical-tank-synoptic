"""
FastAPI main application for tank simulation system.

This module implements the main FastAPI application with dual operation modes:
1. Simulation Mode: Batch processing with configurable parameters
2. Real-time Mode: WebSocket-based continuous operation mimicking a real system
"""

from typing import Dict
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio

from app.src.models.simulation_models import (
    SimulationRequest,
    SimulationResponse,
    RealTimeConfig,
    SetpointCommand
)
from app.src.services.simulation_services import SimulationService
from app.src.services.realtime_service import RealTimeService
from app.src.websocket.connection_manager import ConnectionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
connection_manager = ConnectionManager()
realtime_service: RealTimeService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    Args:
        app: FastAPI application instance.
    """
    # Startup
    global realtime_service
    realtime_service = RealTimeService(connection_manager)
    logger.info("Application started - Real-time service initialized")
    
    yield
    
    # Shutdown
    await realtime_service.shutdown()
    logger.info("Application shutdown - Real-time service stopped")


# Initialize FastAPI application
app = FastAPI(
    title="Tank Simulation API",
    description="API for simulating a 5-tank process control system with batch and real-time modes",
    version="2.0.0",
    lifespan=lifespan
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
        content="""
        <h1>Tank Simulation API</h1>
        <p>Navigate to <a href='/synoptic'>/synoptic</a> for the interface.</p>
        <p>API Documentation: <a href='/docs'>/docs</a></p>
        <h3>Operation Modes:</h3>
        <ul>
            <li><strong>Simulation Mode:</strong> POST to /simulation/batch</li>
            <li><strong>Real-time Mode:</strong> WebSocket connection to /ws/realtime</li>
        </ul>
        """
    )


@app.get("/synoptic", response_class=HTMLResponse)
async def get_synoptic() -> FileResponse:
    """
    Serve the synoptic HTML interface.
    
    This endpoint serves the main HTML page that displays the SVG-based
    synoptic diagram and handles user interactions for both simulation modes.
    
    Returns:
        FileResponse: The index.html file containing the synoptic interface.
        
    Raises:
        HTTPException: If the HTML file is not found.
    """
    try:
        return FileResponse("app/static/index.html")
    except FileNotFoundError:
        logger.error("index.html file not found")
        raise HTTPException(
            status_code=404,
            detail="Synoptic interface file not found"
        )


@app.post("/simulation/batch", response_model=SimulationResponse)
async def run_batch_simulation(request: SimulationRequest) -> SimulationResponse:
    """
    Execute batch simulation with provided parameters (Mode 1).
    
    This endpoint runs a complete simulation from start to finish with
    configurable parameters including step inputs, initial conditions,
    and simulation duration. Results are returned after completion.
    
    Args:
        request (SimulationRequest): Simulation parameters including:
            - initial_conditions: Initial states for all tanks
            - control_inputs: Control signals for pumps and valves
            - simulation_config: Time step, duration, and solver settings
            - step_inputs: Optional step changes in setpoints with timing
            
    Returns:
        SimulationResponse: Complete simulation results including:
            - time_series: Arrays of time-stamped data for all variables
            - metadata: Simulation statistics and performance metrics
            - status: Execution status and any warnings
            
    Raises:
        HTTPException: If simulation parameters are invalid or execution fails.
    """
    try:
        logger.info(f"Received batch simulation request: {request.simulation_config.simulation_id}")
        
        # Execute simulation
        response = simulation_service.execute_simulation(request)
        
        logger.info(f"Batch simulation completed: {request.simulation_config.simulation_id}")
        return response
        
    except ValueError as e:
        logger.error(f"Invalid simulation parameters: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid simulation parameters: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Simulation execution error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Simulation execution failed: {str(e)}"
        )


@app.post("/simulation/initialize")
async def initialize_realtime_simulation(config: RealTimeConfig) -> Dict[str, str]:
    """
    Initialize real-time simulation at equilibrium point.
    
    This endpoint prepares the real-time service with initial conditions
    at the equilibrium operating point before WebSocket connection.
    
    Args:
        config (RealTimeConfig): Real-time configuration including:
            - equilibrium_point: Operating point for all tanks
            - sampling_interval: Data transmission interval in seconds
            - enable_noise: Whether to add measurement noise
            
    Returns:
        Dict[str, str]: Status message and session information.
        
    Raises:
        HTTPException: If initialization fails.
    """
    try:
        session_id = await realtime_service.initialize(config)
        logger.info(f"Real-time simulation initialized: {session_id}")
        
        return {
            "status": "initialized",
            "session_id": session_id,
            "message": "Connect to /ws/realtime to start real-time operation"
        }
        
    except Exception as e:
        logger.error(f"Initialization error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Initialization failed: {str(e)}"
        )


@app.websocket("/ws/realtime")
async def websocket_realtime_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time simulation mode (Mode 2).
    
    This endpoint maintains a persistent connection for real-time data
    streaming and setpoint commands. The system starts at equilibrium
    and responds to setpoint changes sent from the client.
    
    Protocol:
        - Client sends: {"type": "setpoint", "data": {...}} for setpoint changes
        - Server sends: {"type": "data", "timestamp": ..., "variables": {...}}
        
    Args:
        websocket: WebSocket connection instance.
        
    Raises:
        WebSocketDisconnect: When client disconnects.
    """
    await connection_manager.connect(websocket)
    client_id = id(websocket)
    logger.info(f"WebSocket client connected: {client_id}")
    
    try:
        # Send initial state
        initial_state = realtime_service.get_current_state()
        await websocket.send_json({
            "type": "initial_state",
            "data": initial_state
        })
        
        # Start real-time loop in background
        realtime_task = asyncio.create_task(
            realtime_service.run_realtime_loop(websocket)
        )
        
        # Listen for setpoint commands
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "setpoint":
                command = SetpointCommand(**data.get("data", {}))
                await realtime_service.update_setpoint(command)
                logger.info(f"Setpoint updated: {command.tank_id} -> {command.variable}")
                
            elif data.get("type") == "pause":
                await realtime_service.pause()
                logger.info("Real-time simulation paused")
                
            elif data.get("type") == "resume":
                await realtime_service.resume()
                logger.info("Real-time simulation resumed")
                
            elif data.get("type") == "reset":
                await realtime_service.reset()
                logger.info("Real-time simulation reset to equilibrium")
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        logger.info(f"WebSocket client disconnected: {client_id}")
        
        # Cancel real-time loop
        if 'realtime_task' in locals():
            realtime_task.cancel()
            
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        connection_manager.disconnect(websocket)


@app.get("/simulation/status")
async def get_simulation_status() -> Dict[str, any]:
    """
    Get current status of real-time simulation.
    
    Returns:
        Dict containing:
            - is_running: Boolean indicating if simulation is active
            - connected_clients: Number of active WebSocket connections
            - current_state: Current values of all process variables
    """
    return {
        "is_running": realtime_service.is_running,
        "connected_clients": connection_manager.get_connection_count(),
        "current_state": realtime_service.get_current_state()
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for monitoring service availability.
    
    Returns:
        Dict[str, str]: Status message indicating service health.
    """
    return {
        "status": "healthy",
        "service": "Tank Simulation API",
        "version": "2.0.0",
        "modes": ["batch_simulation", "realtime_websocket"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
