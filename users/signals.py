# users/signals.py

import logging
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from .models_profiles import FerianteProfile, ClienteProfile, RepartidorProfile 

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_profile_for_user(sender, instance, created, **kwargs):
    """
    Crea automáticamente el perfil correspondiente según el rol del usuario.
    Usa get_or_create para garantizar idempotencia.
    """
    # Solo ejecutar al crear un usuario nuevo
    if not created:
        return

    # Validar que el usuario tenga un rol asignado
    if not instance.role:
        logger.warning(f"⚠️ Usuario {instance.email} creado sin rol asignado. No se creó perfil.")
        return

    role_name = instance.role.name.strip().upper()

    try:
        with transaction.atomic():
            
            # --- FERIANTE ---
            if role_name == "FERIANTE":
                FerianteProfile.objects.get_or_create(
                    user=instance,
                    defaults={
                        "rut": "",
                        "direccion": "",  # ← CORREGIDO: usa "direccion" no "direccion_base"
                        "puesto": ""
                    }
                )
                logger.info(f"✅ FerianteProfile creado para usuario {instance.email}")

            # --- CLIENTE ---
            elif role_name == "CLIENTE":
                ClienteProfile.objects.get_or_create(
                    user=instance,
                    defaults={
                        "direccion_entrega": ""  # ← CORREGIDO: usa "direccion_entrega"
                    }
                )
                logger.info(f"✅ ClienteProfile creado para usuario {instance.email}")

            # --- REPARTIDOR ---
            elif role_name == "REPARTIDOR":
                RepartidorProfile.objects.get_or_create(
                    user=instance,
                    defaults={
                        "vehiculo": "",      # ← CORREGIDO: usa "vehiculo"
                        "licencia": "",      # ← CORREGIDO: usa "licencia"
                        "zona_cobertura": ""
                    }
                )
                logger.info(f"✅ RepartidorProfile creado para usuario {instance.email}")

            # --- ADMINISTRADOR ---
            elif role_name == "ADMIN" or role_name == "ADMINISTRADOR":
                logger.info(f"👑 Usuario Administrador {instance.email} creado sin perfil específico.")

            # --- ROL DESCONOCIDO ---
            else:
                logger.warning(f"⚠️ Rol '{role_name}' no reconocido para usuario {instance.email}")

    except Exception as e:
        logger.error(f"❌ Error al crear perfil para {instance.email} (Rol: {role_name}): {str(e)}")