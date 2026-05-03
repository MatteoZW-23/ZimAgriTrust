"""
Tests for Enhanced WhatsApp Service
"""

import pytest
from datetime import datetime, timedelta
from app.services.whatsapp_enhanced import whatsapp_enhanced
from app.models.user import User, UserRole


class TestBulkMessaging:
    """Test bulk messaging and broadcast features"""
    
    @pytest.mark.asyncio
    async def test_broadcast_message(self, db_session, test_users):
        """Test broadcasting message to multiple users"""
        result = await whatsapp_enhanced.broadcast_message(
            db_session,
            "Test broadcast message",
            role_filter=UserRole.FARMER
        )
        
        assert result["success"] is True
        assert result["sent"] > 0
        assert result["total_recipients"] > 0
    
    @pytest.mark.asyncio
    async def test_price_alert(self, db_session):
        """Test price alert broadcast"""
        result = await whatsapp_enhanced.send_price_alert(
            db_session,
            commodity="Maize",
            old_price=400.0,
            new_price=450.0,
            province="Harare"
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_weather_alert(self, db_session):
        """Test weather alert broadcast"""
        result = await whatsapp_enhanced.send_weather_alert(
            db_session,
            province="Harare",
            alert_type="rain",
            message_body="Heavy rains expected in the next 24 hours"
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_harvest_reminder(self, db_session):
        """Test harvest reminder broadcast"""
        result = await whatsapp_enhanced.send_harvest_reminder(
            db_session,
            crop_type="Maize",
            province="Harare"
        )
        
        assert result["success"] is True


class TestSmartNotifications:
    """Test smart notification features"""
    
    @pytest.mark.asyncio
    async def test_delivery_reminder(self, db_session, test_user):
        """Test delivery reminder"""
        await whatsapp_enhanced.send_delivery_reminder(
            db_session,
            order_id="ORD-123",
            recipient_phone=test_user.phone_number,
            days_remaining=2
        )
        # Should not raise exception
    
    @pytest.mark.asyncio
    async def test_payment_reminder(self, db_session, test_user):
        """Test payment reminder"""
        due_date = datetime.utcnow() + timedelta(days=7)
        
        await whatsapp_enhanced.send_payment_reminder(
            db_session,
            user_phone=test_user.phone_number,
            amount=500.0,
            due_date=due_date,
            loan_id="LOAN-123"
        )
        # Should not raise exception
    
    @pytest.mark.asyncio
    async def test_verification_reminder(self, db_session, test_user):
        """Test verification reminder"""
        await whatsapp_enhanced.send_verification_reminder(
            db_session,
            user_phone=test_user.phone_number,
            user_name=test_user.full_name,
            verification_type="id"
        )
        # Should not raise exception


class TestLocationServices:
    """Test location sharing features"""
    
    @pytest.mark.asyncio
    async def test_location_share(self, db_session, test_user):
        """Test location sharing"""
        response = await whatsapp_enhanced.process_location_share(
            db_session,
            test_user,
            latitude=-17.8252,
            longitude=31.0335
        )
        
        assert "Location Saved" in response
        assert test_user.latitude == -17.8252
        assert test_user.longitude == 31.0335


class TestMobilePayment:
    """Test mobile money integration"""
    
    @pytest.mark.asyncio
    async def test_initiate_payment(self, db_session, test_user):
        """Test payment initiation"""
        result = await whatsapp_enhanced.initiate_mobile_payment(
            db_session,
            test_user,
            amount=100.0,
            reference="TEST-REF-123",
            provider="ecocash"
        )
        
        assert result["success"] is True
        assert result["status"] == "pending"
        assert "payment_id" in result
    
    @pytest.mark.asyncio
    async def test_payment_receipt(self, db_session, test_user):
        """Test payment receipt"""
        await whatsapp_enhanced.send_payment_receipt(
            db_session,
            user_phone=test_user.phone_number,
            transaction_id="TXN-123",
            amount=100.0,
            recipient="Test Recipient",
            timestamp=datetime.utcnow()
        )
        # Should not raise exception


class TestMarketIntelligence:
    """Test market intelligence features"""
    
    @pytest.mark.asyncio
    async def test_market_demand_prediction(self, db_session):
        """Test market demand prediction"""
        prediction = await whatsapp_enhanced.predict_market_demand(
            db_session,
            crop_type="Maize",
            province="Harare",
            days_ahead=7
        )
        
        assert "crop" in prediction
        assert "demand_level" in prediction
        assert prediction["demand_level"] in ["HIGH", "MEDIUM", "LOW"]


class TestLanguageSupport:
    """Test multi-language features"""
    
    @pytest.mark.asyncio
    async def test_language_detection(self):
        """Test language detection"""
        # English
        lang = await whatsapp_enhanced.detect_language("Hello, how are you?")
        assert lang == "en"
        
        # Shona
        lang = await whatsapp_enhanced.detect_language("Ndiri kuda chibage")
        assert lang == "sn"
    
    @pytest.mark.asyncio
    async def test_message_translation(self):
        """Test message translation"""
        translated = await whatsapp_enhanced.translate_message(
            "Hello, welcome to ZimAgritrust",
            target_language="sn"
        )
        # Should return translated text (placeholder for now)
        assert translated is not None


class TestGroupManagement:
    """Test group chat features"""
    
    @pytest.mark.asyncio
    async def test_create_farmer_group(self, db_session):
        """Test farmer group creation"""
        result = await whatsapp_enhanced.create_farmer_group(
            db_session,
            group_name="Harare Maize Farmers",
            province="Harare",
            crop_type="Maize"
        )
        
        assert result["success"] is True
        assert "group_id" in result


class TestAnalytics:
    """Test analytics and tracking features"""
    
    @pytest.mark.asyncio
    async def test_track_engagement(self, db_session, test_user):
        """Test engagement tracking"""
        await whatsapp_enhanced.track_message_engagement(
            db_session,
            user_id=test_user.id,
            message_type="price_check",
            action_taken="viewed"
        )
        # Should not raise exception
    
    @pytest.mark.asyncio
    async def test_get_engagement_stats(self, db_session, test_user):
        """Test getting engagement statistics"""
        stats = await whatsapp_enhanced.get_user_engagement_stats(
            db_session,
            user_id=test_user.id
        )
        
        assert "messages_sent" in stats
        assert "messages_received" in stats
        assert "response_rate" in stats


# Fixtures
@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        id="test-user-123",
        phone_number="+263771234567",
        full_name="Test User",
        role=UserRole.FARMER,
        is_phone_verified=True,
        trust_score=75
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_users(db_session):
    """Create multiple test users"""
    users = []
    for i in range(5):
        user = User(
            id=f"test-user-{i}",
            phone_number=f"+26377123456{i}",
            full_name=f"Test User {i}",
            role=UserRole.FARMER,
            is_phone_verified=True,
            trust_score=70 + i
        )
        users.append(user)
        db_session.add(user)
    
    db_session.commit()
    return users
