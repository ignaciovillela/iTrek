from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RutaViewSet

router = DefaultRouter()
router.register(r'rutas', RutaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
