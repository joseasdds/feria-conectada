# delivery/views.py
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from delivery.models import DeliveryAssignment
from delivery.permissions import IsRepartidor
from delivery.serializers import DeliveryAssignmentSerializer


class DeliveryAssignmentViewSet(viewsets.ModelViewSet):
    """
    Gestión de asignaciones (admin/sistema). Repartidores usan actions claim/mark_delivered.
    """

    queryset = DeliveryAssignment.objects.all().select_related("order", "repartidor")
    serializer_class = DeliveryAssignmentSerializer

    # delivery/views.py (sólo el método get_permissions)
    def get_permissions(self):
        """
        Control de permisos:
         - Para las actions específicas de repartidor (claim, mark_delivered)
           permitir IsAuthenticated + IsRepartidor.
         - Para operaciones de escritura generales (crear/editar/borrar) dejar
           IsAuthenticated + IsAdminUser (administración).
         - Para lectura estándar, solo IsAuthenticated.
        """
        # Si estamos en una action concreta (e.g. claim, mark_delivered) respetamos eso:
        action = getattr(self, "action", None)
        if action in ("claim", "mark_delivered"):
            return [IsAuthenticated(), IsRepartidor()]

        # Operaciones de escritura globales del viewset -> admin
        if self.request.method in ("POST", "PUT", "PATCH", "DELETE"):
            return [IsAuthenticated(), IsAdminUser()]

        # Lectura por usuarios autenticados
        return [IsAuthenticated()]

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsRepartidor],
    )
    def claim(self, request, pk=None):
        """
        Repartidor reclama la asignación (si está PENDING y no tiene repartidor).
        Operación hecha de forma atómica para evitar race conditions.
        """
        with transaction.atomic():
            assignment = get_object_or_404(
                DeliveryAssignment.objects.select_for_update(), pk=pk
            )
            if (
                assignment.repartidor is not None
                and assignment.repartidor != request.user
            ):
                return Response(
                    {"detail": "Ya asignado a otro repartidor."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if assignment.estado not in (
                DeliveryAssignment.STATE_PENDING,
                DeliveryAssignment.STATE_ASSIGNED,
            ):
                return Response(
                    {"detail": "No se puede reclamar en este estado."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            assignment.repartidor = request.user
            assignment.estado = DeliveryAssignment.STATE_ASSIGNED
            assignment.save()
            return Response(self.get_serializer(assignment).data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsRepartidor],
    )
    def mark_delivered(self, request, pk=None):
        """
        Repartidor marca como entregado (solo el repartidor asignado).
        Actualiza también el estado del Order si existe el campo esperable.
        """
        with transaction.atomic():
            assignment = get_object_or_404(
                DeliveryAssignment.objects.select_for_update(), pk=pk
            )
            if assignment.repartidor_id != request.user.id:
                return Response(
                    {"detail": "No sos el repartidor asignado."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            assignment.estado = DeliveryAssignment.STATE_DELIVERED
            assignment.save()

            # Intentar actualizar estado del Order de forma segura.
            try:
                order = assignment.order
                # Ajusta según el nombre del campo de estado en tu modelo Order.
                if hasattr(order, "estado"):
                    order.estado = "ENTREGADO"
                elif hasattr(order, "status"):
                    order.status = "DELIVERED"
                order.save()
            except Exception:
                pass

            return Response(self.get_serializer(assignment).data)


class MyDeliveriesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/v1/delivery/mias/  -> lista las asignaciones del repartidor autenticado.
    """

    serializer_class = DeliveryAssignmentSerializer
    permission_classes = [IsAuthenticated, IsRepartidor]

    def get_queryset(self):
        user = self.request.user
        return DeliveryAssignment.objects.filter(repartidor=user).order_by(
            "-created_at"
        )
