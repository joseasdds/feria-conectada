import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


# Tarea 40: Envío de email de confirmación
# Usamos @shared_task para evitar la importación explícita de core.celery,
# lo que rompe la dependencia circular.
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_confirmation_email(self, order_id):
    """
    Envía un email de confirmación y detalle del pedido al cliente.
    """
    # Importaciones locales dentro de la tarea para evitar problemas de carga inicial
    from orders.models import Order

    try:
        # Aseguramos que la orden exista y esté completa
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        logger.error(f"Order ID {order_id} not found. Retrying...")
        # Reintenta si la DB aún no ha commitido
        raise self.retry()

    subject = f"Confirmación de Pedido #{order.id} - Feria Conectada"
    message = (
        f"Hola {order.cliente.get_full_name()},\n\n"
        f"Tu pedido (ID: {order.id}) ha sido creado exitosamente.\n"
        f"El monto total es: ${order.total}\n"
        f"El estado actual es: {order.get_estado_display()}\n\n"
        f"Te enviaremos más notificaciones cuando el feriante lo confirme y esté en camino."
    )
    recipient_list = [order.cliente.email]

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=False,
        )
        logger.info(f"Confirmation email queued for Order {order_id}")
    except Exception as exc:
        logger.error(f"Failed to send email for Order {order_id}: {exc}")
        raise self.retry(exc=exc, countdown=300)
