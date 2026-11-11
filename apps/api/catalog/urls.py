from rest_framework.routers import DefaultRouter

from .views import ColorViewSet, InspectionViewSet, PatternViewSet

router = DefaultRouter()
router.include_root_view = False
router.register("patterns", PatternViewSet, basename="pattern")
router.register("colors", ColorViewSet, basename="color")
router.register("inspections", InspectionViewSet, basename="inspection")

urlpatterns = router.urls
