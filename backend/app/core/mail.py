from fastapi_mail import ConnectionConfig
from app.core.config import settings

# Gmail uses implicit SSL on 465 and STARTTLS on 587.
_use_ssl = settings.MAIL_PORT == 465

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=not _use_ssl,
    MAIL_SSL_TLS=_use_ssl,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)
