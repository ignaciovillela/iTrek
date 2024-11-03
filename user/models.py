from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from user.managers import ActiveUserManager


class Usuario(AbstractUser):
    email = models.EmailField(unique=True)
    biografia = models.TextField(blank=True)
    imagen_perfil = models.ImageField(upload_to='imagenes_perfil/', blank=True, null=True)

    objects = ActiveUserManager()
    all_objects = models.Manager()

    def __str__(self):
        return self.username

    @property
    def imagen_perfil_url(self):
        if self.imagen_perfil:
            return self.imagen_perfil.url
        return f'{settings.STATIC_URL}default_profile.jpg'
