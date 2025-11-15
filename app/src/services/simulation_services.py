"""
Service layer for executing tank process simulations.

This module implements the business logic for simulating the 5-tank system,
including model equations, numerical integration, and data aggregation.
"""

from typing import Dict
import time
from datetime import datetime
import numpy as np

from app.src.models.simulation_models import (
    SimulationRequest,
    SimulationResponse,
    TimeSeriesData,
    SimulationMetadata,
)


class SimulationService:
    """
    Service for executing tank process simulations.

    This class encapsulates the simulation logic including model equations,
    numerical integration, and result packaging. Currently returns mocked data.
    """

    def __init__(self):
        """Initialize simulation service with default parameters."""
        # Physical constants (based on project documentation)
        self.BRINE_CONCENTRATION = 360.0  # kg/m³
        self.GRAVITY = 9.81  # m/s²

    def execute_simulation(self, request: SimulationRequest) -> SimulationResponse:
        """
        Execute simulation with provided parameters.

        Args:
            request: Validated simulation request with initial conditions and controls.

        Returns:
            SimulationResponse containing time-series results and metadata.

        Raises:
            ValueError: If simulation parameters are physically inconsistent.
        """
        start_time = time.time()

        # Generate mocked simulation data
        # TODO: Replace with actual tank dynamics integration
        time_series_data = self._generate_mocked_data(request)

        execution_time = time.time() - start_time

        # Calculate number of steps
        num_steps = int(
            request.simulation_config.duration / request.simulation_config.time_step
        )

        # Build metadata
        metadata = SimulationMetadata(
            execution_time=execution_time,
            num_steps=num_steps,
            timestamp=datetime.utcnow().isoformat(),
            solver_used=request.simulation_config.solver,
            success=True,
            warnings=[],
        )

        return SimulationResponse(
            simulation_id=request.simulation_config.simulation_id,
            time_series=time_series_data,
            metadata=metadata,
            status="Simulation completed successfully",
        )

    def _generate_mocked_data(
        self, request: SimulationRequest
    ) -> Dict[str, TimeSeriesData]:
        """
        Generate mocked simulation data for testing.

        Args:
            request: Simulation request with configuration.

        Returns:
            Dictionary mapping variable names to time-series data.
        """
        config = request.simulation_config
        initial = request.initial_conditions

        # Generate time array
        num_points = int(config.duration / config.save_interval) + 1
        time_array = np.linspace(0, config.duration, num_points).tolist()

        # Generate mocked data with simple dynamics
        time_series = {}

        # Tank A (water reservoir) - level
        tank_a_level = self._mock_first_order_response(
            initial.tank_a.level,
            1.5,  # Target setpoint
            time_array,
            tau=300.0,  # Time constant in seconds
        )
        time_series["tank_a_level"] = TimeSeriesData(
            time=time_array, values=tank_a_level, variable_name="Tank A Level", unit="m"
        )

        # Tank B (brine reservoir) - level
        tank_b_level = self._mock_first_order_response(
            initial.tank_b.level, 1.5, time_array, tau=300.0
        )
        time_series["tank_b_level"] = TimeSeriesData(
            time=time_array, values=tank_b_level, variable_name="Tank B Level", unit="m"
        )

        # Tank C - level and concentration
        tank_c_level = self._mock_first_order_response(
            initial.tank_c.level,
            1.5,
            time_array,
            tau=961.0,  # From linearization analysis
        )
        time_series["tank_c_level"] = TimeSeriesData(
            time=time_array, values=tank_c_level, variable_name="Tank C Level", unit="m"
        )

        tank_c_conc = self._mock_first_order_response(
            initial.tank_c.concentration or 180.0, 180.0, time_array, tau=370.0
        )
        time_series["tank_c_concentration"] = TimeSeriesData(
            time=time_array,
            values=tank_c_conc,
            variable_name="Tank C Concentration",
            unit="kg/m³",
        )

        # Tank D - level and concentration
        tank_d_level = self._mock_first_order_response(
            initial.tank_d.level, 1.5, time_array, tau=961.0
        )
        time_series["tank_d_level"] = TimeSeriesData(
            time=time_array, values=tank_d_level, variable_name="Tank D Level", unit="m"
        )

        tank_d_conc = self._mock_first_order_response(
            initial.tank_d.concentration or 180.0, 180.0, time_array, tau=370.0
        )
        time_series["tank_d_concentration"] = TimeSeriesData(
            time=time_array,
            values=tank_d_conc,
            variable_name="Tank D Concentration",
            unit="kg/m³",
        )

        # Tank E - level and concentration
        tank_e_level = self._mock_first_order_response(
            initial.tank_e.level, 1.5, time_array, tau=961.0
        )
        time_series["tank_e_level"] = TimeSeriesData(
            time=time_array, values=tank_e_level, variable_name="Tank E Level", unit="m"
        )

        tank_e_conc = self._mock_first_order_response(
            initial.tank_e.concentration or 180.0, 180.0, time_array, tau=370.0
        )
        time_series["tank_e_concentration"] = TimeSeriesData(
            time=time_array,
            values=tank_e_conc,
            variable_name="Tank E Concentration",
            unit="kg/m³",
        )

        # Control signals (step responses)

        # Tank A controls (only supply valve)
        time_series["tank_a_supply_valve"] = TimeSeriesData(
            time=time_array,
            values=[request.control_inputs.tank_a_control.supply_valve]
            * len(time_array),
            variable_name="Tank A Supply Valve",
            unit="normalized",
        )

        # Tank B controls (only supply valve)
        time_series["tank_b_supply_valve"] = TimeSeriesData(
            time=time_array,
            values=[request.control_inputs.tank_b_control.supply_valve]
            * len(time_array),
            variable_name="Tank B Supply Valve",
            unit="normalized",
        )

        # Tank C controls
        time_series["tank_c_water_pump"] = TimeSeriesData(
            time=time_array,
            values=[request.control_inputs.tank_c_control.water_pump] * len(time_array),
            variable_name="Tank C Water Pump",
            unit="normalized",
        )

        time_series["tank_c_brine_pump"] = TimeSeriesData(
            time=time_array,
            values=[request.control_inputs.tank_c_control.brine_pump] * len(time_array),
            variable_name="Tank C Brine Pump",
            unit="normalized",
        )

        time_series["tank_c_outlet_valve"] = TimeSeriesData(
            time=time_array,
            values=[request.control_inputs.tank_c_control.outlet_valve]
            * len(time_array),
            variable_name="Tank C Outlet Valve",
            unit="normalized",
        )

        # Tank D controls
        time_series["tank_d_water_pump"] = TimeSeriesData(
            time=time_array,
            values=[request.control_inputs.tank_d_control.water_pump] * len(time_array),
            variable_name="Tank D Water Pump",
            unit="normalized",
        )

        time_series["tank_d_brine_pump"] = TimeSeriesData(
            time=time_array,
            values=[request.control_inputs.tank_d_control.brine_pump] * len(time_array),
            variable_name="Tank D Brine Pump",
            unit="normalized",
        )

        time_series["tank_d_outlet_valve"] = TimeSeriesData(
            time=time_array,
            values=[request.control_inputs.tank_d_control.outlet_valve]
            * len(time_array),
            variable_name="Tank D Outlet Valve",
            unit="normalized",
        )

        # Tank E controls
        time_series["tank_e_water_pump"] = TimeSeriesData(
            time=time_array,
            values=[request.control_inputs.tank_e_control.water_pump] * len(time_array),
            variable_name="Tank E Water Pump",
            unit="normalized",
        )

        time_series["tank_e_brine_pump"] = TimeSeriesData(
            time=time_array,
            values=[request.control_inputs.tank_e_control.brine_pump] * len(time_array),
            variable_name="Tank E Brine Pump",
            unit="normalized",
        )

        time_series["tank_e_outlet_valve"] = TimeSeriesData(
            time=time_array,
            values=[request.control_inputs.tank_e_control.outlet_valve]
            * len(time_array),
            variable_name="Tank E Outlet Valve",
            unit="normalized",
        )

        return time_series

    def _mock_first_order_response(
        self, initial_value: float, final_value: float, time_array: list, tau: float
    ) -> list:
        """
        Generate first-order system step response.

        Args:
            initial_value: Starting value.
            final_value: Target steady-state value.
            time_array: Array of time points.
            tau: Time constant in seconds.

        Returns:
            List of values representing first-order response.
        """
        response = []
        for t in time_array:
            value = final_value + (initial_value - final_value) * np.exp(-t / tau)
            response.append(float(value))
        return response
