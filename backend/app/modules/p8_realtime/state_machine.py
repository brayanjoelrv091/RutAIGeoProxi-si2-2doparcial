"""
P8 — Máquina de Estados del Incidente (CU-25).

Define las transiciones válidas entre estados de un incidente vehicular.
Garantiza integridad del flujo de negocio y trazabilidad completa.

Estados:
    pendiente        → Estado inicial al crear el incidente
    buscando_taller  → La IA clasificó y se busca taller cercano
    taller_asignado  → Un taller aceptó la solicitud
    en_camino        → El técnico va en camino al cliente
    en_atencion      → El técnico está atendiendo la emergencia
    finalizado       → Servicio completado exitosamente
    cancelado        → Incidente cancelado (por cliente o sistema)

Diagrama:
    pendiente → buscando_taller → taller_asignado → en_camino → en_atencion → finalizado
                                                                               ↗
    (cualquier estado antes de finalizado) → cancelado
"""

from enum import Enum
from typing import Optional


class EstadoIncidente(str, Enum):
    """Estados posibles de un incidente vehicular."""

    PENDIENTE = "pendiente"
    BUSCANDO_TALLER = "buscando_taller"
    TALLER_ASIGNADO = "taller_asignado"
    EN_CAMINO = "en_camino"
    EN_ATENCION = "en_atencion"
    FINALIZADO = "finalizado"
    CANCELADO = "cancelado"


# ── Grafo de transiciones válidas ──────────────────────────────────────
# Clave: estado actual → Valor: set de estados destino permitidos
_TRANSITIONS: dict[EstadoIncidente, set[EstadoIncidente]] = {
    EstadoIncidente.PENDIENTE: {
        EstadoIncidente.BUSCANDO_TALLER,
        EstadoIncidente.CANCELADO,
    },
    EstadoIncidente.BUSCANDO_TALLER: {
        EstadoIncidente.TALLER_ASIGNADO,
        EstadoIncidente.CANCELADO,
    },
    EstadoIncidente.TALLER_ASIGNADO: {
        EstadoIncidente.EN_CAMINO,
        EstadoIncidente.BUSCANDO_TALLER,  # Si el taller rechaza → buscar otro
        EstadoIncidente.CANCELADO,
    },
    EstadoIncidente.EN_CAMINO: {
        EstadoIncidente.EN_ATENCION,
        EstadoIncidente.CANCELADO,
    },
    EstadoIncidente.EN_ATENCION: {
        EstadoIncidente.FINALIZADO,
        EstadoIncidente.CANCELADO,
    },
    # Estados terminales — no tienen transiciones de salida
    EstadoIncidente.FINALIZADO: set(),
    EstadoIncidente.CANCELADO: set(),
}


class IncidentStateMachine:
    """
    Máquina de estados finitos para el ciclo de vida de incidentes.

    Uso:
        machine = IncidentStateMachine()
        if machine.can_transition("pendiente", "buscando_taller"):
            machine.validate_transition("pendiente", "buscando_taller")
    """

    @staticmethod
    def _to_enum(state: str) -> EstadoIncidente:
        """Convierte string a enum, lanzando ValueError si es inválido."""
        try:
            return EstadoIncidente(state)
        except ValueError:
            valid = [e.value for e in EstadoIncidente]
            raise ValueError(
                f"Estado '{state}' no es válido. "
                f"Estados permitidos: {valid}"
            )

    @classmethod
    def can_transition(cls, current_state: str, target_state: str) -> bool:
        """
        Verifica si la transición es válida sin lanzar excepciones.

        Args:
            current_state: Estado actual del incidente.
            target_state: Estado destino deseado.

        Returns:
            True si la transición es válida, False en caso contrario.
        """
        try:
            current = cls._to_enum(current_state)
            target = cls._to_enum(target_state)
        except ValueError:
            return False

        return target in _TRANSITIONS.get(current, set())

    @classmethod
    def validate_transition(
        cls, current_state: str, target_state: str
    ) -> EstadoIncidente:
        """
        Valida la transición y retorna el estado destino como enum.

        Raises:
            ValueError: Si el estado no existe.
            PermissionError: Si la transición no es permitida.
        """
        current = cls._to_enum(current_state)
        target = cls._to_enum(target_state)

        allowed = _TRANSITIONS.get(current, set())
        if target not in allowed:
            allowed_str = [s.value for s in allowed] if allowed else ["ninguno (estado terminal)"]
            raise PermissionError(
                f"Transición no permitida: '{current.value}' → '{target.value}'. "
                f"Transiciones válidas desde '{current.value}': {allowed_str}"
            )

        return target

    @classmethod
    def get_allowed_transitions(cls, current_state: str) -> list[str]:
        """Retorna la lista de estados a los que se puede transicionar."""
        current = cls._to_enum(current_state)
        return [s.value for s in _TRANSITIONS.get(current, set())]

    @classmethod
    def is_terminal(cls, state: str) -> bool:
        """Verifica si un estado es terminal (sin transiciones de salida)."""
        enum_state = cls._to_enum(state)
        return len(_TRANSITIONS.get(enum_state, set())) == 0

    @classmethod
    def get_label(cls, state: str) -> str:
        """Retorna etiqueta legible para un estado."""
        labels = {
            "pendiente": "⏳ Pendiente",
            "buscando_taller": "🔍 Buscando Taller",
            "taller_asignado": "🏪 Taller Asignado",
            "en_camino": "🚗 En Camino",
            "en_atencion": "🔧 En Atención",
            "finalizado": "✅ Finalizado",
            "cancelado": "❌ Cancelado",
        }
        return labels.get(state, state)
