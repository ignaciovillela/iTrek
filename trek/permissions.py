from rest_framework.permissions import BasePermission


class AllowOnlyAnonymous(BasePermission):
    """
    Permitir acceso solo a usuarios anónimos. Bloquear a los usuarios autenticados.
    """

    def has_permission(self, request, view):
        # Permitir acceso solo si el usuario NO está autenticado
        return not request.user.is_authenticated
