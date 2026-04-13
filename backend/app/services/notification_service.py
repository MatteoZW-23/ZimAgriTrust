import logging

class NotificationService:
    @staticmethod
    def notify_agent_assignment(agent_name, phone, task_type, location):
        """Mock SMS notification for field agents"""
        message = (
            f"AgriTrust Assignment: Hello {agent_name}, you have a new {task_type} task "
            f"in {location}. Please check your dashboard for details."
        )
        print(f"--- MOCK SMS SENT to {phone} ---")
        print(message)
        print("-------------------------------")
        return True

    @staticmethod
    def notify_farmer_on_verification(phone, crop, approved):
        """Mock notification for farmer list verification"""
        status = "APPROVED" if approved else "REJECTED"
        message = f"AgriTrust: Your {crop} listing was {status} by the quality team."
        print(f"--- MOCK SMS SENT to {phone} ---")
        print(message)
        print("-------------------------------")
        return True

    @staticmethod
    def notify_transaction_update(phone, tx_id, status):
        """Mock notification for transaction/escrow state changes"""
        message = f"AgriTrust Transaction #{tx_id}: Status updated to {status}."
        print(f"--- MOCK SMS SENT to {phone} ---")
        print(message)
        print("-------------------------------")
        return True
