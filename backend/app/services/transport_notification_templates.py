"""
ZimAgritrust Transport Notification Templates
Defines notification templates for all transport-related events.
Supports push, SMS, email, and in-app notifications.
"""
from __future__ import annotations

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# ── Notification Template Registry ───────────────────────────────────────────

TRANSPORT_NOTIFICATION_TEMPLATES = {
    # Transport Request Events
    "TRANSPORT_REQUEST_SUBMITTED": {
        "title": "Transport Request Submitted",
        "push_body": "Your transport request has been submitted successfully.",
        "sms_body": "ZimAgritrust: Transport request submitted for order #{order_number}. Status: {status}.",
        "email_subject": "Transport Request Submitted - Order #{order_number}",
        "email_body": """
        <h2>Transport Request Submitted</h2>
        <p>Your transport request for order #{order_number} has been submitted successfully.</p>
        <p><strong>Mode:</strong> {mode}</p>
        <p><strong>Status:</strong> {status}</p>
        <p><strong>Transport Fee:</strong> ${transport_fee:.2f}</p>
        <p>You will be notified once a driver is assigned.</p>
        """,
        "data_keys": ["order_number", "mode", "status", "transport_fee"],
    },
    
    "TRANSPORT_FEE_ASSIGNED": {
        "title": "Transport Fee Assigned",
        "push_body": "You will pay ${transport_fee:.2f} for transport.",
        "sms_body": "ZimAgritrust: Transport fee of ${transport_fee:.2f} assigned for order #{order_number}.",
        "email_subject": "Transport Fee Assigned - Order #{order_number}",
        "email_body": """
        <h2>Transport Fee Assigned</h2>
        <p>A transport fee of <strong>${transport_fee:.2f}</strong> has been assigned to your order #{order_number}.</p>
        <p><strong>Payer:</strong> {payer}</p>
        <p><strong>Mode:</strong> {mode}</p>
        """,
        "data_keys": ["order_number", "transport_fee", "payer", "mode"],
    },
    
    "TRANSPORT_FEE_DEDUCTED": {
        "title": "Transport Fee Deducted",
        "push_body": "${transport_fee:.2f} will be deducted from your settlement for transport.",
        "sms_body": "ZimAgritrust: Transport fee of ${transport_fee:.2f} will be deducted from your settlement for order #{order_number}.",
        "email_subject": "Transport Fee Deduction - Order #{order_number}",
        "email_body": """
        <h2>Transport Fee Deduction</h2>
        <p>A transport fee of <strong>${transport_fee:.2f}</strong> will be deducted from your settlement for order #{order_number}.</p>
        <p>This fee covers the platform delivery service.</p>
        """,
        "data_keys": ["order_number", "transport_fee"],
    },
    
    # Negotiation Events
    "NEGOTIATION_STARTED": {
        "title": "Transport Negotiation Started",
        "push_body": "Negotiation for transport fee (${initial_quote:.2f}) has started. You have 72 hours to agree.",
        "sms_body": "ZimAgritrust: Transport negotiation started for order #{order_number}. Initial quote: ${initial_quote:.2f}. 72 hours to agree.",
        "email_subject": "Transport Negotiation Started - Order #{order_number}",
        "email_body": """
        <h2>Transport Negotiation Started</h2>
        <p>A transport fee negotiation has been initiated for order #{order_number}.</p>
        <p><strong>Initial Quote:</strong> ${initial_quote:.2f}</p>
        <p><strong>Expires At:</strong> {expires_at}</p>
        <p>Please respond within 72 hours to avoid automatic assignment.</p>
        """,
        "data_keys": ["order_number", "initial_quote", "expires_at"],
    },
    
    "NEGOTIATION_OFFER_RECEIVED": {
        "title": "New Transport Offer Received",
        "push_body": "New offer: ${amount:.2f} paid by {payer}",
        "sms_body": "ZimAgritrust: New transport offer received for order #{order_number}. ${amount:.2f} paid by {payer}.",
        "email_subject": "New Transport Offer - Order #{order_number}",
        "email_body": """
        <h2>New Transport Offer Received</h2>
        <p>A new offer has been submitted for order #{order_number}.</p>
        <p><strong>Amount:</strong> ${amount:.2f}</p>
        <p><strong>Payer:</strong> {payer}</p>
        {split_details}
        <p>Please review and respond in the app.</p>
        """,
        "data_keys": ["order_number", "amount", "payer", "split_details"],
    },
    
    "NEGOTIATION_ACCEPTED": {
        "title": "Transport Agreement Reached",
        "push_body": "Transport fee agreement reached. Driver will be assigned shortly.",
        "sms_body": "ZimAgritrust: Transport agreement reached for order #{order_number}. Amount: ${amount:.2f}. Driver assignment pending.",
        "email_subject": "Transport Agreement Reached - Order #{order_number}",
        "email_body": """
        <h2>Transport Agreement Reached</h2>
        <p>Both parties have agreed on the transport fee for order #{order_number}.</p>
        <p><strong>Final Amount:</strong> ${amount:.2f}</p>
        <p><strong>Payer:</strong> {payer}</p>
        <p>A driver will be assigned shortly. You will receive a notification with driver details.</p>
        """,
        "data_keys": ["order_number", "amount", "payer"],
    },
    
    "NEGOTIATION_EXPIRED": {
        "title": "Negotiation Expired",
        "push_body": "Transport negotiation has expired. Decision deferred to counterparty.",
        "sms_body": "ZimAgritrust: Transport negotiation expired for order #{order_number}. Decision deferred to counterparty.",
        "email_subject": "Negotiation Expired - Order #{order_number}",
        "email_body": """
        <h2>Negotiation Expired</h2>
        <p>The transport fee negotiation for order #{order_number} has expired (72-hour window).</p>
        <p>The decision has been deferred to the counterparty, who has 48 hours to choose a transport method.</p>
        """,
        "data_keys": ["order_number"],
    },
    
    # Driver Assignment Events
    "DRIVER_ASSIGNED": {
        "title": "Driver Assigned",
        "push_body": "Driver {driver_name} assigned to your order. Vehicle: {vehicle_registration}",
        "sms_body": "ZimAgritrust: Driver {driver_name} ({vehicle_registration}) assigned to order #{order_number}. ETA: {eta_minutes} min.",
        "email_subject": "Driver Assigned - Order #{order_number}",
        "email_body": """
        <h2>Driver Assigned</h2>
        <p>A driver has been assigned to your order #{order_number}.</p>
        <p><strong>Driver Name:</strong> {driver_name}</p>
        <p><strong>Vehicle:</strong> {vehicle_type} ({vehicle_registration})</p>
        <p><strong>Estimated Arrival:</strong> {eta_minutes} minutes</p>
        <p><strong>Contact:</strong> {driver_phone}</p>
        """,
        "data_keys": ["order_number", "driver_name", "vehicle_type", "vehicle_registration", "eta_minutes", "driver_phone"],
    },
    
    "DRIVER_EN_ROUTE": {
        "title": "Driver En Route",
        "push_body": "Driver is on the way to pickup location.",
        "sms_body": "ZimAgritrust: Driver en route to pickup for order #{order_number}. ETA: {eta_minutes} min.",
        "email_subject": "Driver En Route - Order #{order_number}",
        "email_body": """
        <h2>Driver En Route</h2>
        <p>Your driver is now en route to the pickup location for order #{order_number}.</p>
        <p><strong>Estimated Arrival at Pickup:</strong> {eta_minutes} minutes</p>
        """,
        "data_keys": ["order_number", "eta_minutes"],
    },
    
    # Delivery Events
    "PICKUP_CONFIRMED": {
        "title": "Pickup Confirmed",
        "push_body": "Goods have been picked up. Driver is now in transit.",
        "sms_body": "ZimAgritrust: Pickup confirmed for order #{order_number}. Driver in transit. ETA: {eta_minutes} min.",
        "email_subject": "Pickup Confirmed - Order #{order_number}",
        "email_body": """
        <h2>Pickup Confirmed</h2>
        <p>The goods for order #{order_number} have been picked up by the driver.</p>
        <p><strong>Pickup Code:</strong> {pickup_code}</p>
        <p><strong>Estimated Delivery:</strong> {eta_minutes} minutes</p>
        <p>You will receive a delivery code when the goods arrive.</p>
        """,
        "data_keys": ["order_number", "pickup_code", "eta_minutes"],
    },
    
    "DELIVERY_ARRIVED": {
        "title": "Driver Arrived at Delivery Location",
        "push_body": "Driver has arrived at delivery location. Delivery code: {delivery_code}",
        "sms_body": "ZimAgritrust: Driver arrived for order #{order_number}. Delivery code: {delivery_code}",
        "email_subject": "Driver Arrived - Order #{order_number}",
        "email_body": """
        <h2>Driver Arrived at Delivery Location</h2>
        <p>The driver has arrived at the delivery location for order #{order_number}.</p>
        <p><strong>Delivery Code:</strong> {delivery_code}</p>
        <p>Please provide this code to the driver to complete the delivery.</p>
        """,
        "data_keys": ["order_number", "delivery_code"],
    },
    
    "DELIVERY_CONFIRMED": {
        "title": "Delivery Confirmed",
        "push_body": "Goods have been delivered successfully.",
        "sms_body": "ZimAgritrust: Delivery confirmed for order #{order_number}. Goods delivered successfully.",
        "email_subject": "Delivery Confirmed - Order #{order_number}",
        "email_body": """
        <h2>Delivery Confirmed</h2>
        <p>The goods for order #{order_number} have been delivered successfully.</p>
        <p><strong>Delivered At:</strong> {delivered_at}</p>
        <p><strong>Proof of Delivery:</strong> Available in the app</p>
        <p>Please inspect the goods and confirm receipt within 24 hours.</p>
        """,
        "data_keys": ["order_number", "delivered_at"],
    },
    
    # Payment Events
    "TRANSPORT_PAYMENT_HELD": {
        "title": "Transport Payment Held in Escrow",
        "push_body": "${amount:.2f} held in escrow for transport.",
        "sms_body": "ZimAgritrust: ${amount:.2f} held in escrow for transport on order #{order_number}.",
        "email_subject": "Payment Held in Escrow - Order #{order_number}",
        "email_body": """
        <h2>Payment Held in Escrow</h2>
        <p>A payment of <strong>${amount:.2f}</strong> has been held in escrow for transport on order #{order_number}.</p>
        <p>This will be released to the driver upon successful delivery confirmation.</p>
        """,
        "data_keys": ["order_number", "amount"],
    },
    
    "TRANSPORT_PAYMENT_RELEASED": {
        "title": "Transport Payment Released",
        "push_body": "${amount:.2f} released to driver.",
        "sms_body": "ZimAgritrust: ${amount:.2f} released to driver for order #{order_number}.",
        "email_subject": "Payment Released - Order #{order_number}",
        "email_body": """
        <h2>Payment Released</h2>
        <p>A payment of <strong>${amount:.2f}</strong> has been released to the driver for order #{order_number}.</p>
        <p><strong>Released At:</strong> {released_at}</p>
        """,
        "data_keys": ["order_number", "amount", "released_at"],
    },
    
    "DRIVER_PAYOUT_PROCESSED": {
        "title": "Driver Payout Processed",
        "push_body": "${amount:.2f} added to your wallet for completed delivery.",
        "sms_body": "ZimAgritrust: ${amount:.2f} added to your wallet for order #{order_number}.",
        "email_subject": "Payout Processed - Order #{order_number}",
        "email_body": """
        <h2>Driver Payout Processed</h2>
        <p>A payout of <strong>${amount:.2f}</strong> has been added to your wallet for the completed delivery of order #{order_number}.</p>
        <p><strong>Processed At:</strong> {processed_at}</p>
        """,
        "data_keys": ["order_number", "amount", "processed_at"],
    },
    
    # Self Pickup/Delivery Events
    "PICKUP_CODE_GENERATED": {
        "title": "Pickup Code Generated",
        "push_body": "Your pickup code is: {pickup_code}. Show this to the farmer.",
        "sms_body": "ZimAgritrust: Pickup code for order #{order_number}: {pickup_code}. Show this to the farmer.",
        "email_subject": "Pickup Code Generated - Order #{order_number}",
        "email_body": """
        <h2>Pickup Code Generated</h2>
        <p>Your pickup code for order #{order_number} is: <strong>{pickup_code}</strong></p>
        <p>Please show this code to the farmer when collecting your goods.</p>
        """,
        "data_keys": ["order_number", "pickup_code"],
    },
    
    "BUYER_SELF_PICKUP_SCHEDULED": {
        "title": "Buyer Self Pickup Scheduled",
        "push_body": "The buyer will collect the order directly.",
        "sms_body": "ZimAgritrust: Buyer self-pickup scheduled for order #{order_number}. Pickup code: {pickup_code}",
        "email_subject": "Self Pickup Scheduled - Order #{order_number}",
        "email_body": """
        <h2>Buyer Self Pickup Scheduled</h2>
        <p>The buyer will collect the order #{order_number} directly.</p>
        <p><strong>Pickup Code:</strong> {pickup_code}</p>
        <p>Please verify this code before releasing the goods.</p>
        """,
        "data_keys": ["order_number", "pickup_code"],
    },
    
    # Deferral Events
    "TRANSPORT_DECISION_REQUIRED": {
        "title": "Transport Decision Required",
        "push_body": "The other party deferred the transport decision. You have 48 hours to choose.",
        "sms_body": "ZimAgritrust: Transport decision required for order #{order_number}. You have 48 hours to choose a method.",
        "email_subject": "Transport Decision Required - Order #{order_number}",
        "email_body": """
        <h2>Transport Decision Required</h2>
        <p>The other party has deferred the transport decision for order #{order_number}.</p>
        <p><strong>Decision Deadline:</strong> {decision_deadline}</p>
        <p>Please choose a transport method within 48 hours to avoid automatic assignment.</p>
        """,
        "data_keys": ["order_number", "decision_deadline"],
    },
    
    "TRANSPORT_RESPONSIBILITY_ASSIGNED": {
        "title": "Transport Responsibility Assigned",
        "push_body": "The decision deadline has passed. Platform delivery has been assigned to you.",
        "sms_body": "ZimAgritrust: Transport responsibility assigned to you for order #{order_number}. Platform delivery.",
        "email_subject": "Transport Responsibility Assigned - Order #{order_number}",
        "email_body": """
        <h2>Transport Responsibility Assigned</h2>
        <p>The decision deadline has passed for order #{order_number}.</p>
        <p>Platform delivery has been assigned to you. A driver will be assigned shortly.</p>
        """,
        "data_keys": ["order_number"],
    },
    
    # Error/Warning Events
    "DRIVER_ASSIGNMENT_FAILED": {
        "title": "Driver Assignment Failed",
        "push_body": "Unable to assign driver. Retrying or escalating to admin.",
        "sms_body": "ZimAgritrust: Driver assignment failed for order #{order_number}. Admin notified.",
        "email_subject": "Driver Assignment Failed - Order #{order_number}",
        "email_body": """
        <h2>Driver Assignment Failed</h2>
        <p>We were unable to assign a driver to order #{order_number}.</p>
        <p>Our team has been notified and will resolve this issue shortly.</p>
        <p>We apologize for the inconvenience.</p>
        """,
        "data_keys": ["order_number"],
    },
    
    "DELIVERY_DELAYED": {
        "title": "Delivery Delayed",
        "push_body": "Delivery delayed. New ETA: {new_eta}. Reason: {reason}",
        "sms_body": "ZimAgritrust: Delivery delayed for order #{order_number}. New ETA: {new_eta}. Reason: {reason}",
        "email_subject": "Delivery Delayed - Order #{order_number}",
        "email_body": """
        <h2>Delivery Delayed</h2>
        <p>The delivery for order #{order_number} has been delayed.</p>
        <p><strong>New ETA:</strong> {new_eta}</p>
        <p><strong>Reason:</strong> {reason}</p>
        <p>We apologize for the inconvenience.</p>
        """,
        "data_keys": ["order_number", "new_eta", "reason"],
    },
}


