"""
P1 — Capa de servicios (lógica de negocio) de Usuarios y Seguridad.

Separa la lógica de negocio de los endpoints para mantener
los routes delgados y la lógica testeable.
"""

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.shared.config import settings
from app.shared.security import (
    create_access_token,
    generate_reset_token,
    get_password_hash,
    hash_reset_token,
    verify_password,
)
from app.shared.email import send_reset_email
from app.modules.p1_usuarios.models import (
    TokenRecuperacion,
    TokenRevocado,
    Usuario,
    Vehiculo,
)
from app.modules.p1_usuarios.schemas import (
    AdminUserCreate,
    ChangePasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    PermissionsUpdate,
    ResetPasswordRequest,
    RoleUpdate,
    TokenResponse,
    UserCreate,
    UserProfileUpdate,
    VehicleCreate,
    VehicleUpdate,
)


# ═══════════════════════════════════════════════════════════════════════
# AUTH SERVICE  (CU1, CU2, CU3, CU4)
# ═══════════════════════════════════════════════════════════════════════


class AuthService:
    """Servicio de autenticación y registro."""

    @staticmethod
    def register(db: Session, payload: UserCreate) -> Usuario:
        """CU3 — Registrar usuario (público, rol=cliente)."""
        if db.query(Usuario).filter(Usuario.email == payload.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo ya está registrado",
            )
        user = Usuario(
            nombre=payload.nombre,
            email=payload.email,
            hashed_password=get_password_hash(payload.password),
            rol=payload.rol,
            esta_activo=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def login(db: Session, payload: LoginRequest) -> TokenResponse:
        """CU1 — Inicio de sesión con JWT y Rate Limiting."""
        user = db.query(Usuario).filter(Usuario.email == payload.email).first()
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
            )

        if not user.esta_activo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cuenta desactivada permanentemente. Por favor, contacta a soporte@rutaigeoproxi.com",
            )

        if user.bloqueado_hasta and user.bloqueado_hasta > now:
            mins_left = int((user.bloqueado_hasta - now).total_seconds() / 60)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Demasiados intentos. Tu cuenta ha sido bloqueada temporalmente por {mins_left or 1} minutos por seguridad.",
            )

        if not verify_password(payload.password, user.hashed_password):
            user.intentos_fallidos += 1
            if user.intentos_fallidos == 3:
                user.bloqueado_hasta = now + timedelta(minutes=5)
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Demasiados intentos fallidos (3). Tu cuenta ha sido bloqueada temporalmente por 5 minutos por seguridad.",
                )
            elif user.intentos_fallidos == 4:
                user.bloqueado_hasta = now + timedelta(minutes=7)
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Demasiados intentos fallidos (4). Cuenta bloqueada temporalmente por 7 minutos.",
                )
            elif user.intentos_fallidos >= 5:
                user.esta_activo = False
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Límite máximo de intentos excedido (5). Tu cuenta ha sido bloqueada permanentemente. Por favor, contacta al administrador para desbloquearla.",
                )
            else:
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Contraseña incorrecta. Recuerda respetar las mayúsculas y minúsculas.",
                )

        # Exito: reset intentos
        user.intentos_fallidos = 0
        user.bloqueado_hasta = None
        db.commit()

        token, _jti, expire = create_access_token(user_id=user.id, role=user.rol)
        expires_in = max(0, int((expire - now).total_seconds()))
        return TokenResponse(access_token=token, expires_in=expires_in)

    @staticmethod
    def logout(db: Session, _token: str, payload: dict) -> None:
        """CU2 — Cierre de sesión (revoca JWT)."""
        jti = payload.get("jti")
        exp_ts = payload.get("exp")
        if not jti or exp_ts is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )
        if db.query(TokenRevocado).filter(TokenRevocado.jti == jti).first():
            return
        expires_at = datetime.fromtimestamp(int(exp_ts), tz=timezone.utc)
        db.add(
            TokenRevocado(
                jti=jti,
                expira_en=expires_at,
                revocado_en=datetime.now(timezone.utc),
            )
        )
        db.commit()

    @staticmethod
    def forgot_password(db: Session, email: str) -> ForgotPasswordResponse:
        """CU4a — Solicitar token de recuperación y enviar email vía Brevo."""
        msg = "Si el correo existe en el sistema, recibirás instrucciones para restablecer la contraseña."
        user = db.query(Usuario).filter(Usuario.email == email).first()
        if not user:
            return ForgotPasswordResponse(message=msg, debug_token=None)

        raw = generate_reset_token()
        th = hash_reset_token(raw)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        db.add(
            TokenRecuperacion(
                usuario_id=user.id,
                token_hash=th,
                expira_en=expires_at,
            )
        )
        db.commit()

        # Enviar email
        try:
            send_reset_email(to_email=user.email, token=raw)
        except Exception as e:  # pylint: disable=broad-except
            print("Error email: ", e)

        debug = raw if settings.DEBUG_RESET_TOKEN else None
        return ForgotPasswordResponse(message=msg, debug_token=debug)

    @staticmethod
    def reset_password(db: Session, payload: ResetPasswordRequest) -> None:
        """CU4b — Restablecer contraseña con token válido."""
        th = hash_reset_token(payload.token)
        now = datetime.now(timezone.utc)
        row = (
            db.query(TokenRecuperacion)
            .filter(
                TokenRecuperacion.token_hash == th,
                TokenRecuperacion.usado_en.is_(None),
                TokenRecuperacion.expira_en > now,
            )
            .first()
        )
        if not row:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido o expirado",
            )
        user = db.query(Usuario).filter(Usuario.id == row.usuario_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido",
            )
        user.hashed_password = get_password_hash(payload.new_password)
        row.usado_en = now
        db.commit()


