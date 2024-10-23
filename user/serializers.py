from rest_framework import serializers

from trek.fields import Base64ImageField
from .models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    imagen_perfil = Base64ImageField(required=False, allow_null=True)
    date_joined = serializers.ReadOnlyField()

    class Meta:
        model = Usuario
        fields = [
            'username', 'password', 'email', 'first_name', 'last_name',
            'biografia', 'imagen_perfil', 'date_joined'
        ]

    def create(self, validated_data):
        return Usuario.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            biografia=validated_data.get('biografia', ''),
            imagen_perfil=validated_data.get('imagen_perfil', None)
        )

    def update(self, instance, validated_data):
        # Actualiza los campos permitidos
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.biografia = validated_data.get('biografia', instance.biografia)

        # Solo actualiza la contraseña si se incluye en los datos
        password = validated_data.get('password')
        if password:
            instance.set_password(password)

        # Actualiza la imagen si se proporciona
        instance.imagen_perfil = validated_data.get('imagen_perfil', instance.imagen_perfil)

        instance.save()
        return instance

    def to_representation(self, instance):
        """Modifica la representación del campo imagen_perfil para entregar la URL."""
        representation = super().to_representation(instance)
        if instance.imagen_perfil:
            representation['imagen_perfil'] = instance.imagen_perfil.url
        return representation


class SearchUsuarioSerializer(serializers.ModelSerializer):
    fullname = serializers.CharField()

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'fullname', 'imagen_perfil']
