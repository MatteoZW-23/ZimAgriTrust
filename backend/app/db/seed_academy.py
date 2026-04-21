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

### Task Volume Bonuses

| Tasks Completed (Monthly) | Bonus |
|--------------------------|-------|
| 50-74 tasks | $10 |
| 75-99 tasks | $25 |
| 100-149 tasks | $50 |
| 150+ tasks | $100 |

### Quality Bonuses

| Metric | Target | Bonus |
|--------|--------|-------|
| Verification accuracy | 100% correct for month | $20 |
| No disputed verifications | Zero disputes raised | $15 |
| Perfect user ratings | 5.0 average (min 10 ratings) | $10 |
| Fastest response time | Top 3 in region | $15 |

---

## 🚗 PART 4: TRAVEL & EXPENSE REIMBURSEMENT

### Mileage/Travel Compensation

| Distance | Reimbursement (USD) |
|----------|---------------------|
| 0-5 km | $0.50 |
| 6-10 km | $1.00 |
| 11-20 km | $2.00 |
| 21-30 km | $3.00 |
| 31-50 km | $5.00 |
| 50+ km | $0.20 per additional km |

### Other Expenses

| Expense Type | Reimbursement | Documentation Required |
|--------------|---------------|----------------------|
| Data/airtime for app use | $5-10/month | Receipt or screenshot |
| Phone maintenance | $5/month | Quarterly claim |
| Equipment replacement | Cost price | Receipt + approval |

---

## 🎁 PART 5: ONE-TIME BONUSES

### Sign-Up & Referral Bonuses

| Bonus Type | Amount | Requirements |
|------------|--------|--------------|
| Academy completion bonus | $25 | Pass final exam (80%+) |
| First 10 tasks bonus | $15 | Complete 10 tasks with >90% accuracy |
| Refer a new agent | $30 | Referred agent completes 50 tasks |
| Refer a farmer | $2 | Farmer completes first transaction |
| Refer a buyer | $5 | Buyer completes first purchase |

### Certification Bonuses

| Level | Bonus | Requirements |
|-------|-------|--------------|
| Certified Agent (Level 1) | $25 | Pass final exam + 10 supervised tasks |
| Senior Agent (Level 2) | $50 | 6 months active + 200 tasks + pass exam |
| Master Agent (Level 3) | $100 | 12 months active + 500 tasks + approval |

---

## 📅 PART 6: PAYMENT SCHEDULE & METHODS

### Payment Schedule

| Payment Type | Frequency | Processing Day | Payout Delay |
|--------------|-----------|----------------|--------------|
| Per-task commissions | Weekly | Every Friday | 7 days (quality check) |
| Monthly bonuses | Monthly | 5th of next month | 5-10 days |
| Travel reimbursement | Weekly | Every Friday | 3 days |
| Referral bonuses | Monthly | 5th of next month | 30 days |

---

## 📈 PART 8: PAYMENT PROCESSING WORKFLOW

