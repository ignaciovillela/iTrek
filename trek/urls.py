from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RutaViewSet, buscar_usuario, checklogin_view, login_view

router = DefaultRouter()
router.register(r'rutas', RutaViewSet)

urlpatterns = [
    path('login/', login_view, name='login'),
    path('checklogin/', checklogin_view, name='checklogin'),
    path('buscar_usuario/', buscar_usuario, name='buscar_usuario'),
    path('', include(router.urls)),
]
