from django.contrib.auth import authenticate
from django.db.models import Q, Value
from django.db.models.functions import Concat
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Ruta
from .models import Usuario
from .serializers import (
    RutaBaseSerializer, RutaSerializer,
)
from .serializers import SearchUsuarioSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key}, status=status.HTTP_200_OK)
    return Response({'error': 'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def checklogin_view(request):
    user = request.user
    return Response({'message': 'User is authenticated', 'username': user.username})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def buscar_usuario(request):
    query = request.query_params.get('q', None)

    if not query:
        return Response({'error': 'Se requiere un parámetro de búsqueda.'}, status=status.HTTP_400_BAD_REQUEST)

    total_characters = len(query.replace(" ", ""))

    if total_characters < 3:
        return Response({'error': 'La búsqueda debe tener al menos 3 letras en total.'}, status=status.HTTP_400_BAD_REQUEST)

    search_terms = query.split()

    query_filter = Q()
    for term in search_terms:
        query_filter |= Q(username__icontains=term) | Q(first_name__icontains=term) | Q(last_name__icontains=term)

    usuarios = Usuario.objects.filter(query_filter).exclude(id=request.user.id).annotate(
        fullname=Concat('first_name', Value(' '), 'last_name')
    )
    if not request.user.is_staff:
        usuarios = usuarios.exclude(is_staff=True)
    if not request.user.is_superuser:
        usuarios = usuarios.exclude(is_superuser=True)

    serializer = SearchUsuarioSerializer(usuarios, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


class RutaViewSet(viewsets.ModelViewSet):
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

    @action(detail=True, methods=['post', 'delete'], url_path='compartir/(?P<usuario_id>\d+)')
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
