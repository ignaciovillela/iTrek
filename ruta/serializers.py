from rest_framework import serializers

from trek.fields import Base64ImageField
from user.serializers import UsuarioSerializer
from .models import Punto, PuntoInteres, Ruta, RutaCompartida


class PuntoInteresSerializer(serializers.ModelSerializer):
    imagen = Base64ImageField(required=False)

    class Meta:
        model = PuntoInteres
        fields = ['descripcion', 'imagen']


class PuntoSerializer(serializers.ModelSerializer):
    interes = PuntoInteresSerializer(required=False)

    class Meta:
        model = Punto
        fields = ['latitud', 'longitud', 'orden', 'interes']

    def create(self, validated_data):
        interes_data = validated_data.pop('interes', None)
        punto = Punto.objects.create(**validated_data)

        if interes_data:
            PuntoInteres.objects.create(punto=punto, **interes_data)

        return punto

    def update(self, instance, validated_data):
        interes_data = validated_data.pop('interes', None)

        instance.latitud = validated_data.get('latitud', instance.latitud)
        instance.longitud = validated_data.get('longitud', instance.longitud)
        instance.orden = validated_data.get('orden', instance.orden)
        instance.save()

        if interes_data:
            if hasattr(instance, 'interes'):
                instance.interes.descripcion = interes_data.get('descripcion', instance.interes.descripcion)
                instance.interes.save()
            else:
                PuntoInteres.objects.create(punto=instance, **interes_data)

        return instance


class RutaBaseSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)

    class Meta:
        model = Ruta
        fields = [
            'id', 'nombre', 'descripcion', 'dificultad', 'creado_en',
            'distancia_km', 'tiempo_estimado_minutos', 'usuario', 'publica',
        ]


class RutaSerializer(RutaBaseSerializer):
    puntos = PuntoSerializer(many=True)

    class Meta(RutaBaseSerializer.Meta):
        fields = RutaBaseSerializer.Meta.fields + ['puntos']
        extra_kwargs = {
            'nombre': {'allow_blank': True, 'required': False},
            'descripcion': {'allow_blank': True, 'required': False},
            'dificultad': {'allow_blank': True, 'required': False},
            'distancia_km': {'required': False},
            'tiempo_estimado_minutos': {'required': False},
        }

    def create(self, validated_data):
        puntos_data = validated_data.pop('puntos', [])
        ruta = self.create_ruta(validated_data)
        self.create_puntos(ruta, puntos_data)
        return ruta

    @staticmethod
    def create_ruta(validated_data):
        if not validated_data.get('nombre', '').strip():
            validated_data['nombre'] = f"Ruta sin nombre {Ruta.objects.count() + 1}"
        if not validated_data.get('descripcion', '').strip():
            validated_data['descripcion'] = "Descripción no proporcionada"
        if not validated_data.get('dificultad', '').strip():
            validated_data['dificultad'] = 'facil'

        validated_data['distancia_km'] = validated_data.get('distancia_km', 1.0)
        validated_data['tiempo_estimado_minutos'] = validated_data.get('tiempo_estimado_minutos', 60)

        return Ruta.objects.create(**validated_data)

    @staticmethod
    def create_puntos(ruta, puntos_data):
        for punto_data in puntos_data:
            interes_data = punto_data.pop('interes', None)
            punto = Punto.objects.create(ruta=ruta, **punto_data)
            if interes_data:
                PuntoInteres.objects.create(punto=punto, **interes_data)


class RutaCompartidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RutaCompartida
        fields = ['ruta', 'usuario']

    def validate(self, data):
        ruta = data.get('ruta')
        usuario = data.get('usuario')

        if ruta.usuario == usuario:
            raise serializers.ValidationError("No puedes compartir la ruta contigo mismo.")

        if RutaCompartida.objects.filter(ruta=ruta, usuario=usuario).exists():
            raise serializers.ValidationError("La ruta ya ha sido compartida con este usuario.")

        return data
