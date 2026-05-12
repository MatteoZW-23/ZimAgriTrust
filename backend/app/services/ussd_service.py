import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.listing import Listing, ListingStatus, Sector, Offer, OfferStatus
from app.models.transaction import Order, OrderStatus, Transaction, TransactionType
from app.models.user import User, UserRole
from app.models.dispute import Dispute, DisputeStatus
from app.schemas.ussd import USSDRequest, USSDResponse
from app.services.cache_service import delete_key, get_json, set_json
from app.services.price_service import get_price_prediction
from app.services.notification_service import NotificationService


class USSDService:
    SESSION_PREFIX = "ussd:session:"

    # ─────────────────────────────────────────────────────────────────────────
    # MAIN REQUEST HANDLER
    # ─────────────────────────────────────────────────────────────────────────

    async def handle_request(self, db: Session, payload: USSDRequest) -> USSDResponse:
        session_key = f"{self.SESSION_PREFIX}{payload.session_id}"
        sess = await get_json(session_key) or {"state": "ROOT"}
        text_parts = [p for p in payload.text.split("*") if p]
        latest = text_parts[-1] if text_parts else ""

        state = sess["state"]

        # ── ROOT ──────────────────────────────────────────────────────────────
        if state == "ROOT":
            sess["state"] = "MENU"
            await set_json(session_key, sess)
            return USSDResponse(message=self.root_menu())

        # ── MAIN MENU ─────────────────────────────────────────────────────────
        if state == "MENU":
            # Options that require PIN first
            if latest in {"2", "4", "5", "6", "7", "8"}:
                sess["pending_selection"] = latest
                sess["state"] = "AUTH_PIN"
                await set_json(session_key, sess)
                return USSDResponse(message="CON Enter your 4-digit PIN:")
            return await self._route(db, payload.phone_number, latest, session_key)

        # ── PIN AUTH ──────────────────────────────────────────────────────────
        if state == "AUTH_PIN":
            user = db.query(User).filter(User.phone_number == payload.phone_number).first()
            if not user or not user.ussd_pin_hash:
                await delete_key(session_key)
                return USSDResponse(
                    message="END Phone not registered or no PIN set.\nDownload ZimAgritrust app to register.",
                    end_session=True,
                )
            from app.core.security import verify_password
            if not verify_password(latest, user.ussd_pin_hash):
                sess["pin_attempts"] = sess.get("pin_attempts", 0) + 1
                if sess["pin_attempts"] >= 3:
                    await delete_key(session_key)
                    return USSDResponse(message="END Too many wrong PINs. Dial *123# to retry.", end_session=True)
                await set_json(session_key, sess)
                return USSDResponse(message=f"CON Wrong PIN ({sess['pin_attempts']}/3). Try again:")
            sess["pin_attempts"] = 0
            selection = sess.get("pending_selection")
            return await self._route(db, payload.phone_number, selection, session_key)

        # ── SELL FLOW ─────────────────────────────────────────────────────────
        if state == "SELL_CROP":
            if not latest.strip():
                return USSDResponse(message="CON Enter product name (e.g. Maize):")
            sess["product_type"] = latest.strip().title()
            sess["state"] = "SELL_QTY"
            await set_json(session_key, sess)
            return USSDResponse(message="CON Enter quantity in kg:")

        if state == "SELL_QTY":
            try:
                qty = float(latest)
                if qty <= 0:
                    raise ValueError
                sess["quantity"] = qty
                sess["state"] = "SELL_GRADE"
                await set_json(session_key, sess)
                return USSDResponse(message="CON Enter grade (A / B / C):")
            except ValueError:
                return USSDResponse(message="CON Invalid. Enter a positive number (kg):")

        if state == "SELL_GRADE":
            grade = latest.strip().upper()
            if grade not in {"A", "B", "C"}:
                return USSDResponse(message="CON Enter A, B or C:")
            sess["grade"] = grade
            sess["state"] = "SELL_PRICE"
            await set_json(session_key, sess)
            return USSDResponse(message="CON Enter price per kg (USD):")

        if state == "SELL_PRICE":
            try:
                price = float(latest)
                if price <= 0:
                    raise ValueError
                sess["price"] = price
                sess["state"] = "SELL_PROVINCE"
                await set_json(session_key, sess)
                return USSDResponse(message="CON Enter province (e.g. Harare):")
            except ValueError:
                return USSDResponse(message="CON Invalid. Enter price in USD:")

        if state == "SELL_PROVINCE":
            user = db.query(User).filter(User.phone_number == payload.phone_number).first()
            if not user:
                await delete_key(session_key)
                return USSDResponse(message="END Register via the app first.", end_session=True)

            listing = Listing(
                seller_id=user.id,
                sector=Sector.CROPS,
                product_type=sess["product_type"],
                quantity=float(sess["quantity"]),
                grade=sess["grade"],
                price_per_unit=float(sess["price"]),
                location_province=latest.strip().title(),
                status=ListingStatus.ACTIVE,
            )
            db.add(listing)
            db.commit()
            db.refresh(listing)

            total = listing.quantity * listing.price_per_unit
            await delete_key(session_key)
            return USSDResponse(
                message=(
                    f"END Listing Created!\n"
                    f"{listing.product_type} | {listing.quantity}kg | Grade {listing.grade}\n"
                    f"${listing.price_per_unit:.2f}/kg | Total: ${total:.2f}\n"
                    f"Location: {listing.location_province}"
                ),
                end_session=True,
            )

        # ── BUY FLOW ──────────────────────────────────────────────────────────
        if state == "BUY_BROWSE":
            if latest == "0":
                sess["state"] = "MENU"
                await set_json(session_key, sess)
                return USSDResponse(message=self.root_menu())
            try:
                idx = int(latest) - 1
                ids = sess.get("listing_ids", [])
                if not (0 <= idx < len(ids)):
                    return USSDResponse(message=f"CON Choose 1-{len(ids)} or 0 to go back:")
                sess["selected_listing_id"] = ids[idx]
                sess["state"] = "BUY_QTY"
                await set_json(session_key, sess)
                return USSDResponse(message="CON Enter quantity to buy (kg):")
            except ValueError:
                return USSDResponse(message="CON Enter a number or 0 to go back:")

        if state == "BUY_QTY":
            try:
                qty = float(latest)
                if qty <= 0:
                    raise ValueError
                listing = db.query(Listing).filter(
                    Listing.id == sess["selected_listing_id"]
                ).first()
                if not listing or listing.status != ListingStatus.ACTIVE:
                    await delete_key(session_key)
                    return USSDResponse(message="END Listing no longer available.", end_session=True)
                if qty > listing.quantity:
                    return USSDResponse(
                        message=f"CON Only {listing.quantity:.0f}kg available. Enter quantity:"
                    )
                total = qty * listing.price_per_unit
                sess["buy_qty"] = qty
                sess["buy_total"] = total
                sess["state"] = "BUY_CONFIRM"
                await set_json(session_key, sess)
                return USSDResponse(
                    message=(
                        f"CON Confirm Order:\n"
                        f"{listing.product_type} {qty:.0f}kg\n"
                        f"${listing.price_per_unit:.2f}/kg = ${total:.2f}\n"
                        f"1. Confirm  2. Cancel"
                    )
                )
            except ValueError:
                return USSDResponse(message="CON Invalid. Enter quantity in kg:")

        if state == "BUY_CONFIRM":
            if latest != "1":
                await delete_key(session_key)
                return USSDResponse(message="END Order cancelled.", end_session=True)

            user = db.query(User).filter(User.phone_number == payload.phone_number).first()
            listing = db.query(Listing).filter(
                Listing.id == sess["selected_listing_id"]
            ).first()
            if not user or not listing:
                await delete_key(session_key)
                return USSDResponse(message="END Transaction failed. Try again.", end_session=True)

            qty = float(sess["buy_qty"])
            offer = Offer(
                listing_id=listing.id,
                buyer_id=user.id,
                seller_id=listing.seller_id,
                quantity=qty,
                offered_price=listing.price_per_unit,
                status=OfferStatus.PENDING,
            )
            db.add(offer)
            db.commit()
            db.refresh(offer)

            # Notify seller via SMS
            if listing.seller and listing.seller.phone_number:
                NotificationService._send_sms(
                    listing.seller.phone_number,
                    f"ZimAgritrust: New offer for {listing.product_type} {qty:.0f}kg "
                    f"from {user.full_name}. Check your dashboard.",
                )

            await delete_key(session_key)
            return USSDResponse(
                message=(
                    f"END Offer Sent!\n"
                    f"Ref: #{str(offer.id)[:8].upper()}\n"
                    f"{listing.product_type} {qty:.0f}kg | ${sess['buy_total']:.2f}\n"
                    f"Seller will be notified."
                ),
                end_session=True,
            )

        # ── CHANGE PIN FLOW ───────────────────────────────────────────────────
        if state == "PIN_NEW":
            if len(latest) != 4 or not latest.isdigit():
                return USSDResponse(message="CON PIN must be exactly 4 digits. Enter new PIN:")
            sess["new_pin"] = latest
            sess["state"] = "PIN_CONFIRM"
            await set_json(session_key, sess)
            return USSDResponse(message="CON Confirm new PIN:")

        if state == "PIN_CONFIRM":
            if latest != sess.get("new_pin"):
                await delete_key(session_key)
                return USSDResponse(message="END PINs do not match. Dial *123# to retry.", end_session=True)
            user = db.query(User).filter(User.phone_number == payload.phone_number).first()
            if not user:
                await delete_key(session_key)
                return USSDResponse(message="END User not found.", end_session=True)
            from app.core.security import get_password_hash
            hashed = get_password_hash(latest)
            # Only update ussd_pin_hash for USSD PIN changes
            user.ussd_pin_hash = hashed
            db.commit()
            await delete_key(session_key)
            return USSDResponse(message="END PIN changed successfully!\nUse your new PIN next time.", end_session=True)

        # ── PRICE BACK ────────────────────────────────────────────────────────
        if state == "PRICE_BACK":
            sess["state"] = "MENU"
            await set_json(session_key, sess)
            return USSDResponse(message=self.root_menu())

        # ── TRANSACTION HISTORY ───────────────────────────────────────────────
        if state == "TXN_LIST":
            if latest == "0":
                sess["state"] = "MENU"
                await set_json(session_key, sess)
                return USSDResponse(message=self.root_menu())
            await delete_key(session_key)
            return USSDResponse(message="END Open the ZimAgritrust app for full history.", end_session=True)

        # ── DISPUTE FLOW ──────────────────────────────────────────────────────
        if state == "DISPUTE_SELECT":
            if latest == "0":
                sess["state"] = "MENU"
                await set_json(session_key, sess)
                return USSDResponse(message=self.root_menu())
            try:
                idx = int(latest) - 1
                order_ids = sess.get("dispute_order_ids", [])
                if not (0 <= idx < len(order_ids)):
                    return USSDResponse(message=f"CON Choose 1-{len(order_ids)} or 0 to go back:")
                sess["dispute_order_id"] = order_ids[idx]
                sess["state"] = "DISPUTE_CONFIRM"
                await set_json(session_key, sess)
                return USSDResponse(message="CON Raise dispute for this order?\n1. Yes  2. No")
            except ValueError:
                return USSDResponse(message="CON Enter a number or 0 to go back:")

        if state == "DISPUTE_CONFIRM":
            if latest != "1":
                await delete_key(session_key)
                return USSDResponse(message="END Dispute cancelled.", end_session=True)
            user = db.query(User).filter(User.phone_number == payload.phone_number).first()
            order = db.query(Order).filter(Order.id == sess["dispute_order_id"]).first()
            if not user or not order:
                await delete_key(session_key)
                return USSDResponse(message="END Could not create dispute. Try again.", end_session=True)

            dispute = Dispute(
                order_id=order.id,
                raised_by=user.id,
                type="ussd_dispute",
                description="Raised via USSD *123#",
                status=DisputeStatus.OPEN,
            )
            db.add(dispute)
            db.commit()
            db.refresh(dispute)

            NotificationService._send_sms(
                payload.phone_number,
                f"ZimAgritrust: Dispute #{str(dispute.id)[:8].upper()} created. "
                f"An agent will contact you within 24 hours.",
            )
            await delete_key(session_key)
            return USSDResponse(
                message=(
                    f"END Dispute Raised!\n"
                    f"Ref: #{str(dispute.id)[:8].upper()}\n"
                    f"An agent will call you within 24hrs."
                ),
                end_session=True,
            )

        # Fallback
        await delete_key(session_key)
        return USSDResponse(message="END Session error. Dial *123# to start again.", end_session=True)

    # ─────────────────────────────────────────────────────────────────────────
    # MENU ROUTER
    # ─────────────────────────────────────────────────────────────────────────

    async def _route(self, db: Session, phone: str, selection: str, session_key: str) -> USSDResponse:

        # 1 ── SELL PRODUCT
        if selection == "1":
            await set_json(session_key, {"state": "SELL_CROP"})
            return USSDResponse(message="CON [SELL] Enter product name (e.g. Maize):")

        # 2 ── BUY PRODUCTS  (PIN required)
        if selection == "2":
            listings = (
                db.query(Listing)
                .filter(Listing.status == ListingStatus.ACTIVE, Listing.quantity > 0)
                .order_by(desc(Listing.created_at))
                .limit(5)
                .all()
            )
            if not listings:
                await delete_key(session_key)
                return USSDResponse(message="END No products available right now.", end_session=True)

            lines = ["CON Available Products:"]
            ids = []
            for i, l in enumerate(listings, 1):
                lines.append(f"{i}. {l.product_type} {l.quantity:.0f}kg @${l.price_per_unit:.2f}/kg")
                ids.append(str(l.id))
            lines.append("0. Back")

            sess = await get_json(session_key) or {}
            sess["state"] = "BUY_BROWSE"
            sess["listing_ids"] = ids
            await set_json(session_key, sess)
            return USSDResponse(message="\n".join(lines))

        # 3 ── AI PRICE INTEL  (no PIN)
        if selection == "3":
            crops = ["Maize", "Soya", "Wheat", "Tobacco"]
            lines = ["CON AI Price Intel (USD/t):"]
            for c in crops:
                pred = get_price_prediction(db, c)
                lines.append(f"{c}: ${pred['forecast_30d']}")
            lines.append("0. Back")
            sess = await get_json(session_key) or {}
            sess["state"] = "PRICE_BACK"
            await set_json(session_key, sess)
            return USSDResponse(message="\n".join(lines))

        # 4 ── MY PROFILE  (PIN required)
        if selection == "4":
            user = db.query(User).filter(User.phone_number == phone).first()
            if not user:
                await delete_key(session_key)
                return USSDResponse(message="END User not found.", end_session=True)

            active = db.query(Listing).filter(
                Listing.seller_id == user.id,
                Listing.status == ListingStatus.ACTIVE,
            ).count()
            orders = db.query(Order).filter(
                (Order.seller_id == user.id) | (Order.buyer_id == user.id)
            ).count()
            rating = "A" if user.trust_score > 80 else "B" if user.trust_score > 50 else "C"

            await delete_key(session_key)
            return USSDResponse(
                message=(
                    f"END Profile: {user.full_name}\n"
                    f"Trust: {user.trust_score:.0f}/100 | Class {rating}\n"
                    f"Active Listings: {active}\n"
                    f"Total Orders: {orders}\n"
                    f"Verified: {'Yes' if user.id_verified else 'No'}"
                ),
                end_session=True,
            )

        # 5 ── MY WALLET  (PIN required)
        if selection == "5":
            user = db.query(User).filter(User.phone_number == phone).first()
            if not user:
                await delete_key(session_key)
                return USSDResponse(message="END User not found.", end_session=True)

            if user.role == UserRole.FARMER:
                orders = db.query(Order).filter(Order.seller_id == user.id).all()
                released = sum(o.seller_payout for o in orders if o.status == OrderStatus.COMPLETED)
                locked   = sum(o.seller_payout for o in orders if o.status in {OrderStatus.ESCROW_HELD, OrderStatus.DELIVERED})
                pending  = sum(o.seller_payout for o in orders if o.status == OrderStatus.PENDING)
                await delete_key(session_key)
                return USSDResponse(
                    message=(
                        f"END Wallet (USD):\n"
                        f"Released: ${released:.2f}\n"
                        f"In Escrow: ${locked:.2f}\n"
                        f"Pending: ${pending:.2f}\n"
                        f"Total: ${released + locked + pending:.2f}"
                    ),
                    end_session=True,
                )
            else:
                orders = db.query(Order).filter(Order.buyer_id == user.id).all()
                spent   = sum(o.total_amount for o in orders if o.status == OrderStatus.COMPLETED)
                locked  = sum(o.total_amount for o in orders if o.status in {OrderStatus.ESCROW_HELD, OrderStatus.DELIVERED})
                pending = sum(o.total_amount for o in orders if o.status == OrderStatus.PENDING)
                await delete_key(session_key)
                return USSDResponse(
                    message=(
                        f"END Ledger (USD):\n"
                        f"Completed: ${spent:.2f}\n"
                        f"In Escrow: ${locked:.2f}\n"
                        f"Pending: ${pending:.2f}\n"
                        f"Total Spent: ${spent + locked + pending:.2f}"
                    ),
                    end_session=True,
                )

        # 6 ── RAISE DISPUTE  (PIN required)
        if selection == "6":
            user = db.query(User).filter(User.phone_number == phone).first()
            if not user:
                await delete_key(session_key)
                return USSDResponse(message="END Please register first.", end_session=True)

            orders = (
                db.query(Order)
                .filter(
                    (Order.seller_id == user.id) | (Order.buyer_id == user.id),
                    Order.status.in_([OrderStatus.DELIVERED, OrderStatus.ESCROW_HELD]),
                )
                .order_by(desc(Order.created_at))
                .limit(3)
                .all()
            )
            if not orders:
                await delete_key(session_key)
                return USSDResponse(
                    message="END No disputable orders found.\nContact: +263771234567",
                    end_session=True,
                )

            lines = ["CON Select order to dispute:"]
            ids = []
            for i, o in enumerate(orders, 1):
                product = o.listing.product_type if o.listing else "Order"
                lines.append(f"{i}. {product} ${o.total_amount:.2f}")
                ids.append(str(o.id))
            lines.append("0. Back")

            sess = await get_json(session_key) or {}
            sess["state"] = "DISPUTE_SELECT"
            sess["dispute_order_ids"] = ids
            await set_json(session_key, sess)
            return USSDResponse(message="\n".join(lines))

        # 7 ── CHANGE PIN  (PIN required — old PIN already verified)
        if selection == "7":
            sess = await get_json(session_key) or {}
            sess["state"] = "PIN_NEW"
            await set_json(session_key, sess)
            return USSDResponse(message="CON Enter new 4-digit PIN:")

        # 8 ── TRANSACTION HISTORY  (PIN required)
        if selection == "8":
            user = db.query(User).filter(User.phone_number == phone).first()
            if not user:
                await delete_key(session_key)
                return USSDResponse(message="END User not found.", end_session=True)

            txns = (
                db.query(Transaction)
                .filter(Transaction.user_id == user.id)
                .order_by(desc(Transaction.created_at))
                .limit(5)
                .all()
            )
            if not txns:
                await delete_key(session_key)
                return USSDResponse(message="END No transactions yet.", end_session=True)

            lines = ["CON Recent Transactions:"]
            for i, t in enumerate(txns, 1):
                date_str = t.created_at.strftime("%d/%m")
                lines.append(f"{i}. {t.type.value} ${t.amount:.2f} ({date_str})")
            lines.append("0. Back")

            sess = await get_json(session_key) or {}
            sess["state"] = "TXN_LIST"
            await set_json(session_key, sess)
            return USSDResponse(message="\n".join(lines))

        # 9 ── HELP  (no PIN)
        if selection == "9":
            await delete_key(session_key)
            return USSDResponse(
                message=(
                    "END ZimAgritrust Help:\n"
                    "1-Sell  2-Buy  3-Prices\n"
                    "4-Profile  5-Wallet\n"
                    "6-Dispute  7-PIN  8-History\n"
                    "Support: +263771234567"
                ),
                end_session=True,
            )

        # PRICE BACK handler
        if selection == "0":
            return USSDResponse(message=self.root_menu())

        await delete_key(session_key)
        return USSDResponse(message="END Invalid option. Dial *123# again.", end_session=True)

    # ─────────────────────────────────────────────────────────────────────────
    # ROOT MENU
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def root_menu() -> str:
        return (
            "CON ZimAgritrust *123#\n"
            "1. Sell Product\n"
            "2. Buy Products\n"
            "3. AI Price Intel\n"
            "4. My Profile\n"
            "5. My Wallet\n"
            "6. Raise Dispute\n"
            "7. Change PIN\n"
            "8. Transactions\n"
            "9. Help"
        )
