from rest_framework import serializers
from .models import RutaTrekking, Punto

class PuntoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Punto
        fields = ['latitud', 'longitud', 'orden']

class RutaTrekkingSerializer(serializers.ModelSerializer):
    puntos = PuntoSerializer(many=True)

    class Meta:
        model = RutaTrekking
        fields = ['id', 'nombre', 'descripcion', 'dificultad', 'puntos',
                  'creado_en', 'distancia_km', 'tiempo_estimado_horas', 'usuario']

    def create(self, validated_data):
        puntos_data = validated_data.pop('puntos')
        ruta = RutaTrekking.objects.create(**validated_data)
        for punto_data in puntos_data:
            Punto.objects.create(ruta=ruta, **punto_data)
        return ruta
