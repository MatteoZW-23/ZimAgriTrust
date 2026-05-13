"""
ZimAgriTrust — Presentation Demo Seed Script
=============================================
Seeds the database with realistic Zimbabwe agricultural marketplace data.

Usage:
    docker compose exec backend python -m scripts.seed_demo_data
    OR
    cd backend && python -m scripts.seed_demo_data
"""

import os
import sys
import uuid
import random
from datetime import datetime, timedelta, date

# Ensure backend is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.models.user import User, UserRole, UserStatus, FarmerProfile, BuyerProfile, AgentProfile, TransporterProfile
from app.models.listing import Listing, ListingStatus, Sector, Offer, OfferStatus
from app.models.transaction import Order, OrderStatus, Transaction, TransactionType
from app.models.dispute import Dispute, DisputeStatus
from app.models.agent import Agent, AgentAssignment, AgentStatus, AgentSpecialization
from app.models.price_history import PriceHistory
from app.models.driver import Driver, DriverStatus
from app.models.review import TradeReview

# ---------------------------------------------------------------------------
# Passlib / Argon2 password hashing (same as prod)
# ---------------------------------------------------------------------------
try:
    from passlib.context import CryptContext
    pwd_ctx = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
    def _hash(plain: str) -> str:
        return pwd_ctx.hash(plain)
except Exception:
    import hashlib
    def _hash(plain: str) -> str:
        return hashlib.sha256(plain.encode()).hexdigest()

# ---------------------------------------------------------------------------
# Zimbabwe-specific demo data constants
# ---------------------------------------------------------------------------
PROVINCES = [
    ("Mashonaland East", "Marondera"),
    ("Mashonaland East", "Mutoko"),
    ("Mashonaland West", "Chinhoyi"),
    ("Mashonaland West", "Kadoma"),
    ("Mashonaland Central", "Bindura"),
    ("Mashonaland Central", "Shamva"),
    ("Manicaland", "Mutare"),
    ("Manicaland", "Chipinge"),
    ("Masvingo", "Masvingo"),
    ("Masvingo", "Chiredzi"),
    ("Midlands", "Gweru"),
    ("Midlands", "Kwekwe"),
    ("Matabeleland North", "Lupane"),
    ("Matabeleland South", "Beitbridge"),
    ("Harare", "Harare"),
    ("Bulawayo", "Bulawayo"),
]

CROPS = [
    # (product_type, sector, grade, price_range_per_kg, is_perishable)
    ("Maize",         Sector.CROPS,        "GRADE_A", (0.30, 0.55), False),
    ("Maize",         Sector.CROPS,        "GRADE_B", (0.20, 0.35), False),
    ("Tobacco",       Sector.CROPS,        "EXPORT",  (3.00, 5.50), False),
    ("Soybean",       Sector.CROPS,        "GRADE_A", (0.60, 0.90), False),
    ("Groundnuts",    Sector.CROPS,        "GRADE_A", (1.20, 2.00), False),
    ("Wheat",         Sector.CROPS,        "GRADE_A", (0.40, 0.65), False),
    ("Cotton",        Sector.CROPS,        "GRADE_B", (0.70, 1.10), False),
    ("Sunflower",     Sector.CROPS,        "GRADE_A", (0.50, 0.80), False),
    ("Tomatoes",      Sector.HORTICULTURE, "GRADE_A", (0.80, 1.50), True),
    ("Onions",        Sector.HORTICULTURE, "GRADE_A", (0.60, 1.00), True),
    ("Potatoes",      Sector.HORTICULTURE, "GRADE_B", (0.30, 0.50), True),
    ("Cabbages",      Sector.HORTICULTURE, "GRADE_A", (0.20, 0.40), True),
    ("Green Beans",   Sector.HORTICULTURE, "EXPORT",  (1.50, 2.50), True),
    ("Mangoes",       Sector.HORTICULTURE, "GRADE_A", (0.90, 1.60), True),
    ("Oranges",       Sector.HORTICULTURE, "GRADE_A", (0.40, 0.70), True),
    ("Sugarcane",     Sector.CROPS,        "GRADE_A", (0.05, 0.10), False),
    ("Beef Cattle",   Sector.LIVESTOCK,    "GRADE_A", (3.50, 5.00), False),
    ("Goats",         Sector.LIVESTOCK,    "GRADE_B", (2.50, 4.00), False),
    ("Chickens",      Sector.POULTRY,      "GRADE_A", (4.00, 6.00), True),
    ("Eggs",          Sector.POULTRY,      "GRADE_A", (0.10, 0.18), True),
    ("Milk",          Sector.DAIRY,        "GRADE_A", (0.80, 1.20), True),
    ("Honey",         Sector.APICULTURE,   "EXPORT",  (5.00, 9.00), False),
    ("Tilapia",       Sector.FISHERIES,    "GRADE_A", (3.00, 4.50), True),
    ("Mushrooms",     Sector.HORTICULTURE, "GRADE_A", (3.50, 6.00), True),
]

