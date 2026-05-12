"""Notification subsystem.

Source of truth for the 43 notification templates required by the canonical
ZimAgriTrust spec (functions 245-287). All channel services (sms, whatsapp,
email) must source their templates from `registry.TEMPLATES` so each notification
is traceable to a spec function ID.
"""
from app.services.notifications.registry import (
    TEMPLATES,
    NotificationChannel,
    NotificationTemplate,
    get_template,
    get_templates_by_channel,
)

__all__ = [
    "TEMPLATES",
    "NotificationChannel",
    "NotificationTemplate",
    "get_template",
    "get_templates_by_channel",
]
