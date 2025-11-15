"""
Data models for simulation requests and responses.

This module defines Pydantic models for API request/response validation
and documentation, representing the physical and control parameters of
the 5-tank process system.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field, validator
from datetime import datetime


class TankState(BaseModel):
    """
    State variables for a single tank.

    Attributes:
        level: Current liquid level in meters [0, 3.0].
        concentration: Salt concentration in kg/m³ [0, 360] (only for process tanks C, D, E).
    """

    level: float = Field(..., ge=0.0, le=3.0, description="Tank level in meters")
    concentration: Optional[float] = Field(
        None,
        ge=0.0,
        le=360.0,
        description="Salt concentration in kg/m³ (only for process tanks)",
    )


class ControlInputs(BaseModel):
    """
    Control signals for a process tank (C, D, or E).

    Attributes:
        water_pump: Water pump command [0, 1] normalized flow rate.
        brine_pump: Brine pump command [0, 1] normalized flow rate.
        outlet_valve: Outlet valve opening [0, 1] normalized position.
    """

    water_pump: float = Field(
        ..., ge=0.0, le=1.0, description="Water pump command (normalized)"
    )
    brine_pump: float = Field(
        ..., ge=0.0, le=1.0, description="Brine pump command (normalized)"
    )
    outlet_valve: float = Field(
        ..., ge=0.0, le=1.0, description="Outlet valve opening (normalized)"
    )


class UtilityTankControl(BaseModel):
    """
    Control signals for utility tanks (A and B).

    Attributes:
        supply_valve: Supply valve opening [0, 1] for tank refill.
    """

    supply_valve: float = Field(
        ..., ge=0.0, le=1.0, description="Supply valve opening (normalized)"
    )


class InitialConditions(BaseModel):
    """
    Initial state of all tanks in the system.

    Attributes:
        tank_a: Initial state of water reservoir (cylindrical).
        tank_b: Initial state of brine reservoir (cylindrical).
        tank_c: Initial state of process tank C (truncated cone).
        tank_d: Initial state of process tank D (truncated cone).
        tank_e: Initial state of process tank E (truncated cone).
    """

    tank_a: TankState = Field(..., description="Initial state of water reservoir A")
    tank_b: TankState = Field(..., description="Initial state of brine reservoir B")
    tank_c: TankState = Field(..., description="Initial state of process tank C")
    tank_d: TankState = Field(..., description="Initial state of process tank D")
    tank_e: TankState = Field(..., description="Initial state of process tank E")


class ControlSequence(BaseModel):
    """
    Time-varying control inputs for the entire system.

    Attributes:
        tank_a_control: Control for utility tank A.
        tank_b_control: Control for utility tank B.
        tank_c_control: Control inputs for process tank C.
        tank_d_control: Control inputs for process tank D.
        tank_e_control: Control inputs for process tank E.
    """

    tank_a_control: UtilityTankControl
    tank_b_control: UtilityTankControl
    tank_c_control: ControlInputs
    tank_d_control: ControlInputs
    tank_e_control: ControlInputs


class SimulationConfig(BaseModel):
    """
    Configuration parameters for simulation execution.

    Attributes:
        simulation_id: Unique identifier for this simulation run.
        time_step: Integration time step in seconds.
        duration: Total simulation duration in seconds.
        solver: Numerical solver method (e.g., 'rk4', 'euler').
        save_interval: Interval for saving data points in seconds.
    """

    simulation_id: str = Field(..., description="Unique identifier for the simulation")
    time_step: float = Field(
        0.1, gt=0.0, le=10.0, description="Integration time step in seconds"
    )
    duration: float = Field(
        ..., gt=0.0, description="Total simulation duration in seconds"
    )
    solver: str = Field("rk4", description="Numerical solver method")
    save_interval: float = Field(
        1.0, gt=0.0, description="Data save interval in seconds"
    )

    @validator("solver")
    def validate_solver(cls, v: str) -> str:
        """Validate solver method selection."""
        allowed_solvers = ["rk4", "euler", "ode45"]
        if v not in allowed_solvers:
            raise ValueError(f"Solver must be one of {allowed_solvers}")
        return v


class SimulationRequest(BaseModel):
    """
    Complete simulation request payload.

    Attributes:
        initial_conditions: Starting states for all tanks.
        control_inputs: Control signals to be applied during simulation.
        simulation_config: Simulation execution parameters.
        reference_setpoints: Optional reference trajectories for controlled variables.
    """

    initial_conditions: InitialConditions
    control_inputs: ControlSequence
    simulation_config: SimulationConfig
    reference_setpoints: Optional[Dict[str, List[float]]] = Field(
        None, description="Optional reference trajectories for MPC"
    )


class TimeSeriesData(BaseModel):
    """
    Time-series data for a single variable.

    Attributes:
        time: Array of time stamps in seconds.
        values: Array of variable values corresponding to time stamps.
        variable_name: Name/description of the variable.
        unit: Physical unit of the variable.
    """

    time: List[float] = Field(..., description="Time array in seconds")
    values: List[float] = Field(..., description="Variable values")
    variable_name: str = Field(..., description="Variable identifier")
    unit: str = Field(..., description="Physical unit")


class SimulationMetadata(BaseModel):
    """
    Metadata about simulation execution.

    Attributes:
        execution_time: Wall-clock time for simulation in seconds.
        num_steps: Total number of integration steps.
        timestamp: ISO timestamp of simulation execution.
        solver_used: Numerical solver method applied.
        success: Boolean indicating successful completion.
        warnings: List of any warnings generated during simulation.
    """

    execution_time: float = Field(..., description="Execution time in seconds")
    num_steps: int = Field(..., description="Number of integration steps")
    timestamp: str = Field(..., description="ISO timestamp of execution")
    solver_used: str = Field(..., description="Solver method used")
    success: bool = Field(..., description="Simulation success status")
    warnings: List[str] = Field(default_factory=list, description="Warnings")


class SimulationResponse(BaseModel):
    """
    Complete simulation response with results and metadata.

    Attributes:
        simulation_id: Identifier matching the request.
        time_series: Dictionary mapping variable names to their time-series data.
        metadata: Execution statistics and diagnostic information.
        status: Overall execution status message.
    """

    simulation_id: str
    time_series: Dict[str, TimeSeriesData]
    metadata: SimulationMetadata
    status: str = Field(..., description="Execution status message")
