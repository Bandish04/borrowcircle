from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DisputeViewSet, DisputeEvidenceViewSet

router = DefaultRouter()
router.register('evidence', DisputeEvidenceViewSet, basename='dispute-evidence')
router.register('', DisputeViewSet, basename='dispute')

urlpatterns = [
    path('', include(router.urls)),
]