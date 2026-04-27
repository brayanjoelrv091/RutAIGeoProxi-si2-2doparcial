"""
P1 — Schemas Pydantic para Usuarios y Seguridad.

Agrupa auth, user, vehicle en un solo archivo por módulo.
"""

from typing import Any
import re

from pydantic import BaseModel, EmailStr, Field, field_validator

# ── Roles válidos del sistema ──────────────────────────────────────────
ROLES_VALIDOS = frozenset({"admin", "taller", "cliente"})

def check_password_complexity(v: str) -> str:
    if len(v) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    if not any(c.isupper() for c in v):
        raise ValueError("La contraseña debe contener al menos una mayúscula")
    if not any(c.islower() for c in v):
        raise ValueError("La contraseña debe contener al menos una minúscula")
    if not any(c.isdigit() for c in v):
        raise ValueError("La contraseña debe contener al menos un número")
    return v


# ═══════════════════════════════════════════════════════════════════════
# AUTH  (CU1, CU2, CU4)
# ═══════════════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=10)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validar_pass(cls, v: str) -> str:
        return check_password_complexity(v)

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validar_pass(cls, v: str) -> str:
        return check_password_complexity(v)


class ForgotPasswordResponse(BaseModel):
    message: str
    debug_token: str | None = None


# ═══════════════════════════════════════════════════════════════════════
# VEHÍCULOS  (CU6)
# ═══════════════════════════════════════════════════════════════════════

class VehicleCreate(BaseModel):
    marca: str = Field(min_length=1, max_length=100)
    modelo: str = Field(min_length=1, max_length=100)
    placa: str = Field(min_length=1, max_length=20)
    anio: int | None = Field(default=None, ge=1900, le=2100)
    color: str | None = Field(default=None, max_length=50)


class VehicleUpdate(BaseModel):
    marca: str | None = Field(default=None, min_length=1, max_length=100)
    modelo: str | None = Field(default=None, min_length=1, max_length=100)
    placa: str | None = Field(default=None, min_length=1, max_length=20)
    anio: int | None = Field(default=None, ge=1900, le=2100)
    color: str | None = Field(default=None, max_length=50)


class VehicleOut(BaseModel):
    id: int
    usuario_id: int
    marca: str
    modelo: str
    placa: str
    anio: int | None
    color: str | None

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════
# USUARIOS  (CU3, CU5, CU6)
# ═══════════════════════════════════════════════════════════════════════

class UserCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    rol: str = Field(default="cliente")

    @field_validator("password")
    @classmethod
    def validar_pass(cls, v: str) -> str:
        return check_password_complexity(v)

    @field_validator("rol")
    @classmethod
    def rol_valido(cls, v: str) -> str:
        # Solo permitimos registrarse como cliente o taller públicamente
        if v not in {"cliente", "taller"}:
            raise ValueError("Solo se permite registro para roles 'cliente' o 'taller'")
        return v


class UserOut(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    telefono: str | None
    esta_activo: bool
    rol: str
    permisos: dict[str, Any] | None

    model_config = {"from_attributes": True}


class MeResponse(UserOut):
    vehiculos: list[VehicleOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=200)
    telefono: str | None = Field(default=None, max_length=50)


class AdminUserCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    rol: str
    permisos: dict[str, Any] | None = None

    @field_validator("password")
    @classmethod
    def validar_pass(cls, v: str) -> str:
        return check_password_complexity(v)

    @field_validator("rol")
    @classmethod
    def rol_valido(cls, v: str) -> str:
        if v not in ROLES_VALIDOS:
            raise ValueError(f"Rol inválido. Válidos: {', '.join(sorted(ROLES_VALIDOS))}")
        return v


class RoleUpdate(BaseModel):
    rol: str

    @field_validator("rol")
    @classmethod
    def rol_valido(cls, v: str) -> str:
        if v not in ROLES_VALIDOS:
            raise ValueError(f"Rol inválido. Válidos: {', '.join(sorted(ROLES_VALIDOS))}")
        return v


class PermissionsUpdate(BaseModel):
    permisos: dict[str, Any]


class FCMTokenUpdate(BaseModel):
    fcm_token: str = Field(min_length=1)
