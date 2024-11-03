from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers

from trek.fields import Base64ImageField

User = get_user_model()


class ImageMixin:
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['imagen_perfil'] = instance.imagen_perfil_url
        return representation


class UsuarioSerializer(ImageMixin, serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(max_length=30, required=False)
    last_name = serializers.CharField(max_length=30, required=False)
    biografia = serializers.CharField(required=False, allow_blank=True)
    imagen_perfil = Base64ImageField(required=False, allow_null=True)

    def validate_username(self, value):
        user = self.instance
        queryset = User.objects.filter(username=value)
        if user:
            queryset = queryset.exclude(id=user.id)
        if queryset.exists():
            raise serializers.ValidationError('Este nombre de usuario ya está en uso.')
        return value

    def validate_email(self, value):
        user = self.instance
        queryset = User.objects.filter(email=value)
        if user:
            queryset = queryset.exclude(id=user.id)
        if queryset.exists():
            raise serializers.ValidationError('Este correo electrónico ya está en uso.')
        return value

    def validate_password(self, value):
        user = self.instance
        try:
            validate_password(value, user=user)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages[0])
        return value

    def create(self, validated_data):
        return User.objects.create_user(
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
        model = User
        fields = ['id', 'username', 'fullname', 'imagen_perfil']
