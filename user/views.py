from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.http import urlsafe_base64_decode
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from ruta.models import Ruta, RutaCompartida
from ruta.serializers import (
    ComentarioSerializer, PuntajeSerializer, RutaSerializer,
)
from trek.email import (
    EmailType, get_email_body, send_confirmation_email,
    send_welcome_email,
)
from trek.permissions import AllowOnlyAnonymous
from .models import Usuario
from .serializers import SearchUsuarioSerializer, UsuarioSerializer


class UserViewSet(ViewSet):
    """
    ViewSet que maneja la gestión de usuarios:

    - POST   /users/create/                : Crear un nuevo usuario.
    - GET    /users/confirm-email/<token>/ : Confirma el email del nuevo usuario.
    - PUT    /users/update-profile/        : Actualizar el perfil del usuario autenticado.
    - PUT    /users/change-password/       : Cambiar la contraseña del usuario autenticado.
    - DELETE /users/delete-account/        : Eliminar la cuenta del usuario autenticado.
    - GET    /users/search/                : Buscar usuarios basándose en términos de búsqueda.
    """

    def get_permissions(self):
        print(self.action)
        if self.action in ['create_user', 'confirm_email', 'get_email']:
            return [AllowOnlyAnonymous()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'], url_path='email/(?P<email_type>\w+)')
    def get_email(self, request, email_type):
        email_type = {
            'confirm_email': EmailType.CONFIRM_EMAIL,
            'welcome': EmailType.WELCOME,
            'password_reset': EmailType.PASSWORD_RESET,
        }[email_type]
        return HttpResponse(get_email_body(self.request.user, email_type, self.request, **self.request.GET))

    @action(detail=False, methods=['post'], url_path='create')
    def create_user(self, request):
        """
        Crea un nuevo usuario utilizando el UsuarioSerializer.
        """
        serializer = UsuarioSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            send_confirmation_email(user, request)
            return Response({**serializer.data, 'message': 'Usuario creado. Revisa tu email para terminar tu registro'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='confirm-email/(?P<token>[^/.]+)', name='confirm_email')
    def confirm_email(self, request, token):
        """
        Confirma la dirección de correo electrónico del usuario utilizando el token de confirmación y renderiza una página HTML.
        """

        is_json = request.query_params.get('json') == 'true'

        signer = TimestampSigner()
        try:
            # Decodifica y verifica el token
            decoded_token = urlsafe_base64_decode(token).decode()
            email = signer.unsign(decoded_token, max_age=86400)
            user = Usuario.all_objects.get(email=email)

            # Si el usuario ya está activo
            if user.is_active:
                message = {'message': 'El correo ya está confirmado.'}
                if is_json:
                    return Response(message, status=status.HTTP_400_BAD_REQUEST)
                return render(request, 'welcome.html', message)

            # Activar al usuario
            user.is_active = True
            user.save()

            send_welcome_email(user, request)
            token, _ = Token.objects.get_or_create(user=user)

            data = UsuarioSerializer(user).data
            message = {
                **data,
                'token': token.key,
                'message': 'Correo electrónico confirmado exitosamente.',
            }
            if is_json:
                return Response(message, status=status.HTTP_201_CREATED)
            return render(request, 'welcome.html', message)

        except SignatureExpired:
            message = {'message': 'El enlace de confirmación ha expirado. Solicita un nuevo enlace.'}
            if is_json:
                return Response(message, status=status.HTTP_400_BAD_REQUEST)
            return render(request, 'welcome.html', message)
        except (BadSignature, Usuario.DoesNotExist, ValueError):
            message = {'message': 'El enlace de confirmación no es válido.'}
            if is_json:
                return Response(message, status=status.HTTP_400_BAD_REQUEST)
            return render(request, 'welcome.html', message)

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
        user_id = request.query_params.get('id', None)

        if not query and not user_id:
            return Response({'error': 'Se requiere un parámetro de búsqueda.'}, status=status.HTTP_400_BAD_REQUEST)

        users = Usuario.objects.annotate(
            fullname=Concat('first_name', Value(' '), 'last_name')
        )

        if user_id:
            try:
                user = users.get(pk=user_id)
                serializer = SearchUsuarioSerializer(user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Usuario.DoesNotExist:
                return Response({'error': 'Usuario no existe'}, status=status.HTTP_400_BAD_REQUEST)

        total_characters = len(query.replace(" ", ""))
        if total_characters < 3:
            return Response({'error': 'La búsqueda debe tener al menos 3 letras en total.'}, status=status.HTTP_400_BAD_REQUEST)

        search_terms = query.split()
        query_filter = Q()

        for term in search_terms:
            query_filter &= Q(username__icontains=term) | Q(first_name__icontains=term) | Q(last_name__icontains=term)

        users = users.filter(query_filter).exclude(id=request.user.id)

        if not request.user.is_staff:
            users = users.exclude(is_staff=True)
        if not request.user.is_superuser:
            users = users.exclude(is_superuser=True)

        serializer = SearchUsuarioSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='actividad', name='user_activity')
    def user_activity(self, request):
        """
        Endpoint para mostrar la actividad del usuario.
        Incluye rutas creadas, calificaciones dadas y comentarios realizados.
        """
        user: Usuario = request.user

        # Rutas creadas por el usuario
        rutas = Ruta.objects.filter(usuario=user).prefetch_related('comentarios', 'puntajes')

        # Rutas compartidas con este usuario
        rutas_compartidas = Ruta.objects.filter(rutacompartida__usuario=user)

        # Comentarios realizados por el usuario
        comentarios = user.comentario_set.select_related('ruta')

        # Puntajes dados por el usuario
        puntajes = user.puntaje_set.select_related('ruta')

        # Pasar el contexto al serializador
        context = {'request': request}

        data = {
            'rutas_creadas': RutaSerializer(rutas, many=True, context=context).data,
            'rutas_compartidas': RutaSerializer(rutas_compartidas, many=True, context=context).data,
            'comentarios': ComentarioSerializer(comentarios, many=True, context=context).data,
            'puntajes': PuntajeSerializer(puntajes, many=True, context=context).data,
        }

        return Response(data)

    @action(detail=False, methods=['delete'], url_path='actividad/(?P<_type>\w+)/(?P<pk>\w+)', name='delete_user_activity')
    def delete_user_activity(self, request, _type=None, pk=None):
        """
        Endpoint para eliminar la actividad del usuario.
        Incluye rutas compartidas, calificaciones dadas y comentarios realizados.
        """
        user: Usuario = request.user

        if _type == 'rutas_creadas':
            user_id = request.GET['user_id']
            RutaCompartida.objects.filter(
                ruta_id=pk,
                usuario_id=user_id,
            ).delete()
        elif _type == 'rutas_compartidas':
            RutaCompartida.objects.filter(
                ruta_id=pk,
                usuario=user,
            ).delete()
        elif _type == 'comentarios':
            user.comentario_set.filter(pk=pk).delete()
        elif _type == 'puntajes':
            puntaje = user.puntaje_set.filter(id=pk)
            rutas = Ruta.objects.filter(puntajes__pk=pk)
            puntaje.delete()
            for ruta in rutas:
                ruta.update_puntaje()

        return self.user_activity(request)
