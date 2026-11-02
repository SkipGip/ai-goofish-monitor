"""SMTP recommendation delivery with verified TLS and redacted failures."""
import asyncio
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from .base import NotificationClient


class SmtpClient(NotificationClient):
    channel_key = "smtp"
    display_name = "SMTP 邮箱"

    def __init__(self, settings):
        super().__init__(enabled=bool(settings.smtp_host and settings.smtp_from and settings.smtp_to and settings.smtp_password), pcurl_to_mobile=settings.pcurl_to_mobile)
        self.settings = settings

    async def send(self, product_data, reason):
        message = self._build_message(product_data, reason)
        await asyncio.to_thread(self._send_sync, message)
        return True

    def _send_sync(self, message):
        settings = self.settings
        try:
            mail = EmailMessage()
            mail["Subject"] = message.notification_title.replace("\r", " ").replace("\n", " ")
            mail["From"] = settings.smtp_from
            mail["To"] = settings.smtp_to
            mail["Date"] = formatdate(localtime=True)
            mail["Message-ID"] = make_msgid()
            mail.set_content(message.title + "\n\n" + message.content)
            for filename, mime_type, data in getattr(message, "attachments", []):
                maintype, subtype = mime_type.split("/", 1)
                mail.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)
            security = settings.smtp_security or "ssl"
            if security not in {"ssl", "starttls"}:
                raise ValueError("Unsupported TLS mode")
            port = int(settings.smtp_port or (465 if security == "ssl" else 587))
            context = ssl.create_default_context()
            options = dict(host=settings.smtp_host, port=port, timeout=30)
            if security == "ssl":
                options["context"] = context
            transport = smtplib.SMTP_SSL if security == "ssl" else smtplib.SMTP
            with transport(**options) as connection:
                if security == "starttls":
                    connection.ehlo()
                    connection.starttls(context=context)
                    connection.ehlo()
                connection.login(settings.smtp_username or settings.smtp_from, settings.smtp_password)
                if connection.send_message(mail):
                    raise RuntimeError("Recipient refused")
        except Exception as exc:
            raise RuntimeError(f"SMTP 发送失败（{type(exc).__name__}），请检查邮箱配置与网络") from None
