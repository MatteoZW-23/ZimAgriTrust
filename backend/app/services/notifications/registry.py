"""Canonical notification template registry.

Maps every spec function in §3.10 of `docs/SYSTEM_SPECIFICATION.md` to a
single source-of-truth template definition.

Spec ranges:
- SMS:      245-262 (18 templates)
- WhatsApp: 263-277 (15 templates)
- Email:    278-287 (10 templates)
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class NotificationChannel(str, enum.Enum):
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"
    EMAIL = "EMAIL"


@dataclass(frozen=True)
class NotificationTemplate:
    """A single notification template traceable to a spec function ID."""

    spec_id: int
    """Function ID from `docs/SYSTEM_SPECIFICATION.md` §3.10."""

    key: str
    """Stable string key used by services (e.g. `sms.otp`)."""

    channel: NotificationChannel
    name: str
    body_template: str
    """Body string with `{placeholder}` slots; rendered via str.format(**ctx)."""

    subject_template: Optional[str] = None
    """Only used by EMAIL channel."""

    required_context: List[str] = field(default_factory=list)
    """Names of placeholders the caller must provide."""

    has_attachment: bool = False
    has_buttons: bool = False
    has_image: bool = False


# ---------------------------------------------------------------------------
# SMS templates  (spec 245-262)
# ---------------------------------------------------------------------------
_SMS: List[NotificationTemplate] = [
    NotificationTemplate(245, "sms.otp", NotificationChannel.SMS,
        "OTP verification",
        "ZimAgriTrust: Your verification code is {code}. Valid for 5 minutes. Do not share.",
        required_context=["code"]),
    NotificationTemplate(246, "sms.welcome", NotificationChannel.SMS,
        "Welcome message",
        "Welcome to ZimAgriTrust, {name}! Dial *123# or visit zimagritrust.co.zw to get started.",
        required_context=["name"]),
    NotificationTemplate(247, "sms.id_approved", NotificationChannel.SMS,
        "ID approved",
        "Hi {name}, your ID has been approved. Trust score +15. Welcome aboard!",
        required_context=["name"]),
    NotificationTemplate(248, "sms.id_rejected", NotificationChannel.SMS,
        "ID rejected",
        "Hi {name}, your ID submission was rejected. Reason: {reason}. Please resubmit.",
        required_context=["name", "reason"]),
    NotificationTemplate(249, "sms.id_resubmit", NotificationChannel.SMS,
        "ID resubmission request",
        "Hi {name}, please resubmit a clearer photo of your ID ({slot}). Open the app to retry.",
        required_context=["name", "slot"]),
    NotificationTemplate(250, "sms.offer_received", NotificationChannel.SMS,
        "Offer received (farmer)",
        "New offer on your {crop} listing: ${price}/kg for {qty}kg from {buyer}. Reply to view.",
        required_context=["crop", "price", "qty", "buyer"]),
    NotificationTemplate(251, "sms.offer_accepted", NotificationChannel.SMS,
        "Offer accepted (buyer)",
        "Your offer on {crop} ({qty}kg @ ${price}) was ACCEPTED. Pay into escrow within 24h to secure.",
        required_context=["crop", "qty", "price"]),
    NotificationTemplate(252, "sms.offer_rejected", NotificationChannel.SMS,
        "Offer rejected (buyer)",
        "Your offer on {crop} was rejected. Browse other listings at zimagritrust.co.zw.",
        required_context=["crop"]),
    NotificationTemplate(253, "sms.payment_confirmation", NotificationChannel.SMS,
        "Payment confirmation",
        "Payment of ${amount} {currency} received for order {order_ref}. Held in escrow.",
        required_context=["amount", "currency", "order_ref"]),
    NotificationTemplate(254, "sms.delivery_arranged", NotificationChannel.SMS,
        "Delivery arranged",
        "Delivery scheduled for {date}. Driver {driver} will collect. Order {order_ref}.",
        required_context=["date", "driver", "order_ref"]),
    NotificationTemplate(255, "sms.delivery_reminder", NotificationChannel.SMS,
        "Delivery reminder",
        "Reminder: delivery for order {order_ref} scheduled tomorrow. Ensure goods are ready.",
        required_context=["order_ref"]),
    NotificationTemplate(256, "sms.delivery_confirmed", NotificationChannel.SMS,
        "Delivery confirmed",
        "Delivery confirmed for order {order_ref}. Funds will be released to you within 24h.",
        required_context=["order_ref"]),
    NotificationTemplate(257, "sms.payment_released", NotificationChannel.SMS,
        "Payment released",
        "${amount} {currency} released to your wallet for order {order_ref}. Withdraw via *123#.",
        required_context=["amount", "currency", "order_ref"]),
    NotificationTemplate(258, "sms.dispute_opened", NotificationChannel.SMS,
        "Dispute opened",
        "A dispute has been opened on order {order_ref}. An agent will contact you within 24h.",
        required_context=["order_ref"]),
    NotificationTemplate(259, "sms.dispute_resolved", NotificationChannel.SMS,
        "Dispute resolved",
        "Dispute on order {order_ref} resolved: {resolution}. View details in app.",
        required_context=["order_ref", "resolution"]),
    NotificationTemplate(260, "sms.agent_assigned", NotificationChannel.SMS,
        "Agent assigned",
        "Agent {agent_name} has been assigned to your case ({case_ref}). Phone: {agent_phone}.",
        required_context=["agent_name", "case_ref", "agent_phone"]),
    NotificationTemplate(261, "sms.withdrawal_complete", NotificationChannel.SMS,
        "Withdrawal complete",
        "Withdrawal of ${amount} {currency} to {method} ({masked}) is complete. Ref: {tx_ref}.",
        required_context=["amount", "currency", "method", "masked", "tx_ref"]),
    NotificationTemplate(262, "sms.low_balance", NotificationChannel.SMS,
        "Low balance alert",
        "Your wallet balance is low: ${balance} {currency}. Top up via *123# > 6.",
        required_context=["balance", "currency"]),
]


# ---------------------------------------------------------------------------
# WhatsApp templates  (spec 263-277)
# ---------------------------------------------------------------------------
_WHATSAPP: List[NotificationTemplate] = [
    NotificationTemplate(263, "whatsapp.offer_received", NotificationChannel.WHATSAPP,
        "Offer received (rich with buttons)",
        "🌾 *New offer received!*\n\nCrop: {crop}\nQuantity: {qty}kg\nPrice: ${price}/kg\nBuyer: {buyer} (Trust: {buyer_trust}/100)\n\nTotal: *${total}*",
        required_context=["crop", "qty", "price", "buyer", "buyer_trust", "total"],
        has_buttons=True),
    NotificationTemplate(264, "whatsapp.offer_accepted", NotificationChannel.WHATSAPP,
        "Offer accepted (with payment link)",
        "✅ Your offer on *{crop}* was accepted!\n\nPay into escrow to secure: {payment_link}\n\nDeadline: {deadline}",
        required_context=["crop", "payment_link", "deadline"],
        has_buttons=True),
    NotificationTemplate(265, "whatsapp.payment_confirmation", NotificationChannel.WHATSAPP,
        "Payment confirmation (with receipt)",
        "💰 Payment of *${amount} {currency}* received.\n\nOrder: {order_ref}\nFunds held in escrow until delivery confirmed.",
        required_context=["amount", "currency", "order_ref"],
        has_attachment=True),
    NotificationTemplate(266, "whatsapp.delivery_tracking", NotificationChannel.WHATSAPP,
        "Delivery tracking (live location)",
        "🚚 Driver {driver} is en route.\nETA: *{eta}*\nVehicle: {vehicle}\n\nLive location updates below.",
        required_context=["driver", "eta", "vehicle"],
        has_image=True),
    NotificationTemplate(267, "whatsapp.delivery_confirmed", NotificationChannel.WHATSAPP,
        "Delivery confirmed (with photo)",
        "📦 Delivery confirmed for order *{order_ref}* at {time}.\n\nProof of delivery attached.",
        required_context=["order_ref", "time"],
        has_image=True),
    NotificationTemplate(268, "whatsapp.payment_released", NotificationChannel.WHATSAPP,
        "Payment released (with receipt PDF)",
        "🎉 *${amount} {currency}* released to your wallet!\n\nOrder: {order_ref}\nReceipt PDF attached.",
        required_context=["amount", "currency", "order_ref"],
        has_attachment=True),
    NotificationTemplate(269, "whatsapp.dispute_opened", NotificationChannel.WHATSAPP,
        "Dispute opened (with evidence upload)",
        "⚠️ Dispute opened on order *{order_ref}*.\n\nReason: {reason}\n\nUpload evidence (photos / video) by replying to this message.",
        required_context=["order_ref", "reason"],
        has_buttons=True),
    NotificationTemplate(270, "whatsapp.dispute_update", NotificationChannel.WHATSAPP,
        "Dispute update (with agent contact)",
        "🔄 Update on dispute *{case_ref}*:\n\n{update}\n\nAgent: {agent_name} ({agent_phone})",
        required_context=["case_ref", "update", "agent_name", "agent_phone"]),
    NotificationTemplate(271, "whatsapp.dispute_resolved", NotificationChannel.WHATSAPP,
        "Dispute resolved (with summary)",
        "✅ Dispute *{case_ref}* resolved.\n\nDecision: {decision}\nRefund / Release: ${amount} {currency}\nSummary attached.",
        required_context=["case_ref", "decision", "amount", "currency"],
        has_attachment=True),
    NotificationTemplate(272, "whatsapp.agent_assignment", NotificationChannel.WHATSAPP,
        "Agent assignment (with task details)",
        "📋 New task assigned: *{task_type}*\n\nLocation: {location}\nDeadline: {deadline}\nFee: ${fee}\n\nReply ACCEPT or REJECT.",
        required_context=["task_type", "location", "deadline", "fee"],
        has_buttons=True),
    NotificationTemplate(273, "whatsapp.verification_report", NotificationChannel.WHATSAPP,
        "Verification report (with photo gallery)",
        "🌾 Verification report for listing {listing_ref}\n\nResult: *{result}*\nGrade: {grade}\nPhotos attached.",
        required_context=["listing_ref", "result", "grade"],
        has_image=True),
    NotificationTemplate(274, "whatsapp.price_alert", NotificationChannel.WHATSAPP,
        "Price alert (with chart image)",
        "📈 Price alert: *{crop}* is now *${price}/kg* in {region} (was ${prev_price}).\n\nTrend chart attached.",
        required_context=["crop", "price", "region", "prev_price"],
        has_image=True),
    NotificationTemplate(275, "whatsapp.weather_alert", NotificationChannel.WHATSAPP,
        "Weather alert (with warning)",
        "🌧️ Weather alert for {region}: *{event}*\n\nExpected: {forecast}\nAdvice: {advice}",
        required_context=["region", "event", "forecast", "advice"]),
    NotificationTemplate(276, "whatsapp.loan_approval", NotificationChannel.WHATSAPP,
        "Loan approval (with amount and terms)",
        "🏦 *Loan approved!*\n\nAmount: ${amount} {currency}\nInterest: {interest}% p.a.\nTerm: {months} months\nMonthly: ${monthly}\n\nDisbursement to wallet within 24h.",
        required_context=["amount", "currency", "interest", "months", "monthly"]),
    NotificationTemplate(277, "whatsapp.loan_reminder", NotificationChannel.WHATSAPP,
        "Loan reminder (with repayment link)",
        "💳 Loan repayment of *${amount} {currency}* due on {due_date}.\n\nPay now: {repay_link}",
        required_context=["amount", "currency", "due_date", "repay_link"],
        has_buttons=True),
]


# ---------------------------------------------------------------------------
# Email templates  (spec 278-287)
# ---------------------------------------------------------------------------
_EMAIL: List[NotificationTemplate] = [
    NotificationTemplate(278, "email.welcome", NotificationChannel.EMAIL,
        "Welcome email (with getting started guide)",
        "welcome.html",  # Jinja template filename
        subject_template="Welcome to ZimAgriTrust, {name}!",
        required_context=["name", "role"]),
    NotificationTemplate(279, "email.weekly_summary", NotificationChannel.EMAIL,
        "Weekly summary (with PDF report)",
        "weekly_summary.html",
        subject_template="Your weekly ZimAgriTrust summary ({week_start} – {week_end})",
        required_context=["name", "week_start", "week_end", "stats"],
        has_attachment=True),
    NotificationTemplate(280, "email.monthly_statement", NotificationChannel.EMAIL,
        "Monthly statement (with PDF statement)",
        "monthly_statement.html",
        subject_template="ZimAgriTrust statement for {month}",
        required_context=["name", "month", "summary"],
        has_attachment=True),
    NotificationTemplate(281, "email.transaction_receipt", NotificationChannel.EMAIL,
        "Transaction receipt (with PDF receipt)",
        "transaction_receipt.html",
        subject_template="Receipt for order {order_ref}",
        required_context=["name", "order_ref", "amount", "currency", "date"],
        has_attachment=True),
    NotificationTemplate(282, "email.dispute_resolution", NotificationChannel.EMAIL,
        "Dispute resolution (with PDF report)",
        "dispute_resolution.html",
        subject_template="Resolution of dispute {case_ref}",
        required_context=["name", "case_ref", "decision", "amount", "currency"],
        has_attachment=True),
    NotificationTemplate(283, "email.agent_certification", NotificationChannel.EMAIL,
        "Agent certification (with PDF certificate)",
        "agent_certification.html",
        subject_template="Congratulations — you are now a certified ZimAgriTrust agent",
        required_context=["name", "agent_code", "certified_at"],
        has_attachment=True),
    NotificationTemplate(284, "email.training_reminder", NotificationChannel.EMAIL,
        "Agent training reminder (with training link)",
        "training_reminder.html",
        subject_template="Continue your ZimAgriTrust agent training",
        required_context=["name", "next_module", "training_link"]),
    NotificationTemplate(285, "email.driver_approval", NotificationChannel.EMAIL,
        "Driver approval (with welcome guide)",
        "driver_approval.html",
        subject_template="You're approved to drive for ZimAgriTrust",
        required_context=["name", "tier"]),
    NotificationTemplate(286, "email.platform_update", NotificationChannel.EMAIL,
        "Platform update (with release notes)",
        "platform_update.html",
        subject_template="What's new on ZimAgriTrust ({version})",
        required_context=["version", "highlights"]),
    NotificationTemplate(287, "email.security_alert", NotificationChannel.EMAIL,
        "Security alert (with reset link)",
        "security_alert.html",
        subject_template="Important security alert on your ZimAgriTrust account",
        required_context=["name", "event", "ip", "reset_link"]),
]


_ALL = _SMS + _WHATSAPP + _EMAIL


def get_template(key_or_spec_id: str | int) -> NotificationTemplate:
    """Lookup by string key or integer spec ID."""
    if isinstance(key_or_spec_id, int):
        tpl = TEMPLATES_BY_SPEC_ID.get(key_or_spec_id)
    else:
        tpl = TEMPLATES.get(key_or_spec_id)
    if tpl is None:
        raise KeyError(f"Unknown notification template: {key_or_spec_id!r}")
    return tpl


def get_templates_by_channel(channel: NotificationChannel) -> List[NotificationTemplate]:
    return [t for t in _ALL if t.channel == channel]


# ---------------------------------------------------------------------------
# Supplier Notification Templates  (spec 288-310)
# ---------------------------------------------------------------------------
_SUPPLIER_SMS: List[NotificationTemplate] = [
    NotificationTemplate(288, "sms.supplier_application_received", NotificationChannel.SMS,
        "Supplier application received",
        "ZimAgriTrust: Your supplier application for {business_name} has been received. We'll review it within 48h.",
        required_context=["business_name"]),
    NotificationTemplate(289, "sms.supplier_approved", NotificationChannel.SMS,
        "Supplier application approved",
        "ZimAgriTrust: Congratulations! Your supplier account for {business_name} is APPROVED. Login to start selling.",
        required_context=["business_name"]),
    NotificationTemplate(290, "sms.supplier_rejected", NotificationChannel.SMS,
        "Supplier application rejected",
        "ZimAgriTrust: Your supplier application was rejected. Reason: {reason}. Contact support for assistance.",
        required_context=["reason"]),
    NotificationTemplate(291, "sms.supplier_suspended", NotificationChannel.SMS,
        "Supplier account suspended",
        "ZimAgriTrust: Your supplier account has been SUSPENDED. Reason: {reason}. Contact support to appeal.",
        required_context=["reason"]),
    NotificationTemplate(292, "sms.supplier_order_received", NotificationChannel.SMS,
        "New supplier order received",
        "ZimAgriTrust: New order #{order_number} for {product_name} (Qty: {quantity}). Confirm within 24h.",
        required_context=["order_number", "product_name", "quantity"]),
    NotificationTemplate(293, "sms.supplier_order_shipped", NotificationChannel.SMS,
        "Supplier order shipped",
        "ZimAgriTrust: Order #{order_number} has been shipped. Tracking: {tracking_number}. ETA: {eta}.",
        required_context=["order_number", "tracking_number", "eta"]),
    NotificationTemplate(294, "sms.supplier_order_delivered", NotificationChannel.SMS,
        "Supplier order delivered",
        "ZimAgriTrust: Order #{order_number} delivered. Payment will be released to your wallet within 24h.",
        required_context=["order_number"]),
    NotificationTemplate(295, "sms.supplier_payment_received", NotificationChannel.SMS,
        "Supplier payment received",
        "ZimAgriTrust: ${amount} received for order #{order_number}. Available for withdrawal.",
        required_context=["amount", "order_number"]),
    NotificationTemplate(296, "sms.supplier_low_stock", NotificationChannel.SMS,
        "Low stock alert",
        "ZimAgriTrust: {product_name} is low on stock ({remaining}). Restock to avoid missed sales.",
        required_context=["product_name", "remaining"]),
    NotificationTemplate(297, "sms.supplier_withdrawal_complete", NotificationChannel.SMS,
        "Supplier withdrawal complete",
        "ZimAgriTrust: Withdrawal of ${amount} to {account} complete. Ref: {ref}.",
        required_context=["amount", "account", "ref"]),
]

_SUPPLIER_WHATSAPP: List[NotificationTemplate] = [
    NotificationTemplate(298, "whatsapp.supplier_application_received", NotificationChannel.WHATSAPP,
        "Supplier application received (rich)",
        "📦 *Supplier Application Received*\n\nBusiness: {business_name}\nApplication ID: {app_id}\n\nWe'll review within 48h. Track status in supplier portal.",
        required_context=["business_name", "app_id"]),
    NotificationTemplate(299, "whatsapp.supplier_approved", NotificationChannel.WHATSAPP,
        "Supplier application approved (with portal link)",
        "✅ *Supplier Account Approved*\n\nWelcome to ZimAgriTrust, {business_name}!\n\nYour supplier portal is ready:\n🔗 {portal_link}\n\nStart listing your products today!",
        required_context=["business_name", "portal_link"],
        has_buttons=True),
    NotificationTemplate(300, "whatsapp.supplier_order_received", NotificationChannel.WHATSAPP,
        "New supplier order (with details)",
        "🛒 *New Order Received*\n\nOrder #{order_number}\nProduct: {product_name}\nQty: {quantity}\nTotal: ${total}\n\nConfirm shipment in supplier portal.",
        required_context=["order_number", "product_name", "quantity", "total"],
        has_buttons=True),
    NotificationTemplate(301, "whatsapp.supplier_order_shipped", NotificationChannel.WHATSAPP,
        "Order shipped (with tracking)",
        "🚚 *Order Shipped*\n\nOrder #{order_number}\nCarrier: {carrier}\nTracking: {tracking_number}\nETA: {eta}\n\nTrack live: {tracking_link}",
        required_context=["order_number", "carrier", "tracking_number", "eta", "tracking_link"]),
    NotificationTemplate(302, "whatsapp.supplier_payment_received", NotificationChannel.WHATSAPP,
        "Payment received (with receipt)",
        "💰 *Payment Received*\n\nOrder #{order_number}\nAmount: ${amount}\n\nFunds available for withdrawal. Receipt attached.",
        required_context=["order_number", "amount"],
        has_attachment=True),
    NotificationTemplate(303, "whatsapp.supplier_monthly_summary", NotificationChannel.WHATSAPP,
        "Monthly supplier summary",
        "📊 *Monthly Supplier Summary*\n\nPeriod: {month}\nTotal Sales: ${sales}\nOrders: {orders}\nTop Product: {top_product}\n\nView full report in portal.",
        required_context=["month", "sales", "orders", "top_product"]),
]

_SUPPLIER_EMAIL: List[NotificationTemplate] = [
    NotificationTemplate(304, "email.supplier_application_received", NotificationChannel.EMAIL,
        "Supplier application received email",
        "supplier_application_received.html",
        subject_template="Application Received - {business_name}",
        required_context=["business_name", "app_id"]),
    NotificationTemplate(305, "email.supplier_approved", NotificationChannel.EMAIL,
        "Supplier approval email (with onboarding guide)",
        "supplier_approved.html",
        subject_template="Welcome to ZimAgriTrust Supplier Portal - {business_name}",
        required_context=["business_name", "portal_link"],
        has_attachment=True),
    NotificationTemplate(306, "email.supplier_order_confirmation", NotificationChannel.EMAIL,
        "Supplier order confirmation",
        "supplier_order_confirmation.html",
        subject_template="New Order #{order_number} - {business_name}",
        required_context=["order_number", "business_name", "items", "total"],
        has_attachment=True),
    NotificationTemplate(307, "email.supplier_payment_statement", NotificationChannel.EMAIL,
        "Monthly payment statement",
        "supplier_payment_statement.html",
        subject_template="Payment Statement - {month} - {business_name}",
        required_context=["month", "business_name", "summary"],
        has_attachment=True),
    NotificationTemplate(308, "email.supplier_performance_report", NotificationChannel.EMAIL,
        "Supplier performance report",
        "supplier_performance_report.html",
        subject_template="Performance Report - {business_name}",
        required_context=["business_name", "metrics", "recommendations"],
        has_attachment=True),
]

_ALL = _SMS + _WHATSAPP + _EMAIL + _SUPPLIER_SMS + _SUPPLIER_WHATSAPP + _SUPPLIER_EMAIL

TEMPLATES: Dict[str, NotificationTemplate] = {tpl.key: tpl for tpl in _ALL}
TEMPLATES_BY_SPEC_ID: Dict[int, NotificationTemplate] = {tpl.spec_id: tpl for tpl in _ALL}

# Sanity check on import: spec mandates 18+15+10 = 43 templates + 21 supplier templates = 64 total
assert len(_SMS) == 18, f"SMS templates: expected 18 (spec 245-262), got {len(_SMS)}"
assert len(_WHATSAPP) == 15, f"WhatsApp templates: expected 15 (spec 263-277), got {len(_WHATSAPP)}"
assert len(_EMAIL) == 10, f"Email templates: expected 10 (spec 278-287), got {len(_EMAIL)}"
assert len(_SUPPLIER_SMS) == 10, f"Supplier SMS templates: expected 10 (spec 288-297), got {len(_SUPPLIER_SMS)}"
assert len(_SUPPLIER_WHATSAPP) == 6, f"Supplier WhatsApp templates: expected 6 (spec 298-303), got {len(_SUPPLIER_WHATSAPP)}"
assert len(_SUPPLIER_EMAIL) == 5, f"Supplier Email templates: expected 5 (spec 304-308), got {len(_SUPPLIER_EMAIL)}"
assert len(_ALL) == 64, f"Total templates: expected 64, got {len(_ALL)}"