# Realistic Zimbabwean names
FIRST_NAMES_M = ["Tendai", "Tatenda", "Blessing", "Brighton", "Kudakwashe", "Tapiwa", "Simbarashe", "Farai", "Tawanda", "Nyasha", "Tinashe", "Munyaradzi", "Takudzwa", "Fungai", "Tongai", "Kudzai", "Rumbidzai", "Panashe", "Tinotenda", "Ngonidzashe"]
FIRST_NAMES_F = ["Ruvimbo", "Nyarai", "Tendai", "Chiedza", "Rutendo", "Tsitsi", "Rumbidzai", "Fadzai", "Mercy", "Yeukai", "Shamiso", "Tariro", "Anesu", "Chenai", "Vimbai", "Makanaka", "Ruvarashe", "Tafadzwa", "Ropafadzo", "Mutsawashe"]
SURNAMES = ["Moyo", "Ncube", "Mpofu", "Ndlovu", "Dube", "Sibanda", "Nkomo", "Mhlanga", "Tshuma", "Nyoni", "Chirwa", "Chikwanha", "Hove", "Makoni", "Mutasa", "Chinamasa", "Gumbo", "Mashingaidze", "Nyamupingidza", "Mugabe", "Chinyanga", "Mataruse", "Zinyemba", "Maposa", "Chigumira"]

COMPANY_NAMES = [
    "Grain Millers Zimbabwe", "National Foods Ltd", "Delta Beverages",
    "Dairibord Holdings", "Cairns Foods", "Schweppes Zimbabwe",
    "Surface Wilmar Zimbabwe", "Chegutu Canners", "Olivine Industries",
    "Harare Fresh Produce Market", "Mbare Musika Traders Co-op",
    "Bulawayo Grain Exchange", "Mutare Agri Processors",
    "Chiredzi Sugar Estate", "Mazoe Citrus Estate",
    "Victoria Falls Hotel Kitchen", "Nyanga Fresh Exports",
    "Chipinge Coffee Co-op", "Zimbabwe Farmers Union",
    "AgriBank Zimbabwe",
]


def rand_zw_phone():
    prefix = random.choice(["263771", "263772", "263773", "263774", "263775", "263778", "263782", "263783", "263784"])
    return f"+{prefix}{random.randint(100000, 999999)}"


def rand_name():
    if random.random() < 0.5:
        first = random.choice(FIRST_NAMES_M)
    else:
        first = random.choice(FIRST_NAMES_F)
    return f"{first} {random.choice(SURNAMES)}"


def rand_location():
    return random.choice(PROVINCES)


def rand_lat_lng(province):
    base = {
        "Harare": (-17.83, 31.05),
        "Bulawayo": (-20.15, 28.58),
        "Mashonaland East": (-18.19, 31.55),
        "Mashonaland West": (-17.36, 30.20),
        "Mashonaland Central": (-16.76, 31.08),
        "Manicaland": (-19.47, 32.63),
        "Masvingo": (-20.07, 30.83),
        "Midlands": (-19.45, 29.82),
        "Matabeleland North": (-19.00, 27.50),
        "Matabeleland South": (-21.00, 29.00),
    }
    lat, lng = base.get(province, (-18.0, 31.0))
    return (lat + random.uniform(-0.5, 0.5), lng + random.uniform(-0.5, 0.5))


