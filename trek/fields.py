import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):
        decoded_file = None

        if isinstance(data, str):
            if 'data:' in data and ';base64,' in data:
                _, data = data.split(';base64,')

            try:
                decoded_file = base64.b64decode(data)
            except (TypeError, ValueError):
                self.fail('invalid_image')

            file_name = str(uuid.uuid4())[:12]
            file_extension = 'jpg'

            complete_file_name = f"{file_name}.{file_extension}"

            data = ContentFile(decoded_file, name=complete_file_name)

        else:
            self.fail('invalid_type')

        return super(Base64ImageField, self).to_internal_value(data)
