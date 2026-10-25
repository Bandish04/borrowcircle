from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoanViewSet

router = DefaultRouter()
router.register('', LoanViewSet, basename='loan')

urlpatterns = [
    path('', include(router.urls)),
]