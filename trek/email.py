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



def get_email_body(user, email_type: EmailType, request=None, **context):
    template_name = f'{email_type.name.lower()}.html'

    c = {
        'user': user,
    }
    if request is not None:
        base_url = request.build_absolute_uri('/')[:-1].strip('/')
        c['base_url'] = base_url
    c.update(context)

    return render_to_string(template_name, c)


def send_mail(user, email_type: EmailType, request=None, **context):
    body = get_email_body(user, email_type, request=request, **context)

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


def send_confirmation_email(user, request=None):
    signer = TimestampSigner()
    token = signer.sign(user.email)
    encoded_token = urlsafe_base64_encode(force_bytes(token))
    confirm_url = reverse('users-confirm-email', args=[encoded_token])

    send_mail(user, EmailType.CONFIRM_EMAIL, request, confirm_url=confirm_url)


def send_welcome_email(user, request=None):
    send_mail(user, EmailType.WELCOME, request)
