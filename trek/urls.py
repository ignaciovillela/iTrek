from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RutaTrekkingViewSet

router = DefaultRouter()
router.register(r'rutas', RutaTrekkingViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
