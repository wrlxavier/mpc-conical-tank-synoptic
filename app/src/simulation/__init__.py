"""
Núcleo de simulação física e controle MPC.

Módulos importados do repositório mpc-conical-tank-simulation.
"""

from .parametros_sistema import (
    # Constantes físicas
    TANQUES_PROCESSO,
    TANQUES_UTILIDADES,
    PONTO_OPERACAO,
    # Parâmetros MPC
    MPC_HORIZONTES,
    MPC_PESOS,
    LIMITES_NIVEL,
    LIMITES_CONCENTRACAO,
    LIMITES_ATUADORES,
    LIMITES_VARIACAO,
    # Modelo linearizado
    A_CONTINUA,
    B_CONTINUA,
    C_CONTINUA,
    D_CONTINUA,
    # Configuração
    TS_CONTROLADOR,
    DT_INTEGRACAO,
)

from .modelo_tanques import (
    TanqueCilindrico,
    TanqueTroncoConico,
    SistemaCompleto,
)

from .controlador_mpc import (
    ControladorMPC,
    ControladorPID,
    SistemaControle,
)

# Compatibilidade com a API anterior (ModeloSistemaTanques -> SistemaCompleto)
ModeloSistemaTanques = SistemaCompleto

__all__ = [
    # Parâmetros
    "TANQUES_PROCESSO",
    "TANQUES_UTILIDADES",
    "PONTO_OPERACAO",
    "MPC_HORIZONTES",
    "MPC_PESOS",
    "TS_CONTROLADOR",
    "DT_INTEGRACAO",
    # Modelos
    "TanqueCilindrico",
    "TanqueTroncoConico",
    "SistemaCompleto",
    "ModeloSistemaTanques",
    # Controle
    "ControladorMPC",
    "ControladorPID",
    "SistemaControle",
]
