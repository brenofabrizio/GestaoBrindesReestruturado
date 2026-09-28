from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", include("apps.core.urls")),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/catalog/", include("apps.catalog.urls")),
    path("api/v1/inventory/", include("apps.inventory.urls")),
    path("api/v1/orders/", include("apps.orders.urls")),
    path("api/v1/audit/", include("apps.audit.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