# ═══════════════════════════════════════════════════════════════════════
# USER SERVICE  (CU5, CU6)
# ═══════════════════════════════════════════════════════════════════════


class UserService:
    """Servicio de gestión de usuarios (perfil y admin)."""

    @staticmethod
    def get_me(db: Session, user_id: int) -> Usuario:
        """CU6 — Obtener perfil con vehículos."""
        user = (
            db.query(Usuario)
            .options(joinedload(Usuario.vehiculos))
            .filter(Usuario.id == user_id)
            .first()
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )
        return user

    @staticmethod
    def update_profile(
        db: Session, user_id: int, payload: UserProfileUpdate
    ) -> Usuario:
        """CU6 — Actualizar nombre/teléfono del perfil."""
        user = (
            db.query(Usuario)
            .options(joinedload(Usuario.vehiculos))
            .filter(Usuario.id == user_id)
            .first()
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )
        data = payload.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(user, k, v)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def list_all(db: Session) -> list[Usuario]:
        """CU5 — Listar todos los usuarios (admin)."""
        return db.query(Usuario).order_by(Usuario.id).all()

    @staticmethod
    def admin_create(db: Session, payload: AdminUserCreate) -> Usuario:
        """CU5 — Crear usuario con rol específico (admin)."""
        if db.query(Usuario).filter(Usuario.email == payload.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo ya está registrado",
            )
        user = Usuario(
            nombre=payload.nombre,
            email=payload.email,
            hashed_password=get_password_hash(payload.password),
            rol=payload.rol,
            esta_activo=True,
            permisos=payload.permisos,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_role(
        db: Session, user_id: int, payload: RoleUpdate, admin_id: int
    ) -> Usuario:
        """CU5 — Cambiar rol de un usuario (admin)."""
        user = db.query(Usuario).filter(Usuario.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )
        if user.id == admin_id and payload.rol != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes quitarte el rol de administrador a ti mismo",
            )
        user.rol = payload.rol
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_permissions(
        db: Session, user_id: int, payload: PermissionsUpdate
    ) -> Usuario:
        """CU5 — Actualizar permisos de un usuario (admin)."""
        user = db.query(Usuario).filter(Usuario.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )
        user.permisos = payload.permisos
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def change_password(
        db: Session, user_id: int, payload: ChangePasswordRequest
    ) -> dict:
        """Cambio de contraseña interno desde el perfil."""
        user = db.query(Usuario).filter(Usuario.id == user_id).first()
        if not user or not verify_password(
            payload.current_password, user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña actual es incorrecta",
            )

        user.hashed_password = get_password_hash(payload.new_password)
        db.commit()
        return {"message": "Contraseña actualizada exitosamente"}


# ═══════════════════════════════════════════════════════════════════════
# VEHICLE SERVICE  (CU6)
# ═══════════════════════════════════════════════════════════════════════


class VehicleService:
    """Servicio de gestión de vehículos del cliente."""

    @staticmethod
    def list_by_user(db: Session, user_id: int) -> list[Vehiculo]:
        return (
            db.query(Vehiculo)
            .filter(Vehiculo.usuario_id == user_id)
            .order_by(Vehiculo.id)
            .all()
        )

    @staticmethod
    def create(db: Session, user_id: int, payload: VehicleCreate) -> Vehiculo:
        v = Vehiculo(
            usuario_id=user_id,
            marca=payload.marca,
            modelo=payload.modelo,
            placa=payload.placa.strip().upper(),
            anio=payload.anio,
            color=payload.color,
        )
        db.add(v)
        db.commit()
        db.refresh(v)
        return v

    @staticmethod
    def update(
        db: Session, vehicle_id: int, user_id: int, payload: VehicleUpdate
    ) -> Vehiculo:
        v = (
            db.query(Vehiculo)
            .filter(Vehiculo.id == vehicle_id, Vehiculo.usuario_id == user_id)
            .first()
        )
        if not v:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehículo no encontrado",
            )
        data = payload.model_dump(exclude_unset=True)
        if "placa" in data and data["placa"] is not None:
            data["placa"] = data["placa"].strip().upper()
        for k, val in data.items():
            setattr(v, k, val)
        db.commit()
        db.refresh(v)
        return v

    @staticmethod
    def delete(db: Session, vehicle_id: int, user_id: int) -> None:
        v = (
            db.query(Vehiculo)
            .filter(Vehiculo.id == vehicle_id, Vehiculo.usuario_id == user_id)
            .first()
        )
        if not v:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehículo no encontrado",
            )
        db.delete(v)
        db.commit()
