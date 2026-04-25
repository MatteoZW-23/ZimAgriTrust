"""
AgriTrust SMS Service — AfricasTalking Integration
89 templates across 8 categories. Real API credentials are injected via env vars.
Simulates (logs) when SMS_API_KEY is not set.
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Low-level sender (AfricasTalking)
# ---------------------------------------------------------------------------

def _send_sms(phone: str, message: str) -> bool:
    """
    Send SMS via AfricasTalking (or any gateway that matches the env config).
    Falls back to simulation log when credentials are absent.
    """
    api_key = os.getenv("SMS_API_KEY")
    username = os.getenv("SMS_USERNAME", "sandbox")
    sender_id = os.getenv("SMS_SENDER_ID", "AgriTrust")

    if not api_key:
        logger.warning(f"[SMS-SIM] → {phone}: {message}")
        return False

    try:
        import africastalking  # type: ignore
        africastalking.initialize(username, api_key)
        sms = africastalking.SMS
        response = sms.send(message, [phone], sender_id)
        logger.info(f"[SMS] Sent to {phone}: {response}")
        return True
    except Exception as exc:
        logger.error(f"[SMS] Failed to send to {phone}: {exc}")
        return False


# ---------------------------------------------------------------------------
# PART 1 — VERIFICATION & ONBOARDING
# ---------------------------------------------------------------------------

def send_otp(phone: str, code: str) -> bool:
    """VERIFY_001 — OTP code"""
    return _send_sms(phone, f"AgriTrust: Your verification code is {code}. Valid for 5 minutes. Never share this code.")


def resend_otp(phone: str, code: str) -> bool:
    """VERIFY_002 — OTP resend"""
    return _send_sms(phone, f"AgriTrust: New verification code: {code}. Valid for 5 minutes.")


def notify_phone_verified(phone: str, score: int) -> bool:
    """VERIFY_003 — Verification success"""
    return _send_sms(phone, f"AgriTrust: \u2705 Phone verified successfully! Your trust score: {score}/100. Dial *123# to start trading.")


def notify_verification_failed(phone: str) -> bool:
    """VERIFY_004 — Verification failed"""
    return _send_sms(phone, "AgriTrust: \u274c Verification failed. Please try again or contact support.")


def notify_documents_received(phone: str) -> bool:
    """VERIFY_005 — Documents received"""
    return _send_sms(phone, "AgriTrust: \U0001f4c4 Your ID documents have been received. Review takes 24-48 hours.")


def notify_id_approved(phone: str, score: int) -> bool:
    """VERIFY_006 — ID approved"""
    return _send_sms(phone, f"AgriTrust: \u2705 Your identity has been verified! Trust score +15. New score: {score}/100.")


def notify_id_rejected(phone: str, reason: str) -> bool:
    """VERIFY_007 — ID rejected"""
    return _send_sms(phone, f"AgriTrust: \u274c Your ID was rejected. Reason: {reason}. Please upload a clearer photo via WhatsApp.")


def notify_farm_visit_scheduled(phone: str, agent_name: str, date: str, time: str) -> bool:
    """VERIFY_008 — Farm verification scheduled"""
    return _send_sms(phone, f"AgriTrust: \U0001f4cd Agent {agent_name} will visit your farm on {date} between {time}. Reply OK to confirm.")


def notify_farm_verified(phone: str, score: int) -> bool:
    """VERIFY_009 — Farm verified"""
    return _send_sms(phone, f"AgriTrust: \u2705 Your farm has been verified! Trust score +20. New score: {score}/100.")


# ---------------------------------------------------------------------------
# PART 2 — LISTING & OFFER
# ---------------------------------------------------------------------------

def notify_listing_created(phone: str, listing_id: str, quantity: int, crop: str, price: float) -> bool:
    """LIST_001 — Listing created"""
    return _send_sms(phone, f"AgriTrust: \u2705 Listing created! ID: {listing_id}. {quantity}kg {crop} at ${price}/kg. View offers via *123#.")


def notify_listing_expired(phone: str, listing_id: str) -> bool:
    """LIST_002 — Listing expired"""
    return _send_sms(phone, f"AgriTrust: \u23f0 Listing {listing_id} has expired. Repost via *123# to continue selling.")


def notify_listing_sold(phone: str, crop: str, txn_id: str) -> bool:
    """LIST_003 — Listing sold"""
    return _send_sms(phone, f"AgriTrust: \U0001f389 Your {crop} listing has been sold! Transaction #{txn_id}. Funds held in escrow.")


def notify_listing_edited(phone: str, listing_id: str, price: float) -> bool:
    """LIST_004 — Listing edited"""
    return _send_sms(phone, f"AgriTrust: \u270f\ufe0f Listing {listing_id} updated. New price: ${price}/kg.")


def notify_listing_deleted(phone: str, listing_id: str) -> bool:
    """LIST_005 — Listing deleted"""
    return _send_sms(phone, f"AgriTrust: \U0001f5d1\ufe0f Listing {listing_id} has been deleted.")


def notify_offer_received(phone: str, crop: str, price: float, quantity: int, total: float, offer_id: str) -> bool:
    """OFFER_001 — New offer received (farmer)"""
    return _send_sms(phone, f"AgriTrust: \U0001f514 New offer on {crop} listing! Buyer offers ${price}/kg for {quantity}kg. Total: ${total}. Reply ACCEPT {offer_id} or REJECT {offer_id}.")


def notify_offer_accepted_farmer(phone: str, txn_id: str) -> bool:
    """OFFER_002 — Offer accepted (farmer)"""
    return _send_sms(phone, f"AgriTrust: \u2705 You accepted the offer! Transaction #{txn_id} created. Buyer will arrange delivery.")


def notify_offer_rejected_farmer(phone: str, buyer_name: str) -> bool:
    """OFFER_003 — Offer rejected (farmer)"""
    return _send_sms(phone, f"AgriTrust: \u274c You rejected the offer from {buyer_name}.")


def notify_counter_offer_sent(phone: str, price: float) -> bool:
    """OFFER_004 — Counter offer sent"""
    return _send_sms(phone, f"AgriTrust: \U0001f4e4 Counter offer of ${price}/kg sent to buyer. Waiting for response.")


def notify_offer_submitted(phone: str, price: float, crop: str) -> bool:
    """OFFER_005 — Offer submitted (buyer)"""
    return _send_sms(phone, f"AgriTrust: \U0001f4e4 Your offer of ${price}/kg for {crop} has been sent to the seller.")


def notify_offer_accepted_buyer(phone: str, total: float, payment_link: str) -> bool:
    """OFFER_006 — Offer accepted (buyer)"""
    return _send_sms(phone, f"AgriTrust: \U0001f389 Your offer was accepted! Pay ${total} via *123# or link: {payment_link}.")


def notify_offer_rejected_buyer(phone: str, crop: str) -> bool:
    """OFFER_007 — Offer rejected (buyer)"""
    return _send_sms(phone, f"AgriTrust: \u274c Your offer for {crop} was rejected by the seller.")


def notify_counter_offer_received(phone: str, price: float, crop: str) -> bool:
    """OFFER_008 — Counter offer received (buyer)"""
    return _send_sms(phone, f"AgriTrust: \U0001f4e9 Seller counter-offered ${price}/kg for {crop}. Reply ACCEPT or COUNTER {{PRICE}}.")


# ---------------------------------------------------------------------------
# PART 3 — PAYMENT & ESCROW
# ---------------------------------------------------------------------------

def notify_payment_request(phone: str, txn_id: str, amount: float, payment_link: str) -> bool:
    """PAY_001 — Payment request"""
    return _send_sms(phone, f"AgriTrust: \U0001f4b3 Payment required for order #{txn_id}. Amount: ${amount}. Dial *123# or click: {payment_link}")


def notify_ecocash_instructions(phone: str, amount: float, code: str) -> bool:
    """PAY_002 — EcoCash payment instructions"""
    return _send_sms(phone, f"AgriTrust: To pay ${amount}: Dial *151# \u2192 Enter merchant {code} \u2192 Enter amount \u2192 Confirm.")


def notify_payment_received(phone: str, amount: float, txn_id: str) -> bool:
    """PAY_003 — Payment received"""
    return _send_sms(phone, f"AgriTrust: \u2705 Payment of ${amount} received for order #{txn_id}. Funds held in escrow. Seller notified.")


def notify_payment_failed(phone: str, amount: float, reason: str) -> bool:
    """PAY_004 — Payment failed"""
    return _send_sms(phone, f"AgriTrust: \u274c Payment of ${amount} failed. Reason: {reason}. Try again via *123#.")


def notify_escrow_held(phone: str, amount: float, txn_id: str) -> bool:
    """ESCROW_001 — Funds held in escrow"""
    return _send_sms(phone, f"AgriTrust: \U0001f512 ${amount} held in escrow for order #{txn_id}. Seller will prepare delivery.")


def notify_escrow_released(phone: str, amount: float, txn_id: str) -> bool:
    """ESCROW_002 — Payment released to seller"""
    return _send_sms(phone, f"AgriTrust: \U0001f4b0 ${amount} released to seller for order #{txn_id}. Transaction complete. Rate buyer via *123#.")


def notify_refund_issued(phone: str, amount: float, txn_id: str) -> bool:
    """ESCROW_003 — Refund issued"""
    return _send_sms(phone, f"AgriTrust: \u21a9\ufe0f ${amount} refunded to your wallet for order #{txn_id}. Check balance via *123#.")


def notify_partial_release(phone: str, amount: float, refund: float, txn_id: str) -> bool:
    """ESCROW_004 — Partial release"""
    return _send_sms(phone, f"AgriTrust: \u2696\ufe0f Partial release: ${amount} to seller, ${refund} refunded to buyer for order #{txn_id}.")


def notify_wallet_deposit(phone: str, amount: float, balance: float) -> bool:
    """WALLET_001 — Deposit confirmation"""
    return _send_sms(phone, f"AgriTrust: \u2705 ${amount} added to your wallet. New balance: ${balance}.")


def notify_wallet_withdrawal(phone: str, amount: float, method: str, ref: str, balance: float) -> bool:
    """WALLET_002 — Withdrawal confirmation"""
    return _send_sms(phone, f"AgriTrust: \U0001f4b8 ${amount} withdrawn to {method}. Reference: {ref}. New balance: ${balance}.")


def notify_low_balance(phone: str, balance: float) -> bool:
    """WALLET_003 — Low balance alert"""
    return _send_sms(phone, f"AgriTrust: \u26a0\ufe0f Your wallet balance is ${balance}. Add funds via *123# to continue trading.")


def notify_fee_deducted(phone: str, fee: float, txn_id: str) -> bool:
    """WALLET_004 — Platform fee deducted"""
    return _send_sms(phone, f"AgriTrust: \U0001f4ca Platform fee of ${fee} deducted from transaction #{txn_id}.")


# ---------------------------------------------------------------------------
# PART 4 — ORDER & DELIVERY
# ---------------------------------------------------------------------------

def notify_order_created(phone: str, txn_id: str, quantity: int, crop: str, seller_name: str, total: float) -> bool:
    """ORDER_001 — Order created"""
    return _send_sms(phone, f"AgriTrust: \U0001f4e6 Order #{txn_id} created. {quantity}kg {crop} from {seller_name}. Total: ${total}.")


def notify_order_status(phone: str, txn_id: str, status: str) -> bool:
    """ORDER_002 — Order status update"""
    return _send_sms(phone, f"AgriTrust: \U0001f4e6 Order #{txn_id} status: {status}. Dial *123# for details.")


def notify_order_completed(phone: str, txn_id: str) -> bool:
    """ORDER_003 — Order completed"""
    return _send_sms(phone, f"AgriTrust: \u2705 Order #{txn_id} completed. Rate your counterparty via *123#.")


def notify_order_cancelled(phone: str, txn_id: str, amount: float) -> bool:
    """ORDER_004 — Order cancelled"""
    return _send_sms(phone, f"AgriTrust: \u274c Order #{txn_id} cancelled. Refund of ${amount} processed.")


def notify_delivery_arranged(phone: str, txn_id: str, date: str, time: str) -> bool:
    """DELIVERY_001 — Delivery arranged"""
    return _send_sms(phone, f"AgriTrust: \U0001f69a Delivery arranged for order #{txn_id}. Expected: {date} between {time}.")


def notify_goods_dispatched(phone: str, txn_id: str, tracking: str) -> bool:
    """DELIVERY_002 — Goods dispatched"""
    return _send_sms(phone, f"AgriTrust: \U0001f4e4 Seller has dispatched your order #{txn_id}. Tracking: {tracking}")


def notify_delivery_confirm_buyer(phone: str, txn_id: str) -> bool:
    """DELIVERY_003 — Delivery confirmation request (buyer)"""
    return _send_sms(phone, f"AgriTrust: \U0001f4e6 Have you received order #{txn_id}? Reply YES to release payment to seller.")


def notify_delivery_confirm_seller(phone: str, txn_id: str) -> bool:
    """DELIVERY_004 — Delivery confirmation request (seller)"""
    return _send_sms(phone, f"AgriTrust: \U0001f4e6 Has buyer received order #{txn_id}? Reply YES to confirm delivery.")


def notify_delivery_confirmed(phone: str, txn_id: str) -> bool:
    """DELIVERY_005 — Delivery confirmed"""
    return _send_sms(phone, f"AgriTrust: \u2705 Delivery confirmed for order #{txn_id}. Payment will be released within 24 hours.")


def notify_rating_request(phone: str, counterparty: str, txn_id: str) -> bool:
    """RATING_001 — Rating request"""
    return _send_sms(phone, f"AgriTrust: \u2b50 Rate your experience with {counterparty} for order #{txn_id}. Reply 1-5 stars.")


def notify_rating_sent(phone: str, counterparty: str, score: int) -> bool:
    """RATING_002 — Rating received confirmation"""
    return _send_sms(phone, f"AgriTrust: \u2705 Thank you for rating! {counterparty} now has {score}/100 trust score.")


def notify_rating_received(phone: str, buyer_name: str, stars: int, txn_id: str, score: int) -> bool:
    """RATING_003 — New rating received"""
    return _send_sms(phone, f"AgriTrust: \u2b50 {buyer_name} rated you {stars} stars for order #{txn_id}. Trust score: {score}/100.")


# ---------------------------------------------------------------------------
# PART 5 — DISPUTE
# ---------------------------------------------------------------------------

def notify_dispute_opened(phone: str, dispute_id: str, txn_id: str, reason: str) -> bool:
    """DISPUTE_001 — Dispute opened"""
    return _send_sms(phone, f"AgriTrust: \u26a0\ufe0f Dispute #{dispute_id} opened on order #{txn_id}. Reason: {reason}. Agent assigned within 24 hours.")


def notify_evidence_request(phone: str, dispute_id: str) -> bool:
    """DISPUTE_002 — Evidence request"""
    return _send_sms(phone, f"AgriTrust: \U0001f4f8 Please send evidence for dispute #{dispute_id} via WhatsApp. Photos, receipts, or chat screenshots.")


def notify_evidence_received(phone: str, dispute_id: str) -> bool:
    """DISPUTE_003 — Evidence received"""
    return _send_sms(phone, f"AgriTrust: \u2705 Evidence received for dispute #{dispute_id}. Agent will review.")


def notify_dispute_agent_assigned(phone: str, agent_name: str, dispute_id: str) -> bool:
    """DISPUTE_004 — Agent assigned to dispute"""
    return _send_sms(phone, f"AgriTrust: \U0001f468\u200d\U0001f4bc Agent {agent_name} assigned to dispute #{dispute_id}. They will contact you within 24 hours.")


def notify_resolution_proposed(phone: str, dispute_id: str, resolution: str) -> bool:
    """DISPUTE_005 — Resolution proposed"""
    return _send_sms(phone, f"AgriTrust: \u2696\ufe0f Proposed resolution for dispute #{dispute_id}: {resolution}. Reply ACCEPT or APPEAL within 48 hours.")


def notify_resolution_accepted(phone: str, dispute_id: str) -> bool:
    """DISPUTE_006 — Resolution accepted"""
    return _send_sms(phone, f"AgriTrust: \u2705 You accepted the resolution for dispute #{dispute_id}. Case closed.")


def notify_resolution_rejected(phone: str) -> bool:
    """DISPUTE_007 — Resolution rejected"""
    return _send_sms(phone, "AgriTrust: \u274c You rejected the resolution. Admin will review within 24 hours.")


def notify_admin_decision(phone: str, dispute_id: str, decision: str, amount: float, action: str) -> bool:
    """DISPUTE_008 — Final admin decision"""
    return _send_sms(phone, f"AgriTrust: \U0001f451 Final decision on dispute #{dispute_id}: {decision}. ${amount} will be {action}.")


def notify_dispute_closed(phone: str, dispute_id: str, resolution: str) -> bool:
    """DISPUTE_009 — Dispute closed"""
    return _send_sms(phone, f"AgriTrust: \U0001f512 Dispute #{dispute_id} closed. Resolution: {resolution}.")


# ---------------------------------------------------------------------------
# PART 6 — AGENT
# ---------------------------------------------------------------------------

def notify_agent_new_task(phone: str, task_id: str, crop: str, quantity: int, location: str) -> bool:
    """AGENT_001 — New task assigned"""
    return _send_sms(phone, f"AgriTrust: \U0001f4cb New verification task #{task_id}. {crop}, {quantity}kg in {location}. Reply ACCEPT or REJECT.")


def notify_agent_task_accepted(phone: str, task_id: str, location: str) -> bool:
    """AGENT_002 — Task accepted"""
    return _send_sms(phone, f"AgriTrust: \u2705 Task #{task_id} accepted. Visit farmer at {location} within 24 hours.")


def notify_agent_task_rejected(phone: str, task_id: str) -> bool:
    """AGENT_003 — Task rejected"""
    return _send_sms(phone, f"AgriTrust: \u274c Task #{task_id} rejected. Reason recorded.")


def notify_agent_task_reminder(phone: str, task_id: str, hours: int, location: str) -> bool:
    """AGENT_004 — Task reminder"""
    return _send_sms(phone, f"AgriTrust: \u23f0 Reminder: Task #{task_id} due in {hours} hours. Location: {location}.")


def notify_agent_task_overdue(phone: str, task_id: str) -> bool:
    """AGENT_005 — Task overdue"""
    return _send_sms(phone, f"AgriTrust: \u26a0\ufe0f Task #{task_id} is overdue. Please complete or reassign.")


def notify_agent_verification_submitted(phone: str, task_id: str) -> bool:
    """AGENT_006 — Verification submitted"""
    return _send_sms(phone, f"AgriTrust: \U0001f4f8 Verification report for task #{task_id} submitted. Pending admin review.")


def notify_agent_verification_approved(phone: str, task_id: str, commission: float) -> bool:
    """AGENT_007 — Verification approved"""
    return _send_sms(phone, f"AgriTrust: \u2705 Verification #{task_id} approved. Commission: ${commission} added.")


def notify_agent_verification_rejected(phone: str, task_id: str, reason: str) -> bool:
    """AGENT_008 — Verification rejected"""
    return _send_sms(phone, f"AgriTrust: \u274c Verification #{task_id} rejected. Reason: {reason}. Please resubmit.")


def notify_agent_dispute_assigned(phone: str, dispute_id: str) -> bool:
    """AGENT_009 — Dispute assigned to agent"""
    return _send_sms(phone, f"AgriTrust: \u2696\ufe0f Dispute #{dispute_id} assigned to you. Review evidence and submit resolution.")


def notify_agent_investigation_note(phone: str, dispute_id: str) -> bool:
    """AGENT_010 — Investigation note added"""
    return _send_sms(phone, f"AgriTrust: \U0001f4dd Investigation note added to dispute #{dispute_id}.")


def notify_agent_resolution_submitted(phone: str, dispute_id: str) -> bool:
    """AGENT_011 — Resolution submitted"""
    return _send_sms(phone, f"AgriTrust: \U0001f4e4 Resolution for dispute #{dispute_id} submitted. Awaiting admin approval.")


def notify_agent_commission_earned(phone: str, amount: float, task_id: str, total: float) -> bool:
    """AGENT_012 — Commission earned"""
    return _send_sms(phone, f"AgriTrust: \U0001f4b0 ${amount} commission added for task #{task_id}. Total earnings: ${total}.")


def notify_agent_weekly_summary(phone: str, amount: float, count: int, accuracy: float) -> bool:
    """AGENT_013 — Weekly earnings summary"""
    return _send_sms(phone, f"AgriTrust: \U0001f4ca Weekly earnings: ${amount}. Tasks completed: {count}. Accuracy: {accuracy}%.")


def notify_agent_payout(phone: str, amount: float, method: str, ref: str) -> bool:
    """AGENT_014 — Payout sent"""
    return _send_sms(phone, f"AgriTrust: \U0001f4b8 ${amount} sent to your {method}. Reference: {ref}.")


def notify_agent_application_received(phone: str) -> bool:
    """AGENT_015 — Application received"""
    return _send_sms(phone, "AgriTrust: \U0001f4dd Agent application received. We'll review within 3-5 business days.")


def notify_agent_application_approved(phone: str) -> bool:
    """AGENT_016 — Application approved"""
    return _send_sms(phone, "AgriTrust: \U0001f389 Congratulations! Your agent application is approved. Start training via WhatsApp.")


def notify_agent_application_rejected(phone: str, reason: str) -> bool:
    """AGENT_017 — Application rejected"""
    return _send_sms(phone, f"AgriTrust: \u274c Your agent application was rejected. Reason: {reason}.")


def notify_agent_training_module(phone: str, module: str) -> bool:
    """AGENT_018 — Training module available"""
    return _send_sms(phone, f"AgriTrust: \U0001f4da Module {module} is now available. Reply START to begin.")


def notify_agent_exam_passed(phone: str, exam_name: str, score: float) -> bool:
    """AGENT_019 — Exam passed"""
    return _send_sms(phone, f"AgriTrust: \U0001f393 Congratulations! You passed the {exam_name} with {score}%.")


def notify_agent_certified(phone: str, agent_id: str) -> bool:
    """AGENT_020 — Certification issued"""
    return _send_sms(phone, f"AgriTrust: \U0001f3c6 You are now a certified AgriTrust agent! Agent ID: {agent_id}.")


# ---------------------------------------------------------------------------
# PART 7 — ADMIN
# ---------------------------------------------------------------------------

def notify_admin_daily_summary(phone: str, users: int, txns: int, volume: float, disputes: int) -> bool:
    """ADMIN_001 — Daily summary"""
    return _send_sms(phone, f"AgriTrust Admin: \U0001f4ca Daily summary - Users: {users}, Transactions: {txns}, Volume: ${volume}, Disputes: {disputes}.")


def notify_admin_high_risk(phone: str, txn_id: str, amount: float, score: float) -> bool:
    """ADMIN_002 — High-risk alert"""
    return _send_sms(phone, f"AgriTrust Admin: \U0001f6a8 High-risk transaction detected. ID: {txn_id}, Amount: ${amount}, Risk score: {score}%.")


def notify_admin_system_down(phone: str, service: str) -> bool:
    """ADMIN_003 — System down alert"""
    return _send_sms(phone, f"AgriTrust Admin: \U0001f6a8 System alert: {service} is down. Manual intervention required.")


def notify_admin_system_recovered(phone: str, service: str, minutes: int) -> bool:
    """ADMIN_004 — System recovered"""
    return _send_sms(phone, f"AgriTrust Admin: \u2705 {service} is back online. Downtime: {minutes} minutes.")


def notify_admin_pending_approvals(phone: str, count: int) -> bool:
    """ADMIN_005 — Pending approvals"""
    return _send_sms(phone, f"AgriTrust Admin: \U0001f465 {count} agent applications pending approval.")


def notify_admin_agent_performance(phone: str, agent_name: str, accuracy: float) -> bool:
    """ADMIN_006 — Agent performance alert"""
    return _send_sms(phone, f"AgriTrust Admin: \u26a0\ufe0f Agent {agent_name} accuracy dropped to {accuracy}%. Review recommended.")


def notify_admin_backup_complete(phone: str, size: float) -> bool:
    """ADMIN_007 — Backup completed"""
    return _send_sms(phone, f"AgriTrust Admin: \U0001f4be Database backup completed. Size: {size}MB.")


def notify_admin_backup_failed(phone: str) -> bool:
    """ADMIN_008 — Backup failed"""
    return _send_sms(phone, "AgriTrust Admin: \u274c Database backup failed. Check logs immediately.")


# ---------------------------------------------------------------------------
# PART 8 — GENERAL NOTIFICATIONS
# ---------------------------------------------------------------------------

def notify_price_alert(phone: str, crop: str, price: float, change: float) -> bool:
    """NOTIFY_001 — Price alert"""
    return _send_sms(phone, f"AgriTrust: \U0001f4c8 Price alert! {crop} is now ${price}/kg ({change:+.1f}% from yesterday).")


def notify_weather_alert(phone: str, region: str, condition: str, advice: str) -> bool:
    """NOTIFY_002 — Weather alert"""
    return _send_sms(phone, f"AgriTrust: \u2601\ufe0f Weather alert for {region}: {condition}. {advice}")


def notify_trust_score_change(phone: str, old: int, new: int, reason: str) -> bool:
    """NOTIFY_003 — Trust score change"""
    return _send_sms(phone, f"AgriTrust: \U0001f4ca Your trust score changed from {old} to {new}/100. Reason: {reason}.")


def notify_promo_offer(phone: str) -> bool:
    """NOTIFY_004 — Promotional offer"""
    return _send_sms(phone, "AgriTrust: \U0001f389 Special offer: 0% platform fees for your first 3 transactions! Limited time.")


def notify_maintenance_scheduled(phone: str, date: str, start: str, end: str) -> bool:
    """NOTIFY_005 — System maintenance"""
    return _send_sms(phone, f"AgriTrust: \U0001f527 Scheduled maintenance on {date} from {start} to {end}. Platform may be unavailable.")


def notify_maintenance_complete(phone: str) -> bool:
    """NOTIFY_006 — Maintenance complete"""
    return _send_sms(phone, "AgriTrust: \u2705 Maintenance complete. All systems operational.")


def notify_feedback_request(phone: str) -> bool:
    """NOTIFY_007 — Feedback request"""
    return _send_sms(phone, "AgriTrust: \U0001f4dd How was your experience? Reply with feedback to help us improve.")


def notify_broadcast(phone: str, message: str) -> bool:
    """NOTIFY_008 — Broadcast message"""
    return _send_sms(phone, f"AgriTrust: \U0001f4e2 {message}")
