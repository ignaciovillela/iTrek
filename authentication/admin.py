from django.contrib import admin
from django.contrib.auth.models import Group

# Desregistrar el modelo Group del admin
admin.site.unregister(Group)
