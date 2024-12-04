from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from ruta import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include([
        path('auth/', include('authentication.urls')),
        path('users/', include('user.urls')),
        path('routes/', include('ruta.urls')),
    ])),
    path('share/route/<int:route_id>/', views.share, name='share'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
