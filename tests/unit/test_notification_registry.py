"""Unit tests for the notification template registry.

These tests guarantee the registry stays spec-compliant: 18 SMS + 15 WhatsApp
+ 10 email = 43 templates, with every spec ID in 245-287 represented exactly
once, and every required-context placeholder appearing in the body template.
"""
import string

import pytest

from backend.app.services.notifications.registry import (
    TEMPLATES,
    TEMPLATES_BY_SPEC_ID,
    NotificationChannel,
    get_template,
    get_templates_by_channel,
)


def test_total_count_matches_spec():
    assert len(TEMPLATES) == 64


def test_unique_spec_ids_cover_245_to_287():
    spec_ids = sorted(TEMPLATES_BY_SPEC_ID.keys())
    assert spec_ids == list(range(245, 309))


def test_channel_split_matches_spec():
    sms = get_templates_by_channel(NotificationChannel.SMS)
    whatsapp = get_templates_by_channel(NotificationChannel.WHATSAPP)
    email = get_templates_by_channel(NotificationChannel.EMAIL)
    assert (len(sms), len(whatsapp), len(email)) == (28, 21, 15)
    # SMS: spec 245-262 + 288-297, WhatsApp: 263-277 + 298-303, Email: 278-287 + 304-308
    assert {t.spec_id for t in sms} == set(range(245, 263)).union(set(range(288, 298)))
    assert {t.spec_id for t in whatsapp} == set(range(263, 278)).union(set(range(298, 304)))
    assert {t.spec_id for t in email} == set(range(278, 288)).union(set(range(304, 309)))


def test_get_template_by_key_and_id_match():
    by_key = get_template("sms.otp")
    by_id = get_template(245)
    assert by_key is by_id
    assert by_key.spec_id == 245


def test_unknown_template_raises():
    with pytest.raises(KeyError):
        get_template("does.not.exist")
    with pytest.raises(KeyError):
        get_template(999)


def test_required_context_placeholders_are_present_in_body():
    """For SMS/WhatsApp templates the body uses str.format placeholders.
    Every required_context key must appear as a {placeholder} in body_template.
    Email templates store filenames, not formattable bodies.
    """
    formatter = string.Formatter()
    for tpl in TEMPLATES.values():
        if tpl.channel is NotificationChannel.EMAIL:
            continue
        placeholders = {
            field for _, field, _, _ in formatter.parse(tpl.body_template) if field
        }
        missing = set(tpl.required_context) - placeholders
        assert not missing, (
            f"Template {tpl.key} (spec #{tpl.spec_id}) missing placeholders {missing} "
            f"in body_template"
        )


def test_email_templates_have_subject_and_filename():
    for tpl in get_templates_by_channel(NotificationChannel.EMAIL):
        assert tpl.subject_template, f"{tpl.key} missing subject_template"
        assert tpl.body_template.endswith(".html"), (
            f"{tpl.key} body_template should be a Jinja filename, got {tpl.body_template!r}"
        )
