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
    Crea automáticamente el perfil correspondiente según el rol del usuario al crearse.

    Roles soportados:
    - Feriante → FerianteProfile
    - Cliente → ClienteProfile
    - Repartidor → RepartidorProfile
    - Administrador → sin perfil

    Args:
        sender: Modelo que envía la señal (User)
        instance: Instancia del usuario creado
        created: Boolean que indica si es una creación nueva
        **kwargs: Argumentos adicionales de la señal
    """

    # Solo ejecutar al crear un usuario nuevo
    if not created:
        return

    # Validar que el usuario tenga un rol asignado
    if not instance.role:
        logger.warning(f"⚠️ Usuario {instance.email} creado sin rol asignado. No se creó perfil.")
        return

    role_name = instance.role.name.strip().lower()

    try:
        with transaction.atomic():
            # FERIANE
            if role_name == "feriante":
                if not hasattr(instance, "ferianteprofile"):
                    FerianteProfile.objects.create(
                        user=instance,
                        rut="",  # Se completará después
                        direccion=""
                    )
                    logger.info(f"✅ FerianteProfile creado para usuario {instance.email}")
                else:
                    logger.warning(f"FerianteProfile ya existe para {instance.email}")

            # CLIENTE
            elif role_name == "cliente":
                if not hasattr(instance, "clienteprofile"):
                    ClienteProfile.objects.create(
                        user=instance,
                        direccion_entrega=""
                    )
                    logger.info(f"✅ ClienteProfile creado para usuario {instance.email}")
                else:
                    logger.warning(f"ClienteProfile ya existe para {instance.email}")

            # REPARTIDOR
            elif role_name == "repartidor":
                if not hasattr(instance, "repartidorprofile"):
                    RepartidorProfile.objects.create(
                        user=instance,
                        vehiculo="",
                        licencia="",
                        zona_cobertura=""
                    )
                    logger.info(f"✅ RepartidorProfile creado para usuario {instance.email}")
                else:
                    logger.warning(f"RepartidorProfile ya existe para {instance.email}")

            # ADMINISTRADOR
            elif role_name == "administrador":
                logger.info(f"👑 Usuario Administrador {instance.email} creado sin perfil específico")

            # ROL DESCONOCIDO
            else:
                logger.warning(f"⚠️ Rol '{role_name}' no reconocido para usuario {instance.email}")

    except Exception as e:
        logger.error(f"❌ Error al crear perfil para {instance.email}: {str(e)}")
        # No se relanza la excepción para no interrumpir la creación del usuario
