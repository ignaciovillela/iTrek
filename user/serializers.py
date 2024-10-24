from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers

from trek.fields import Base64ImageField
from .models import Usuario

User = get_user_model()


class ImageMixin:
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.imagen_perfil:
            representation['imagen_perfil'] = instance.imagen_perfil.url
        else:
            representation['imagen_perfil'] = f'{settings.STATIC_URL}default_profile.jpg'
        return representation


class UsuarioSerializer(ImageMixin, serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(max_length=30, required=False)
    last_name = serializers.CharField(max_length=30, required=False)
    biografia = serializers.CharField(required=False, allow_blank=True)
    imagen_perfil = Base64ImageField(required=False, allow_null=True)

    def validate_unique(self, *args, validation_error=None, **kwargs):
        if User.objects.filter(*args, **kwargs).exists():
            raise serializers.ValidationError(validation_error)

    def validate(self, data):
        user = self.instance

        id_filter = {}
        if user:
            id_filter['id'] = user.id
        email = data.get('email')
        self.validate_unique(email=email, validation_error={'email': 'Este correo electrónico ya está en uso.'})
        username = data.get('username')
        self.validate_unique(username=username, validation_error={'username': 'Este nombre de usuario ya está en uso.'})

        return data

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
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.biografia = validated_data.get('biografia', instance.biografia)
        instance.imagen_perfil = validated_data.get('imagen_perfil', instance.imagen_perfil)

        instance.save()
        return instance


class SearchUsuarioSerializer(ImageMixin, serializers.ModelSerializer):
    fullname = serializers.CharField()

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'fullname', 'imagen_perfil']
