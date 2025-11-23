# delivery/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from delivery.views import DeliveryAssignmentViewSet, MyDeliveriesViewSet

router = DefaultRouter()
router.register(
    r"assignments", DeliveryAssignmentViewSet, basename="delivery-assignment"
)
router.register(r"mias", MyDeliveriesViewSet, basename="my-deliveries")

urlpatterns = [
    path("", include(router.urls)),
]
