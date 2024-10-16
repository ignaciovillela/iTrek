from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RutaViewSet, checklogin_view, login_view

router = DefaultRouter()
router.register(r'rutas', RutaViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('login/', login_view, name='login'),
    path('checklogin/', checklogin_view, name='checklogin'),
]
