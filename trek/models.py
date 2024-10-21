from django.contrib.auth.models import AbstractUser
from django.db import models

from trek.managers import ActiveUserManager


class Usuario(AbstractUser):
    email = models.EmailField(unique=True)
    biografia = models.TextField(blank=True)
    imagen_perfil = models.ImageField(upload_to='imagenes_perfil/', blank=True, null=True)

    objects = ActiveUserManager()
    all_objects = models.Manager()

    def __str__(self):
        return self.username


class Ruta(models.Model):
    OPCIONES_DIFICULTAD = [
        ('facil', 'Fácil'),
        ('moderada', 'Moderada'),
        ('dificil', 'Difícil'),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='rutas', null=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    dificultad = models.CharField(max_length=10, choices=OPCIONES_DIFICULTAD, default='moderada')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    distancia_km = models.FloatField()
    tiempo_estimado_horas = models.FloatField()
    publica = models.BooleanField(default=True)
    compartida_con = models.ManyToManyField(Usuario, through='RutaCompartida', related_name='rutas_compartidas_conmigo', blank=True)

    def __str__(self):
        return self.nombre


class RutaCompartida(models.Model):
    ruta = models.ForeignKey(Ruta, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('ruta', 'usuario')

    def __str__(self):
        return f"{self.ruta.nombre} compartida con {self.usuario.username}"


class Punto(models.Model):
    ruta = models.ForeignKey(Ruta, on_delete=models.CASCADE, related_name='puntos')
    latitud = models.FloatField()
    longitud = models.FloatField()
    orden = models.IntegerField()

    def __str__(self):
        return f"Punto {self.orden} - Lat: {self.latitud}, Lon: {self.longitud}"


class PuntoInteres(models.Model):
    punto = models.OneToOneField(Punto, on_delete=models.CASCADE, related_name='interes')
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='imagenes/', blank=True, null=True)
