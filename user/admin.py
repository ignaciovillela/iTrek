from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.html import format_html

from .models import Usuario

if admin.site.is_registered(Group):
    admin.site.unregister(Group)

@admin.register(Usuario)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'imagen_perfil_thumbnail', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    readonly_fields = ('imagen_perfil_large',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información personal', {'fields': ('first_name', 'last_name', 'email', 'biografia', 'imagen_perfil', 'imagen_perfil_large')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Fechas importantes', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'first_name', 'last_name'),
        }),
    )

    list_editable = ('is_staff',)

    default_image_url = '/media/imagenes_perfil/default_user_3.jpg'

    def imagen_perfil_thumbnail(self, obj):
        if obj.imagen_perfil:
            return format_html('<img src="{}" width="30" height="30" style="border-radius:50%;" />', obj.imagen_perfil.url)
        return format_html('<img src="{}" width="30" height="30" style="border-radius:50%;" />', self.default_image_url)

    imagen_perfil_thumbnail.short_description = 'Imagen'

    def imagen_perfil_large(self, obj):
        if obj.imagen_perfil:
            return format_html('<img src="{}" width="150" height="150" style="border-radius:50%;" />', obj.imagen_perfil.url)
        return format_html('<img src="{}" width="150" height="150" style="border-radius:50%;" />', self.default_image_url)

    imagen_perfil_large.short_description = 'Imagen de perfil grande'
