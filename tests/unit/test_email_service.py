"""Smoke tests for the email service using the console provider.

These tests don't require any network or DB; they exercise template
selection, missing-context validation, and rendering path.
"""
import pytest

from backend.app.services.email_service import EmailService, _ConsoleProvider


def _force_console(monkeypatch):
    """Ensure tests run against the console provider regardless of env."""
    from backend.app.core import config as cfg

    monkeypatch.setattr(cfg.settings, "EMAIL_PROVIDER", "console", raising=False)


def test_send_template_console_ok(monkeypatch, caplog):
    _force_console(monkeypatch)
    svc = EmailService()
    assert isinstance(svc._provider, _ConsoleProvider)

    ok = svc.send_template(
        "email.welcome",
        to="alice@example.com",
        context={"name": "Alice", "role": "FARMER"},
    )
    assert ok is True


def test_send_template_missing_context_raises(monkeypatch):
    _force_console(monkeypatch)
    svc = EmailService()
    with pytest.raises(ValueError) as exc:
        svc.send_template("email.welcome", to="bob@example.com", context={})
    assert "missing context keys" in str(exc.value)


def test_send_template_rejects_non_email_channel(monkeypatch):
    _force_console(monkeypatch)
    svc = EmailService()
    with pytest.raises(ValueError) as exc:
        # sms.otp is a SMS template, not email
        svc.send_template("sms.otp", to="x@y.z", context={"code": "1234"})
    assert "not an email template" in str(exc.value)


def test_unknown_template_raises(monkeypatch):
    _force_console(monkeypatch)
    svc = EmailService()
    with pytest.raises(KeyError):
        svc.send_template("email.nope", to="x@y.z", context={})


def test_list_email_templates_returns_ten(monkeypatch):
    _force_console(monkeypatch)
    svc = EmailService()
    templates = svc.list_templates()
    assert len(templates) == 10
    spec_ids = [t[0] for t in templates]
    assert sorted(spec_ids) == list(range(278, 288))
