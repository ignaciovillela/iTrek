from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Case, Sum, When

from user.managers import ActiveUserManager


class Usuario(AbstractUser):
    email = models.EmailField(unique=True)
    biografia = models.TextField(blank=True)
    imagen_perfil = models.ImageField(upload_to='imagenes_perfil/', blank=True, null=True)

    objects = ActiveUserManager()
    all_objects = models.Manager()

    NIVELES = {
        1: {
            'nombre': 'Iniciado en Senderismo',
            'descripcion': '¡Bienvenido al senderismo! Aún no has comenzado tu aventura. Registra tu primera ruta y empieza a explorar el mundo.',
            'puntos_min': 0,
        },
        2: {
            'nombre': 'Explorador Principiante',
            'descripcion': '¡Sigue así! Suma kilómetros y registra más rutas. Estás a {falta_puntos} puntos de convertirte en un Trekker Intermedio.',
            'puntos_min': 1,
        },
        3: {
            'nombre': 'Trekker Intermedio',
            'descripcion': 'Para alcanzar el nivel Aventurero Experto necesitas seguir explorando rutas más largas o desafiantes. Te faltan {falta_puntos} puntos.',
            'puntos_min': 500,
        },
        4: {
            'nombre': 'Aventurero Experto',
            'descripcion': '¡Increíble trabajo! Estás cerca de convertirte en una Leyenda del Senderismo. Solo te faltan {falta_puntos} puntos. ¡Mantén el ritmo!',
            'puntos_min': 1000,
        },
        5: {
            'nombre': 'Leyenda del Senderismo',
            'descripcion': '¡Felicidades! Has alcanzado el nivel máximo. Eres una inspiración para otros exploradores.',
            'puntos_min': 2000,
        },
    }

    def __str__(self):
        return self.username

    @property
    def imagen_perfil_url(self):
        if self.imagen_perfil:
            return self.imagen_perfil.url
        return f'{settings.STATIC_URL}default_profile.jpg'

    def get_dias_creacion_cuenta(self):
        """
        Calcula los días desde la creación de la cuenta.
        """
        return (datetime.now().date() - self.date_joined.date()).days

    def get_distancia_trek(self):
        """
        Calcula la distancia total recorrida por el usuario en kilómetros.
        """
        return self.rutas.aggregate(total_distancia=Sum('distancia_km'))['total_distancia'] or 0.0

    def get_minutos_trek(self):
        """
        Calcula el tiempo total estimado en minutos de las rutas del usuario.
        """
        return self.rutas.aggregate(total_minutos=Sum('tiempo_estimado_minutos'))['total_minutos'] or 0

    def get_puntos_estrellas(self):
        """
        Calcula los puntos adicionales o penalizaciones basadas en las estrellas de las rutas del usuario.
        """
        estrellas = self.rutas.aggregate(
            estrellas_puntos=Sum(
                Case(
                    When(puntaje=1, then=-1),
                    When(puntaje=2, then=0),
                    When(puntaje__in=[3, 4], then=1),
                    When(puntaje=5, then=2),
                    default=0,
                    output_field=models.IntegerField()
                )
            )
        )
        return estrellas['estrellas_puntos'] or 0

    def get_puntos_trek(self):
        """
        Calcula el puntaje total del usuario basado en días, distancia, tiempo y estrellas.
        """
        dias_cuenta = self.get_dias_creacion_cuenta()
        distancia_total = self.get_distancia_trek()
        minutos_totales = self.get_minutos_trek()
        puntos_estrellas = self.get_puntos_estrellas()

        puntos_trek = (dias_cuenta * 1) + (distancia_total * 10) + (minutos_totales * 1) + puntos_estrellas
        return round(puntos_trek)

    def get_nivel(self):
        """
        Determina el nivel del usuario basado en los puntos.
        """
        puntos_trek = self.get_puntos_trek()

        for nivel, datos in reversed(self.NIVELES.items()):
            if puntos_trek >= datos['puntos_min']:
                return nivel

        return 1  # Nivel mínimo como fallback

    def get_nombre_nivel(self):
        """
        Obtiene el nombre del nivel del usuario.
        """
        nivel = self.get_nivel()
        return self.NIVELES[nivel]['nombre']

    def get_descripcion_nivel(self):
        """
        Obtiene la descripción del nivel del usuario, formateada con los puntos restantes si aplica.
        """
        nivel = self.get_nivel()
        puntos_trek = self.get_puntos_trek()

        # Verifica si hay un siguiente nivel
        if nivel < len(self.NIVELES):
            puntos_min_siguiente = self.NIVELES[nivel + 1]['puntos_min']
            falta_puntos = puntos_min_siguiente - puntos_trek
        else:
            falta_puntos = 0  # Nivel máximo alcanzado

        # Formatea la descripción con los puntos restantes
        descripcion = self.NIVELES[nivel]['descripcion']
        return descripcion.format(falta_puntos=falta_puntos)
