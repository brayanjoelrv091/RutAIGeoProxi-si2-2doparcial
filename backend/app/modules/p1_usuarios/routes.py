"""
P1 — Rutas (endpoints) de Usuarios y Seguridad.

Consolida los 3 routers anteriores (auth, admin, profile) en un
módulo cohesivo con tags separados para Swagger.

Prefijos:
    /auth/*   → CU1, CU2, CU3, CU4
    /admin/*  → CU5
    /me/*     → CU6
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.shared.deps import (
    get_current_user,
    get_db,
    get_token_credentials,
    require_roles,
)
from app.shared.security import jwt_payload_safe
from app.modules.p1_usuarios.models import Usuario
from app.modules.p1_usuarios.schemas import (
    AdminUserCreate,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    MeResponse,
    PermissionsUpdate,
    ResetPasswordRequest,
    RoleUpdate,
    TokenResponse,
    UserCreate,
    UserOut,
    UserProfileUpdate,
    VehicleCreate,
    VehicleOut,
    VehicleUpdate,
    FCMTokenUpdate,
)
from app.modules.p1_usuarios.services import AuthService, UserService, VehicleService
from app.modules.p6_auditoria.services import AuditService

# ── Routers ────────────────────────────────────────────────────────────
auth_router = APIRouter(prefix="/auth", tags=["P1 · Autenticación"])
admin_router = APIRouter(prefix="/admin", tags=["P1 · Administración"])
profile_router = APIRouter(prefix="/me", tags=["P1 · Perfil y Vehículos"])

admin_dep = require_roles("admin")


# ═══════════════════════════════════════════════════════════════════════
# AUTH  (CU1 · Login, CU2 · Logout, CU3 · Registro, CU4 · Recuperar)
# ═══════════════════════════════════════════════════════════════════════

@auth_router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="CU3 · Registrar usuario",
)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    return AuthService.register(db, payload)


@auth_router.post(
    "/login",
    response_model=TokenResponse,
    summary="CU1 · Iniciar sesión",
)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    token_resp = AuthService.login(db, payload)
    AuditService.log(db, accion=f"Inicio de sesión exitoso ({payload.email})", request=request)
    return token_resp


@auth_router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="CU2 · Cerrar sesión",
)
def logout(
    db: Session = Depends(get_db),
    token: str = Depends(get_token_credentials),
):
    payload = jwt_payload_safe(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )
    AuthService.logout(db, token, payload)


@auth_router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    summary="CU4 · Solicitar recuperación de contraseña",
)
def forgot_password(
    payload: ForgotPasswordRequest, db: Session = Depends(get_db)
):
    return AuthService.forgot_password(db, payload.email)


@auth_router.post(
    "/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="CU4 · Restablecer contraseña con token",
)
def reset_password(
    payload: ResetPasswordRequest, db: Session = Depends(get_db)
):
    AuthService.reset_password(db, payload)


# ═══════════════════════════════════════════════════════════════════════
# ADMIN  (CU5 · Roles y permisos)
# ═══════════════════════════════════════════════════════════════════════

@admin_router.post(
    "/users",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="CU5 · Crear usuario (admin)",
)
def admin_create_user(
    payload: AdminUserCreate,
    db: Session = Depends(get_db),
    _current: Usuario = Depends(admin_dep),
):
    return UserService.admin_create(db, payload)


@admin_router.get(
    "/users",
    response_model=list[UserOut],
    summary="CU5 · Listar usuarios (admin)",
)
def admin_list_users(
    db: Session = Depends(get_db),
    _current: Usuario = Depends(admin_dep),
):
    return UserService.list_all(db)


@admin_router.patch(
    "/users/{user_id}/role",
    response_model=UserOut,
    summary="CU5 · Cambiar rol de usuario",
)
def admin_update_role(
    user_id: int,
    payload: RoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current: Usuario = Depends(admin_dep),
):
    user = UserService.update_role(db, user_id, payload, current.id)
    AuditService.log(
        db,
        accion=f"Cambió rol de usuario {user_id} a {payload.rol}",
        request=request,
        usuario_id=current.id,
        rol=current.rol,
    )
    return user


@admin_router.patch(
    "/users/{user_id}/permissions",
    response_model=UserOut,
    summary="CU5 · Actualizar permisos",
)
def admin_update_permissions(
    user_id: int,
    payload: PermissionsUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current: Usuario = Depends(admin_dep),
):
    user = UserService.update_permissions(db, user_id, payload)
    AuditService.log(
        db,
        accion=f"Actualizó permisos del usuario {user_id}",
        request=request,
        usuario_id=current.id,
        rol=current.rol,
    )
    return user


# ═══════════════════════════════════════════════════════════════════════
# PERFIL  (CU6 · Datos de usuario y vehículo)
# ═══════════════════════════════════════════════════════════════════════

@profile_router.get(
    "",
    response_model=MeResponse,
    summary="CU6 · Ver mi perfil",
)
def get_me(
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
):
    return UserService.get_me(db, current.id)


@profile_router.patch(
    "",
    response_model=MeResponse,
    summary="CU6 · Actualizar mi perfil",
)
def update_me(
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
):
    return UserService.update_profile(db, current.id, payload)


@profile_router.patch(
    "/fcm-token",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Actualizar token de notificaciones FCM",
)
def update_fcm_token(
    payload: FCMTokenUpdate,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
):
    """Guarda el token del dispositivo para enviar notificaciones Push."""
    current.fcm_token = payload.fcm_token
    db.commit()
    return None

@profile_router.patch(
    "/password",
    summary="Cambiar contraseña internamente",
)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
):
    res = UserService.change_password(db, current.id, payload)
    AuditService.log(db, usuario_id=current.id, rol=current.rol, accion="Cambio de contraseña interno", request=request)
    return res


@profile_router.get(
    "/vehicles",
    response_model=list[VehicleOut],
    summary="CU6 · Listar mis vehículos",
)
def list_vehicles(
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
):
    return VehicleService.list_by_user(db, current.id)


@profile_router.post(
    "/vehicles",
    response_model=VehicleOut,
    status_code=status.HTTP_201_CREATED,
    summary="CU6 · Registrar vehículo",
)
def create_vehicle(
    payload: VehicleCreate,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
):
    if current.rol != "cliente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo clientes pueden registrar vehículos",
        )
    return VehicleService.create(db, current.id, payload)


@profile_router.patch(
    "/vehicles/{vehicle_id}",
    response_model=VehicleOut,
    summary="CU6 · Actualizar vehículo",
)
def update_vehicle(
    vehicle_id: int,
    payload: VehicleUpdate,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
):
    return VehicleService.update(db, vehicle_id, current.id, payload)


@profile_router.delete(
    "/vehicles/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="CU6 · Eliminar vehículo",
)
def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
):
    VehicleService.delete(db, vehicle_id, current.id)

@auth_router.post("/seed-demo", status_code=status.HTTP_201_CREATED)
def seed_demo_users_quick(
    db: Session = Depends(get_db),
    current: Usuario = Depends(admin_dep),
):
    """Inyectar 3 usuarios fijos (Admin, Taller, Cliente) creados desde el backend (solo admin)"""
    import secrets
    from app.shared.security import get_password_hash
    password = secrets.token_urlsafe(8)
    hashed_pw = get_password_hash(password)
    creados = 0
    usuarios_demo = [
        {"nombre": "Super Admin UI", "email": "admin@ruta.com", "rol": "admin"},
        {"nombre": "Taller Mecanico Centro", "email": "taller@ruta.com", "rol": "taller"},
        {"nombre": "Cliente VIP", "email": "cliente@ruta.com", "rol": "cliente"}
    ]
    for u in usuarios_demo:
        if not db.query(Usuario).filter(Usuario.email == u["email"]).first():
            db.add(Usuario(
                nombre=u["nombre"], email=u["email"], 
                hashed_password=hashed_pw, rol=u["rol"],
                esta_activo=True, intentos_fallidos=0
            ))
            creados += 1
    db.commit()
    return {"message": f"Se inyectaron {creados} usuarios demo."}
