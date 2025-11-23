# orders/views_webhooks.py
import hashlib
import hmac
import json
import logging
from decimal import Decimal

from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


def map_provider_status_to_payment_status(provider_status: str) -> str:
    s = (provider_status or "").lower()
    if s in ("approved", "paid", "success"):
        return "SUCCESS"
    if s in ("pending", "in_process"):
        return "PENDING"
    return "FAILED"


@csrf_exempt
def payment_webhook(request):
    """
    Endpoint para recibir webhooks de proveedores de pago.
    Espera JSON en body.
    Firma HMAC esperada en header X-Signature si WEBHOOK_SECRET está definido.
    """
    if request.method != "POST":
        return HttpResponse(status=405)

    raw_body = request.body  # bytes

    # 1. Parsing del JSON y manejo de errores
    try:
        payload = json.loads(raw_body.decode("utf-8") or "{}")
    except Exception as exc:
        logger.exception("Invalid JSON payload")
        return HttpResponse(status=400)

    # 2. HMAC signature verification (si secret configurado)
    secret = getattr(settings, "WEBHOOK_SECRET", None)
    if secret:
        received_sig = request.META.get("HTTP_X_SIGNATURE") or ""
        expected_sig = hmac.new(
            secret.encode("utf-8"), raw_body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(received_sig, expected_sig):
            logger.warning(
                "Invalid webhook signature received: %s (Expected prefix: %s)",
                received_sig,
                expected_sig[:8],
            )
            return HttpResponseForbidden("Invalid signature")

    # 3. Extracción de datos
    provider = request.META.get("HTTP_X_PROVIDER") or "mercadopago"
    provider_ref = payload.get("id") or payload.get("provider_ref")
    external_reference = payload.get("external_reference")
    provider_status = payload.get("status")
    amount = payload.get("amount")

    logger.info(
        "Webhook received: provider=%s provider_ref=%s external_reference=%s status=%s",
        provider,
        provider_ref,
        external_reference,
        provider_status,
    )

    if not provider_ref:
        logger.warning("Missing provider_ref in webhook payload")
        return HttpResponse(status=400)

    # 4. Importación de modelos y constantes
    try:
        from orders.models import (ORDER_CONFIRMED, PAYMENT_STATUS_CHOICES,
                                   Order, Payment, PaymentLog)

        PAYMENT_STATUS_VALUES = {k for k, _ in PAYMENT_STATUS_CHOICES}
    except ImportError:
        logger.error(
            "Failed to import models (Order, Payment, etc.). Check orders.models."
        )
        return HttpResponse(status=500)

    # 5. Idempotencia: intentar crear PaymentLog (get_or_create) antes de procesar
    try:
        log_defaults = {"provider": provider}
        # Detectar campo de payload en PaymentLog
        pl_field_names = [f.name for f in PaymentLog._meta.get_fields()]
        payload_field = next(
            (
                f
                for f in ["raw_payload", "payload", "data", "raw", "body"]
                if f in pl_field_names
            ),
            None,
        )
        if payload_field:
            log_defaults[payload_field] = json.dumps(payload)

        payment_log, log_created = PaymentLog.objects.get_or_create(
            provider=provider, provider_ref=provider_ref, defaults=log_defaults
        )

        if not log_created:
            logger.info(
                "PaymentLog already exists for provider=%s provider_ref=%s: skipping (idempotent)",
                provider,
                provider_ref,
            )
            return HttpResponse(status=200)
    except Exception:
        logger.exception("Error creating PaymentLog for provider_ref=%s", provider_ref)
        # No fallar el webhook por log
        pass

    # 6. Mapeo de estado
    try:
        mapped_status = map_provider_status_to_payment_status(provider_status)
        if mapped_status not in PAYMENT_STATUS_VALUES:
            logger.warning(
                "Mapped status %s not valid, defaulting to FAILED", mapped_status
            )
            mapped_status = "FAILED"
    except Exception:
        logger.exception("Error mapping provider status %s", provider_status)
        mapped_status = "FAILED"

    # 7. Guardar Payment (con protección ante races)
    try:
        with transaction.atomic():
            order_obj = None
            if external_reference:
                try:
                    order_obj = Order.objects.select_for_update().get(
                        id=external_reference
                    )
                except Order.DoesNotExist:
                    logger.warning(
                        "Order not found for external_reference=%s", external_reference
                    )
                    order_obj = None

            defaults = {
                "order": order_obj,
                "provider": provider,
                "status": mapped_status,
                "metodo": provider,
            }

            if amount is not None:
                try:
                    defaults["monto"] = Decimal(str(amount))
                except Exception:
                    logger.exception("Invalid amount format in webhook: %s", amount)

            defaults = {k: v for k, v in defaults.items() if v is not None}

            try:
                payment, created = Payment.objects.update_or_create(
                    provider_ref=provider_ref, defaults=defaults
                )
            except IntegrityError:
                logger.warning(
                    "IntegrityError on update_or_create for provider_ref=%s, retrying with get()",
                    provider_ref,
                )
                try:
                    payment = Payment.objects.get(provider_ref=provider_ref)
                    for k, v in defaults.items():
                        setattr(payment, k, v)
                    payment.save(update_fields=list(defaults.keys()))
                    created = False
                except Payment.DoesNotExist:
                    logger.warning(
                        "Payment disappeared after IntegrityError; re-creating."
                    )
                    payment = Payment.objects.create(
                        provider_ref=provider_ref, **defaults
                    )
                    created = True
                except Exception:
                    logger.exception(
                        "Failed to fallback and retrieve/update payment %s",
                        provider_ref,
                    )
                    raise

            logger.info(
                "Payment %s (provider_ref=%s) created=%s status=%s monto=%s",
                getattr(payment, "id", None),
                provider_ref,
                created,
                payment.status,
                getattr(payment, "monto", None),
            )

            # 8. Confirmar Order si el pago fue exitoso
            if order_obj and mapped_status == "SUCCESS":
                if order_obj.estado != ORDER_CONFIRMED:
                    order_obj.estado = ORDER_CONFIRMED
                    order_obj.save(update_fields=["estado"])
                    logger.info(
                        "Order %s estado actualizado a %s",
                        order_obj.id,
                        order_obj.estado,
                    )
                else:
                    logger.info(
                        "Order %s ya estaba en estado CONFIRMED. No se requiere actualización.",
                        order_obj.id,
                    )

    except Exception:
        logger.exception(
            "Unhandled exception while processing payment webhook for provider_ref=%s",
            provider_ref,
        )
        return HttpResponse(status=500)

    return JsonResponse({"ok": True})