# ── Notification Template Service ───────────────────────────────────────────

class TransportNotificationTemplateService:
    """Service for formatting transport notification templates"""
    
    @staticmethod
    def get_template(notification_type: str) -> Optional[Dict[str, Any]]:
        """Get notification template by type"""
        return TRANSPORT_NOTIFICATION_TEMPLATES.get(notification_type)
    
    @staticmethod
    def format_template(
        notification_type: str,
        data: Dict[str, Any],
        channels: list[str] = None,
    ) -> Dict[str, Any]:
        """
        Format notification template with provided data.
        
        Returns formatted content for requested channels.
        """
        template = TRANSPORT_NOTIFICATION_TEMPLATES.get(notification_type)
        if not template:
            logger.warning(f"Template not found for notification type: {notification_type}")
            return {}
        
        if channels is None:
            channels = ["push", "sms"]
        
        formatted = {
            "type": notification_type,
            "title": template["title"],
        }
        
        # Format each requested channel
        if "push" in channels:
            formatted["push_body"] = template["push_body"].format(**data)
        
        if "sms" in channels:
            formatted["sms_body"] = template["sms_body"].format(**data)
        
        if "email" in channels:
            formatted["email_subject"] = template["email_subject"].format(**data)
            formatted["email_body"] = template["email_body"].format(**data)
        
        # Include data for in-app notifications
        formatted["data"] = data
        
        return formatted
    
    @staticmethod
    def validate_template_data(
        notification_type: str,
        data: Dict[str, Any],
    ) -> tuple[bool, list[str]]:
        """
        Validate that all required data keys are present for a template.
        
        Returns (is_valid, missing_keys)
        """
        template = TRANSPORT_NOTIFICATION_TEMPLATES.get(notification_type)
        if not template:
            return False, []
        
        required_keys = template.get("data_keys", [])
        missing_keys = [key for key in required_keys if key not in data]
        
        return len(missing_keys) == 0, missing_keys
    
    @staticmethod
    def get_available_templates() -> list[str]:
        """Get list of all available notification template types"""
        return list(TRANSPORT_NOTIFICATION_TEMPLATES.keys())


# ── Helper Functions ─────────────────────────────────────────────────────────

def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amount"""
    return f"{currency} {amount:.2f}"


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M") -> str:
    """Format datetime"""
    return dt.strftime(format_str)


def format_minutes_to_hours(minutes: int) -> str:
    """Format minutes to hours and minutes"""
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"
