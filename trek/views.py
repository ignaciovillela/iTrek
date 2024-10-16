from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response

from .models import Ruta, Usuario
from .serializers import RutaSerializer


class RutaViewSet(viewsets.ModelViewSet):
    queryset = Ruta.objects.all()
    serializer_class = RutaSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def perform_create(self, serializer):
        if self.request.user.is_anonymous:
            default_user = Usuario.objects.get(username='default')
            serializer.save(usuario=default_user)
        else:
            serializer.save(usuario=self.request.user)
