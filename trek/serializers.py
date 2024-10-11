from rest_framework import serializers

from .models import Punto, Ruta, Usuario


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
        extra_kwargs = {
            'nombre': {'allow_blank': True, 'required': False},
            'descripcion': {'allow_blank': True, 'required': False},
            'dificultad': {'allow_blank': True, 'required': False},
            'distancia_km': {'required': False},
            'tiempo_estimado_horas': {'required': False},
        }

    def create(self, validated_data):
        puntos_data = validated_data.pop('puntos', [])

        nombre = validated_data.get('nombre', '').strip()
        if not nombre:
            validated_data['nombre'] = f"Ruta sin nombre {Ruta.objects.count() + 1}"

        descripcion = validated_data.get('descripcion', '').strip()
        if not descripcion:
            validated_data['descripcion'] = "Descripción no proporcionada"

        dificultad = validated_data.get('dificultad', '').strip()
        if not dificultad:
            validated_data['dificultad'] = 'facil'

        validated_data['distancia_km'] = validated_data.get('distancia_km', 1.0)
        validated_data['tiempo_estimado_horas'] = validated_data.get('tiempo_estimado_horas', 1.0)

        ruta = Ruta.objects.create(**validated_data)

        for punto_data in puntos_data:
            Punto.objects.create(ruta=ruta, **punto_data)

        return ruta
