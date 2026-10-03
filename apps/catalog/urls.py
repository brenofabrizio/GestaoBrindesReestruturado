from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, IndustryViewSet, ProductViewSet

router = DefaultRouter()
router.register("industries", IndustryViewSet, basename="industry")
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")

urlpatterns = router.urls

