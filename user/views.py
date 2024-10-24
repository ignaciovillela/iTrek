from django.db.models import Q, Value
from django.db.models.functions import Concat
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from trek.permissions import AllowOnlyAnonymous
from .models import Usuario
from .serializers import SearchUsuarioSerializer, UsuarioSerializer


class UserViewSet(ViewSet):
    """
    ViewSet que maneja la gestión de usuarios:

    - POST   /users/create/          : Crear un nuevo usuario.
    - PUT    /users/update-profile/  : Actualizar el perfil del usuario autenticado.
    - PUT    /users/change-password/ : Cambiar la contraseña del usuario autenticado.
    - DELETE /users/delete-account/  : Eliminar la cuenta del usuario autenticado.
    - GET    /users/search/          : Buscar usuarios basándose en términos de búsqueda.
    """

    def get_permissions(self):
        if self.action in ['create_user']:
            return [AllowOnlyAnonymous()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['post'], url_path='create')
    def create_user(self, request):
        """
        Crea un nuevo usuario utilizando el UsuarioSerializer.
        """
        serializer = UsuarioSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({**serializer.data, 'message': 'Usuario creado exitosamente.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['put'], url_path='update-profile')
    def update_profile(self, request):
        """
        Permite a un usuario autenticado actualizar su perfil.
        """
        serializer = UsuarioSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({**serializer.data, 'message': 'Perfil actualizado correctamente.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['put'], url_path='change-password')
    def change_password(self, request):
        """
        Permite a un usuario autenticado cambiar su contraseña.
        """
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not user.check_password(current_password):
            return Response({'error': 'La contraseña actual es incorrecta.'}, status=status.HTTP_400_BAD_REQUEST)

        if not new_password:
            return Response({'error': 'Debe proporcionar una nueva contraseña.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({'message': 'Contraseña actualizada exitosamente.'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'], url_path='delete-account')
    def delete_account(self, request):
        """
        Permite a un usuario autenticado eliminar su cuenta.
        """
        request.user.delete()
        return Response({'message': 'Cuenta eliminada exitosamente.'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='search')
    def search_user(self, request):
        """
        Buscar usuarios basándose en los términos de búsqueda proporcionados.
        """
        query = request.query_params.get('q', None)

        if not query:
            return Response({'error': 'Se requiere un parámetro de búsqueda.'}, status=status.HTTP_400_BAD_REQUEST)

        total_characters = len(query.replace(" ", ""))
        if total_characters < 3:
            return Response({'error': 'La búsqueda debe tener al menos 3 letras en total.'}, status=status.HTTP_400_BAD_REQUEST)

        search_terms = query.split()
        query_filter = Q()

        for term in search_terms:
            query_filter &= Q(username__icontains=term) | Q(first_name__icontains=term) | Q(last_name__icontains=term)

        usuarios = Usuario.objects.filter(query_filter).exclude(id=request.user.id).annotate(
            fullname=Concat('first_name', Value(' '), 'last_name')
        )

        if not request.user.is_staff:
            usuarios = usuarios.exclude(is_staff=True)
        if not request.user.is_superuser:
            usuarios = usuarios.exclude(is_superuser=True)

        serializer = SearchUsuarioSerializer(usuarios, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
