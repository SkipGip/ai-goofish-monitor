import asyncio
from unittest.mock import patch, MagicMock
import pytest
from src.infrastructure.external.notification_clients.smtp_client import SmtpClient
from src.services.notification_config_service import prepare_notification_settings_update, build_notification_settings_response, prepare_notification_test_settings
from src.infrastructure.config.settings import NotificationSettings


def configured():
    return NotificationSettings.model_construct(smtp_host="smtp.example.com", smtp_port="465", smtp_security="ssl", smtp_username="sender@example.com", smtp_password="secret", smtp_from="sender@example.com", smtp_to="recipient@example.com")


def test_smtp_sends_recommendation_over_tls():
    client = SmtpClient(configured())
    with patch("smtplib.SMTP_SSL") as connect:
        connection = connect.return_value.__enter__.return_value
        connection.send_message.return_value = {}
        assert asyncio.run(client.send({"商品标题": "完整主机", "当前售价": "4200", "商品链接": "https://www.goofish.com/item?id=1"}, "配置合理"))
        connection.login.assert_called_once_with("sender@example.com", "secret")
        mail = connection.send_message.call_args.args[0]
        assert "完整主机" in mail.get_content()
        assert "4200" in mail.get_content()
        assert "配置合理" in mail.get_content()
        assert connect.call_args.kwargs["context"].check_hostname


def test_password_is_masked_and_preserved_when_omitted():
    settings = configured()
    assert build_notification_settings_response(settings)["SMTP_PASSWORD"] == ""
    assert build_notification_settings_response(settings)["SMTP_PASSWORD_SET"] is True
    _, _, updated = prepare_notification_settings_update({"SMTP_TO": "other@example.com"}, settings)
    assert updated.smtp_password == "secret"
    assert "smtp" in build_notification_settings_response(updated)["CONFIGURED_CHANNELS"]
    isolated = prepare_notification_test_settings({}, settings, channel="ntfy")
    assert not isolated.smtp_host


def test_bad_port_and_header_injection_rejected():
    for patch_value in ({"SMTP_PORT": "99999"}, {"SMTP_TO": "x@example.com\nBcc: leak@example.com"}):
        with pytest.raises(ValueError):
            prepare_notification_settings_update(patch_value, configured())


def test_starttls_and_redacted_failure():
    settings = configured()
    settings.smtp_security = "starttls"
    settings.smtp_port = "587"
    with patch("smtplib.SMTP") as connect:
        connection = connect.return_value.__enter__.return_value
        connection.login.side_effect = RuntimeError("secret")
        with pytest.raises(RuntimeError, match="SMTP.*RuntimeError") as error:
            asyncio.run(SmtpClient(settings).send({}, "test"))
        assert "secret" not in str(error.value)
        connection.starttls.assert_called_once()
