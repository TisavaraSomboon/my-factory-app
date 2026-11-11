from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import FabricRulesView, OrderViewSet

router = DefaultRouter()
router.include_root_view = False
router.register("orders", OrderViewSet, basename="order")

urlpatterns = [path("fabric-rules/", FabricRulesView.as_view(), name="fabric-rules")] + router.urls