1. **Task Completed by Agent**
2. **Quality Check (3-7 days)**: Photos reviewed, GPS verified, Accuracy assessed.
3. **Approved → Payment queued** | **Rejected → Agent notified** (no payment, appeal possible).
4. **Payment Processing (Friday)**: Weekly totals, bonuses, and reimbursements calculated.
5. **Payment Disbursement**: Transfer via EcoCash, OneMoney, or Bank, SMS notification sent.

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
            "topics": [{"id": "3.1", "title": "Crop Grading", "pages": 20}],
            "quiz_questions": {
                 "questions": [
                    {"id": "q3_1", "text": "What is the 'Moisture Threshold' for Grade A Maize?", "options": ["10%", "12.5%", "14%", "15%"], "correct_index": 1},
                    {"id": "q3_2", "text": "How many samples should be taken from a 1-ton listing?", "options": ["1", "3", "5 from different depths", "None"], "correct_index": 2},
                    {"id": "q3_3", "text": "Which tool is used for visual disease detection?", "options": ["Microscope", "The Agent Portal's ML-Camera", "A magnifying glass", "Flashlight"], "correct_index": 1},
                    {"id": "q3_4", "text": "What is 'Foreign Matter' in a grain sample?", "options": ["Grains from other countries", "Stones, dirt, and chaff", "Different colored grains", "Insects"], "correct_index": 1},
                    {"id": "q3_5", "text": "A 'Grade C' crop typically suggests...", "options": ["Premium Quality", "Good for processing only", "Unfit for human consumption", "Medium quality with minor defects"], "correct_index": 3},
                    {"id": "q3_6", "text": "What happens if an Agent finds Aflatoxins in the crop?", "options": ["Mark as Grade C", "Immediate rejection and quarantine", "Mix with better grain", "Wait 10 days"], "correct_index": 1},
                    {"id": "q3_7", "text": "Which photo is mandatory during verification?", "options": ["The Farmer's house", "Close-up of the grain with the batch tag", "The Agent's motorbike", "The nearby road"], "correct_index": 1},
                    {"id": "q3_8", "text": "How is 'Weight' verified in a warehouse?", "options": ["Estimation by eye", "Using a platform scale with a photo of the display", "Taking the farmer's word", "Counting bags"], "correct_index": 1},
                    {"id": "q3_9", "text": "What is 'Admixture' in seed lots?", "options": ["Chemicals", "Other varieties mixed in", "Water", "Dust"], "correct_index": 1},
                    {"id": "q3_10", "text": "What does a 'Pungency Test' apply to?", "options": ["Maize", "Chili/Pepper", "Coffee", "Beans"], "correct_index": 1},
                    {"id": "q3_11", "text": "Who is responsible for the cost of transport to the warehouse?", "options": ["Agent", "Buyer usually", "Farmer usually (pre-negotiated)", "Platform"], "correct_index": 2},
                    {"id": "q3_12", "text": "Internal mold is often caused by...", "options": ["High moisture during storage", "Too much sun", "Insects only", "Bad seeds"], "correct_index": 0},
                    {"id": "q3_13", "text": "What is the 'Batch Identifier'?", "options": ["A serial number for a specific lot of crop", "The Farmer's ID", "The Agent's name", "The date"], "correct_index": 0},
                    {"id": "q3_14", "text": "Which crop requires 'Brix' testing for sugar?", "options": ["Wheat", "Sugarcane/Fruits", "Rice", "Cotton"], "correct_index": 1},
                    {"id": "q3_15", "text": "What happens if the Agent's moisture meter is uncalibrated?", "options": ["Ignore it", "Report a 'Calibration Flag' and use a backup", "Guess the moisture", "Quit"], "correct_index": 1},
                    {"id": "q3_16", "text": "A 'Verified Listing' on the marketplace shows...", "options": ["A green badge", "The Agent's photo", "A 5-star rating", "A generic tick"], "correct_index": 0},
                    {"id": "q3_17", "text": "Maximum allowed 'Broken Grains' for Grade A?", "options": ["1%", "3%", "5%", "10%"], "correct_index": 1},
                    {"id": "q3_18", "text": "What determines 'Purity' in coffee beans?", "options": ["Color sorting and size", "Weight only", "Smell only", "Bag type"], "correct_index": 0},
                    {"id": "q3_19", "text": "What is a 'Representative Sample'?", "options": ["The best sample", "A sample that reflects the true quality of the whole lot", "The smallest sample", "A random photo"], "correct_index": 1},
                    {"id": "q3_20", "text": "Discoloration in grains often indicates...", "options": ["Better nutrition", "Fungal growth or damage", "A rare variety", "Old age"], "correct_index": 1},
                    {"id": "q3_21", "text": "Who provides the 'Standard Grading Guide'?", "options": ["The Farmer", "AgriTrust Operations", "Local Government only", "The Buyer"], "correct_index": 1},
                    {"id": "q3_22", "text": "How many photos are required per verification at minimum?", "options": ["1", "4", "10", "2"], "correct_index": 1},
                    {"id": "q3_23", "text": "What is 'Traceability'?", "options": ["Tracking the crop from farm to consumer", "Finding a farm on a map", "Drawing on the grain", "None"], "correct_index": 0},
                    {"id": "q3_24", "text": "Re-verification is required if...", "options": ["The buyer asks", "The crop sits in storage for >30 days", "The weather is bad", "Always"], "correct_index": 1},
                    {"id": "q3_25", "text": "Passing score for Module 3 Verification Assessment?", "options": ["75%", "80%", "85%", "100%"], "correct_index": 2}
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
                    {"id": "q4_3", "text": "What is the 'Cooling-off Period'?", "options": ["24 hours after a dispute is logged for parties to settle privately", "Time to wait for rain", "The Agent's vacation", "A server maintenance window"], "correct_index": 0},
                    {"id": "q4_4", "text": "Which evidence is prioritized in a quality dispute?", "options": ["Farmer's testimonial", "GPS-tagged photos taken by the Agent at time of seal", "Buyer's unboxing video", "The warehouse receipt"], "correct_index": 1},
                    {"id": "q4_5", "text": "What is 'Arbitration' in AgriTrust?", "options": ["A friendly chat", "A binding decision made by an Auditor when consensus fails", "A court case", "A random coin flip"], "correct_index": 1},
                    {"id": "q4_6", "text": "Which role can NEVER investigate a dispute they were involved in?", "options": ["Administrator", "The original Field Agent", "Neutral Auditor", "Support Team"], "correct_index": 1},
                    {"id": "q4_7", "text": "What is a 'Frivolous Claim'?", "options": ["A valid complaint", "A dispute logged without evidence or merit to delay payment", "A question about fees", "A thank you note"], "correct_index": 1},
                    {"id": "q4_8", "text": "How does a Dispute affect the Escrow funds?", "options": ["Funds are returned to Buyer", "Funds are frozen in the Pool until a resolution is signed", "Funds are paid to the Farmer", "Funds are deleted"], "correct_index": 1},
                    {"id": "q4_9", "text": "What is the maximum resolution timeline for a standard dispute?", "options": ["24 Hours", "72 Hours", "30 Days", "Forever"], "correct_index": 1},
                    {"id": "q4_10", "text": "Which document outlines the dispute process?", "options": ["The AgriTrust Charter", "The Agent Handbook", "The Dispute Resolution SOP (Standard Operating Procedure)", "None"], "correct_index": 2},
                    {"id": "q4_11", "text": "What is 'Escalation'?", "options": ["Moving a case to a higher administrative level", "Increasing the price", "Adding more crops", "Quitting the case"], "correct_index": 0},
                    {"id": "q4_12", "text": "Can a Farmer appeal a resolution decision?", "options": ["Yes, once, if new evidence is provided", "No, decisions are final", "Only if they pay a fee", "Always"], "correct_index": 0},
                    {"id": "q4_13", "text": "What is a 'Site Visit' during investigation?", "options": ["A vacation", "An Auditor visiting the farm or warehouse to inspect disputed stock", "The Buyer visiting the Farmer", "A digital map check"], "correct_index": 1},
                    {"id": "q4_14", "text": "What happens if an Agent is found to have falsified data?", "options": ["A warning", "Immediate de-certification and platform ban", "A $10 fine", "Apology"], "correct_index": 1},
                    {"id": "q4_15", "text": "A 'Partial Settlement' decision means...", "options": ["The Buyer gets half and Farmer gets half", "Payment is adjusted based on actual vs reported quality", "Only half the crops are moved", "The dispute is ignored"], "correct_index": 1},
                    {"id": "q4_16", "text": "Who pays the 'Auditor Fee' in a lost dispute?", "options": ["The losing party (usually deducted from escrow)", "Platform always", "Agent always", "The government"], "correct_index": 0},
                    {"id": "q4_17", "text": "What is 'Evidence Tampering'?", "options": ["Taking better photos", "Altering digital records or physical samples to influence outcome", "Losing a phone", "Cleaning the crops"], "correct_index": 1},
                    {"id": "q4_18", "text": "Which app feature handles dispute evidence upload?", "options": ["The 'Evidence Vault'", "The Chat", "The Gallery", "Email"], "correct_index": 0},
                    {"id": "q4_19", "text": "What is a 'Consensus Agreement'?", "options": ["A vote", "Both parties agreeing to a resolution before arbitration", "The Agent deciding for everyone", "The Buyer winning"], "correct_index": 1},
                    {"id": "q4_20", "text": "If a crop is 'Quarantined', where does it go?", "options": ["Back home", "A certified secure holding area pending final lab results", "The trash", "To the Buyer"], "correct_index": 1},
                    {"id": "q4_21", "text": "The Auditor's report is visible to...", "options": ["Only Admins", "Only the Farmer", "All involved parties", "No one"], "correct_index": 2},
                    {"id": "q4_22", "text": "What happens to the Agent's Trust Score during a dispute?", "options": ["It increases", "It is temporarily flagged but only drops if fault is proven", "It drops immediately", "Nothing ever"], "correct_index": 1},
                    {"id": "q4_23", "text": "A 'Force Majeure' event refers to...", "options": ["Human error", "Uncontrollable events like natural disasters that affect trade", "A stolen phone", "High fees"], "correct_index": 1},
                    {"id": "q4_24", "text": "What is the final step in the dispute lifecycle?", "options": ["Signing the Resolution Certificate and executing funds", "Closing the app", "Deleting the order", "Starting a new trade"], "correct_index": 0},
                    {"id": "q4_25", "text": "Passing score for Module 4 Dispute Resolution?", "options": ["75%", "80%", "85%", "100%"], "correct_index": 2}
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
            "topics": [{"id": "5.1", "title": "Trust Scores", "pages": 10}],
            "quiz_questions": {
                "questions": [
                    {"id": "q5_1", "text": "What is the 'Base Trust Score' for a new certified Agent?", "options": ["50", "85", "100", "0"], "correct_index": 1},
                    {"id": "q5_2", "text": "How many successful trades are needed to reach 'Gold' status?", "options": ["10", "50", "100", "500"], "correct_index": 2},
                    {"id": "q5_3", "text": "Which action has the most positive impact on a Farmer's score?", "options": ["Fast listings", "Consistently high-quality grade A deliveries without disputes", "Buying better equipment", "Being friendly"], "correct_index": 1},
                    {"id": "q5_4", "text": "What is a 'Red Flag' in the reputation system?", "options": ["A decoration", "An indicator of suspicious or fraudulent behavior", "A high-priority trade", "A system update"], "correct_index": 1},
                    {"id": "q5_5", "text": "Trust Score decay refers to...", "options": ["The score dropping over time due to inactivity", "A bug in the system", "Losing points for disputes", "The score getting old"], "correct_index": 0},
                    {"id": "q5_6", "text": "How does a 'Certified Badge' affect an Agent?", "options": ["No change", "Visibility to higher-value institutional buyers", "Higher taxes", "A physical trophy"], "correct_index": 1},
                    {"id": "q5_7", "text": "Which factor is NOT calculated in the Trust Score?", "options": ["Speed of response", "Accuracy of grading", "Personal bank balance", "Volume of trade"], "correct_index": 2},
                    {"id": "q5_8", "text": "What is 'Peer-to-Peer Rating'?", "options": ["Admins rating agents", "Farmers and Buyers rating each other after a trade", "Agents rating other agents", "The public rating the app"], "correct_index": 1},
                    {"id": "q5_9", "text": "A 'Suspended' status occurs when the Trust Score falls below...", "options": ["90", "70", "40", "0"], "correct_index": 2},
                    {"id": "q5_10", "text": "What is the 'Social Trust' component?", "options": ["Facebook likes", "Verification of community/village leadership backing", "Number of WhatsApp contacts", "A party"], "correct_index": 1},
                    {"id": "q5_11", "text": "How long does a 'Negative Feedback' stay on a profile?", "options": ["Forever", "12 Months (for score calculation)", "1 Month", "1 Week"], "correct_index": 1},
                    {"id": "q5_12", "text": "Can a user 'buy' a higher Trust Score?", "options": ["Yes", "No, it is strictly earned through verified performance", "Only if they donate to charity", "Only during promotions"], "correct_index": 1},
                    {"id": "q5_13", "text": "What is a 'Verified Identity' check?", "options": ["Looking at a photo", "Cryptographic matching of government ID and biometrics", "Asking a neighbor", "Checking a social media profile"], "correct_index": 1},
                    {"id": "q5_14", "text": "Which status provides access to low-interest credit via the platform?", "options": ["Newbie", "Silver", "Platinum (based on Trust Score > 95)", "Admin"], "correct_index": 2},
                    {"id": "q5_15", "text": "What does 'Sovereign Integrity' mean in this context?", "options": ["A person's character", "The mathematical assurance that reputation data is tamper-proof", "A large database", "A government rule"], "correct_index": 1},
                    {"id": "q5_16", "text": "Who can see a Farmer's full trade history?", "options": ["Everyone", "No one", "Prospective Buyers before they fund escrow", "Only the government"], "correct_index": 2},
                    {"id": "q5_17", "text": "What is an 'Endorsement'?", "options": ["A paid ad", "A vetted vouch for an Agent by a Senior Lead Auditor", "A sticker", "A signature"], "correct_index": 1},
                    {"id": "q5_18", "text": "How does the ML engine adjust scores?", "options": ["By analyzing patterns of grade inflation or misreporting", "Randomly", "By checking the time", "It doesn't"], "correct_index": 0},
                    {"id": "q5_19", "text": "A 'Market Leader' badge is given to top...", "options": ["10%", "5%", "1%", "50%"], "correct_index": 1},
                    {"id": "q5_20", "text": "What happens if a Farmer is blacklisted?", "options": ["Lower prices", "Immediate loss of access to the platform services", "A warning", "Nothing"], "correct_index": 1},
                    {"id": "q5_21", "text": "The 'Consistency Score' tracks...", "options": ["Variability in quality reports", "Number of days active", "Total weight shipped", "None"], "correct_index": 0},
                    {"id": "q5_22", "text": "How is 'Privacy' maintained for high-reputation users?", "options": ["Blurring their names", "Allowing them to use handles while maintaining verified backing", "Hiding their location", "They have no privacy"], "correct_index": 1},
                    {"id": "q5_23", "text": "What is 'Reputation Portability'?", "options": ["Moving it to another phone", "The ability to export verified trade history for bank loan applications", "Sharing it on social media", "None"], "correct_index": 1},
                    {"id": "q5_24", "text": "Who manages the algorithm logic for Trust Scores?", "options": ["Agents", "The AgriTrust Core Developers and Governance Board", "Users by voting", "The Government"], "correct_index": 1},
                    {"id": "q5_25", "text": "Passing score for Module 5 Reputation Assessment?", "options": ["70%", "75%", "80%", "100%"], "correct_index": 2}
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
            "topics": [{"id": "6.1", "title": "Code of Conduct", "pages": 10}],
            "quiz_questions": {
                "questions": [
                    {"id": "q6_1", "text": "What is the 'Zero-Bribe' policy?", "options": ["Small gifts are okay", "Strict prohibition of any gifts or payments to influence grading", "Payment for speed is allowed", "Only cash is forbidden"], "correct_index": 1},
                    {"id": "q6_2", "text": "What constitutes a 'Conflict of Interest' for an Agent?", "options": ["Knowing the farmer", "Verifying a crop owned by the Agent's own family business without disclosure", "Working on weekends", "Using a personal phone"], "correct_index": 1},
                    {"id": "q6_3", "text": "How should Farmer personal data be handled?", "options": ["Shared with other farmers", "Shared on social media for marketing", "Kept strictly confidential and used only for platform-verified trade", "Deleted immediately"], "correct_index": 2},
                    {"id": "q6_4", "text": "What is 'Fair Pricing' oversight?", "options": ["Setting fixed prices", "Ensuring no party is coerced into a trade through misinformation", "Giving everything away for free", "Low taxes"], "correct_index": 1},
                    {"id": "q6_5", "text": "What is 'Collusion' in the marketplace?", "options": ["Working together", "Secret agreements between Agent and Farmer to defraud the Buyer", "Buying in bulk", "Sharing a ride"], "correct_index": 1},
                    {"id": "q6_6", "text": "Which behavior promotes 'Social Integrity'?", "options": ["Ignoring small errors", "Transparent reporting of all field findings even if unfavorable", "Helping friends first", "Charging extra for help"], "correct_index": 1},
                    {"id": "q6_7", "text": "What is 'Whistleblowing'?", "options": ["Reporting a colleague for ethical violations via the secure platform channel", "Singing", "Calling the police for traffic", "Quitting"], "correct_index": 0},
                    {"id": "q6_8", "text": "Agent accountability means...", "options": ["Blaming the system", "Taking responsibility for the accuracy of one's own signed reports", "Working for free", "Always being right"], "correct_index": 1},
                    {"id": "q6_9", "text": "What happens if an Agent witnesses a Farmer using banned pesticides?", "options": ["Ignore it", "Report a 'Safety Hazard Flag' in the quality assessment", "Buy the crop anyway", "Tell the neighbors"], "correct_index": 1},
                    {"id": "q6_10", "text": "Which entity handles ethical investigations?", "options": ["The Ethics & Compliance Board", "The Farmer's Union", "Other Agents", "Local Government only"], "correct_index": 0},
                    {"id": "q6_11", "text": "Is it ethical to charge a farmer for 'Fast-Track' verification?", "options": ["Yes, for extra effort", "No, all fees must be transparent and platform-sanctioned", "Only if it's a small amount", "Only on holidays"], "correct_index": 1},
                    {"id": "q6_12", "text": "What is 'Price Gouging'?", "options": ["Setting fair prices", "Artificially inflating prices during a shortage to exploit buyers/farmers", "Lowering prices", "Selling at cost"], "correct_index": 1},
                    {"id": "q6_13", "text": "The 'Sovereign Agent Oath' includes...", "options": ["A promise of profit", "A commitment to objective truth and rural empowerment", "A vow of silence", "A promise to work 24/7"], "correct_index": 1},
                    {"id": "q6_14", "text": "Insects in grain samples should be...", "options": ["Hidden", "Reported as 'Infestation' regardless of friendship with the farmer", "Cleaned before photo", "Ignored"], "correct_index": 1},
                    {"id": "q6_15", "text": "What does 'Transparency' mean in trade?", "options": ["Clear windows", "Full disclosure of quality, origin, and fees to all parties", "Sharing everyone's password", "None"], "correct_index": 1},
                    {"id": "q6_16", "text": "Can an Agent buy the crop they just verified?", "options": ["Yes", "No, it is a conflict of interest unless explicitly allowed and disclosed", "Only if they pay more", "Only if it's Grade C"], "correct_index": 1},
                    {"id": "q6_17", "text": "Ethical marketing requires...", "options": ["Exaggerating yields", "Accurate representation of the platform's capabilities and risks", "Promises of wealth", "Using fake photos"], "correct_index": 1},
                    {"id": "q6_18", "text": "What is 'System Integrity'?", "options": ["Having a fast computer", "Using the software correctly without trying to bypass security protocols", "Being a fast typer", "None"], "correct_index": 1},
                    {"id": "q6_19", "text": "How do you handle a Farmer who offers a 'Commission' for a better grade?", "options": ["Accept it", "Reject it and log a 'Solicitation Flag' in the system", "Negotiate", "Tell no one"], "correct_index": 1},
                    {"id": "q6_20", "text": "The 'AgriTrust Code' applies to...", "options": ["Only Agents", "All users (Farmers, Agents, Buyers, Admins)", "Only Admins", "Only the CEO"], "correct_index": 1},
                    {"id": "q6_21", "text": "What is 'Inclusion' in the marketplace?", "options": ["Excluding small farmers", "Ensuring women and marginalized groups have equal access to verification services", "Only working with big farms", "None"], "correct_index": 1},
                    {"id": "q6_22", "text": "What is the penalty for sharing platform passwords?", "options": ["None", "Immediate account termination", "A small warning", "A thank you note"], "correct_index": 1},
                    {"id": "q6_23", "text": "A 'Dishonest Listing' is...", "options": ["A listing with a typo", "Intentional misrepresentation of quantity or crop type", "A listing with no photo", "None"], "correct_index": 1},
                    {"id": "q6_24", "text": "Who is the ultimate guardian of trust in the field?", "options": ["The algorithm", "You (The Agent)", "The Buyer", "The Police"], "correct_index": 1},
                    {"id": "q6_25", "text": "Passing score for Module 6 Ethics?", "options": ["70%", "80%", "90%", "100%"], "correct_index": 1}
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
            "topics": [{"id": "7.1", "title": "Micro-finance Integration", "pages": 15}],
            "quiz_questions": {
                "questions": [
                    {"id": "q7_1", "text": "What is 'Inventory-Backed Lending'?", "options": ["Lending based on a farmer's house", "Loans secured by verified crops currently held in escrow/warehouse", "Loans based on future promises", "Giving away money"], "correct_index": 1},
                    {"id": "q7_2", "text": "How does an Agent's verification help a Farmer get a loan?", "options": ["It doesn't", "It provides the 'Proof of Asset' required by financial partners", "The agent gives the loan", "The agent pays the bank"], "correct_index": 1},
                    {"id": "q7_3", "text": "What is a 'Sovereign Credit Score'?", "options": ["A state-issued score", "A credit rating derived from valid trade history on the AgriTrust ledger", "A social media score", "A bank balance"], "correct_index": 1},
                    {"id": "q7_4", "text": "What is 'Predatory Lending'?", "options": ["Low interest loans", "Loans with extremely high interest rates and unfair terms targeted at the vulnerable", "Loans from family", "Loans for tractors"], "correct_index": 1},
                    {"id": "q7_5", "text": "AgriTrust partners with... to provide credit.", "options": ["Venture Capitalists only", "Approved Micro-Finance Institutions (MFIs) and Impact Funds", "Local shops", "Themselves only"], "correct_index": 1},
                    {"id": "q7_6", "text": "What is 'Crop Insurance' integration?", "options": ["Ensuring a car", "Protecting farmers against yield loss from weather via automatic triggers", "Buying a fence", "Building a dam"], "correct_index": 1},
                    {"id": "q7_7", "text": "What is a 'Smart Contract Loan'?", "options": ["A loan from a person", "A self-executing loan agreement where repayments are automatically deducted from trade settlements", "A loan with a paper contract", "A verbal agreement"], "correct_index": 1},
                    {"id": "q7_8", "text": "What is 'Financial Literacy'?", "options": ["Knowing how to read", "Understanding how to manage money, credit, and savings effectively", "Being rich", "Having a calculator"], "correct_index": 1},
                    {"id": "q7_9", "text": "Why do traditional banks often reject smallholder farmers?", "options": ["They don't like them", "Lack of collateral and verifiable income data", "Too many farmers", "Not enough banks"], "correct_index": 1},
                    {"id": "q7_10", "text": "What is 'Working Capital'?", "options": ["The city of money", "Funds used for day-to-day operations like seeds and fertilizer", "Savings for 10 years", "A large loan for a house"], "correct_index": 1},
                    {"id": "q7_11", "text": "The platform's role in finance is...", "options": ["The Lender", "The Data Provider and Verification Layer", "The Bank", "The Borrower"], "correct_index": 1},
                    {"id": "q7_12", "text": "What is an 'Escrow Repayment Trigger'?", "options": ["A gun", "Automatic repayment of a loan when escrow funds are released to a farmer", "Paying back early", "Forgiving a loan"], "correct_index": 1},
                    {"id": "q7_13", "text": "How is 'Interest Rate' typically expressed?", "options": ["As a dollar amount", "As a percentage of the principal (APR)", "As a bag of grain", "None"], "correct_index": 1},
                    {"id": "q7_14", "text": "What is 'Collateral'?", "options": ["A gift", "An asset pledged to secure a loan (e.g., the crop)", "A debt", "A savings account"], "correct_index": 1},
                    {"id": "q7_15", "text": "What is 'DeFi' in the context of rural finance?", "options": ["Deficit finance", "Decentralized Finance using digital stablecoins for lending", "Deep finance", "Defunct finance"], "correct_index": 1},
                    {"id": "q7_16", "text": "A 'Loan Default' happens when...", "options": ["A farmer gets a loan", "A borrower fails to meet the legal obligations of the loan", "The bank closes", "Prices go up"], "correct_index": 1},
                    {"id": "q7_17", "text": "What is 'Grace Period'?", "options": ["Prayer time", "Time before the first payment is due", "A style of walking", "A gift of money"], "correct_index": 1},
                    {"id": "q7_18", "text": "AgriTrust's 'Credit Engine' analyzes...", "options": ["Farmer's age", "Past trade volume, quality consistency, and dispute history", "Number of cows", "Political views"], "correct_index": 1},
                    {"id": "q7_19", "text": "What are 'Input Credits'?", "options": ["Loans specifically for seeds, fertilizer, and tools", "Credits for phone airtime", "Bank deposits", "None"], "correct_index": 0},
                    {"id": "q7_20", "text": "Who is responsible for the loan repayment?", "options": ["The Agent", "The Farmer (Borrower)", "The Buyer", "The Platform"], "correct_index": 1},
                    {"id": "q7_21", "text": "What is 'Micro-Insurance'?", "options": ["Small insurance for small costs", "Insurance with low premiums for smallholder farmers", "Insurance for insects", "None"], "correct_index": 1},
                    {"id": "q7_22", "text": "A 'Sovereign Wallet' allows farmers to...", "options": ["Store physical money", "Securely receive and manage their digital earnings and credit", "Buy clothes", "None"], "correct_index": 1},
                    {"id": "q7_23", "text": "Why is 'Verified Yield' important for lenders?", "options": ["It looks good", "It reduces risk by proving the farmer actually has the means to repay", "It increases taxes", "None"], "correct_index": 1},
                    {"id": "q7_24", "text": "What is 'Debt-to-Income Ratio'?", "options": ["A math problem", "The percentage of income going toward debt payments", "How much a house costs", "None"], "correct_index": 1},
                    {"id": "q7_25", "text": "Passing score for Module 7 Finance?", "options": ["70%", "75%", "80%", "100%"], "correct_index": 2}
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
            "topics": [{"id": "8.1", "title": "Agricultural Law", "pages": 12}],
            "quiz_questions": {
                "questions": [
                    {"id": "q8_1", "text": "What is a 'Binding Contract'?", "options": ["A friendly promise", "A legal agreement enforceable by law once signed digitaly via the platform", "An email", "A handshake"], "correct_index": 1},
                    {"id": "q8_2", "text": "Which local law governs food safety standards?", "options": ["The Traffic Act", "The Public Health (Food) Act", "The Land Act", "None"], "correct_index": 1},
                    {"id": "q8_3", "text": "What is 'Intellectual Property' in farming?", "options": ["Owning the land", "Protecting rights to unique seeds or process innovations", "Having a tractor", "None"], "correct_index": 1},
                    {"id": "q8_4", "text": "What is 'Land Tenure'?", "options": ["The size of the farm", "The legal regime in which land is owned or occupied", "The crop yield", "The weather"], "correct_index": 1},
                    {"id": "q8_5", "text": "Who is legally responsible for accurate crop grading?", "options": ["The Farmer", "The Field Agent (you) as the signatory of the verification report", "The Buyer", "The Platform developers"], "correct_index": 1},
                    {"id": "q8_6", "text": "What is 'GDPR' compliance?", "options": ["General Data Protection Regulation for privacy", "A grain standard", "A law about tractors", "None"], "correct_index": 0},
                    {"id": "q8_7", "text": "What is 'Force Majeure'?", "options": ["Human error", "Extraordinary events beyond control that excuse contract performance", "A type of harvest", "A bank fee"], "correct_index": 1},
                    {"id": "q8_8", "text": "Which entity issues phytosanitary certificates for export?", "options": ["The Agent", "National Plant Protection Organizations (NPPOs)", "The Farmer", "The USSD app"], "correct_index": 1},
                    {"id": "q8_9", "text": "What is 'Adulteration' under law?", "options": ["Cleaning crops", "Illegal mixing of inferior substances into high-quality grain", "Packing crops", "None"], "correct_index": 1},
                    {"id": "q8_10", "text": "Is digital signature valid in local courts?", "options": ["Yes, under the e-Transactions Act/equivalent", "No", "Only for small amounts", "Only in the city"], "correct_index": 0},
                    {"id": "q8_11", "text": "What is a 'Breach of Contract'?", "options": ["Finishing the work", "Failure to perform any term of a contract without a legitimate legal excuse", "Asking a question", "Updating the app"], "correct_index": 1},
                    {"id": "q8_12", "text": "Agent liability insurance protects against...", "options": ["Car accidents", "Errors and omissions in verification reports", "Rain", "Poor crops"], "correct_index": 1},
                    {"id": "q8_13", "text": "What is 'Traceability' law?", "options": ["Drawing a line", "Mandatory requirement to track food origin for safety", "Finding a farm", "None"], "correct_index": 1},
                    {"id": "q8_14", "text": "What is 'Fair Labor' under platform policy?", "options": ["Working fast", "Ensuring no child or forced labor is used in the production of listed crops", "Paying everyone the same", "Working 24/7"], "correct_index": 1},
                    {"id": "q8_15", "text": "What is 'Indemnity'?", "options": ["A gift", "Compensation for loss or damage provided in a contract", "A fine", "A loan"], "correct_index": 1},
                    {"id": "q8_16", "text": "Which act prevents anti-competitive behavior?", "options": ["The Competition Act", "The Farming Act", "The Seller Act", "None"], "correct_index": 0},
                    {"id": "q8_17", "text": "What is 'Due Diligence'?", "options": ["Working hard", "The care that a reasonable person exercises to avoid harm or error", "Paying taxes", "None"], "correct_index": 1},
                    {"id": "q8_18", "text": "Can a property lease be used as collateral?", "options": ["Yes, depending on local finance laws", "Never", "Only for 1 month", "Only for premium users"], "correct_index": 0},
                    {"id": "q8_19", "text": "What is 'Sub-leasing'?", "options": ["New lease", "Leasing a property to a third party by the original lessee", "Selling a house", "Buying a farm"], "correct_index": 1},
                    {"id": "q8_20", "text": "What is 'Arbitration Clause'?", "options": ["A section about prices", "A contract provision requiring parties to resolve disputes outside of court", "A type of crop", "None"], "correct_index": 1},
                    {"id": "q8_21", "text": "Are international quality standards (ISO) mandatory?", "options": ["Always", "Often required for export-grade trades", "Never", "Only for coffee"], "correct_index": 1},
                    {"id": "q8_22", "text": "What is 'Environmental Compliance'?", "options": ["Weather reports", "Adherence to laws regarding sustainable water and pesticide use", "Planting trees", "None"], "correct_index": 1},
                    {"id": "q8_23", "text": "What is 'Legal Capacity'?", "options": ["Full farm", "The legal ability to enter into a binding contract", "Number of lawyers", "None"], "correct_index": 1},
                    {"id": "q8_24", "text": "Who interprets complex legal disputes on the platform?", "options": ["The Agent", "The Legal Counsel/Governance Committee", "The USSD app", "The Farmer"], "correct_index": 1},
                    {"id": "q8_25", "text": "Passing score for Module 8 Legal?", "options": ["70%", "75%", "80%", "100%"], "correct_index": 2}
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
            "topics": [{"id": "9.1", "title": "Smart Sensing", "pages": 20}],
            "quiz_questions": {
                "questions": [
                    {"id": "q9_1", "text": "What is an 'IoT Sensor'?", "options": ["A smartphone", "An interconnected device that collects and transmits data in real-time", "A satellite", "A laptop"], "correct_index": 1},
                    {"id": "q9_2", "text": "Which sensor measures warehouse humidity?", "options": ["Hygrometer", "Thermometer", "Scale", "GPS"], "correct_index": 0},
                    {"id": "q9_3", "text": "What is 'Remote Sensing'?", "options": ["Using a remote control", "Obtaining info about crops from a distance via satellites or drones", "Touching the crop", "Smelling the grain"], "correct_index": 1},
                    {"id": "q9_4", "text": "What does 'NDVI' measure in drone imagery?", "options": ["Crop weight", "Vegetation health and density", "Soil type", "Wind speed"], "correct_index": 1},
                    {"id": "q9_5", "text": "How does 'Blockchain' enhance tech trust?", "options": ["By making apps faster", "By providing an immutable log of all sensor data readouts", "By increasing battery life", "None"], "correct_index": 1},
                    {"id": "q9_6", "text": "What is a 'Smart Silo'?", "options": ["A clean silo", "A storage unit equipped with automated temperature and aeration controls", "A large silo", "None"], "correct_index": 1},
                    {"id": "q9_7", "text": "What is 'Predictive Analytics'?", "options": ["Guessing the future", "Using historical data and ML to forecast yields and prices", "Reading a map", "Watching the news"], "correct_index": 1},
                    {"id": "q9_8", "text": "Which technology tracks inventory movement in real-time?", "options": ["RFID / QR Codes", "Paper logs", "Counting by hand", "Memory"], "correct_index": 0},
                    {"id": "q9_9", "text": "What is 'Geofencing'?", "options": ["Building a fence", "Virtual geographic boundaries that trigger alerts when assets enter or exit", "Painting the soil", "None"], "correct_index": 1},
                    {"id": "q9_10", "text": "Why use 'Edge Computing' in rural areas?", "options": ["Better graphics", "Processing data locally to save bandwidth and reduce latency in low-connectivity areas", "It is cheaper", "None"], "correct_index": 1},
                    {"id": "q9_11", "text": "What is a 'Soil Moisture Probe'?", "options": ["A tool for digging", "A sensor that measures volumetric water content in soil", "A water pipe", "None"], "correct_index": 1},
                    {"id": "q9_12", "text": "How can ML detect pests in photos?", "options": ["Color analysis", "Pattern recognition of leaf damage and insect presence", "Counting leaves", "None"], "correct_index": 1},
                    {"id": "q9_13", "text": "What is 'Telematics'?", "options": ["Television for farmers", "Long-distance transmission of computer information for farm machinery tracking", "Phone calls", "None"], "correct_index": 1},
                    {"id": "q9_14", "text": "A 'Digital Warehouse Receipt' is backed by...", "options": ["A piece of paper", "Verified IoT weight and quality sensor data", "The manager's word", "None"], "correct_index": 1},
                    {"id": "q9_15", "text": "What is 'Precision Agriculture'?", "options": ["Farming with tools", "Using technology to ensure crops receive exactly what they need for optimum health", "Farming in a city", "None"], "correct_index": 1},
                    {"id": "q9_16", "text": "Which connectivity protocol is best for low-power sensors?", "options": ["5G", "LoRaWAN", "Bluetooth", "Satellite"], "correct_index": 1},
                    {"id": "q9_17", "text": "What is 'Auto-Steer' in tractors?", "options": ["A driver-assist system using GPS for precise rows", "A robot driver", "Self-driving car", "None"], "correct_index": 0},
                    {"id": "q9_18", "text": "What is 'Variable Rate Technology' (VRT)?", "options": ["Different prices", "Applying inputs (seeds, fertilizer) at different rates across a field based on data", "Changing gears in a tractor", "None"], "correct_index": 1},
                    {"id": "q9_19", "text": "How do drones help in dispute resolution?", "options": ["By delivering mail", "By providing high-res bird's eye evidence of field size and health", "By taking selfies", "None"], "correct_index": 1},
                    {"id": "q9_20", "text": "What is 'Yield Mapping'?", "options": ["Finding a farm", "A map showing variability of harvest quality/quantity across a farm area", "A price list", "None"], "correct_index": 1},
                    {"id": "q9_21", "text": "Which device is the primary interface for Ag-Tech in the field?", "options": ["Laptop", "Rugged Tablet or Smartphone", "Desktop PC", "Mainframe"], "correct_index": 1},
                    {"id": "q9_22", "text": "What is 'Data Interoperability'?", "options": ["Sharing data on social media", "The ability of different tech systems to work together and share data", "Buying new software", "None"], "correct_index": 1},
                    {"id": "q9_23", "text": "What is 'Hydroponics' monitoring?", "options": ["Tracking soil", "Tracking nutrient levels in water-based growth systems", "Checking the rain", "None"], "correct_index": 1},
                    {"id": "q9_24", "text": "A 'Sensor Fault' is reported when...", "options": ["The weather is bad", "A device hardware error or anomaly is detected", "The crop is poor", "None"], "correct_index": 1},
                    {"id": "q9_25", "text": "Passing score for Module 9 Ag-Tech?", "options": ["75%", "80%", "85%", "100%"], "correct_index": 2}
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
            "topics": [{"id": "10.1", "title": "Service Standards", "pages": 10}],
            "quiz_questions": {
                "questions": [
                    {"id": "q10_1", "text": "What is the primary goal of an Agent during a farm visit?", "options": ["Getting paid", "Building trust and delivering professional verification service", "Talking to neighbors", "Taking photos only"], "correct_index": 1},
                    {"id": "q10_2", "text": "How should you handle an angry Farmer?", "options": ["Shout back", "Active listening and calm explanation of platform standards", "Walk away immediately", "Agree with everything they say regardless of truth"], "correct_index": 1},
                    {"id": "q10_3", "text": "What is 'Proactive Communication'?", "options": ["Responding to messages", "Informing parties of delays or issues before they become problems", "Talking a lot", "None"], "correct_index": 1},
                    {"id": "q10_4", "text": "Which attire is appropriate for a Field Agent?", "options": ["Formal suit", "Clean professional branded gear or neat casual attire suitable for field work", "Dirty clothes", "Swimwear"], "correct_index": 1},
                    {"id": "q10_5", "text": "What is 'Punctuality' in service?", "options": ["Being early", "Arriving exactly at the scheduled time for verification", "Calling when you are late", "None"], "correct_index": 1},
                    {"id": "q10_6", "text": "What is 'Active Listening'?", "options": ["Hearing words", "Fully concentrating and responding thoughtfully to what is being said", "Waiting to speak", "Nodding only"], "correct_index": 1},
                    {"id": "q10_7", "text": "How do you handle 'Language Barriers'?", "options": ["Speak louder", "Use simple terms, visual aids, or local translation if possible", "Give up", "Ignore the person"], "correct_index": 1},
                    {"id": "q10_8", "text": "What is 'Empathy' in customer service?", "options": ["Feeling sorry", "Understanding and sharing the feelings of the farmer or buyer", "Agreeing with them", "None"], "correct_index": 1},
                    {"id": "q10_9", "text": "Professionalism includes...", "options": ["Being fast", "Integrity, reliability, and respect in all interactions", "Being smart", "None"], "correct_index": 1},
                    {"id": "q10_10", "text": "A 'Premium Agent' is defined by...", "options": ["Their car", "Their high rating (>4.8) and flawless trade consistency", "Their age", "Their clothing"], "correct_index": 1},
                    {"id": "q10_11", "text": "How do you handle a 'Conflict' with a Buyer?", "options": ["Argue", "Refer to the verified data and maintain a calm, objective stance", "Block them", "Agree to a discount"], "correct_index": 1},
                    {"id": "q10_12", "text": "What is 'Feedback Loop'?", "options": ["A repeat sound", "Actively seeking and acting on user feedback to improve service", "Asking for money", "None"], "correct_index": 1},
                    {"id": "q10_13", "text": "A 'Thank You' note after a trade...", "options": ["Is a waste of time", "Builds long-term retention and trust", "Is mandatory", "None"], "correct_index": 1},
                    {"id": "q10_14", "text": "What is 'Personal Branding' for an Agent?", "options": ["A tattoo", "Consistently high service quality that makes you the preferred choice in your region", "A logo", "None"], "correct_index": 1},
                    {"id": "q10_15", "text": "Which skill is most important for dispute de-escalation?", "options": ["Strength", "Emotional Intelligence (EQ)", "Speed", "Technology"], "correct_index": 1},
                    {"id": "q10_16", "text": "What is 'Service Recovery'?", "options": ["Fixing a car", "Correcting a service failure and regaining the user's trust", "Asking for a second chance", "None"], "correct_index": 1},
                    {"id": "q10_17", "text": "How do you ensure 'Safety' in the field?", "options": ["Taking risks", "Adhering to local security protocols and reporting hazards", "Going anywhere at anytime", "None"], "correct_index": 1},
                    {"id": "q10_18", "text": "What is 'Documentation Excellence'?", "options": ["Writing a lot", "Clear, accurate, and complete data entry in every report", "Using fancy words", "None"], "correct_index": 1},
                    {"id": "q10_19", "text": "Who is the 'Internal Customer'?", "options": ["The Farmer", "Colleagues, Admins, and Support staff you interact with", "The Buyer", "The family"], "correct_index": 1},
                    {"id": "q10_20", "text": "What is 'Adaptability'?", "options": ["Changing clothes", "The ability to handle diverse field conditions and different personalities", "Being fast", "None"], "correct_index": 1},
                    {"id": "q10_21", "text": "When should you 'Escalate' a customer issue?", "options": ["Immediately", "When you cannot resolve it within your authorized protocol or competence", "Never", "When you are bored"], "correct_index": 1},
                    {"id": "q10_22", "text": "What is 'Value-Add' service?", "options": ["Adding fees", "Providing helpful tips or info to farmers beyond just verification", "Asking for tips", "None"], "correct_index": 1},
                    {"id": "q10_23", "text": "Maintaining 'Objectivity' means...", "options": ["Being cold", "Not letting personal feelings or relationships affect grading results", "Being fast", "None"], "correct_index": 1},
                    {"id": "q10_24", "text": "What is 'Continuous Improvement'?", "options": ["Buying new tools", "Constantly learning new skills and technologies through the Academy", "Working more hours", "None"], "correct_index": 1},
                    {"id": "q10_25", "text": "Passing score for Module 10 Excellence?", "options": ["80%", "85%", "90%", "100%"], "correct_index": 2}
                ]
            }
        }
    ]

    for m_data in modules:
        # Check if we need to auto-generate questions for modules that are missing them
        if not m_data["quiz_questions"]["questions"]:
            m_data["quiz_questions"]["questions"] = [
                {"id": f"q{m_data['module_number']}_{j}", "text": f"Question {j} for {m_data['title']}?", "options": ["Option A", "Option B", "Option C", "Option D"], "correct_index": 0}
                for j in range(1, 26)
            ]

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
