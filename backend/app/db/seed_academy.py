import uuid
import os
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.academy import AcademyModule

def seed_academy_modules():
    db = SessionLocal()
    modules = [
        {
            "module_number": 1,
            "title": "Platform Operations (Core)",
            "description": "50 pages | 25 quiz questions | Passing Score: 80%",
            "duration_hours": 4.0,
            "order": 1,
            "passing_score": 80.0,
            "topics": [
                {"id": "1.1", "title": "Welcome to AgriTrust", "pages": 5, "content": "# Welcome to AgriTrust\n\nOur mission is to eliminate the 'trust deficit' that plagues rural agricultural markets. In most developing regions, farmers lack access to fair markets and finance because there is no reliable way to verify their yield or quality without expensive intermediaries.\n\nAgriTrust solves this through:\n* **Sovereign Identity**: Giving every farmer a verified digital twin.\n* **Verifiable Proof**: Using field agents (you) to provide ground-truth data.\n* **Smart Escrow**: Ensuring payment is only released when quality is confirmed." },
                {"id": "1.2", "title": "System Architecture Overview", "pages": 8, "content": "# System Architecture\n\nAgriTrust is a multi-layered infrastructure designed for low-connectivity environments:\n\n1. **Core Backend**: A FastAPI-driven engine that handles the ledger, escrow, and user management.\n2. **Agent Portal**: A high-performance web application designed for mobile devices in the field.\n3. **Farmer Interface**: Primarily USSD and WhatsApp-based.\n4. **IoT Gateway**: Automated sensors in warehouses.\n5. **ML Intelligence**: AI models that analyze crop photos." },
                {"id": "1.3", "title": "User Roles & Responsibilities", "pages": 6, "content": "# Roles & Responsibilities\n\n* **Farmers**: The producers. They list crops and request verification.\n* **Agents (You)**: The Verifiers. You are the ONLY source of truth for the digital system.\n* **Buyers**: Wholesalers who purchase listed crops.\n* **Administrators**: Global monitors who handle disputes." },
                {"id": "1.4", "title": "Transaction Lifecycle", "pages": 10, "content": "# The 6 Steps of Trade\n\n1. **Listing**: Farmer lists crops via WhatsApp.\n2. **Commitment**: Buyer deposits 100% of the value into Escrow.\n3. **Verification**: Agent receives notification and travels to the farm.\n4. **Grading**: Agent assigns a Grade based on moisture and purity.\n5. **Delivery**: Crop is moved to a certified warehouse.\n6. **Settlement**: Escrow System automatically releases funds." },
                {"id": "1.5", "title": "Platform Policies", "pages": 6, "content": "# Platform Policies\n\n* **Zero Tolerance for Bribery**: Accepting gifts results in immediate permanent ban.\n* **Data Privacy**: Farmer details must never be shared outside the platform.\n* **Timeliness**: Verification requests must be actioned within 24 hours.\n* **Accuracy**: Intentional misreporting of weight is considered fraud." },
                {"id": "1.6", "title": "Core Agent Functions", "pages": 8, "content": """# 👨💼 AGENTS – MAIN FUNCTIONS ON THE PLATFORM (Simplified)

Here are the **core/primary functions** agents perform on the AgriTrust platform – the essential duties without the detailed breakdown.

---

## 🎯 CORE FUNCTIONS (What Agents Actually Do)

### 1. VERIFY LISTINGS
| # | Function |
|---|----------|
| 1 | Visit farm location |
| 2 | Confirm crops exist |
| 3 | Check quantity (kg/tonnes) |
| 4 | Assess quality grade (A/B/C) |
| 5 | Take geotagged photos |
| 6 | Submit verification report |
| 7 | Approve or reject listing |

### 2. CONFIRM DELIVERIES
| # | Function |
|---|----------|
| 8 | Witness delivery handover |
| 9 | Verify delivered quantity matches order |
| 10 | Check quality at delivery |
| 11 | Take delivery photos |
| 12 | Mark transaction as delivered |

### 3. RESOLVE DISPUTES
| # | Function |
|---|----------|
| 13 | Review evidence (photos, messages) |
| 14 | Interview farmer and buyer |
| 15 | Inspect disputed goods |
| 16 | Determine who is at fault |
| 17 | Recommend resolution (refund/release/partial) |

### 4. SUPPORT FARMERS
| # | Function |
|---|----------|
| 18 | Help farmers register on platform |
| 19 | Teach USSD usage (*123#) |
| 20 | Assist with creating first listing |
| 21 | Help reset forgotten PINs |

### 5. VERIFY LOANS (Financial Services)
| # | Function |
|---|----------|
| 22 | Confirm farmer identity for loan application |
| 23 | Assess farm viability |
| 24 | Submit verification for loan approval |

---

## QUICK SUMMARY TABLE

| Core Function | Description | Priority |
|---------------|-------------|----------|
| **Listing Verification** | Visit farms, inspect crops, grade quality | HIGH |
| **Delivery Confirmation** | Witness handover, verify goods | HIGH |
| **Dispute Resolution** | Investigate, interview, decide outcome | HIGH |
| **Farmer Support** | Onboarding, training, USSD assistance | MEDIUM |
| **Loan Verification** | Confirm farmer details for loans | LOW |"""}
                ,
                {"id": "1.7", "title": "WhatsApp AI Agent Assistant", "pages": 8, "content": """# YOUR WHATSAPP AI ASSISTANT

The WhatsApp bot is not just for farmers; it is your **Field Support AI Agent**.

### Key Capabilities for You
*   **Instant Alerts**: Notifies you of new tasks in real-time.
*   **Verification Checklists**: Guides you through 'Ground Truth' visits.
*   **Earnings Query**: Simply send 'earnings' to see your current balance.
*   **Dispute Setup**: It automatically collects photos from buyers and sellers, so you have evidence ready before you even arrive.

### How it Works
The bot uses **Intent Detection** to simultaneously support thousands of users. It understands if you are an Agent looking for tasks or a Farmer looking for prices.

> **Remember**: The bot handles the 'Digital Data', but YOU handle the 'Physical Reality'. You are a team.""" }
            ],
            "quiz_questions": {
                "questions": [
                    {"id": "q1_1", "text": "What is the primary mission of AgriTrust?", "options": ["Profit Maximization", "Sovereign Trust in Trade", "Data Harvesting", "Government Surveillance"], "correct_index": 1},
                    {"id": "q1_2", "text": "Which interface is the primary tool for Farmers?", "options": ["USSD / WhatsApp", "React Native Pro", "Python Scripting", "Desktop Dashboard"], "correct_index": 0},
                    {"id": "q1_3", "text": "Who is considered the 'Point of Truth' in the field?", "options": ["The Farmer", "The Buyer", "The Field Agent", "The Warehouse Manager"], "correct_index": 2},
                    {"id": "q1_4", "text": "At what stage are funds released to the Farmer?", "options": ["Before planting", "When the buyer orders", "After Agent verification and delivery", "6 months after sale"], "correct_index": 2},
                    {"id": "q1_5", "text": "What happens if an Agent accepts a bribe to inflate a crop grade?", "options": ["A small fine", "A warning email", "Immediate and permanent ban", "Nothing"], "correct_index": 2},
                    {"id": "q1_6", "text": "Which technology ensures that the ledger cannot be tampered with?", "options": ["Excel Spreadsheets", "Blockchain-inspired Immutable Ledger", "Centralized SQL Trigger", "Manual Paper Records"], "correct_index": 1},
                    {"id": "q1_7", "text": "What is the maximum time allowed for a Verification request to be actioned?", "options": ["12 Hours", "24 Hours", "48 Hours", "1 Week"], "correct_index": 1},
                    {"id": "q1_8", "text": "Which hardware device tracks moisture in real-time in warehouses?", "options": ["Smartphone Camera", "IoT Sensor Gateway", "Analog Thermometer", "Laser Pointer"], "correct_index": 1},
                    {"id": "q1_9", "text": "What does 'Sovereign Identity' mean for a farmer?", "options": ["They are controlled by the state", "They own and control their own digital data/credentials", "They have a physical passport", "They are a king"], "correct_index": 1},
                    {"id": "q1_10", "text": "Who triggers the release of funds from Escrow?", "options": ["The Buyer manually", "The Agent via verification app", "The Farmer via WhatsApp", "The Bank Manager"], "correct_index": 1},
                    {"id": "q1_11", "text": "Which backend framework powers the AgriTrust API?", "options": ["Django", "Express.js", "FastAPI", "Ruby on Rails"], "correct_index": 2},
                    {"id": "q1_12", "text": "In a Low-Connectivity zone, how does the Agent app behave?", "options": ["It crashes", "It works in Offline Mode and syncs later", "It requires a Satellite connection", "It disables all features"], "correct_index": 1},
                    {"id": "q1_13", "text": "What is the primary crop listed in the example lifecycle?", "options": ["Maize", "Coffee", "Cocoa", "Wheat"], "correct_index": 0},
                    {"id": "q1_14", "text": "How much of the order value must the buyer deposit into Escrow initially?", "options": ["10%", "50%", "100%", "0%"], "correct_index": 2},
                    {"id": "q1_15", "text": "What is the role of 'ML Intelligence' in the platform?", "options": ["Automated Chatbot", "Crop Disease Detection via Photos", "Financial Auditing", "GPS Tracking"], "correct_index": 1},
                    {"id": "q1_16", "text": "Which document is mandatory for all Field Agents?", "options": ["AgriTrust Operations Handbook", "Generic Driver's License", "Social Media Guidelines", "None"], "correct_index": 0},
                    {"id": "q1_17", "text": "What is the 'Trust Deficit' in agricultural markets?", "options": ["Banks not having enough money", "Lack of verified data between producers and buyers", "Farmers not trusting their neighbors", "High taxes"], "correct_index": 1},
                    {"id": "q1_18", "text": "Which role manages global disputes and certifications?", "options": ["Field Agent", "Administrator", "Customer", "Farmer"], "correct_index": 1},
                    {"id": "q1_19", "text": "What is a 'Digital Twin' in the context of AgriTrust?", "options": ["A second farmer", "A digital representation of a physical asset/identity", "A duplicate database", "A smartphone"], "correct_index": 1},
                    {"id": "q1_20", "text": "What happens if a photo is not GPS-tagged during verification?", "options": ["It is accepted", "It is flagged for review/rejection", "It is automatically blurred", "It is deleted"], "correct_index": 1},
                    {"id": "q1_21", "text": "Which protocol governs the ethical behavior of Agents?", "options": ["Sovereign Protocol", "Nairobi Protocol", "Standard Operating Procedure", "Agent Manual"], "correct_index": 0},
                    {"id": "q1_22", "text": "What is the first step of an AgriTrust trade?", "options": ["Payment", "Listing", "Verification", "Grading"], "correct_index": 1},
                    {"id": "q1_23", "text": "Why do farmers use WhatsApp instead of the mobile app?", "options": ["Apps are too expensive", "Data usage is lower and it works on basic smartphones", "WhatsApp is more secure", "There is no app"], "correct_index": 1},
                    {"id": "q1_24", "text": "The Agent commission is released...", "options": ["Monthly at fixed rate", "Along with the Farmer's settlement", "Before the work starts", "In cash in the field"], "correct_index": 1},
                    {"id": "q1_25", "text": "What is the passing score for Module 1?", "options": ["50%", "75%", "80%", "100%"], "correct_index": 2}
                ]
            }
        },
        {
            "module_number": 2,
            "title": "Escrow & Payment System",
            "description": "40 pages | 25 quiz questions | Passing Score: 80%",
            "duration_hours": 5.0,
            "order": 2,
            "passing_score": 80.0,
            "topics": [
                {"id": "2.1", "title": "Escrow Storage & Legal Flow", "pages": 12, "content": """# 💰 ESCROW & PAYMENT HOLDING - PHYSICALLY & LEGALLY

### 🏛️ WHERE IS THE MONEY STORED?
The escrow money is NOT stored in our company's operating bank account. It is held in separate, dedicated **Trust Accounts** at licensed partner banks (NMB, Agribank, or CBZ).

* **USD Transactions**: Held in a dedicated **USD Trust Account**.
* **ZiG Transactions**: Held in a dedicated **ZiG Trust Account**.
* **EcoCash Transactions**: Held in a **segregated EcoCash Merchant Escrow Wallet**.

**LEGAL PRINCIPLE:** We act as a fiduciary (Trustee). The money never passes through our corporate operational accounts. If the company fails, these funds are legally protected and returned to buyers/sellers.

### ⏱️ THE 4-STAGE MONEY MOVEMENT
1. **Payment**: Buyer pays. Money moves from Buyer to **Escrow Trust Account**.
2. **Holding**: Product is prepared. Money is **FROZEN** (Platform acts as Trustee).
3. **Delivery**: Product arrives. Money stays in **Escrow Holding**.
4. **Release**: Buyer confirms arrival. Money moves to **Seller Virtual Wallet**.

### 🏦 THE WITHDRAWAL PROCESS
When a seller or agent 'withdraws' money:
1. System checks the virtual ledger balance.
2. System instructs the bank/EcoCash to transfer REAL money from the pooled Trust Account to the user's personal account.
3. The money officially leaves the ecosystem.""" },
                {"id": "2.2", "title": "Payment Methods", "pages": 8, "content": """# 📱 FULLY DIGITAL – NO CASH

All transactions on AgriTrust are online-based. We do not use cash for trades or commissions.

### Supported Methods (Zimbabwe)
| Method | Type | Coverage |
|--------|------|----------|
| **EcoCash** | Mobile Money | Nationwide |
| **OneMoney** | Mobile Money | Nationwide |
| **Innbucks** | Mobile Money | Nationwide |
| **Bank Transfer** | Digital | RTGS/Internal |

### Payout Flow
* **Platform Trust Account** → **Farmer/Agent Mobile Wallet**
* No physical visits to banks or offices are required for payment.""" },
                {"id": "2.3", "title": "Fee Structure", "pages": 6, "content": "# Platform Fees\n\n* **Platform Fee**: 2.5% of the gross trade value.\n* **Agent Commission**: Deducted from the platform fee or added as a service charge.\n* **Network Fees**: Standard mobile money or bank fees apply per transaction." },
                {"id": "2.4", "title": "Payment Disputes", "pages": 8, "content": """# 🔒 WHAT IF A DISPUTE HAPPENS?

If a dispute is raised (e.g., poor quality or wrong quantity), the ESCROW is immediately **FROZEN**.

### Dispute Timeline
1. **Dispute Raised**: Buyer or Farmer clicks 'Dispute'.
2. **Funds Frozen**: Money stays in escrow; cannot be released.
3. **Investigation**: Agent (you) visits and reviews evidence.
4. **Resolution**:
   *   **Refund to Buyer** (if farmer at fault)
   *   **Release to Farmer** (if buyer at fault)""" },
                {"id": "2.5", "title": "Regulatory Framework", "pages": 6, "content": """# ⚖️ REGULATORY FRAMEWORK & COMPLIANCE

### 📑 THE TRUST DEED
A Trust Account is NOT owned by the company. It is owned by the Trust. We act as the **Trustee**.
* **Legally Protected**: If AgriTrust goes bankrupt, creditors cannot touch escrow funds.
* **Bank Oversight**: Partner banks (NMB/CBZ) monitor for suspicious activity and only release funds on valid instructions.

### 🇿🇼 RBZ COMPLIANCE
We operate under the **Reserve Bank of Zimbabwe** (RBZ) guidelines for Payment Service Providers:
1. **Zero Commingling**: Operating expenses never touch escrow principal.
2. **AML/KYC**: Mandatory "Know Your Customer" verification for all traders.
3. **Audit Trail**: All transactions recorded for 7 years on the Sovereign Ledger.
4. **Reporting**: Suspicious transactions over $1,000 USD are flagged for review.""" },
                {"id": "2.6", "title": "How Agents Get Paid", "pages": 15, "content": """# 💰 HOW AGENTS GET PAID – Complete Payment Structure

Here is the **complete breakdown** of how agents earn money on the AgriTrust platform.

---

## 📊 PART 1: PAYMENT MODEL OVERVIEW

| Payment Component | Type | Frequency | Priority |
|------------------|------|-----------|----------|
| Per-task commission | Variable | Per completed task | 🔴 HIGH |
| Performance bonus | Variable | Monthly | 🟡 MEDIUM |
| Travel reimbursement | Fixed | Per task | 🟡 MEDIUM |
| Sign-up bonus | Fixed | One-time | 🟢 LOW |
| Referral bonus | Fixed | Per referral | 🟢 LOW |
| Certification bonus | Fixed | One-time | 🟢 LOW |

---

## 💵 PART 2: PER-TASK PAYMENT STRUCTURE

### Task-Based Earnings (Primary Income)

| Task Type | Base Payment (USD) | Bonus Eligibility | Average Time |
|-----------|-------------------|-------------------|--------------|
| Basic listing verification (small farm, <$500) | $3 - $5 | ✅ | 30-45 min |
| Large listing verification (>$500 value) | $8 - $12 | ✅ | 1-2 hours |
| Premium crop verification (tobacco, paprika) | $10 - $15 | ✅ | 1-2 hours |
| Delivery confirmation | $2 - $4 | ❌ | 15-30 min |
| Dispute resolution (basic) | $10 - $15 | ✅ | 1-2 hours |
| Dispute resolution (complex) | $15 - $25 | ✅ | 2-3 hours |
| Farmer onboarding (new user training) | $2 - $3 | ❌ | 30 min |
| Loan application verification | $5 - $8 | ✅ | 45 min |
| Quality audit (random check) | $4 - $6 | ❌ | 30 min |

### Sample Daily Earnings Calculation

```
Morning (4 hours):
├── Large listing verification (maize, 2000kg) → $10
├── Basic listing verification (soybeans) → $4
└── Delivery confirmation → $3

Afternoon (4 hours):
├── Dispute resolution (quality issue) → $12
├── Basic listing verification (wheat) → $4
├── Farmer onboarding (new user) → $3
└── Delivery confirmation → $3

Daily Total = $39
Weekly Total (6 days) = $234
Monthly Total (4 weeks) = $936
```

---

## 🏆 PART 3: PERFORMANCE BONUSES

### Monthly Bonus Tiers

| Tier | Requirements | Bonus Amount |
|------|--------------|--------------|
| **Platinum** | Top 5% performers, >98% accuracy, >4.8 rating, >150 tasks | $150 |
| **Gold** | Top 20% performers, >95% accuracy, >4.5 rating, >120 tasks | $75 |
| **Silver** | Above average, >90% accuracy, >4.0 rating, >80 tasks | $35 |
| **Bronze** | Met minimum requirements, >85% accuracy, >50 tasks | $15 |

---

## ✅ PART 10: SUMMARY TABLE

| Payment Type | Amount Range | Frequency | Processing Time |
|--------------|--------------|-----------|-----------------|
| Basic verification | $3 - $5 | Per task | Weekly |
| Large verification | $8 - $12 | Per task | Weekly |
| Delivery confirmation | $2 - $4 | Per task | Weekly |
| Dispute resolution | $10 - $25 | Per task | Weekly |
| Monthly bonuses | $15 - $150 | Monthly | 5th of month |
| Travel reimbursement | $0.50 - $5+ | Per task | Weekly |
"""}
            ],
            "quiz_questions": {
                "questions": [
                    {"id": "q2_1", "text": "What is the 'Sovereign Escrow Pool'?", "options": ["A private bank account", "A decentralized pool holding funds until contract terms are met", "A government tax fund", "An insurance policy"], "correct_index": 1},
                    {"id": "q2_2", "text": "Who is the 'Escrow Custodian' in the AgriTrust system?", "options": ["The Bank Manager", "The Smart Contract Logic", "The Field Agent", "The Farmer"], "correct_index": 1},
                    {"id": "q2_3", "text": "What does a Buyer do to initiate an order?", "options": ["Sends cash to the agent", "Deposits full amount into Escrow", "Promises to pay later", "Sends a check to the farmer"], "correct_index": 1},
                    {"id": "q2_4", "text": "When is the Escrow released to the Farmer?", "options": ["Upon delivery confirmation", "When the order is placed", "After 30 days regardless of quality", "When the Agent starts traveling"], "correct_index": 0},
                    {"id": "q2_5", "text": "What happens if a Buyer cancels an order after verification but before delivery?", "options": ["Full refund automatically", "Cancellation fee is deducted from the deposit", "Buyer loses 100% of the funds", "No refund possible"], "correct_index": 1},
                    {"id": "q2_6", "text": "Which payment method is NOT supported?", "options": ["Mobile Money", "Stablecoin (Digital Dollars)", "Bank Transfer", "Direct Cash via Post"], "correct_index": 3},
                    {"id": "q2_7", "text": "What is the standard AgriTrust platform fee percentage?", "options": ["1%", "2.5%", "5%", "10%"], "correct_index": 1},
                    {"id": "q2_8", "text": "What is a 'Settlement Ledger'?", "options": ["A book of receipts", "A digital record of all completed transfers", "An unpaid bill list", "A map of warehouses"], "correct_index": 1},
                    {"id": "q2_9", "text": "How does the system prevent 'Double Spending'?", "options": ["By checking IDs", "Through cryptographic sequencing", "By calling the bank", "It doesn't"], "correct_index": 1},
                    {"id": "q2_10", "text": "Which role receives a commission for every successful verification?", "options": ["Farmer", "Buyer", "Field Agent", "Admin Assistant"], "correct_index": 2},
                    {"id": "q2_11", "text": "What happens in a 'Payment Dispute'?", "options": ["Funds stay in Escrow until resolved", "Funds are split 50/50 immediately", "Funds return to Buyer immediately", "Funds go to the Agent"], "correct_index": 0},
                    {"id": "q2_12", "text": "The stability of the payment system is ensured by...", "options": ["USD pegging of digital assets", "Gold bars in a vault", "Trust in the agent", "Government promises"], "correct_index": 0},
                    {"id": "q2_13", "text": "How long does a Farmer have to wait for funds after Agent 'Seals' the deal?", "options": ["Instantly (via Mobile Money)", "2-5 Days", "14 Days", "Upon buyer's secondary approval"], "correct_index": 0},
                    {"id": "q2_14", "text": "What is a 'Flash Audit' in the payment system?", "options": ["A quick look at the books", "Real-time automated reconciliation of pool funds", "A buyer checking their balance", "A farmer asking for more money"], "correct_index": 1},
                    {"id": "q2_15", "text": "Which security measure protects the Agent's wallet?", "options": ["Biometric/PIN authentication", "Physical locks", "Hiding the phone", "Calling support"], "correct_index": 0},
                    {"id": "q2_16", "text": "Can a Farmer withdraw funds to a traditional bank account?", "options": ["Yes, via integrated gateways", "No, only Mobile Money", "No, only cash", "Only if they are premium"], "correct_index": 0},
                    {"id": "q2_17", "text": "What is 'Partial Settlement'?", "options": ["Paying for half the crop", "Settling a portion while investigating a minor dispute", "Paying in two currencies", "Not a feature"], "correct_index": 1},
                    {"id": "q2_18", "text": "The transaction ID is generated...", "options": ["Manually", "At the time of Listing", "After delivery", "By the bank"], "correct_index": 1},
                    {"id": "q2_19", "text": "Who pays the transaction network fees?", "options": ["Farmer only", "Buyer only", "The Seller/Farmer usually has it deducted from the gross", "The platform absorbes all fees"], "correct_index": 2},
                    {"id": "q2_20", "text": "What is a 'Zero-Knowledge Proof' in payments?", "options": ["Proving a transaction is valid without revealing sensitive data", "A type of password", "Knowing nothing about the trade", "A system error"], "correct_index": 0},
                    {"id": "q2_21", "text": "Maximum amount allowed per single Escrow transaction?", "options": ["$1,000", "$10,000", "$50,000", "No limit if verified"], "correct_index": 3},
                    {"id": "q2_22", "text": "Which entity handles the currency conversion?", "options": ["Liquidity Providers", "The Farmer", "The Agent", "The Buyer"], "correct_index": 0},
                    {"id": "q2_23", "text": "Fraudulent payment attempts result in...", "options": ["Warning", "System ban and report to local authorities", "Loss of 10 points", "A retry"], "correct_index": 1},
                    {"id": "q2_24", "text": "What triggers a 'Chargeback' in this system?", "options": ["Nothing (Escrow is finality once settled)", "Buyer's bank request", "Farmer's request", "Agent's request"], "correct_index": 0},
                    {"id": "q2_25", "text": "What is the passing score for Module 2?", "options": ["70%", "80%", "90%", "100%"], "correct_index": 1}
                ]
            }
        },
        {
            "module_number": 3,
            "title": "Crop Verification & Quality Standards",
            "description": "55 pages | 25 quiz questions | Passing Score: 85%",
            "duration_hours": 6.0,
            "order": 3,
            "passing_score": 85.0,
            "topics": [
                {"id": "3.1", "title": "Crop Grading Standards", "pages": 15, "content": """# CROP GRADING & QUALITY STANDARDS
                
AgriTrust uses standardized grading to ensure that buyers get exactly what they pay for. As an agent, your grading is the final word in the transaction.

## 🌽 Maize (Corn) Grading Guide
| Metric | Grade A (Premium) | Grade B (Standard) | Grade C (Industrial) |
|--------|-------------------|-------------------|---------------------|
| Moisture | < 12.5% | 12.5% - 14.0% | 14.1% - 15.5% |
| Broken Grains | < 2% | 2% - 5% | 5% - 10% |
| Foreign Matter | < 0.5% | 0.5% - 1.5% | 1.5% - 3.0% |
| Infestation | ZERO | ZERO | Trace allowed |

## 🛡️ The 'Reject' Criteria
Crops MUST be rejected if you find Aflatoxins (visible mold), chemical residue, or internal heat (indicates fermentation)."""},
                {"id": "3.2", "title": "Sampling Techniques", "pages": 10, "content": """# 🧪 SCIENTIFIC SAMPLING TECHNIQUES

You cannot inspect every grain in a 10-tonne truck. You must use **Representative Sampling**.

## The 5-Point Probe Method
1.  **Bottom-Left**: Insert probe to the base.
2.  **Top-Right**: Insert probe diagonally.
3.  **Center**: Take a core sample from the middle.
4.  **Opposite Corners**: Complete the pattern.

## Guidelines
*   Mix the 5 samples in a clean bucket.
*   Take your test sample from this well-mixed composite.
*   Never take samples only from the top layer; farmers may hide poor quality at the bottom."""},
                {"id": "3.3", "title": "Visual Disease Detection", "pages": 12, "content": """# 🔍 VISUAL DISEASE DETECTION

Your eyes are the first line of defense. Use the Agent App's **AI Lens** to confirm these common issues:

## Common Pathogens
*   **Aflatoxin (Aspergillus)**: Yellow-green mold. Extremely toxic. Must be quarantined.
*   **Maize Lethal Necrosis**: Streaking on leaves and shriveled cobs.
*   **Large Grain Borer**: Visible holes and 'flour' inside the bag.

## Protocol
If you suspect disease, take 3 high-resolution macro photos and flag the listing for 'Senior Audit' review."""},
                {"id": "3.4", "title": "Using Verification Hardware", "pages": 8, "content": """# 📏 HARDWARE CALIBRATION & USE

Every Field Agent is issued a **Sovereign Verification Kit**.

## Tools of the Trade
1.  **Digital Moisture Meter**: Must be calibrated against a known standard every 30 days.
2.  **Bluetooth Platform Scale**: Automatically syncs the weight to the ledger to prevent 'fat-finger' errors.
3.  **GPS Geotagger**: Built into your tablet; ensures you are actually at the farm location.

**Pro-Tip**: Low battery on your moisture meter can cause false high readings. Sync your hardware status daily."""},
                {"id": "3.5", "title": "Batch Tagging & Sealing", "pages": 10, "content": """# 🏷️ TRACEABILITY: BATCH TAGGING

Once verified, the crop must be 'Sealed' to prevent tampering before it reaches the warehouse.

## The Sealing Process
1.  **Generate QR Code**: App creates a unique Batch ID.
2.  **Attach Physical Tag**: Use the high-security tamper-evident tags provided.
3.  **The 'Seal' Photo**: Take a photo of the tag attached to the bags.
4.  **Digital Handover**: The transit driver must scan this QR code to accept responsibility for the goods."""}
            ],
            "quiz_questions": {
                 "questions": [
                    {"id": "q3_1", "text": "What is the 'Moisture Threshold' for Grade A Maize?", "options": ["10%", "12.5%", "14%", "15%"], "correct_index": 1},
                    {"id": "q3_2", "text": "How many samples should be taken from a 1-ton listing?", "options": ["1", "3", "5 from different depths", "None"], "correct_index": 2},
                    {"id": "q3_3", "text": "Which tool is used for visual disease detection?", "options": ["Microscope", "The Agent Portal's ML-Camera", "A magnifying glass", "Flashlight"], "correct_index": 1},
                    {"id": "q3_4", "text": "What is 'Foreign Matter' in a grain sample?", "options": ["Grains from other countries", "Stones, dirt, and chaff", "Different colored grains", "Insects"], "correct_index": 1},
                    {"id": "q3_5", "text": "A 'Grade C' crop typically suggests...", "options": ["Premium Quality", "Good for processing only", "Unfit for human consumption", "Medium quality with minor defects"], "correct_index": 3}
                 ]
            }
        },
        {
            "module_number": 4,
            "title": "Dispute Resolution",
            "description": "50 pages | 25 quiz questions | Passing Score: 85%",
            "duration_hours": 6.0,
            "order": 4,
            "passing_score": 85.0,
            "topics": [
                {"id": "4.1", "title": "Negotiation Hub & Encryption", "pages": 12, "content": """# 🔐 THE NEGOTIATION HUB

The Negotiation Hub is the heart of the buyer-seller relationship. It is **End-to-End Encrypted (E2EE)** by default.

### 🔒 Privacy First
*   **Encrypted State**: Normally, neither Agents nor Admins can read the chat.
*   **Dispute Override**: Only during an active dispute can an Admin grant **temporary decryption access** to a Field Agent.
*   **Audit Logging**: All access is recorded on the immutable ledger for accountability.""" },
                {"id": "4.2", "title": "Dispute Access Protocol", "pages": 10, "content": """# 🔓 ACCESS PROTOCOL

When a dispute is raised, the following workflow is triggered:

1.  **Raise Dispute**: Buyer or Farmer flags a transaction.
2.  **Admin Review**: A global admin assesses the dispute sensitivity.
3.  **Grant Access**: Admin issues a TEMPORARY key (valid for 7 days).
4.  **Agent Investigation**: You gain access to the chat logs and media.
5.  **Revocation**: Access is automatically blocked once the case is resolved.""" },
                {"id": "4.3", "title": "Evidence Analysis", "pages": 15, "content": """# 📜 INVESTIGATION EVIDENCE

During an investigation, you must review:
*   **Chat History**: Promises made regarding grade, price, or timing.
*   **Media**: Photos and videos of the crop before and after shipping.
*   **Verification Reports**: Your original field notes from the farm visit.
*   **Tracking Data**: GPS logs of the transport route.""" },
                {"id": "4.4", "title": "Conflict Resolution Workflow", "pages": 8, "content": """# ⚖️ RESOLUTION DECISIONS

Based on evidence, you will recommend one of the following:

*   **Refund**: Funds return to Buyer.
*   **Release**: Funds move to Farmer.
*   **Partial Settlement**: Funds split based on a compromised quality grade.
*   **Escalation**: Move to a Senior Auditor if evidence is inconclusive.""" }
            ],
            "quiz_questions": {
                "questions": [
                    {"id": "q4_1", "text": "Who is a 'Neutral Auditor' in a resolution case?", "options": ["The Farmer's relative", "An independent certified professional appointed by the platform", "The original Field Agent", "The Buyer's employee"], "correct_index": 1},
                    {"id": "q4_2", "text": "What triggers a 'Dispute' status on an order?", "options": ["A formal disagreement logged by either Buyer or Farmer via the portal", "A late payment only", "A bad weather report", "The Agent being busy"], "correct_index": 0},
                    {"id": "q4_3", "text": "What is the 'Cooling-off Period'?", "options": ["24 hours after a dispute is logged for parties to settle privately", "Time to wait for rain", "The Agent's vacation", "A server maintenance window"], "correct_index": 0}
                ]
            }
        },
        {
            "module_number": 5,
            "title": "Trust & Reputation System",
            "description": "30 pages | 25 quiz questions | Passing Score: 80%",
            "duration_hours": 4.0,
            "order": 5,
            "passing_score": 80.0,
            "topics": [
                {"id": "5.1", "title": "The Trust Score Algorithm", "pages": 10, "content": """# 🌟 THE TRUST SCORE ALGORITHM

Your **Trust Score** is a real-time reflection of your professionalism and accuracy.

## Calculation Weights
*   **Grading Accuracy (40%)**: Does your grade hold up during warehouse audits?
*   **Response Time (30%)**: Are you visiting farms within 24 hours of a request?
*   **User Feedback (20%)**: Professionalism ratings from farmers.
*   **System Integrity (10%)**: Proper tool usage and sync frequency.

A score below **70/100** results in temporary suspension. Below **40/100** is a permanent ban."""},
                {"id": "5.2", "title": "Review & Rating Management", "pages": 10, "content": """# 💬 MANAGING REVIEWS

After every trade, the Farmer rates you. These ratings are public to other famers.

## High-Performance Tips
*   **Explain the Grade**: If a crop is Grade B, explain WHY (e.g., moisture was 13%).
*   **Punctuality**: If delayed, send a WhatsApp message via the app.
*   **Support**: Help the farmer understand how to list their next crop.

**Note**: You can appeal 'bad-faith' reviews if you have evidence (GPS logs/Photos) that the complaint is false."""},
                {"id": "5.3", "title": "Career Progression Levels", "pages": 10, "content": """# 📈 CAREER ADVANCEMENT

AgriTrust is a career path, not just a gig.

## The Levels
1.  **Field Trainee**: You are here. Supervised verification.
2.  **Certified Agent**: Independent verification rights.
3.  **Senior Agent**: High-value listings ($10k+) and MFI loan verification.
4.  **Lead Auditor**: You investigate disputes raised by other agents.

Every level unlocked increases your base commission percentage."""}
            ],
            "quiz_questions": {
                "questions": [
                    {"id": "q5_1", "text": "What is the 'Base Trust Score' for a new certified Agent?", "options": ["50", "85", "100", "0"], "correct_index": 1},
                    {"id": "q5_2", "text": "How many successful trades are needed to reach 'Gold' status?", "options": ["10", "50", "100", "500"], "correct_index": 2}
                ]
            }
        },
        {
            "module_number": 6,
            "title": "Marketplace Ethics & Integrity",
            "description": "35 pages | 25 quiz questions | Passing Score: 80%",
            "duration_hours": 4.0,
            "order": 6,
            "passing_score": 80.0,
            "topics": [
                {"id": "6.1", "title": "Professional Ethics", "pages": 10, "content": """# ⚖️ PROFESSIONAL ETHICS

AgriTrust is built on the **Soveriegn Protocol**. Corruption is the enemy of prosperity.

## Zero Tolerance Policies
*   **No Bribery**: Accepting any gift (cash or kind) results in immediate dismissal.
*   **No Collusion**: Artificially inflating a grade to help a friend is fraud.
*   **No Poaching**: Never encourage farmers to trade 'off-platform' to avoid fees.

**Sanctions**: Violations are recorded on the blockchain and shared with the National Credit Bureau."""},
                {"id": "6.2", "title": "Data Privacy & Security", "pages": 10, "content": """# 🔒 DATA PRIVACY

You handle sensitive farmer data: GPS locations, IDs, and financial earnings.

## The 'Need to Know' Rule
1.  **Confidentiality**: Never share photos of a farmer's warehouse on social media.
2.  **Security**: Your device must be PIN-protected at all times.
3.  **E2EE**: All chats in the Negotiation Hub are encrypted; you only gain access during a dispute."""},
                {"id": "6.3", "title": "Conflict of Interest", "pages": 15, "content": """# 🎭 CONFLICT OF INTEREST

You must remain a **Neutral Point of Truth**.

## Common Scenarios
*   **Family Farms**: You cannot verify a crop owned by a relative.
*   **Side Trades**: You cannot act as a Buyer for a crop you verified.
*   **Competing Platforms**: Disclosure is required if you work for other ag-tech firms.

**Rule**: If you suspect a conflict, click 'Recuse' in the app and the task will be reassigned to another agent."""}
            ],
            "quiz_questions": {
                "questions": [
                    {"id": "q6_1", "text": "What is the 'Zero-Bribe' policy?", "options": ["Small gifts are okay", "Strict prohibition of any gifts or payments to influence grading", "Payment for speed is allowed", "Only cash is forbidden"], "correct_index": 1},
                    {"id": "q6_2", "text": "What constitutes a 'Conflict of Interest' for an Agent?", "options": ["Knowing the farmer", "Verifying a crop owned by the Agent's own family business without disclosure", "Working on weekends", "Using a personal phone"], "correct_index": 1}
                ]
            }
        },
        {
            "module_number": 7,
            "title": "Rural Finance & Credit Access",
            "description": "45 pages | 25 quiz questions | Passing Score: 80%",
            "duration_hours": 5.0,
            "order": 7,
            "passing_score": 80.0,
            "topics": [
                {"id": "7.1", "title": "Inventory-Backed Lending", "pages": 15, "content": """# 🏦 INVENTORY-BACKED LENDING

Millions of farmers have assets (crops) but no cash. We solve this through **Collateralized Verification**.

## The Flow
1.  **Seal**: You verify and tag 10 tonnes of maize.
2.  **Lock**: The listing is locked in the system.
3.  **Lend**: The bank issues a $500 loan to the farmer instantly.
4.  **Settlement**: When a buyer pays $1000, $500 goes to the bank and $500 goes to the farmer.

**Your Role**: You are the 'Collateral Officer'. If you misreport the weight, the bank loses money and you are liable."""},
                {"id": "7.2", "title": "Credit Scoring for Smallholders", "pages": 15, "content": """# 📉 SOVEREIGN CREDIT SCORES

Traditional banks use pay slips. AgriTrust uses **Ledger History**.

## Data Points
*   **Yield Growth**: Is the farmer producing more each year?
*   **Repayment Rate**: Do they fulfill their trade commitments?
*   **Quality Consistency**: Is their maize always Grade A?

Providing this data is the greatest service you offer. It enables farmers to buy tractors and better seeds."""},
                {"id": "7.3", "title": "Insurance & Risk", "pages": 15, "content": """# ⛈️ CLIMATE & CROP INSURANCE

Drought and pests are real risks.

## Integrated Insurance
*   **Parametric Triggers**: If satellite data shows zero rain for 30 days, insurance payouts are triggered.
*   **Verification Audits**: In the event of a total crop loss, you may be sent to verify the field conditions for a claim.

**Note**: Insurance ensures that the farmer (and your commission) survives even a bad season."""}
            ],
            "quiz_questions": {
                "questions": [
                    {"id": "q7_1", "text": "What is 'Inventory-Backed Lending'?", "options": ["Lending based on a farmer's house", "Loans secured by verified crops currently held in escrow/warehouse", "Loans based on future promises", "Giving away money"], "correct_index": 1}
                ]
            }
        },
        {
            "module_number": 8,
            "title": "Legal & Regulatory Framework",
            "description": "40 pages | 25 quiz questions | Passing Score: 80%",
            "duration_hours": 5.0,
            "order": 8,
            "passing_score": 80.0,
            "topics": [
                {"id": "8.1", "title": "The Trust Deed & Terms", "pages": 10, "content": """# 📜 THE SOVEREIGN TRUST DEED

Every user signs the **Global Trust Deed** upon registration. This is the legal foundation of the platform.

## Key Clauses
*   **Escrow Finality**: Once delivery is confirmed, funds are legally irreversible.
*   **Agent Signatory**: Your digital signature on a report makes you a 'Legal Witness' to the quality.
*   **Arbitration**: Disputes are settled by Neutral Auditors, not local courts, to ensure speed."""},
                {"id": "8.2", "title": "Land Tenure & Rights", "pages": 15, "content": """# 🗺️ LAND TENURE & USAGE RIGHTS

Verifying WHO owns the land is as important as the crop.

## Verification Types
1.  **Title Deeds**: Formal ownership.
2.  **Leasehold**: Right to use the land for a specific period.
3.  **Communal Allotment**: Traditional leader's verification.

**Your Job**: Use the app to capture a photo of the land permit/deed. It ensures the buyer isn't buying stolen goods."""},
                {"id": "8.3", "title": "RBZ & Regulatory Compliance", "pages": 15, "content": """# 🇿🇼 REGULATORY COMPLIANCE

We operate under the **Reserve Bank of Zimbabwe** (RBZ) Fintech Sandbox.

## Compliance Rules
*   **AML (Anti-Money Laundering)**: Flag any transaction over $10,000 that seems suspicious.
*   **KYC (Know Your Customer)**: You must verify the farmer's physical National ID.
*   **Zero-Commingling**: Corporate money and Escrow money are stored in different bank accounts."""}
            ],
            "quiz_questions": {
                "questions": [
                    {"id": "q8_1", "text": "What is a 'Binding Contract'?", "options": ["A friendly promise", "A legal agreement enforceable by law once signed digitaly via the platform", "An email", "A handshake"], "correct_index": 1}
                ]
            }
        },
        {
            "module_number": 9,
            "title": "Advanced Ag-Tech & IoT",
            "description": "50 pages | 25 quiz questions | Passing Score: 85%",
            "duration_hours": 6.0,
            "order": 9,
            "passing_score": 85.0,
            "topics": [
                {"id": "9.1", "title": "IoT & Smart Sensors", "pages": 15, "content": """# 📡 IOT & SMART SENSING

Technology is your force-multiplier.

## Connected Tools
*   **Bluetooth Probes**: Measure moisture and protein levels instantly.
*   **Smart Scales**: The weight display is captured via your camera to prevent manual entry errors.
*   **Soil Sensors**: Analyze nitrogen/phosphorous levels to predict future yield.

**Troubleshooting**: If a sensor loses calibration, the app will 'Flag' the report. Use a secondary tool immediately."""},
                {"id": "9.2", "title": "Drone & Satellite Imagery", "pages": 20, "content": """# 🛰️ THE EYE IN THE SKY

We use **Sentinel-2 Satellite Imagery** to verify farm size.

## Drone Operations
*   **NDVI Maps**: Identifying 'hotspots' of disease from the air before you even arrive at the farm.
*   **Area Verification**: Ensuring a farmer isn't claiming 10 hectares when they only have 2.

**Your Role**: You don't need to fly drones, but you must be able to interpret the NDVI (health) maps provided in your dashboard."""},
                {"id": "9.3", "title": "Blockchain & Immutability", "pages": 15, "content": """# 🔗 THE SOVEREIGN LEDGER

AgriTrust does not use a central database for transactions. We use a **Distributed Ledger**.

## Why Immutability Matters
1.  **No Deletions**: Once you sign a report, it can never be deleted or altered.
2.  **Audit Trail**: Every change is recorded with a timestamp and your ID.
3.  **Buyer Confidence**: International buyers trust our data because they know it's mathematically impossible to forge.

**Remember**: Your ID is your reputation. If you sign a false report, it stays on the ledger FOREVER."""}
            ],
            "quiz_questions": {
                "questions": [
                    {"id": "q9_1", "text": "What is an 'IoT Sensor'?", "options": ["A smartphone", "An interconnected device that collects and transmits data in real-time", "A satellite", "A laptop"], "correct_index": 1}
                ]
            }
        },
        {
            "module_number": 10,
            "title": "Premium Customer Excellence",
            "description": "30 pages | 25 quiz questions | Passing Score: 90%",
            "duration_hours": 4.0,
            "order": 10,
            "passing_score": 90.0,
            "topics": [
                {"id": "10.1", "title": "The Golden Service Rule", "pages": 10, "content": """# 🌟 THE GOLDEN SERVICE RULE

As an AgriTrust Agent, you are a consultant, not just a bureaucrat.

## Etiquette
*   **Farm Greet**: Always greet the farmer and village elders respectfully.
*   **Transparency**: Show the moisture meter reading to the farmer. Don't hide the data.
*   **Timeliness**: Arrive on time. A farmer's time is as valuable as yours.

**Goal**: Every farmer should want YOU back for their next harvest."""},
                {"id": "10.2", "title": "Conflict De-escalation", "pages": 10, "content": """# 🧘 CONFLICT DE-ESCALATION

Sometimes a grade isn't what the farmer expected.

## The '3-Step' De-escalation
1.  **Acknowledge**: "I understand you were expecting Grade A."
2.  **Show Evidence**: "The moisture meter shows 14.5%, which is Grade B standards."
3.  **Propose Action**: "If we dry the grain for 2 more days, I can re-verify and it might reach Grade A."

Never argue. Use the technical data to let the platform make the 'bad' news."""},
                {"id": "10.3", "title": "Community Leadership", "pages": 10, "content": """# 📣 COMMUNITY LEADERSHIP

You are the ambassador of technology in the village.

## Your Influence
*   **Digital Literacy**: Teach farmers how to use USSD (*123#).
*   **Market Intelligence**: Share the current regional prices with them.
*   **Ethics**: Be known as the agent who CANNOT be bribed.

**Final Thought**: When the community trusts the agent, the system prospers. Go forth and verify with integrity."""}
            ],
            "quiz_questions": {
                "questions": [
                    {"id": "q10_1", "text": "What is the primary goal of an Agent during a farm visit?", "options": ["Getting paid", "Building trust and delivering professional verification service", "Talking to neighbors", "Taking photos only"], "correct_index": 1}
                ]
            }
        }
    ]

    for m_data in modules:
        # Check if we need to auto-generate questions for modules that are missing them
        if not m_data["quiz_questions"]["questions"] or len(m_data["quiz_questions"]["questions"]) < 25:
            current_questions = m_data["quiz_questions"]["questions"]
            current_q_count = len(current_questions)
            topics = m_data.get("topics", [])
            
            for j in range(current_q_count + 1, 26):
                 # Use topic titles to make questions "meaningful"
                 related_topic = topics[(j-1) % len(topics)] if topics else {"title": "General Protocol"}
                 
                 topic_title = related_topic["title"]
                 m_data["quiz_questions"]["questions"].append({
                    "id": f"q{m_data['module_number']}_{j}", 
                    "text": f"In the context of '{topic_title}', what is the primary operational objective?", 
                    "options": [
                        "Ensuring data integrity and transparency through verified reporting",
                        "Maximizing personal speed regardless of accuracy",
                        "Minimizing farm visits to save transport costs",
                        "Prioritizing buyer preferences over actual farm reality"
                    ], 
                    "correct_index": 0
                 })

    for m_data in modules:
        existing = db.query(AcademyModule).filter(AcademyModule.module_number == m_data["module_number"]).first()
        if existing:
            db.delete(existing)
        
        module = AcademyModule(**m_data)
        db.add(module)
        print(f"Added module {m_data['module_number']}: {m_data['title']}")
    
    db.commit()
    db.close()

if __name__ == "__main__":
    seed_academy_modules()
