from django.db.models import Q
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from user.models import Usuario
from .models import Comentario, Puntaje, Ruta
from .serializers import (
    ComentarioSerializer, RutaBaseSerializer,
    RutaSerializer,
)


class RutaViewSet(viewsets.ModelViewSet):
    """
    ViewSet que maneja la gestión de rutas.

    - GET    /routes/                         : Listar todas las rutas visibles al usuario autenticado.
    - POST   /routes/                         : Crear una nueva ruta.
    - GET    /routes/{id}/                    : Obtener los detalles de una ruta específica.
    - PATCH  /routes/{id}/                    : Actualizar una ruta específica.
    - DELETE /routes/{id}/                    : Eliminar una ruta específica.
    - POST   /routes/{id}/share/{usuario_id}/ : Compartir una ruta con un usuario específico.
    - DELETE /routes/{id}/share/{usuario_id}/ : Dejar de compartir una ruta con un usuario específico.
    """

    queryset = Ruta.objects.all()
    list_serializer_class = RutaBaseSerializer
    serializer_class = RutaSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return self.list_serializer_class
        return self.serializer_class

    def get_queryset(self):
        return Ruta.objects.filter(
            Q(usuario=self.request.user) |
            Q(compartida_con=self.request.user) |
            Q(publica=True)
        ).distinct()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    @action(detail=True, methods=['post', 'delete'], url_path='share/(?P<usuario_id>\d+)')
    def compartir(self, request, pk=None, usuario_id=None):
        ruta = self.get_object()
        is_share = request.method == 'POST'
        is_share_text = "compartir" if is_share else "dejar de compartir"

        if ruta.usuario != request.user:
            return Response({'error': f'Solo puedes {is_share_text} rutas que te pertenecen.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            usuario_compartido = Usuario.objects.get(id=usuario_id)

            if is_share:
                if usuario_compartido == request.user:
                    return Response({'error': 'No puedes compartir la ruta contigo mismo.'}, status=status.HTTP_400_BAD_REQUEST)
                return self.compartir_ruta(ruta, usuario_compartido)
            else:
                return self.dejar_de_compartir_ruta(ruta, usuario_compartido)

        except Usuario.DoesNotExist:
            return Response({'error': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    @staticmethod
    def compartir_ruta(ruta, usuario_compartido):
        if usuario_compartido in ruta.compartida_con.all():
            return Response({'error': 'La ruta ya ha sido compartida con este usuario.'}, status=status.HTTP_400_BAD_REQUEST)

        ruta.compartida_con.add(usuario_compartido)
        return Response({'message': 'Ruta compartida con éxito.'}, status=status.HTTP_201_CREATED)

    @staticmethod
    def dejar_de_compartir_ruta(ruta, usuario_compartido):
        if usuario_compartido not in ruta.compartida_con.all():
            return Response({'error': 'La ruta no está compartida con este usuario.'}, status=status.HTTP_400_BAD_REQUEST)

        ruta.compartida_con.remove(usuario_compartido)
        return Response({'message': 'Ruta dejada de compartir con éxito.'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        ruta = self.get_object()

        if 'puntaje' not in request.data:
            return Response({'error': 'Debes proporcionar un puntaje.'}, status=status.HTTP_400_BAD_REQUEST)

        puntaje_value = request.data.get('puntaje')

        if puntaje_value is None:
            message = 'Puntaje eliminado con éxito.'
            Puntaje.objects.filter(
                usuario=request.user,
                ruta=ruta,
            ).delete()
        else:
            message = 'Puntaje registrado con éxito.'
            try:
                puntaje_value = int(puntaje_value)
                if not (1 <= puntaje_value <= 5):
                    return Response({'error': 'El puntaje debe ser entre 1 y 5.'}, status=status.HTTP_400_BAD_REQUEST)
            except ValueError:
                return Response({'error': 'El puntaje debe ser un número.'}, status=status.HTTP_400_BAD_REQUEST)

            Puntaje.objects.update_or_create(
                usuario=request.user,
                ruta=ruta,
                defaults={'puntaje': puntaje_value}
            )

        ruta.update_puntaje()

        return Response({'message': message, 'mi_puntaje': puntaje_value, 'puntaje': ruta.puntaje}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def comment(self, request, pk=None):
        ruta = self.get_object()

        comment = request.data.get('comment')

        if not comment:
            return Response({'error': 'Debes proporcionar un comentario.'}, status=status.HTTP_400_BAD_REQUEST)

        message = 'Comentario registrado con éxito.'

        Comentario.objects.create(
            usuario=request.user,
            ruta=ruta,
            descripcion=comment,
        )
        messages = Comentario.objects.filter(
            usuario=request.user,
            ruta=ruta,
        )
        messages_data = ComentarioSerializer(messages, many=True).data

        return Response({'message': message, 'comentarios': messages_data}, status=status.HTTP_200_OK)
