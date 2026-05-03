import logging

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def _send_sms(phone: str, message: str) -> bool:
        """Delegate to sms_service which handles AfricasTalking + simulation."""
        from app.services.sms_service import _send_sms
        return _send_sms(phone, message)

    @staticmethod
    async def _send_whatsapp(phone: str, message: str):
        """Send WhatsApp message via WhatsApp bridge."""
        try:
            from app.services.whatsapp_service import WhatsAppService
            await WhatsAppService.send_whatsapp_message(phone, message)
            return True
        except Exception as e:
            logger.error(f"Failed to send WhatsApp to {phone}: {e}")
            return False

    @staticmethod
    async def _notify_both_channels(phone: str, message: str):
        """Send to WhatsApp (primary) and SMS (fallback)."""
        wa_sent = await NotificationService._send_whatsapp(phone, message)
        if not wa_sent:
            NotificationService._send_sms(phone, message)

    @staticmethod
    def notify_agent_assignment(agent_name, phone, task_type, location):
        """SMS notification for field agents"""
        message = (
            f"ZimAgritrust Assignment: Hello {agent_name}, you have a new {task_type} task "
            f"in {location}. Please check your dashboard for details."
        )
        return NotificationService._send_sms(phone, message)

    @staticmethod
    def notify_farmer_on_verification(phone, crop, approved):
        """Notification for farmer list verification"""
        status = "APPROVED" if approved else "REJECTED"
        message = f"ZimAgritrust: Your {crop} listing was {status} by the quality team."
        return NotificationService._send_sms(phone, message)

    @staticmethod
    def notify_transaction_update(phone, tx_id, status):
        """Notification for transaction/escrow state changes"""
        message = f"ZimAgritrust Transaction #{tx_id}: Status updated to {status}."
        return NotificationService._send_sms(phone, message)

    # --- AGENT ONBOARDING TEMPLATES ---

    @staticmethod
    def notify_onboarding_documentation(phone, name, portal_url):
        message = f"Welcome {name}! You've been screened for the ZimAgritrust Agent role. Sign your digital contract here: {portal_url}. Success, HQ."
        return NotificationService._send_sms(phone, message)

    @staticmethod
    def notify_training_milestone(phone, progress):
        message = f"ZimAgritrust: Great work! You are now {progress}% through your training. Complete the next module to unlock shadowing: http://ZimAgritrust.app/academy"
        return NotificationService._send_sms(phone, message)

    @staticmethod
    def notify_certification_ready(phone, name):
        message = f"Congratulations {name}! You are now a Certified ZimAgritrust Agent. Your credentials have been activated. Welcome to the field!"
        return NotificationService._send_sms(phone, message)

    @staticmethod
    async def send_verification_code(phone: str, code: str, resend: bool = False):
        """Sends OTP via SMS (VERIFY_001/002) and WhatsApp for maximum reliability."""
        from app.services import sms_service
        # SMS — use correct template
        if resend:
            sms_service.resend_otp(phone, code)
        else:
            sms_service.send_otp(phone, code)

        # WhatsApp
        try:
            from app.services.whatsapp_service import whatsapp_service
            await whatsapp_service.send_whatsapp_message(
                phone,
                f"\U0001f510 *ZimAgritrust Security Code*\n\nYour 2-step verification code is: *{code}*\n\nThis code expires in 5 minutes. If you did not request this, please contact support."
            )
        except Exception as e:
            logger.error(f"Failed to send 2FA via WhatsApp: {e}")

    # --- VERIFICATION NOTIFICATIONS ---

    @staticmethod
    async def notify_phone_verified(phone: str, trust_score: int):
        """Notify user that phone has been verified."""
        msg = (
            f"✅ *Phone Verified*\n\n"
            f"Your phone number has been verified successfully.\n\n"
            f"⭐ Trust Score: +5\n"
            f"Current Score: {trust_score}/100\n\n"
            f"Next step: Complete identity verification with `verify id`"
        )
        await NotificationService._notify_both_channels(phone, msg)

    @staticmethod
    async def notify_documents_submitted(phone: str):
        """Notify user that documents are under review."""
        msg = "📄 Your documents have been submitted for review. We'll notify you within 24 hours."
        await NotificationService._send_whatsapp(phone, msg)

    @staticmethod
    async def notify_id_approved(phone: str, trust_score: int):
        """Notify user that ID has been approved."""
        msg = (
            f"✅ *Identity Verified*\n\n"
            f"Your identity has been verified! Trust Score +15\n"
            f"Current Score: {trust_score}/100"
        )
        await NotificationService._notify_both_channels(phone, msg)

    @staticmethod
    async def notify_id_rejected(phone: str, reason: str = None):
        """Notify user that ID was rejected."""
        msg = (
            f"❌ *ID Verification Rejected*\n\n"
            f"{reason or 'Please upload a clearer photo of your National ID.'}\n\n"
            f"Reply `verify id` to retry."
        )
        await NotificationService._notify_both_channels(phone, msg)

    @staticmethod
    async def notify_agent_assigned(phone: str, agent_name: str, time_slot: str = "tomorrow between 9-11 AM"):
        """Notify farmer that an agent has been assigned for farm verification."""
        msg = (
            f"📍 *Farm Verification Scheduled*\n\n"
            f"Agent {agent_name} has been assigned to verify your farm.\n"
            f"They will arrive {time_slot}.\n\n"
            f"Please ensure someone is available at the farm."
        )
        await NotificationService._notify_both_channels(phone, msg)

    @staticmethod
    async def notify_farm_verified(phone: str, trust_score: int):
        """Notify farmer that farm has been verified."""
        msg = (
            f"✅ *Farm Verified*\n\n"
            f"Your farm has been verified! Trust Score +20\n"
            f"Current Score: {trust_score}/100\n\n"
            f"You can now list crops and access loans."
        )
        await NotificationService._notify_both_channels(phone, msg)

    @staticmethod
    async def notify_business_verified(phone: str, trust_score: int):
        """Notify buyer that business account has been verified."""
        msg = (
            f"✅ *Business Account Verified*\n\n"
            f"Your business account has been verified! Trust Score +25\n"
            f"Current Score: {trust_score}/100\n\n"
            f"You can now make bulk purchases."
        )
        await NotificationService._send_whatsapp(phone, msg)

    @staticmethod
    async def notify_background_cleared(phone: str, trust_score: int):
        """Notify agent that background check is complete."""
        msg = (
            f"✅ *Background Check Complete*\n\n"
            f"Status: CLEAR\n"
            f"Trust Score +10\n"
            f"Current Score: {trust_score}/100\n\n"
            f"Next: Complete training modules."
        )
        await NotificationService._send_whatsapp(phone, msg)

    @staticmethod
    async def notify_training_module_complete(phone: str, module_num: int, progress_pct: int, quiz_score: int = None):
        """Notify agent of training milestone."""
        msg = f"📚 Module {module_num} completed! {progress_pct}% towards certification."
        if quiz_score:
            msg += f" Quiz score: {quiz_score}%."
        await NotificationService._send_whatsapp(phone, msg)

    @staticmethod
    async def notify_agent_certified(phone: str, trust_score: int):
        """Notify agent of certification completion."""
        msg = (
            f"🎉 *Congratulations!*\n\n"
            f"You are now a certified ZimAgritrust Agent!\n\n"
            f"Trust Score: {trust_score}/100\n\n"
            f"Your credentials have been activated. Welcome to the field!"
        )
        await NotificationService._notify_both_channels(phone, msg)

    # --- TRUST SCORE NOTIFICATIONS ---

    @staticmethod
    async def notify_trust_score_increase(phone: str, new_score: int, reason: str):
        """Notify user of trust score increase."""
        msg = (
            f"📈 *Trust Score Update*\n\n"
            f"Your trust score increased to {new_score}/100!\n\n"
            f"Reason: {reason}"
        )
        await NotificationService._send_whatsapp(phone, msg)

    @staticmethod
    async def notify_trust_score_decrease(phone: str, new_score: int, reason: str):
        """Notify user of trust score decrease."""
        msg = (
            f"📉 *Trust Score Update*\n\n"
            f"Your trust score decreased to {new_score}/100.\n\n"
            f"Reason: {reason}\n\n"
            f"Complete successful transactions to recover your score."
        )
        await NotificationService._send_whatsapp(phone, msg)

    @staticmethod
    async def notify_milestone_reached(phone: str, milestone: str, trust_score: int):
        """Notify user of milestone achievement."""
        msg = (
            f"🏆 *Milestone Reached*\n\n"
            f"{milestone}\n\n"
            f"Trust Score: {trust_score}/100"
        )
        await NotificationService._send_whatsapp(phone, msg)

    # --- DISPUTE NOTIFICATIONS ---

    @staticmethod
    async def notify_dispute_opened(phone: str, transaction_id: str, role: str = "party"):
        """Notify both parties that a dispute has been opened."""
        msg = (
            f"⚠️ *Dispute Alert*\n\n"
            f"A dispute has been opened for transaction #{transaction_id}.\n\n"
            f"Your trust score is temporarily frozen pending resolution.\n\n"
            f"Our team will review and update you shortly."
        )
        await NotificationService._notify_both_channels(phone, msg)

    @staticmethod
    async def notify_dispute_resolved(phone: str, transaction_id: str, outcome: str, trust_delta: int = 0):
        """Notify parties of dispute resolution."""
        emoji = "✅" if trust_delta >= 0 else "❌"
        msg = (
            f"⚖️ *Dispute Resolved*\n\n"
            f"Transaction #{transaction_id}\n"
            f"Decision: {outcome}\n\n"
        )
        if trust_delta != 0:
            msg += f"{emoji} Trust Score: {trust_delta:+d}\n\n"
        msg += "Thank you for your patience."
        await NotificationService._notify_both_channels(phone, msg)

    # --- TRANSACTION NOTIFICATIONS ---

    @staticmethod
    async def notify_first_transaction_complete(phone: str, trust_score: int, role: str = "seller"):
        """Notify user of first successful transaction."""
        msg = (
            f"✅ *First {role.title()} Complete*\n\n"
            f"Congratulations on your first successful transaction!\n\n"
            f"Trust Score +10\n"
            f"Current Score: {trust_score}/100"
        )
        await NotificationService._send_whatsapp(phone, msg)

    @staticmethod
    async def notify_payment_failed(phone: str, trust_score: int):
        """Notify buyer of payment failure."""
        msg = (
            f"⚠️ *Payment Failed*\n\n"
            f"Your payment could not be processed. Please check your wallet balance.\n\n"
            f"Trust Score: -10\n"
            f"Current Score: {trust_score}/100\n\n"
            f"Reply `wallet` to check balance."
        )
        await NotificationService._send_whatsapp(phone, msg)

    @staticmethod
    async def notify_fraudulent_listing_removed(phone: str, trust_score: int):
        """Notify farmer of fraudulent listing removal."""
        msg = (
            f"🚨 *Listing Removed*\n\n"
            f"Your listing was removed for fraud/policy violation.\n\n"
            f"Trust Score: -50\n"
            f"Current Score: {trust_score}/100\n\n"
            f"Multiple violations may result in account suspension."
        )
        await NotificationService._notify_both_channels(phone, msg)

    @staticmethod
    async def notify_inactivity_penalty(phone: str, trust_score: int, days: int):
        """Notify user of inactivity penalty."""
        msg = (
            f"⚠️ *Inactivity Notice*\n\n"
            f"No activity detected for {days} days.\n"
            f"Trust Score decreased due to inactivity.\n\n"
            f"Current Score: {trust_score}/100\n\n"
            f"Complete a transaction to restore your score."
        )
        await NotificationService._send_whatsapp(phone, msg)

    # --- AGENT-SPECIFIC NOTIFICATIONS ---

    @staticmethod
    async def notify_verification_flagged(phone: str, verification_id: str):
        """Notify agent of verification error."""
        msg = (
            f"⚠️ *Verification Flagged*\n\n"
            f"Verification #{verification_id} had errors.\n\n"
            f"Please review and correct.\n"
            f"Trust Score: -5"
        )
        await NotificationService._send_whatsapp(phone, msg)

    @staticmethod
    async def notify_agent_suspended(phone: str, reason: str):
        """Notify agent of account suspension."""
        msg = (
            f"🚨 *Account Suspended*\n\n"
            f"Reason: {reason}\n\n"
            f"Your agent privileges have been revoked pending investigation.\n\n"
            f"Contact support for more information."
        )
        await NotificationService._send_whatsapp(phone, msg)

    @staticmethod
    async def notify_agent_terminated(phone: str, reason: str):
        """Notify agent of permanent termination."""
        msg = (
            f"🚨 *Agent Privileges Revoked*\n\n"
            f"Reason: {reason}\n\n"
            f"This decision is permanent. Contact HQ for appeal options."
        )
        await NotificationService._send_whatsapp(phone, msg)
            
    @staticmethod
    async def send_whatsapp_vision_result(phone: str, result: dict):
        """Sends AI vision analysis results directly to farmer's WhatsApp."""
        from app.services.whatsapp_service import whatsapp_service
        
        status_emoji = "✅" if result.get("success") else "⚠️"
        crop_name = result.get("crop", {}).get("crop_name", "Produce")
        grade = result.get("grade", {}).get("grade", "Standard")
        
        message = (
            f"{status_emoji} *ZimAgritrust AI Analysis Complete*\n\n"
            f"🌿 *Produce:* {crop_name}\n"
            f"⭐ *Grade Estimate:* {grade}\n"
            f"📊 *AI Confidence:* {int(result.get('crop', {}).get('confidence', 0)*100)}%\n\n"
            f"This analysis has been logged to your listing. "
            f"Our agents will use this to fast-track your verification."
        )
        
        return await whatsapp_service.send_whatsapp_message(phone, message)


notification_service = NotificationService()
