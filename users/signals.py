# users/signals.py
import logging
import random
import uuid

from django.db import IntegrityError, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User
from .models_profiles import ClienteProfile, FerianteProfile, RepartidorProfile

logger = logging.getLogger(__name__)

# Intentar importar utilidades para RUT (si ya creaste users/utils.py)
try:
    from .utils import generate_random_rut, normalize_rut, validate_rut
except Exception:
    # Fallback simple si no existe users/utils.py: genera RUTs básicos (8 dígitos + DV)
    def calculate_dv(rut_number: int) -> str:
        total = 0
        factor = 2
        for d in reversed(str(rut_number)):
            total += int(d) * factor
            factor += 1
            if factor > 7:
                factor = 2
        remainder = 11 - (total % 11)
        if remainder == 11:
            return "0"
        if remainder == 10:
            return "K"
        return str(remainder)

    def generate_random_rut(base_digits: int = 8, with_hyphen: bool = False) -> str:
        if base_digits not in (7, 8):
            raise ValueError("base_digits debe ser 7 u 8")
        start = 10 ** (base_digits - 1)
        end = 10**base_digits - 1
        num = random.randint(start, end)
        dv = calculate_dv(num)
        return f"{num}{dv}" if not with_hyphen else f"{num}-{dv}"

    def normalize_rut(rut: str) -> str:
        if not rut:
            return ""
        import re

        cleaned = re.sub(r"[^0-9Kk]", "", rut)
        return cleaned.upper()

    def validate_rut(rut: str) -> bool:
        if not rut:
            return False
        cleaned = normalize_rut(rut)
        if len(cleaned) < 2:
            return False
        number, dv = cleaned[:-1], cleaned[-1]
        if not number.isdigit():
            return False
        return calculate_dv(int(number)) == dv.upper()


def _unique_rut_candidate(max_attempts: int = 10) -> str:
    """
    Genera candidatos de RUT y verifica que no existan en FerianteProfile.
    Devuelve el candidate (string) o un fallback corto si no encuentra.
    Usa formato sin guion: '123456785' (8 dígitos + DV).
    """
    for _ in range(max_attempts):
        candidate = generate_random_rut(base_digits=8, with_hyphen=False)
        if not FerianteProfile.objects.filter(rut=candidate).exists():
            return candidate
    # fallback: prefijo corto + uuid hex slice (asegura longitud razonable <=12)
    return f"F{uuid.uuid4().hex[:7].upper()}"


@receiver(post_save, sender=User)
def create_profile_for_user(sender, instance, created, **kwargs):
    """
    Crea automáticamente el perfil correspondiente según el rol del usuario.
    - Si el usuario trae rut válido: lo usa (normalizado).
    - Si no, genera un rut válido y único (o fallback).
    - Usa update_or_create para idempotencia.
    """
    if not created:
        return

    if not instance.role:
        logger.warning(
            f"⚠️ Usuario {instance.email} creado sin rol asignado. No se creó perfil."
        )
        return

    role_name = getattr(instance.role, "name", "").strip().upper()

    try:
        with transaction.atomic():
            # --- FERIANTE ---
            if role_name == "FERIANTE":
                # Intentar usar rut provisto por el usuario, si existe y es válido
                provided_rut = getattr(instance, "rut", None)
                if provided_rut:
                    provided_rut = normalize_rut(provided_rut)
                    if not validate_rut(provided_rut):
                        logger.warning(
                            f"⚠️ RUT provisto no válido para {instance.email}: {provided_rut}. Se generará uno nuevo."
                        )
                        provided_rut = None

                # Si no hay uno válido, generar candidato único
                if not provided_rut:
                    provided_rut = _unique_rut_candidate()

                # Asegurarnos que la longitud quepa en CharField(max_length) (tu modelo usa 12)
                if len(provided_rut) > 12:
                    provided_rut = provided_rut[:12]

                created_profile = False
                attempts = 0
                # Intentar crear/actualizar con reintentos en caso de race condition / IntegrityError
                while attempts < 5:
                    try:
                        FerianteProfile.objects.update_or_create(
                            user=instance,
                            defaults={
                                "rut": provided_rut,
                                "direccion": getattr(instance, "direccion", "") or "",
                                "puesto": getattr(instance, "puesto", "") or "",
                            },
                        )
                        created_profile = True
                        break
                    except IntegrityError as e:
                        # Si hubo conflicto (otro proceso creó el mismo rut), generar otro candidate y reintentar
                        logger.warning(
                            f"IntegrityError al crear FerianteProfile para {instance.email}: {e}. Reintentando con nuevo RUT..."
                        )
                        provided_rut = _unique_rut_candidate()
                        if len(provided_rut) > 12:
                            provided_rut = provided_rut[:12]
                        attempts += 1

                if not created_profile:
                    # último recurso: usar uuid corto como rut único
                    fallback = f"F{uuid.uuid4().hex[:8].upper()}"
                    FerianteProfile.objects.update_or_create(
                        user=instance,
                        defaults={
                            "rut": fallback,
                            "direccion": getattr(instance, "direccion", "") or "",
                            "puesto": getattr(instance, "puesto", "") or "",
                        },
                    )
                    logger.error(
                        f"⚠️ Se usó RUT fallback para {instance.email}: {fallback}"
                    )
                else:
                    logger.info(
                        f"✅ FerianteProfile creado/actualizado para usuario {instance.email} (RUT: {provided_rut})"
                    )

            # --- CLIENTE ---
            elif role_name == "CLIENTE":
                ClienteProfile.objects.update_or_create(
                    user=instance,
                    defaults={
                        "direccion_entrega": getattr(instance, "direccion_entrega", "")
                        or ""
                    },
                )
                logger.info(
                    f"✅ ClienteProfile creado/actualizado para usuario {instance.email}"
                )

            # --- REPARTIDOR ---
            elif role_name == "REPARTIDOR":
                RepartidorProfile.objects.update_or_create(
                    user=instance,
                    defaults={
                        "vehiculo": getattr(instance, "vehiculo", "") or "",
                        "licencia": getattr(instance, "licencia", "") or "",
                        "zona_cobertura": getattr(instance, "zona_cobertura", "") or "",
                    },
                )
                logger.info(
                    f"✅ RepartidorProfile creado/actualizado para usuario {instance.email}"
                )

            # --- ADMIN / ADMINISTRADOR (no profile) ---
            elif role_name in ["ADMIN", "ADMINISTRADOR"]:
                logger.info(
                    f"👑 Usuario Administrador {instance.email} creado sin perfil específico."
                )

            else:
                logger.warning(
                    f"⚠️ Rol '{role_name}' no reconocido para usuario {instance.email}"
                )

    except Exception as e:
        logger.exception(
            f"❌ Error creando perfil para {instance.email} (Rol: {role_name}): {e}"
        )
