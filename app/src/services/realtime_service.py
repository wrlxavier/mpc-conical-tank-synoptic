"""
Service for real-time simulation mode with WebSocket support.

This module implements the real-time operation mode where the system
starts at equilibrium and responds to setpoint changes in real-time.
"""

import asyncio
import time
from typing import Dict, Optional
import numpy as np
from fastapi import WebSocket
import logging
import uuid

from app.src.models.simulation_models import (
    RealTimeConfig,
    SetpointCommand,
    RealTimeState
)
from app.src.websocket.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


class RealTimeService:
    """
    Service for managing real-time simulation with WebSocket communication.
    
    This service maintains the system state, integrates dynamics in real-time,
    and broadcasts updates to connected clients via WebSocket.
    """
    
    def __init__(self, connection_manager: ConnectionManager):
        """
        Initialize real-time service.
        
        Args:
            connection_manager: WebSocket connection manager instance.
        """
        self.connection_manager = connection_manager
        self.is_running = False
        self.is_paused = False
        self.session_id: Optional[str] = None
        
        # Configuration
        self.config: Optional[RealTimeConfig] = None
        self.sampling_interval = 0.5  # seconds
        
        # State variables
        self.current_state: Dict[str, float] = {}
        self.setpoints: Dict[str, float] = {}
        self.controls: Dict[str, float] = {}
        
        # Physical constants
        self.BRINE_CONCENTRATION = 360.0  # kg/m³
        self.GRAVITY = 9.81  # m/s²
        
        # Integration
        self.last_update_time = time.time()
        
    async def initialize(self, config: RealTimeConfig) -> str:
        """
        Initialize real-time simulation at equilibrium.
        
        Args:
            config: Real-time configuration with equilibrium point.
            
        Returns:
            Session ID for this simulation instance.
        """
        self.config = config
        self.session_id = str(uuid.uuid4())
        self.sampling_interval = config.sampling_interval
        
        # Initialize state at equilibrium
        self.current_state = {
            **{f"{k}_level": v for k, v in config.equilibrium_point.levels.items()},
            **{f"{k}_concentration": v for k, v in config.equilibrium_point.concentrations.items()}
        }
        
        # Initialize setpoints (same as equilibrium initially)
        self.setpoints = self.current_state.copy()
        
        # Initialize controls at equilibrium
        self.controls = config.equilibrium_point.controls.copy()
        
        self.is_running = True
        self.is_paused = False
        self.last_update_time = time.time()
        
        logger.info(f"Real-time simulation initialized: {self.session_id}")
        return self.session_id
    
    async def run_realtime_loop(self, websocket: WebSocket):
        """
        Main real-time loop that integrates dynamics and sends updates.
        
        Args:
            websocket: WebSocket connection for sending data.
        """
        logger.info("Starting real-time loop")
        
        while self.is_running:
            try:
                if not self.is_paused:
                    # Calculate time since last update
                    current_time = time.time()
                    dt = current_time - self.last_update_time
                    
                    # Integrate dynamics (TODO: replace with actual model)
                    self._integrate_step(dt)
                    
                    # Update control signals (simple PI control for demo)
                    self._update_controls()
                    
                    self.last_update_time = current_time
                    
                    # Prepare state message
                    state = RealTimeState(
                        timestamp=current_time,
                        variables=self.current_state,
                        setpoints=self.setpoints,
                        controls=self.controls
                    )
                    
                    # Send to client
                    await websocket.send_json({
                        "type": "state_update",
                        "data": state.dict()
                    })
                
                # Wait for next sampling interval
                await asyncio.sleep(self.sampling_interval)
                
            except asyncio.CancelledError:
                logger.info("Real-time loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in real-time loop: {str(e)}")
                break
    
    def _integrate_step(self, dt: float):
        """
        Integrate system dynamics for one time step.
        
        Args:
            dt: Time step in seconds.
        """
        # TODO: Replace with actual tank dynamics
        # For now, simple first-order response toward setpoint
        
        for key in self.current_state:
            if key in self.setpoints:
                setpoint = self.setpoints[key]
                current = self.current_state[key]
                
                # First-order dynamics: dx/dt = (setpoint - current) / tau
                tau = 300.0  # Time constant in seconds
                derivative = (setpoint - current) / tau
                
                # Euler integration
                self.current_state[key] += derivative * dt
                
                # Add noise if enabled
                if self.config and self.config.enable_noise:
                    noise = np.random.normal(0, self.config.noise_level * abs(current))
                    self.current_state[key] += noise
                
                # Clamp to physical limits
                if 'level' in key:
                    self.current_state[key] = max(0.0, min(3.0, self.current_state[key]))
                elif 'concentration' in key:
                    self.current_state[key] = max(0.0, min(360.0, self.current_state[key]))
    
    def _update_controls(self):
        """
        Update control signals based on current errors (simple PI control).
        
        TODO: Replace with actual MPC or PID controller.
        """
        # Simple proportional control for demo
        Kp = 0.1
        
        for key in self.setpoints:
            if key in self.current_state:
                error = self.setpoints[key] - self.current_state[key]
                
                # Determine which control to adjust
                control_key = self._get_control_for_variable(key)
                if control_key and control_key in self.controls:
                    # Proportional action
                    self.controls[control_key] += Kp * error
                    
                    # Clamp to [0, 1]
                    self.controls[control_key] = max(0.0, min(1.0, self.controls[control_key]))
    
    def _get_control_for_variable(self, variable_key: str) -> Optional[str]:
        """
        Map variable to its primary control signal.
        
        Args:
            variable_key: Variable identifier (e.g., 'tank_c_level').
            
        Returns:
            Control signal key or None.
        """
        # Simplified mapping for demonstration
        if 'tank_c_level' in variable_key:
            return 'tank_c_water_pump'
        elif 'tank_c_concentration' in variable_key:
            return 'tank_c_brine_pump'
        elif 'tank_d_level' in variable_key:
            return 'tank_d_water_pump'
        elif 'tank_d_concentration' in variable_key:
            return 'tank_d_brine_pump'
        elif 'tank_e_level' in variable_key:
            return 'tank_e_water_pump'
        elif 'tank_e_concentration' in variable_key:
            return 'tank_e_brine_pump'
        return None
    
    async def update_setpoint(self, command: SetpointCommand):
        """
        Update setpoint in response to user command.
        
        Args:
            command: Setpoint change command from WebSocket.
        """
        key = f"{command.tank_id}_{command.variable}"
        
        if key in self.setpoints:
            old_value = self.setpoints[key]
            self.setpoints[key] = command.value
            logger.info(f"Setpoint changed: {key} from {old_value:.2f} to {command.value:.2f}")
        else:
            logger.warning(f"Unknown setpoint key: {key}")
    
    def get_current_state(self) -> Dict[str, any]:
        """
        Get current simulation state.
        
        Returns:
            Dictionary with current variables, setpoints, and controls.
        """
        return {
            "variables": self.current_state,
            "setpoints": self.setpoints,
            "controls": self.controls,
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "session_id": self.session_id
        }
    
    async def pause(self):
        """Pause real-time simulation."""
        self.is_paused = True
        logger.info("Real-time simulation paused")
    
    async def resume(self):
        """Resume real-time simulation."""
        self.is_paused = False
        self.last_update_time = time.time()  # Reset time reference
        logger.info("Real-time simulation resumed")
    
    async def reset(self):
        """Reset simulation to equilibrium point."""
        if self.config:
            self.current_state = {
                **{f"{k}_level": v for k, v in self.config.equilibrium_point.levels.items()},
                **{f"{k}_concentration": v for k, v in self.config.equilibrium_point.concentrations.items()}
            }
            self.setpoints = self.current_state.copy()
            self.controls = self.config.equilibrium_point.controls.copy()
            self.last_update_time = time.time()
            logger.info("Real-time simulation reset to equilibrium")
    
    async def shutdown(self):
        """Shutdown real-time service."""
        self.is_running = False
        logger.info("Real-time service shutdown")
