"""
Data models for the real-time simulation API.

These Pydantic models describe configuration, commands, and streaming payloads
used by the WebSocket-based simulator.
"""

from typing import Optional, Dict
from pydantic import BaseModel, Field, validator


class EquilibriumPoint(BaseModel):
    """
    Equilibrium operating point for real-time simulation.

    Attributes:
        levels: Dictionary mapping tank IDs to equilibrium levels.
        concentrations: Dictionary mapping process tank IDs to equilibrium concentrations.
        controls: Dictionary mapping control signals to equilibrium values.
    """

    levels: Dict[str, float] = Field(
        ..., description="Equilibrium levels for all tanks"
    )
    concentrations: Dict[str, float] = Field(
        ..., description="Equilibrium concentrations for process tanks"
    )
    controls: Dict[str, float] = Field(..., description="Equilibrium control signals")


class RealTimeConfig(BaseModel):
    """
    Configuration for real-time simulation mode.

    Attributes:
        equilibrium_point: Operating point where simulation starts.
        sampling_interval: Data transmission interval in seconds.
        enable_noise: Whether to add measurement noise.
        noise_level: Standard deviation of measurement noise (if enabled).
    """

    equilibrium_point: EquilibriumPoint
    sampling_interval: float = Field(
        0.5,
        gt=0.0,
        le=5.0,
        description="Data sampling/transmission interval in seconds",
    )
    enable_noise: bool = Field(False, description="Enable measurement noise simulation")
    noise_level: float = Field(
        0.01, ge=0.0, le=0.1, description="Noise standard deviation (normalized)"
    )


class SetpointCommand(BaseModel):
    """
    Setpoint change command for real-time mode.

    Attributes:
        tank_id: Tank identifier.
        variable: Variable to change ('level' or 'concentration').
        value: New setpoint value.
        timestamp: Optional client timestamp.
    """

    tank_id: str = Field(..., description="Tank identifier")
    variable: str = Field(..., description="Variable to control")
    value: float = Field(..., description="New setpoint value")
    timestamp: Optional[float] = Field(None, description="Client timestamp")

    @validator("tank_id")
    def validate_tank_id(cls, v: str) -> str:
        """Validate tank identifier."""
        allowed = ["tank_a", "tank_b", "tank_c", "tank_d", "tank_e"]
        if v not in allowed:
            raise ValueError(f"Tank ID must be one of {allowed}")
        return v

    @validator("variable")
    def validate_variable(cls, v: str) -> str:
        """Validate variable name."""
        allowed = ["level", "concentration"]
        if v not in allowed:
            raise ValueError(f"Variable must be one of {allowed}")
        return v


class RealTimeState(BaseModel):
    """
    Current state snapshot for real-time mode.

    Attributes:
        timestamp: Server timestamp in seconds since epoch.
        variables: Dictionary of current variable values.
        setpoints: Dictionary of current setpoint values.
        controls: Dictionary of current control signal values.
    """

    timestamp: float = Field(..., description="Server timestamp")
    variables: Dict[str, float] = Field(..., description="Current process variables")
    setpoints: Dict[str, float] = Field(..., description="Current setpoints")
    controls: Dict[str, float] = Field(..., description="Current control signals")