def days_ago(n):
    return datetime.utcnow() - timedelta(days=n)


def date_ago(n):
    return date.today() - timedelta(days=n)


# ---------------------------------------------------------------------------
# Main seed function
# ---------------------------------------------------------------------------
def seed(db):
    print("=" * 60)
    print("  ZimAgriTrust — Seeding Presentation Demo Data")
    print("=" * 60)

    # ── 1. ADMIN / SUPER ADMIN ─────────────────────────────────
    print("\n[1/9] Creating admin users...")
    admin_pw = _hash("Admin@12345678")

    super_admin = User(
        id=uuid.uuid4(),
        phone_number="+263771000001",
        full_name="System Administrator",
        email="admin@zimagritrust.co.zw",
        password_hash=admin_pw,
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
        province="Harare",
        district="Harare",
        trust_score=100,
        risk_score=0,
        is_phone_verified=True,
        id_verified=True,
        balance_usd=0.0,
        mfa_enabled=False,
    )

    regional_admin = User(
        id=uuid.uuid4(),
        phone_number="+263771000002",
        full_name="Shamiso Hove",
        email="shamiso@zimagritrust.co.zw",
        password_hash=admin_pw,
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        province="Mashonaland East",
        district="Marondera",
        trust_score=95,
        risk_score=5,
        is_phone_verified=True,
        id_verified=True,
        balance_usd=0.0,
    )
    db.add_all([super_admin, regional_admin])
    db.flush()
    print(f"  ✓ Super Admin: +263771000001 / Admin@12345678")
    print(f"  ✓ Regional Admin: +263771000002 / Admin@12345678")

    # ── 2. FARMERS ─────────────────────────────────────────────
    print("\n[2/9] Creating farmers...")
    farmer_pw = _hash("1234")
    farmers = []
    for i in range(25):
        prov, dist = rand_location()
        lat, lng = rand_lat_lng(prov)
        name = rand_name()
        phone = rand_zw_phone()
        trust = random.randint(55, 98)
        f = User(
            id=uuid.uuid4(),
            phone_number=phone,
            full_name=name,
            password_hash=farmer_pw,
            role=UserRole.FARMER,
            status=UserStatus.ACTIVE,
            province=prov,
            district=dist,
            latitude=lat,
            longitude=lng,
            trust_score=trust,
            risk_score=max(0, 100 - trust - random.randint(0, 15)),
            is_phone_verified=True,
            id_verified=random.random() > 0.2,
            is_location_verified=random.random() > 0.3,
            balance_usd=round(random.uniform(5, 350), 2),
            balance_zig=round(random.uniform(100, 5000), 2),
            last_activity_at=days_ago(random.randint(0, 14)),
            created_at=days_ago(random.randint(30, 180)),
        )
        farmers.append(f)
    db.add_all(farmers)
    db.flush()

    # Farmer profiles
    farm_names = [
        "Sunrise Farm", "Musha Wekurimwa", "Green Valley", "Zvimba Estates",
        "Shungu Farm", "Munda Wangu", "Bountiful Acres", "Zunde raMambo",
        "Chimurenga Fields", "Hope Farm", "Harvest Moon", "Kusina Musoro",
        "Makahambe Irrigations", "Ruwa Plot 12", "Mount Pleasant Greens",
    ]
    for f in farmers:
        crops_list = random.sample([c[0] for c in CROPS[:16]], random.randint(1, 4))
        fp = FarmerProfile(
            user_id=f.id,
            farm_name=random.choice(farm_names) + f" ({f.district})",
            farm_size_hectares=round(random.uniform(0.5, 50.0), 1),
            primary_crops=", ".join(crops_list),
            production_scale=random.choice(["SMALLHOLDER", "SMALLHOLDER", "SMALLHOLDER", "MEDIUM", "COMMERCIAL"]),
        )
        db.add(fp)
    db.flush()
    print(f"  ✓ {len(farmers)} farmers created with profiles")

    # ── 3. BUYERS ──────────────────────────────────────────────
    print("\n[3/9] Creating buyers...")
    buyer_pw = _hash("1234")
    buyers = []
    for i in range(15):
        prov, dist = rand_location()
        lat, lng = rand_lat_lng(prov)
        b = User(
            id=uuid.uuid4(),
            phone_number=rand_zw_phone(),
            full_name=rand_name(),
            password_hash=buyer_pw,
            role=UserRole.BUYER,
            status=UserStatus.ACTIVE,
            province=prov,
            district=dist,
            latitude=lat,
            longitude=lng,
            trust_score=random.randint(60, 95),
            risk_score=random.randint(5, 30),
            is_phone_verified=True,
            id_verified=random.random() > 0.3,
            business_verified=random.random() > 0.5,
            balance_usd=round(random.uniform(50, 2000), 2),
            balance_zig=round(random.uniform(1000, 50000), 2),
            last_activity_at=days_ago(random.randint(0, 7)),
            created_at=days_ago(random.randint(30, 180)),
        )
        buyers.append(b)
    db.add_all(buyers)
    db.flush()

    for b in buyers:
        bp = BuyerProfile(
            user_id=b.id,
            company_name=random.choice(COMPANY_NAMES),
            procurement_focus=random.choice(["Grains", "Fresh Produce", "Livestock", "Mixed Commodities", "Export"]),
            buyer_tier=random.choice(["STANDARD", "STANDARD", "PREMIUM", "ENTERPRISE"]),
        )
        db.add(bp)
    db.flush()
    print(f"  ✓ {len(buyers)} buyers created with profiles")

    # ── 4. AGENTS ──────────────────────────────────────────────
    print("\n[4/9] Creating field agents...")
    agent_pw = _hash("1234")
    agent_users = []
    agents = []
    specs = list(AgentSpecialization)
    for i in range(8):
        prov, dist = rand_location()
        au = User(
            id=uuid.uuid4(),
            phone_number=rand_zw_phone(),
            full_name=rand_name(),
            password_hash=agent_pw,
            role=UserRole.AGENT,
            status=UserStatus.ACTIVE,
            province=prov,
            district=dist,
            trust_score=random.randint(75, 99),
            risk_score=random.randint(0, 10),
            is_phone_verified=True,
            id_verified=True,
            training_completed=True,
            practical_passed=True,
            balance_usd=round(random.uniform(20, 500), 2),
            created_at=days_ago(random.randint(60, 365)),
        )
        agent_users.append(au)
    db.add_all(agent_users)
    db.flush()

    for idx, au in enumerate(agent_users):
        code = f"AGT-{au.province[:3].upper()}-{1001 + idx}"
        a = Agent(
            id=uuid.uuid4(),
            user_id=au.id,
            agent_code=code,
            specialization=random.choice(specs),
            status=random.choice([AgentStatus.ACTIVE, AgentStatus.ACTIVE, AgentStatus.BUSY]),
            province=au.province,
            district=au.district,
            rating=round(random.uniform(3.5, 5.0), 1),
            current_load=random.randint(0, 5),
            wallet_balance=round(random.uniform(10, 300), 2),
            pending_earnings=round(random.uniform(0, 80), 2),
            avg_response_time=round(random.uniform(1, 24), 1),
        )
        agents.append(a)
        ap = AgentProfile(
            user_id=au.id,
            assigned_zone=au.district,
            verification_count=random.randint(10, 150),
            agent_level=random.randint(1, 5),
        )
        db.add_all([a, ap])
    db.flush()
    print(f"  ✓ {len(agents)} agents created with profiles")

    # ── 5. DRIVERS / TRANSPORTERS ──────────────────────────────
    print("\n[5/9] Creating drivers...")
    driver_pw = _hash("1234")
    driver_users = []
    for i in range(6):
        prov, dist = rand_location()
        du = User(
            id=uuid.uuid4(),
            phone_number=rand_zw_phone(),
            full_name=rand_name(),
            password_hash=driver_pw,
            role=UserRole.TRANSPORTER,
            status=UserStatus.ACTIVE,
            province=prov,
            district=dist,
            trust_score=random.randint(65, 95),
            is_phone_verified=True,
            balance_usd=round(random.uniform(10, 200), 2),
            created_at=days_ago(random.randint(30, 200)),
        )
        driver_users.append(du)
    db.add_all(driver_users)
    db.flush()

    vehicles = ["Pickup Truck", "3-ton Lorry", "Motorcycle", "10-ton Truck", "Van", "Tractor + Trailer"]
    for du in driver_users:
        veh = random.choice(vehicles)
        cap = {"Pickup Truck": 800, "3-ton Lorry": 3000, "Motorcycle": 100, "10-ton Truck": 10000, "Van": 1500, "Tractor + Trailer": 5000}
        vreg = f"A{random.choice(['BJ','BL','BN','BK','BM'])}-{random.randint(1000,9999)}-{random.choice('ABCDEFGHJKLMNPRSTUVWXYZ')}{random.choice('ABCDEFGHJKLMNPRSTUVWXYZ')}"
        d = Driver(
            id=uuid.uuid4(),
            user_id=du.id,
            vehicle_reg=vreg,
            vehicle_type=veh,
            vehicle_capacity_kg=float(cap.get(veh, 1000)),
            license_number=f"ZW-{random.randint(10000,99999)}",
            license_verified=True,
            insurance_verified=random.random() > 0.3,
            background_cleared=True,
            status=DriverStatus.ACTIVE,
            total_deliveries=random.randint(5, 120),
            successful_deliveries=random.randint(5, 100),
            avg_rating=round(random.uniform(3.5, 5.0), 1),
            current_district=du.district,
        )
        tp = TransporterProfile(
            user_id=du.id,
            vehicle_type=veh,
            carrying_capacity_kg=float(cap.get(veh, 1000)),
            operating_district=du.district,
        )
        db.add_all([d, tp])
    db.flush()
    print(f"  ✓ {len(driver_users)} drivers created")

    # ── 6. LISTINGS ────────────────────────────────────────────
    print("\n[6/9] Creating listings...")
    listings = []
    for _ in range(60):
        seller = random.choice(farmers)
        crop_info = random.choice(CROPS)
        product_type, sector, grade, (pmin, pmax), perishable = crop_info
        price = round(random.uniform(pmin, pmax), 2)
        qty = round(random.uniform(50, 5000), 0)
        lat, lng = rand_lat_lng(seller.province or "Harare")
        age_days = random.randint(0, 60)
        statuses = [ListingStatus.ACTIVE] * 6 + [ListingStatus.SOLD, ListingStatus.PENDING, ListingStatus.EXPIRED]

        l = Listing(
            id=uuid.uuid4(),
            seller_id=seller.id,
            sector=sector,
            product_type=product_type,
            grade=grade,
            quantity=qty,
            quantity_unit="kg",
            price_per_unit=price,
            currency="USD",
            location_province=seller.province,
            location_district=seller.district,
            latitude=lat,
            longitude=lng,
            is_location_verified=random.random() > 0.3,
            status=random.choice(statuses),
            is_perishable=perishable,
            harvest_date=date_ago(random.randint(1, 30)) if random.random() > 0.4 else None,
            storage_requirements=random.choice(["Ambient", "Dry", "Cold Storage", None]),
            crop=product_type,
            verification_status=random.choice(["verified", "verified", "verified", "pending"]),
            ai_verified=random.random() > 0.4,
            ai_confidence=round(random.uniform(0.7, 0.99), 2) if random.random() > 0.3 else None,
            view_count=random.randint(5, 500),
            created_at=days_ago(age_days),
        )
        listings.append(l)
    db.add_all(listings)
    db.flush()
    print(f"  ✓ {len(listings)} listings created")

    # ── 7. OFFERS, ORDERS, TRANSACTIONS ────────────────────────
    print("\n[7/9] Creating offers, orders & transactions...")
    active_listings = [l for l in listings if l.status in (ListingStatus.ACTIVE, ListingStatus.SOLD)]
    order_count = 0
    txn_count = 0
    offers_created = 0

    for l in random.sample(active_listings, min(35, len(active_listings))):
        buyer = random.choice(buyers)
        offer_price = round(l.price_per_unit * random.uniform(0.85, 1.05), 2)
        offer_qty = round(min(l.quantity, random.uniform(50, l.quantity)), 0)

        offer = Offer(
            id=uuid.uuid4(),
            listing_id=l.id,
            buyer_id=buyer.id,
            seller_id=l.seller_id,
            quantity=offer_qty,
            offered_price=offer_price,
            currency="USD",
            status=random.choice([OfferStatus.ACCEPTED, OfferStatus.ACCEPTED, OfferStatus.PENDING, OfferStatus.DECLINED]),
            buyer_message=random.choice([
                "Good quality? Need delivery to Harare.",
                "Can you do bulk discount for 2 tons?",
                "Need by Friday. Let me know.",
                "We buy weekly, interested in supply contract.",
                None,
            ]),
            created_at=l.created_at + timedelta(hours=random.randint(1, 72)),
        )
        db.add(offer)
        db.flush()
        offers_created += 1

        if offer.status == OfferStatus.ACCEPTED:
            total = round(offer_qty * offer_price, 2)
            fee = round(total * 0.035, 2)
            payout = round(total - fee, 2)
            order_num = f"ORD-{random.randint(100000, 999999)}"

            statuses_pool = [OrderStatus.COMPLETED] * 4 + [OrderStatus.ESCROW_HELD, OrderStatus.DELIVERED, OrderStatus.PENDING, OrderStatus.DISPUTED]
            order_status = random.choice(statuses_pool)

            order = Order(
                id=uuid.uuid4(),
                offer_id=offer.id,
                listing_id=l.id,
                buyer_id=buyer.id,
                seller_id=l.seller_id,
                order_number=order_num,
                quantity=offer_qty,
                total_amount=total,
                platform_fee=fee,
                seller_payout=payout,
                currency="USD",
                status=order_status,
                transport_fee=round(random.uniform(2, 25), 2),
                fraud_risk_score=round(random.uniform(0, 0.3), 2),
                fraud_risk_level="low",
                created_at=offer.created_at + timedelta(hours=random.randint(1, 24)),
            )
            db.add(order)
            db.flush()
            order_count += 1

            # Escrow hold transaction
            t1 = Transaction(
                id=uuid.uuid4(),
                order_id=order.id,
                user_id=buyer.id,
                type=TransactionType.ESCROW_HOLD,
                amount=total,
                currency="USD",
                status="completed",
                created_at=order.created_at,
            )
            db.add(t1)
            txn_count += 1

            if order_status in (OrderStatus.COMPLETED, OrderStatus.DELIVERED):
                t2 = Transaction(
                    id=uuid.uuid4(),
                    order_id=order.id,
                    user_id=l.seller_id,
                    type=TransactionType.ESCROW_RELEASE,
                    amount=payout,
                    currency="USD",
                    status="completed",
                    created_at=order.created_at + timedelta(days=random.randint(1, 5)),
                )
                t3 = Transaction(
                    id=uuid.uuid4(),
                    order_id=order.id,
                    user_id=l.seller_id,
                    type=TransactionType.FEE,
                    amount=fee,
                    currency="USD",
                    status="completed",
                    created_at=t2.created_at,
                )
                db.add_all([t2, t3])
                txn_count += 2

                # Trade review
                if random.random() > 0.3:
                    review = TradeReview(
                        id=uuid.uuid4(),
                        order_id=order.id,
                        reviewer_id=buyer.id,
                        reviewee_id=l.seller_id,
                        rating=random.randint(3, 5),
                        comment=random.choice([
                            "Excellent quality maize, well graded.",
                            "Good produce, arrived on time.",
                            "Slightly under quantity but fair quality.",
                            "Fast delivery, will buy again.",
                            "Grade was lower than advertised.",
                            "Professional farmer, highly recommended.",
                        ]),
                        created_at=t2.created_at + timedelta(hours=random.randint(1, 48)),
                    )
                    db.add(review)

            # Disputes for DISPUTED orders
            if order_status == OrderStatus.DISPUTED:
                agent_for_dispute = random.choice(agents)
                d = Dispute(
                    id=uuid.uuid4(),
                    order_id=order.id,
                    raised_by=buyer.id,
                    agent_assigned=agent_for_dispute.user_id,
                    type=random.choice(["quality_issue", "quantity_shortage", "late_delivery", "wrong_product"]),
                    description=random.choice([
                        "Received Grade B instead of Grade A maize.",
                        "Delivery was 200kg short of the agreed amount.",
                        "Product arrived 3 days late, some spoilage.",
                        "Wrong crop type delivered entirely.",
                        "Produce had visible pest damage not disclosed.",
                    ]),
                    status=random.choice([DisputeStatus.OPEN, DisputeStatus.UNDER_REVIEW, DisputeStatus.RESOLVED]),
                    created_at=order.created_at + timedelta(days=random.randint(1, 7)),
                )
                db.add(d)

    db.flush()
    print(f"  ✓ {offers_created} offers, {order_count} orders, {txn_count} transactions")

    # ── 8. PRICE HISTORY ───────────────────────────────────────
    print("\n[8/9] Seeding price history (90 days)...")
    ph_count = 0
    for crop_info in CROPS[:12]:
        product_type, _, grade, (pmin, pmax), _ = crop_info
        for day_offset in range(90):
            price = round(random.uniform(pmin, pmax) * (1 + random.uniform(-0.1, 0.1)), 2)
            prov, _ = rand_location()
            ph = PriceHistory(
                id=uuid.uuid4(),
                product_type=product_type,
                grade=grade,
                location=prov,
                price_per_unit=price,
                date=date_ago(day_offset),
                source=random.choice(["transaction", "market_survey", "agent_report"]),
            )
            db.add(ph)
            ph_count += 1
    db.flush()
    print(f"  ✓ {ph_count} price history records")

    # ── 9. AGENT ASSIGNMENTS ───────────────────────────────────
    print("\n[9/9] Creating agent assignments...")
    assign_count = 0
    for agent in agents:
        for _ in range(random.randint(2, 8)):
            target_listing = random.choice(listings)
            aa = AgentAssignment(
                id=uuid.uuid4(),
                agent_id=agent.id,
                assignment_type=random.choice(["listing", "order", "dispute", "kyc_visit"]),
                listing_id=target_listing.id,
                status=random.choice(["assigned", "accepted", "completed", "completed", "completed"]),
                priority=random.randint(1, 3),
                bounty_amount=round(random.uniform(1, 10), 2),
                agent_notes=random.choice([
                    "Farm visited, crop verified Grade A.",
                    "Weighing confirmed at 2350kg.",
                    "GPS coordinates matched.",
                    None,
                ]),
            )
            db.add(aa)
            assign_count += 1
    db.flush()
    print(f"  ✓ {assign_count} agent assignments")

    # ── COMMIT ─────────────────────────────────────────────────
    db.commit()

    print("\n" + "=" * 60)
    print("  SEED COMPLETE — Demo data ready for presentation!")
    print("=" * 60)
    print(f"""
  Summary:
    Admins:       2    (PIN: Admin@12345678)
    Farmers:      {len(farmers)}   (PIN: 1234)
    Buyers:       {len(buyers)}   (PIN: 1234)
    Agents:       {len(agents)}    (PIN: 1234)
    Drivers:      {len(driver_users)}    (PIN: 1234)
    Listings:     {len(listings)}
    Offers:       {offers_created}
    Orders:       {order_count}
    Transactions: {txn_count}
    Price History: {ph_count}
    Assignments:  {assign_count}

  Login credentials:
    Super Admin:  +263771000001 / Admin@12345678
    Reg. Admin:   +263771000002 / Admin@12345678
    All farmers, buyers, agents, drivers: PIN 1234
""")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        seed(db)
    except Exception as e:
        db.rollback()
        print(f"\n✗ SEED FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()
