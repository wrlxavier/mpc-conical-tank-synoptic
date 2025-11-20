"""
Service for real-time simulation with actual tank physics and MPC control.
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
    RealTimeState,
)
from app.src.websocket.connection_manager import ConnectionManager

# Importar núcleo de simulação
from app.src.simulation import (
    ModeloSistemaTanques,
    SistemaControle,
    PONTO_OPERACAO,
    TS_CONTROLADOR,
    DT_INTEGRACAO,
)

logger = logging.getLogger(__name__)


class RealTimeService:
    """
    Real-time simulation service with actual tank physics and MPC control.

    Integrates:
    - ModeloSistemaTanques: Non-linear tank physics
    - SistemaControle: MPC controllers (C, D, E) + PID (A, B)
    """

    def __init__(self, connection_manager: ConnectionManager):
        """Initialize real-time service with simulation core."""
        self.connection_manager = connection_manager
        self.is_running = False
        self.is_paused = False
        self.session_id: Optional[str] = None

        # Configuração
        self.config: Optional[RealTimeConfig] = None
        self.sampling_interval = 0.5  # WebSocket update rate (seconds)
        self.control_interval = TS_CONTROLADOR  # MPC execution rate (5s)
        self.integration_step = DT_INTEGRACAO  # Physics integration step (0.5s)

        # Núcleo de simulação
        self.modelo: Optional[ModeloSistemaTanques] = None
        self.controladores: Optional[SistemaControle] = None

        # Estado do sistema
        self.current_state: Dict[str, float] = {}
        self.setpoints: Dict[str, float] = {}
        self.control_actions: Dict[str, float] = {}

        # Temporização
        self.last_update_time = time.time()
        self.last_control_time = time.time()

    async def initialize(self, config: RealTimeConfig) -> str:
        """
        Initialize simulation at equilibrium point.

        Args:
            config: Real-time configuration.

        Returns:
            Session ID.
        """
        self.config = config
        self.session_id = str(uuid.uuid4())
        self.sampling_interval = config.sampling_interval

        # Instanciar modelo físico
        self.modelo = ModeloSistemaTanques()

        # Condições iniciais no ponto de operação
        estado_inicial = np.array(
            [
                PONTO_OPERACAO["hA_eq"],
                PONTO_OPERACAO["hB_eq"],
                PONTO_OPERACAO["h_eq"],  # hC
                PONTO_OPERACAO["C_eq"],  # CC
                PONTO_OPERACAO["h_eq"],  # hD
                PONTO_OPERACAO["C_eq"],  # CD
                PONTO_OPERACAO["h_eq"],  # hE
                PONTO_OPERACAO["C_eq"],  # CE
            ]
        )

        self.modelo.definir_estado(estado_inicial)

        # Instanciar sistema de controle (MPC + PID)
        self.controladores = SistemaControle(Ts=self.control_interval)

        # Estado atual (para WebSocket)
        self.current_state = {
            "tank_a_level": estado_inicial[0],
            "tank_b_level": estado_inicial[1],
            "tank_c_level": estado_inicial[2],
            "tank_c_concentration": estado_inicial[3],
            "tank_d_level": estado_inicial[4],
            "tank_d_concentration": estado_inicial[5],
            "tank_e_level": estado_inicial[6],
            "tank_e_concentration": estado_inicial[7],
        }

        # Setpoints iniciais (mesmos do equilíbrio)
        self.setpoints = self.current_state.copy()

        # Controles iniciais
        self.control_actions = {
            "tank_a_supply_valve": PONTO_OPERACAO["uA_eq"],
            "tank_b_supply_valve": PONTO_OPERACAO["uB_eq"],
            "tank_c_water_pump": PONTO_OPERACAO["u1_eq"],
            "tank_c_brine_pump": PONTO_OPERACAO["u2_eq"],
            "tank_c_outlet_valve": PONTO_OPERACAO["u3_eq"],
            "tank_d_water_pump": PONTO_OPERACAO["u1_eq"],
            "tank_d_brine_pump": PONTO_OPERACAO["u2_eq"],
            "tank_d_outlet_valve": PONTO_OPERACAO["u3_eq"],
            "tank_e_water_pump": PONTO_OPERACAO["u1_eq"],
            "tank_e_brine_pump": PONTO_OPERACAO["u2_eq"],
            "tank_e_outlet_valve": PONTO_OPERACAO["u3_eq"],
        }

        self.is_running = True
        self.is_paused = False
        self.last_update_time = time.time()
        self.last_control_time = time.time()

        logger.info(f"Real-time simulation initialized with MPC: {self.session_id}")
        return self.session_id

    async def run_realtime_loop(self, websocket: WebSocket):
        """
        Main real-time loop: integrate physics + execute MPC.

        Args:
            websocket: WebSocket connection for streaming data.
        """
        logger.info("Starting real-time loop with MPC control")

        while self.is_running:
            try:
                if not self.is_paused:
                    current_time = time.time()

                    # 1. Executar MPC a cada control_interval (5s)
                    if (current_time - self.last_control_time) >= self.control_interval:
                        self._execute_mpc_step()
                        self.last_control_time = current_time

                    # 2. Integrar física a cada integration_step (0.5s)
                    dt = current_time - self.last_update_time
                    if dt >= self.integration_step:
                        self._integrate_physics_step(dt)
                        self.last_update_time = current_time

                    # 3. Atualizar current_state a partir do modelo
                    self._update_state_from_model()

                    # 4. Enviar dados via WebSocket
                    state = RealTimeState(
                        timestamp=current_time,
                        variables=self.current_state,
                        setpoints=self.setpoints,
                        controls=self.control_actions,
                    )

                    await websocket.send_json(
                        {"type": "state_update", "data": state.dict()}
                    )

                # Aguardar próximo sampling_interval (0.5s)
                await asyncio.sleep(self.sampling_interval)

            except asyncio.CancelledError:
                logger.info("Real-time loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in real-time loop: {str(e)}", exc_info=True)
                break

    def _execute_mpc_step(self):
        """
        Execute MPC optimization and update control actions.
        """
        if not self.modelo or not self.controladores:
            logger.warning("MPC step skipped: simulation core not initialized")
            return

        # Obter estado atual do modelo
        estado_atual = self.modelo.obter_estado()

        # Montar dicionário de estados para controladores
        estados = {
            "hA": estado_atual[0],
            "hB": estado_atual[1],
            "hC": estado_atual[2],
            "CC": estado_atual[3],
            "hD": estado_atual[4],
            "CD": estado_atual[5],
            "hE": estado_atual[6],
            "CE": estado_atual[7],
        }

        # Montar dicionário de referências (setpoints)
        referencias = {
            "hC_ref": self.setpoints["tank_c_level"],
            "CC_ref": self.setpoints["tank_c_concentration"],
            "hD_ref": self.setpoints["tank_d_level"],
            "CD_ref": self.setpoints["tank_d_concentration"],
            "hE_ref": self.setpoints["tank_e_level"],
            "CE_ref": self.setpoints["tank_e_concentration"],
        }

        # Executar MPC (calcula ações ótimas)
        acoes = self.controladores.calcular_acoes(estados, referencias)

        # Atualizar control_actions
        self.control_actions = {
            "tank_a_supply_valve": acoes["uA"],
            "tank_b_supply_valve": acoes["uB"],
            "tank_c_water_pump": acoes["uC1"],
            "tank_c_brine_pump": acoes["uC2"],
            "tank_c_outlet_valve": acoes["uC3"],
            "tank_d_water_pump": acoes["uD1"],
            "tank_d_brine_pump": acoes["uD2"],
            "tank_d_outlet_valve": acoes["uD3"],
            "tank_e_water_pump": acoes["uE1"],
            "tank_e_brine_pump": acoes["uE2"],
            "tank_e_outlet_valve": acoes["uE3"],
        }

        logger.debug(f"MPC step executed: {acoes}")

    def _integrate_physics_step(self, dt: float):
        """
        Integrate tank physics for one time step.

        Args:
            dt: Time step (seconds).
        """
        if not self.modelo:
            logger.warning("Physics integration skipped: model not initialized")
            return

        # Montar vetor de controles
        u = np.array(
            [
                self.control_actions["tank_a_supply_valve"],
                self.control_actions["tank_b_supply_valve"],
                self.control_actions["tank_c_water_pump"],
                self.control_actions["tank_c_brine_pump"],
                self.control_actions["tank_c_outlet_valve"],
                self.control_actions["tank_d_water_pump"],
                self.control_actions["tank_d_brine_pump"],
                self.control_actions["tank_d_outlet_valve"],
                self.control_actions["tank_e_water_pump"],
                self.control_actions["tank_e_brine_pump"],
                self.control_actions["tank_e_outlet_valve"],
            ]
        )

        # Integrar modelo físico (RK4 ou Euler)
        self.modelo.integrar_passo(u, dt, metodo="euler")

    def _update_state_from_model(self):
        """Update current_state dictionary from model state vector."""
        if not self.modelo:
            return

        estado = self.modelo.obter_estado()

        self.current_state = {
            "tank_a_level": float(estado[0]),
            "tank_b_level": float(estado[1]),
            "tank_c_level": float(estado[2]),
            "tank_c_concentration": float(estado[3]),
            "tank_d_level": float(estado[4]),
            "tank_d_concentration": float(estado[5]),
            "tank_e_level": float(estado[6]),
            "tank_e_concentration": float(estado[7]),
        }

    async def update_setpoint(self, command: SetpointCommand):
        """
        Update setpoint from user command.

        Args:
            command: Setpoint change command.
        """
        key = f"{command.tank_id}_{command.variable}"

        if key in self.setpoints:
            old_value = self.setpoints[key]
            self.setpoints[key] = command.value
            logger.info(
                f"Setpoint changed: {key} from {old_value:.2f} to {command.value:.2f}"
            )
        else:
            logger.warning(f"Unknown setpoint key: {key}")

    def get_current_state(self) -> Dict[str, any]:
        """Get current simulation state."""
        return {
            "variables": self.current_state,
            "setpoints": self.setpoints,
            "controls": self.control_actions,
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "session_id": self.session_id,
        }

    async def pause(self):
        """Pause simulation."""
        self.is_paused = True
        logger.info("Simulation paused")

    async def resume(self):
        """Resume simulation."""
        self.is_paused = False
        self.last_update_time = time.time()
        self.last_control_time = time.time()
        logger.info("Simulation resumed")

    async def reset(self):
        """Reset to equilibrium point."""
        if self.modelo and self.controladores:
            # Reinicializar estado
            estado_inicial = np.array(
                [
                    PONTO_OPERACAO["hA_eq"],
                    PONTO_OPERACAO["hB_eq"],
                    PONTO_OPERACAO["h_eq"],
                    PONTO_OPERACAO["C_eq"],
                    PONTO_OPERACAO["h_eq"],
                    PONTO_OPERACAO["C_eq"],
                    PONTO_OPERACAO["h_eq"],
                    PONTO_OPERACAO["C_eq"],
                ]
            )

            self.modelo.definir_estado(estado_inicial)
            self._update_state_from_model()
            self.setpoints = self.current_state.copy()

            logger.info("Simulation reset to equilibrium")

    async def shutdown(self):
        """Shutdown service."""
        self.is_running = False
        logger.info("Real-time service shutdown")
