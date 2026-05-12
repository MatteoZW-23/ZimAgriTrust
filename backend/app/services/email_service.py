"""Email service.

Implements spec §3.10 email channel (functions 278-287) and §3.11 #297
(receipt via email). Designed as a dual-provider abstraction so we are not
locked to SendGrid or AWS SES. A console fallback is used in development.

Templates are sourced from `app.services.notifications.registry.TEMPLATES`,
keyed by spec ID, ensuring traceability. HTML bodies live in
`app/templates/email/*.html` (Jinja2).
"""
from __future__ import annotations

import base64
import logging
import smtplib
from dataclasses import dataclass
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from app.core.config import settings
from app.services.notifications.registry import (
    NotificationChannel,
    NotificationTemplate,
    get_template,
    get_templates_by_channel,
)

logger = logging.getLogger(__name__)

try:
    from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape
except ImportError:  # pragma: no cover - jinja2 should be installed; fail soft
    Environment = None  # type: ignore
    FileSystemLoader = None  # type: ignore
    select_autoescape = None  # type: ignore
    TemplateNotFound = Exception  # type: ignore


@dataclass
class EmailAttachment:
    filename: str
    content: bytes
    mime_type: str = "application/pdf"

    def to_b64(self) -> str:
        return base64.b64encode(self.content).decode("ascii")


@dataclass
class EmailMessage:
    to: str
    subject: str
    html_body: str
    text_body: Optional[str] = None
    attachments: List[EmailAttachment] = None  # type: ignore[assignment]
    spec_id: Optional[int] = None
    template_key: Optional[str] = None

    def __post_init__(self) -> None:
        if self.attachments is None:
            self.attachments = []


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------
class _Provider:
    name = "base"

    def send(self, msg: EmailMessage) -> bool:  # pragma: no cover
        raise NotImplementedError


class _ConsoleProvider(_Provider):
    """Logs the email instead of sending — used in development & tests."""

    name = "console"

    def send(self, msg: EmailMessage) -> bool:
        logger.info(
            "[email:console] to=%s subject=%s spec_id=%s template=%s attachments=%d",
            msg.to, msg.subject, msg.spec_id, msg.template_key, len(msg.attachments),
        )
        # In dev we also emit the body so devs can inspect.
        logger.debug("[email:console] body=\n%s", msg.html_body)
        return True


class _SendGridProvider(_Provider):
    name = "sendgrid"

    def send(self, msg: EmailMessage) -> bool:
        if not settings.SENDGRID_API_KEY:
            logger.error("SendGrid configured but SENDGRID_API_KEY is empty")
            return False
        try:
            import httpx  # SendGrid v3 REST API

            payload: Dict[str, Any] = {
                "personalizations": [{"to": [{"email": msg.to}]}],
                "from": {
                    "email": settings.EMAIL_FROM_ADDRESS,
                    "name": settings.EMAIL_FROM_NAME,
                },
                "reply_to": {"email": settings.EMAIL_REPLY_TO},
                "subject": msg.subject,
                "content": [
                    {"type": "text/plain", "value": msg.text_body or _strip_html(msg.html_body)},
                    {"type": "text/html", "value": msg.html_body},
                ],
            }
            if msg.attachments:
                payload["attachments"] = [
                    {
                        "content": a.to_b64(),
                        "type": a.mime_type,
                        "filename": a.filename,
                        "disposition": "attachment",
                    }
                    for a in msg.attachments
                ]
            r = httpx.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={"Authorization": f"Bearer {settings.SENDGRID_API_KEY}"},
                json=payload,
                timeout=10.0,
            )
            ok = 200 <= r.status_code < 300
            if not ok:
                logger.error("SendGrid send failed: %s %s", r.status_code, r.text[:500])
            return ok
        except Exception as e:  # pragma: no cover
            logger.exception("SendGrid send raised: %s", e)
            return False


class _SESProvider(_Provider):
    name = "ses"

    def send(self, msg: EmailMessage) -> bool:
        try:
            import boto3  # type: ignore
            from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
        except ImportError:
            logger.error("AWS SES selected but boto3 not installed")
            return False

        client = boto3.client(
            "ses",
            region_name=settings.AWS_SES_REGION,
            aws_access_key_id=settings.AWS_SES_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SES_SECRET_ACCESS_KEY or None,
        )

        # If attachments, must use raw email
        if msg.attachments:
            mime = _build_mime(msg)
            try:
                client.send_raw_email(
                    Source=f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>",
                    Destinations=[msg.to],
                    RawMessage={"Data": mime.as_string()},
                )
                return True
            except (BotoCoreError, ClientError) as e:
                logger.error("SES raw send failed: %s", e)
                return False
        try:
            client.send_email(
                Source=f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>",
                Destination={"ToAddresses": [msg.to]},
                Message={
                    "Subject": {"Data": msg.subject, "Charset": "UTF-8"},
                    "Body": {
                        "Html": {"Data": msg.html_body, "Charset": "UTF-8"},
                        "Text": {"Data": msg.text_body or _strip_html(msg.html_body), "Charset": "UTF-8"},
                    },
                },
                ReplyToAddresses=[settings.EMAIL_REPLY_TO],
            )
            return True
        except (BotoCoreError, ClientError) as e:
            logger.error("SES send failed: %s", e)
            return False


