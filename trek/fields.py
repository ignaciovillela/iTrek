import base64
import imghdr
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):
        """
        Convierte una imagen codificada en base64 en un archivo válido.
        Verifica el formato y lo decodifica antes de almacenarlo.
        """
        decoded_file = None

        if isinstance(data, str):
            # Comprobamos si el string tiene la estructura de base64
            if 'data:' in data and ';base64,' in data:
                header, data = data.split(';base64,')

            try:
                # Decodificamos el archivo de base64
                decoded_file = base64.b64decode(data)
            except (TypeError, ValueError):
                self.fail('invalid_image')

            # Generamos un nombre de archivo único
            file_name = str(uuid.uuid4())[:12]

            # Detecta la extensión del archivo (puede ser jpg, png, etc.)
            file_extension = self.get_file_extension(decoded_file)

            if not file_extension:
                self.fail('invalid_image')

            complete_file_name = f"{file_name}.{file_extension}"

            # Crea un archivo en memoria usando el contenido decodificado
            data = ContentFile(decoded_file, name=complete_file_name)

        else:
            self.fail('invalid_type')

        return super(Base64ImageField, self).to_internal_value(data)

    def get_file_extension(self, decoded_file):
        """
        Detecta la extensión del archivo usando la cabecera del archivo.
        Usamos 'imghdr' para identificar el tipo de imagen.
        """
        file_type = imghdr.what(None, decoded_file)
        extension_map = {
            'jpeg': 'jpg',
            'png': 'png',
            'gif': 'gif'
        }
        return extension_map.get(file_type)
