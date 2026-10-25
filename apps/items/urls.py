from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ItemViewSet

router = DefaultRouter()
router.register(f'categories', CategoryViewSet, basename='category')
router.register(f'', ItemViewSet, basename='item')

urlpatterns = [
    path('', include(router.urls)),
]