class _SMTPProvider(_Provider):
    name = "smtp"

    def send(self, msg: EmailMessage) -> bool:
        if not settings.SMTP_HOST:
            logger.error("SMTP provider selected but SMTP_HOST is empty")
            return False
        try:
            mime = _build_mime(msg)
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as s:
                if settings.SMTP_USE_TLS:
                    s.starttls()
                if settings.SMTP_USER:
                    s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                s.sendmail(settings.EMAIL_FROM_ADDRESS, [msg.to], mime.as_string())
            return True
        except Exception as e:
            logger.exception("SMTP send failed: %s", e)
            return False


def _build_mime(msg: EmailMessage) -> MIMEMultipart:
    mime = MIMEMultipart("mixed")
    mime["Subject"] = msg.subject
    mime["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>"
    mime["To"] = msg.to
    mime["Reply-To"] = settings.EMAIL_REPLY_TO

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(msg.text_body or _strip_html(msg.html_body), "plain", "utf-8"))
    alt.attach(MIMEText(msg.html_body, "html", "utf-8"))
    mime.attach(alt)

    for a in msg.attachments:
        part = MIMEApplication(a.content, Name=a.filename)
        part["Content-Disposition"] = f"attachment; filename=\"{a.filename}\""
        mime.attach(part)
    return mime


def _strip_html(html: str) -> str:
    """Minimal HTML→text fallback when caller didn't supply text_body."""
    import re

    text = re.sub(r"<\s*br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------
class EmailService:
    def __init__(self) -> None:
        self._provider = self._build_provider()
        self._jinja = self._build_jinja()

    @staticmethod
    def _build_provider() -> _Provider:
        choice = (settings.EMAIL_PROVIDER or "console").lower()
        if choice == "sendgrid":
            return _SendGridProvider()
        if choice == "ses":
            return _SESProvider()
        if choice == "smtp":
            return _SMTPProvider()
        return _ConsoleProvider()

    @staticmethod
    def _build_jinja():
        if Environment is None:
            return None
        template_dir = Path(settings.EMAIL_TEMPLATE_DIR)
        if not template_dir.exists():
            # Try resolving relative to backend/ working dir
            alt = Path("backend") / template_dir
            if alt.exists():
                template_dir = alt
        return Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def send_template(
        self,
        template_key_or_spec_id: str | int,
        to: str,
        context: Dict[str, Any],
        attachments: Optional[Iterable[EmailAttachment]] = None,
    ) -> bool:
        """Render the registered template and send.

        Spec compliance: every email send MUST go through this method so
        that every notification is traceable to a §3.10 function ID.
        """
        tpl = get_template(template_key_or_spec_id)
        if tpl.channel is not NotificationChannel.EMAIL:
            raise ValueError(f"Template {tpl.key} is not an email template (channel={tpl.channel})")

        missing = [k for k in tpl.required_context if k not in context]
        if missing:
            raise ValueError(
                f"Email template {tpl.key} (spec #{tpl.spec_id}) missing context keys: {missing}"
            )

        subject = (tpl.subject_template or "ZimAgriTrust").format(**context)
        html_body = self._render_html(tpl, context)

        msg = EmailMessage(
            to=to,
            subject=subject,
            html_body=html_body,
            attachments=list(attachments or []),
            spec_id=tpl.spec_id,
            template_key=tpl.key,
        )
        ok = self._provider.send(msg)
        logger.info(
            "email.sent provider=%s spec_id=%d template=%s to=%s ok=%s",
            self._provider.name, tpl.spec_id, tpl.key, _mask_email(to), ok,
        )
        return ok

    def _render_html(self, tpl: NotificationTemplate, context: Dict[str, Any]) -> str:
        # `body_template` holds the template filename for email templates.
        if self._jinja is not None:
            try:
                rendered = self._jinja.get_template(tpl.body_template).render(**context)
                return rendered
            except TemplateNotFound:
                logger.warning(
                    "Jinja template %s not found, falling back to plain layout", tpl.body_template
                )
        # Fallback when jinja is absent or template file is missing.
        return self._fallback_html(tpl, context)

    @staticmethod
    def _fallback_html(tpl: NotificationTemplate, context: Dict[str, Any]) -> str:
        body_lines = "<br/>".join(f"<b>{k}</b>: {v}" for k, v in context.items())
        return (
            "<html><body style='font-family:Arial,sans-serif;padding:24px;'>"
            f"<h2>ZimAgriTrust — {tpl.name}</h2>"
            f"<p>{body_lines}</p>"
            "<hr/><small>If you did not expect this email, contact support@zimagritrust.co.zw.</small>"
            "</body></html>"
        )

    def list_templates(self) -> List[Tuple[int, str]]:
        return [(t.spec_id, t.key) for t in get_templates_by_channel(NotificationChannel.EMAIL)]


def _mask_email(addr: str) -> str:
    if "@" not in addr:
        return "***"
    name, domain = addr.split("@", 1)
    if len(name) <= 2:
        return f"{'*' * len(name)}@{domain}"
    return f"{name[0]}***{name[-1]}@{domain}"


# Singleton
email_service = EmailService()
