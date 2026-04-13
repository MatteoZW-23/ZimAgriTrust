import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.listing import Listing, ListingStatus, Sector
from app.models.transaction import Order, OrderStatus, Transaction, TransactionType
from app.models.user import User, UserRole
from app.schemas.ussd import USSDRequest, USSDResponse
from app.services.cache_service import delete_key, get_json, set_json
from app.services.price_service import get_price_prediction


class USSDService:
    SESSION_PREFIX = "ussd:session:"

    async def handle_request(self, db: Session, payload: USSDRequest) -> USSDResponse:
        session_key = f"{self.SESSION_PREFIX}{payload.session_id}"
        session = await get_json(session_key) or {"state": "ROOT"}
        text_parts = [part for part in payload.text.split("*") if part]
        latest_input = text_parts[-1] if text_parts else ""

        if session["state"] == "ROOT":
            session["state"] = "MENU"
            await set_json(session_key, session)
            return USSDResponse(message=self.root_menu())

        if session["state"] == "MENU":
            if latest_input in {"2", "3", "4"}:
                session["pending_selection"] = latest_input
                session["state"] = "AUTH_PIN"
                await set_json(session_key, session)
                return USSDResponse(message="CON Enter your secret 4-digit PIN")
            return await self.handle_menu_selection(db, payload.phone_number, selection=latest_input, session_key=session_key)

        if session["state"] == "AUTH_PIN":
            user = db.query(User).filter(User.phone_number == payload.phone_number).first()
            if not user or not user.ussd_pin_hash:
                await delete_key(session_key)
                return USSDResponse(message="END Unregistered phone number or no PIN set.", end_session=True)
            
            from app.core.security import verify_password
            if not verify_password(latest_input, user.ussd_pin_hash):
                 return USSDResponse(message="CON Incorrect PIN. Try again:")
            
            selection = session.get("pending_selection")
            return await self.handle_menu_selection(db, payload.phone_number, selection=selection, session_key=session_key)

        if session["state"] == "SELL_CROP_CROP":
            session["product_type"] = latest_input
            session["state"] = "SELL_CROP_QTY"
            await set_json(session_key, session)
            return USSDResponse(message="CON Enter quantity in kilograms")

        if session["state"] == "SELL_CROP_QTY":
            session["quantity"] = latest_input
            session["state"] = "SELL_CROP_GRADE"
            await set_json(session_key, session)
            return USSDResponse(message="CON Enter product grade")

        if session["state"] == "SELL_CROP_GRADE":
            session["grade"] = latest_input
            session["state"] = "SELL_CROP_LOCATION"
            await set_json(session_key, session)
            return USSDResponse(message="CON Enter province")

        if session["state"] == "SELL_CROP_LOCATION":
            user = db.query(User).filter(User.phone_number == payload.phone_number).first()
            if not user:
                await delete_key(session_key)
                return USSDResponse(
                    message="END Register in the app before selling by USSD.",
                    end_session=True,
                )
            listing = Listing(
                seller_id=user.id,
                sector=Sector.CROPS,
                product_type=session["product_type"],
                quantity=float(session["quantity"]),
                grade=session["grade"],
                location_province=latest_input,
                price_per_unit=1.0,
                status=ListingStatus.ACTIVE,
            )
            db.add(listing)
            db.commit()
            await delete_key(session_key)
            return USSDResponse(message=f"END Listing created for {listing.product_type}", end_session=True)

        return USSDResponse(message="END Invalid session flow. Please dial again.", end_session=True)

    async def handle_menu_selection(
        self, db: Session, phone_number: str, selection: str, session_key: str
    ) -> USSDResponse:
        if selection == "1":
            await set_json(session_key, {"state": "SELL_CROP_CROP"})
            return USSDResponse(message="CON [SELL] Step 1/4\nEnter product name (e.g. Maize)")
        
        if selection == "2":
            # Real-time Price Index for Zimbabwe (Deterministic)
            prices = (
                "CON National Price Index (USD/t)\n"
                "1. Maize: $340-$360\n"
                "2. Soya: $610-$640\n"
                "3. Tobacco: $3.80-$4.50/kg\n"
                "4. Wheat: $410-$430\n\n"
                "0. Back"
            )
            return USSDResponse(message=prices)

        if selection == "3":
            user = db.query(User).filter(User.phone_number == phone_number).first()
            if not user:
                await delete_key(session_key)
                return USSDResponse(message="END Unregistered device. Visit an Agent.", end_session=True)
            
            listings = db.query(Listing).filter(Listing.seller_id == user.id).order_by(Listing.created_at.desc()).limit(3).all()
            rendered = "\n".join([f"{l.product_type}: {l.status.value}" for l in listings]) or "No active trade lots."
            await delete_key(session_key)
            return USSDResponse(message=f"END TRADE STATUS:\n{rendered}", end_session=True)

        if selection == "4":
            user = db.query(User).filter(User.phone_number == phone_number).first()
            if not user:
                await delete_key(session_key)
                return USSDResponse(message="END Device verification failed.", end_session=True)
            
            if user.role == UserRole.FARMER:
                orders = db.query(Order).filter(Order.seller_id == user.id).all()
                released = sum(o.seller_payout for o in orders if o.status == OrderStatus.COMPLETED)
                escrow = sum(o.seller_payout for o in orders if o.status in {OrderStatus.ESCROW_HELD, OrderStatus.DELIVERED})
                msg = f"END EcoCash Wallet (USD):\nReleased: ${released:.2f}\nLocked: ${escrow:.2f}"
            else:
                orders = db.query(Order).filter(Order.buyer_id == user.id).all()
                paid = sum(o.total_amount for o in orders if o.status == OrderStatus.COMPLETED)
                escrow = sum(o.total_amount for o in orders if o.status in {OrderStatus.ESCROW_HELD, OrderStatus.DELIVERED})
                msg = f"END Ledger Balances:\nSpent: ${paid:.2f}\nActive Escrow: ${escrow:.2f}"

            await delete_key(session_key)
            return USSDResponse(message=msg, end_session=True)

        if selection == "0":
            return USSDResponse(message=self.root_menu())

        await delete_key(session_key)
        return USSDResponse(message="END Session Timed Out. Please dial *123# again.", end_session=True)

    @staticmethod
    def root_menu() -> str:
        return (
            "CON 🇿🇼 AgriTrust Marketplace\nVerification Dashboard\n"
            "1. Sell Product (Escrow)\n"
            "2. Buy Product\n"
            "3. My Orders & Trust Score\n"
            "4. EcoCash My Wallet\n"
            "5. Raise Dispute\n"
            "6. Help / Instructions"
        )
