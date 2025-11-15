# Tank Simulation API

FastAPI-based simulation system for a 5-tank industrial process control project.

## Overview

This API simulates a tank mixing process with:
- 2 cylindrical utility tanks (A: water, B: brine)
- 3 truncated-cone process tanks (C, D, E) with level and concentration control

## Architecture

```
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── models/
│   │   └── simulation_models.py   # Pydantic models for request/response
│   ├── services/
│   │   └── simulation_service.py  # Simulation business logic
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

### POST /simulation
Executes simulation with provided parameters.

**Request Body:**
```
{
  "initial_conditions": {
    "tank_a": {"level": 1.5, "concentration": null},
    "tank_b": {"level": 1.5, "concentration": null},
    "tank_c": {"level": 1.5, "concentration": 180.0},
    "tank_d": {"level": 1.5, "concentration": 180.0},
    "tank_e": {"level": 1.5, "concentration": 180.0}
  },
  "control_inputs": {
    "tank_a_control": {"supply_valve": 0.5},
    "tank_b_control": {"supply_valve": 0.5},
    "tank_c_control": {
      "water_pump": 0.6,
      "brine_pump": 0.6,
      "outlet_valve": 0.5
    },
    "tank_d_control": {
      "water_pump": 0.6,
      "brine_pump": 0.6,
      "outlet_valve": 0.5
    },
    "tank_e_control": {
      "water_pump": 0.6,
      "brine_pump": 0.6,
      "outlet_valve": 0.5
    }
  },
  "simulation_config": {
    "simulation_id": "sim_001",
    "time_step": 0.1,
    "duration": 3000.0,
    "solver": "rk4",
    "save_interval": 1.0
  }
}
```

**Response:**
```
{
  "simulation_id": "sim_001",
  "time_series": {
    "tank_c_level": {
      "time": [0.0, 1.0, 2.0, ...],
      "values": [1.5, 1.51, 1.52, ...],
      "variable_name": "Tank C Level",
      "unit": "m"
    },
    ...
  },
  "metadata": {
    "execution_time": 0.234,
    "num_steps": 30000,
    "timestamp": "2025-11-15T19:22:00.123Z",
    "solver_used": "rk4",
    "success": true,
    "warnings": []
  },
  "status": "Simulation completed successfully"
}
```

## Development Notes

- The `/simulation` endpoint currently returns **mocked data** based on first-order dynamics
- Replace `_generate_mocked_data()` in `simulation_service.py` with actual tank model integration
- Implement nonlinear ODEs from project documentation (truncated cone geometry + Torricelli discharge)
- Add MPC controller integration when control algorithms are ready

## System Requirements

- Python 3.11+
- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum

## License

Academic project - UFMG Control Engineering