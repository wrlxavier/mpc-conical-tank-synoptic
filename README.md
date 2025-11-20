# Tank Simulation API

FastAPI-based simulation system for a 5-tank industrial process control project.

## Overview

This API simulates a tank mixing process with:
- 2 cylindrical utility tanks (A: water, B: brine)
- 3 truncated-cone process tanks (C, D, E) with level and concentration control

**Real-time focus:**  
The backend streams a continuous simulation via `app.main.initialize_realtime_simulation` (REST) and `/ws/realtime` (WebSocket). Real-time mode is managed by `app.src.services.realtime_service.RealTimeService`, enabling continuous monitoring and setpoint adjustments.

## Architecture

```
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── models/
│   │   └── simulation_models.py   # Pydantic models for request/response
│   ├── services/
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

### POST /simulation/initialize
Prepares the real-time simulation session using `app.src.models.simulation_models.RealTimeConfig`.

**Request Body:**
```
{
  "equilibrium_point": {
    "levels": {
      "tank_a": 1.5,
      "tank_b": 1.5,
      "tank_c": 1.5,
      "tank_d": 1.5,
      "tank_e": 1.5
    },
    "concentrations": {
      "tank_c": 180,
      "tank_d": 180,
      "tank_e": 180
    },
    "controls": {
      "tank_a_supply_valve": 0.5,
      "tank_b_supply_valve": 0.5,
      "tank_c_water_pump": 0.6,
      "tank_c_brine_pump": 0.6,
      "tank_c_outlet_valve": 0.5,
      "tank_d_water_pump": 0.6,
      "tank_d_brine_pump": 0.6,
      "tank_d_outlet_valve": 0.5,
      "tank_e_water_pump": 0.6,
      "tank_e_brine_pump": 0.6,
      "tank_e_outlet_valve": 0.5
    }
  },
  "sampling_interval": 0.5,
  "enable_noise": false,
  "noise_level": 0.01
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

- Real-time mode currently relies on the physics core under `app/src/simulation` driven by `RealTimeService`
- Implement nonlinear ODE refinements or improved MPC tuning directly in the real-time loop
- Extend the WebSocket payload if additional diagnostics or KPIs are required

## System Requirements

- Python 3.11+
- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum

## License

Academic project - UFMG Control Engineering