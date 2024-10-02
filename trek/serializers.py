from rest_framework import serializers
from .models import Usuario, Ruta, Punto

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'biografia', 'imagen_perfil']

class PuntoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Punto
        fields = ['latitud', 'longitud', 'orden']

class RutaSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    puntos = PuntoSerializer(many=True)

    class Meta:
        model = Ruta
        fields = ['id', 'nombre', 'descripcion', 'dificultad', 'puntos',
                  'creado_en', 'distancia_km', 'tiempo_estimado_horas', 'usuario']

    def create(self, validated_data):
        puntos_data = validated_data.pop('puntos')
        ruta = Ruta.objects.create(**validated_data)
        for punto_data in puntos_data:
            Punto.objects.create(ruta=ruta, **punto_data)
        return ruta
