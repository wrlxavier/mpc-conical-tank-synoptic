# Tank Simulation API

FastAPI-based simulation system for a 5-tank industrial process control project.

## Overview

This API simulates a tank mixing process with:
- 2 cylindrical utility tanks (A: water, B: brine)
- 3 truncated-cone process tanks (C, D, E) with level and concentration control

**Dual-mode architecture:**  
The backend supports both batch execution (`app.main.run_batch_simulation`) and real-time operation via `app.main.initialize_realtime_simulation` and WebSocket `/ws/realtime`. Real-time mode is managed by `app.src.services.realtime_service.RealTimeService`, enabling continuous simulation and control.

## Architecture

```
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── models/
│   │   └── simulation_models.py   # Pydantic models for request/response
│   ├── services/
│   │   ├── simulation_service.py  # Batch simulation business logic
│   │   └── realtime_service.py    # Real-time simulation loop
│   └── static/
│       └── index.html             # Synoptic web interface
├── nginx/
│   └── nginx.conf                 # Nginx reverse proxy configuration
├── docker-compose.yml             # Docker orchestration
├── Dockerfile                     # Container image definition
└── requirements.txt               # Python dependencies
```

## Quick Start

### Using Docker Compose (Recommended)

```
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Access the application:
- Synoptic Interface: http://localhost/synoptic
- API Documentation: http://localhost/docs
- Health Check: http://localhost/health

### Local Development

```
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python app/main.py
```

Access at http://localhost:8000

## API Endpoints

### GET /synoptic
Serves the HTML synoptic interface with SVG-based process visualization.

### POST /simulation/batch
Executes batch simulation with provided parameters and optional step inputs.

**Request Body:**
```
{
  "initial_conditions": { ... },
  "control_inputs": { ... },
  "simulation_config": { ... },
  "step_inputs": [
    {
      "time": 120.0,
      "tank_id": "tank_c",
      "variable": "level",
      "value": 2.0
    }
    // Validated by app.src.models.simulation_models.StepInput
  ]
}
```

**Response:**  
Same format as previous, with time-series and metadata.

### POST /simulation/initialize
Prepares real-time simulation session using `app.src.models.simulation_models.RealTimeConfig`.

**Request Body:**
```
{
  "initial_conditions": { ... },
  "control_inputs": { ... },
  "realtime_config": {
    "simulation_id": "rt_001",
    "sampling_interval": 0.5,
    "duration": 600.0,
    "noise": true
  }
}
```

**Response:**  
Session info and initial state.

### WebSocket /ws/realtime
Streams real-time state updates. Messages of type `state_update` are emitted by `RealTimeService.run_realtime_loop`:

```
{
  "type": "state_update",
  "data": {
    "timestamp": ...,
    "variables": { ... },
    "controls": { ... },
    "setpoints": { ... }
  }
}
```

## Real-time Loop

The real-time loop integrates tank dynamics continuously, applying physical clamping and optional noise in `RealTimeService._integrate_step`. Control signals are updated using a simplified proportional controller in `RealTimeService._update_controls`. State updates are sent via WebSocket at the configured interval.

## Development Notes

- The `/simulation/batch` endpoint currently returns **mocked data** based on first-order dynamics
- Replace `_generate_mocked_data()` in `app.src.services.simulation_service.SimulationService` with actual tank model integration
- Implement nonlinear ODEs from project documentation (truncated cone geometry + Torricelli discharge)
- Add MPC controller integration when control algorithms are ready
- The real-time mode uses first-order dynamics and proportional control; contributions for full MPC or physical pipeline are welcome

## System Requirements

- Python 3.11+
- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum

## License

Academic project - UFMG Control Engineering