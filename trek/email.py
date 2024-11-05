from concurrent.futures import ThreadPoolExecutor
from enum import Enum

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.signing import TimestampSigner
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


class EmailType(Enum):
    CONFIRM_EMAIL = "Confirma tu dirección de correo en iTrek"
    WELCOME = "Bienvenido a iTrek"
    PASSWORD_RESET = "Restablecimiento de contraseña"


executor = ThreadPoolExecutor(max_workers=5)


def send_mail(user, email_type, **context):
    template_name = f'{email_type.name.lower()}.html'

    context = {
        'user': user,
        **context,
    }
    body = render_to_string(template_name, context)

    mensaje = EmailMessage(
        subject=email_type.value,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )

    message_id = f"<{user.id}-{email_type.name.lower()}@itrek.com>"
    mensaje.extra_headers['Message-ID'] = message_id
    mensaje.extra_headers['References'] = message_id
    mensaje.content_subtype = 'html'

    executor.submit(mensaje.send)


def send_confirmation_email(user):
    signer = TimestampSigner()
    token = signer.sign(user.email)
    encoded_token = urlsafe_base64_encode(force_bytes(token))
    confirmation_url = reverse('users-confirm-email', args=[encoded_token])
    full_url = f'{settings.BASE_URL}{confirmation_url}'

    send_mail(user, EmailType.CONFIRM_EMAIL, confirm_url=full_url)


def send_welcome_email(user):
    send_mail(user, EmailType.WELCOME)
