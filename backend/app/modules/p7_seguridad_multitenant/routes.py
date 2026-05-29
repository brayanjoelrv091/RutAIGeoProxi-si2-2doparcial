"""
P7 — Rutas de Seguridad y Multi-Tenant (Ciclo 5 — Placeholder).

Endpoints futuros:
    POST   /tenants              → Crear tenant
    GET    /tenants              → Listar tenants (superadmin)
    PATCH  /tenants/{id}         → Actualizar tenant
    POST   /tenants/{id}/members → Agregar miembro
"""

from fastapi import APIRouter

router = APIRouter(
    prefix="/tenants",
    tags=["P7 · Seguridad y Multi-Tenant (Ciclo 5)"],
)


@router.get("/health", summary="Health check del módulo P7")
def health():
    """Verifica que el módulo P7 está registrado correctamente."""
    return {
        "modulo": "P7_Seguridad_Multitenant",
        "estado": "placeholder",
        "ciclo": 5,
        "mensaje": "Módulo registrado — implementación pendiente Ciclo 5.",
    }
