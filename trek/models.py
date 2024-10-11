from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    email = models.EmailField(unique=True)
    biografia = models.TextField(blank=True)
    imagen_perfil = models.ImageField(upload_to='imagenes_perfil/', blank=True, null=True)

    def __str__(self):
        return self.username


class Ruta(models.Model):
    class DificultadChoices(models.TextChoices):
        FACIL = 'facil', 'Fácil'
        MODERADA = 'moderada', 'Moderada'
        DIFICIL = 'dificil', 'Difícil'

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='rutas', null=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    dificultad = models.CharField(
        max_length=10,
        choices=DificultadChoices.choices,
        default=DificultadChoices.MODERADA
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    distancia_km = models.FloatField()
    tiempo_estimado_horas = models.FloatField()

    def __str__(self):
        return self.nombre


class Punto(models.Model):
    ruta = models.ForeignKey(Ruta, on_delete=models.CASCADE, related_name='puntos')
    latitud = models.FloatField()
    longitud = models.FloatField()
    orden = models.IntegerField()

    def __str__(self):
        return f"Punto {self.orden} - Lat: {self.latitud}, Lon: {self.longitud}"
