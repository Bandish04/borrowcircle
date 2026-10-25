from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/items/', include('apps.items.urls')),
    path('api/v1/reservations/', include('apps.reservations.urls')),
    path('api/v1/loans/', include('apps.loans.urls')),
    path('api/v1/reviews/', include('apps.reviews.urls')),
    path('api/v1/messaging', include('apps.messaging.urls')),
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]