from django.db import models

class RutaTrekking(models.Model):
    OPCIONES_DIFICULTAD = [
        ('facil', 'Fácil'),
        ('moderada', 'Moderada'),
        ('dificil', 'Difícil'),
    ]

    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    dificultad = models.CharField(max_length=10, choices=OPCIONES_DIFICULTAD, default='moderada')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    distancia_km = models.FloatField()
    tiempo_estimado_horas = models.FloatField()

    def __str__(self):
        return self.nombre

class Punto(models.Model):
    ruta = models.ForeignKey(RutaTrekking, on_delete=models.CASCADE, related_name='puntos')
    latitud = models.FloatField()
    longitud = models.FloatField()
    orden = models.IntegerField()

    def __str__(self):
        return f"Punto {self.orden} - Lat: {self.latitud}, Lon: {self.longitud}"
