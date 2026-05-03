# ZimAgritrust System Specification & Governance

> **Last Updated:** May 1, 2026
> **Status:** Authoritative Master Document

---

## 📋 PART 1: SYSTEM NAME & ACCESS SUMMARY

| Role | Name | USSD | Mobile App | Web Portal |
|------|------|------|------------|------------|
| Farmer | **Farmer** | ✅ Yes | ✅ Yes | ✅ Yes |
| Buyer | **Buyer** | ✅ Yes | ✅ Yes | ✅ Yes |
| Driver | **Driver** | ❌ No | ✅ Yes | ❌ No |
| Agent | **Agent** | ❌ No | ❌ No | ✅ Yes |
| Admin | **Admin** | ❌ No | ❌ No | ✅ Yes |

---

## 🎯 PART 2: THE WHOLE IDEA – ZimAgritrust

### What Is ZimAgritrust?

| Aspect | Description |
|--------|-------------|
| **Name** | ZimAgritrust (Zimbabwe Agricultural Trust Platform) |
| **What it is** | Zimbabwe's first agricultural marketplace connecting farmers directly to buyers |
| **Core Innovation** | USSD technology (*123#) works on ANY phone – no smartphone or internet required |
| **Primary Country** | Zimbabwe |
| **Target Users** | Smallholder farmers (70% of Zimbabwe's population), buyers, delivery drivers |

### The Problem We Solve

| Problem | Before ZimAgritrust | After ZimAgritrust |
|---------|---------------------|---------------------|
| **Market access** | Farmers sell to local middlemen at exploitative prices | Farmers connect directly to buyers nationwide |
| **Price transparency** | Farmers don't know fair market prices | Real-time prices from ZAMACE/GMB via USSD/App/Web |
| **Payment security** | Farmers paid late or never | Escrow holds payment until delivery confirmed |
| **Trust** | Buyers can't verify crop quality | Agents physically verify crops |
| **Disputes** | Farmers have no recourse | Formal dispute resolution process |
| **Logistics** | No reliable transport for farm goods | Driver network for delivery |

---

## 👥 PART 3: WHO IS INVOLVED – All User Types

| Role | Number (Target) | Access Method | Primary Device |
|------|----------------|---------------|----------------|
| **Farmer** | 10,000+ | USSD + App + Web | Any phone + Computer |
| **Buyer** | 2,000+ | USSD + App + Web | Any phone + Computer |
| **Driver** | 500+ | App ONLY | Smartphone |
| **Agent** | 200+ | Web ONLY | Laptop/Desktop |
| **Admin** | 5-10 | Web ONLY | Laptop/Desktop |

---

## 👨‍🌾 PART 4: FARMER – Complete Core Functions (30 Total)

### Access Methods: USSD (*123#) + Mobile App + Web Portal

| # | Function | USSD | App | Web | Description |
|---|----------|------|-----|-----|-------------|
| 1 | Register account | ✅ | ✅ | ✅ | Sign up with phone number |
| 2 | Verify identity | ❌ | ✅ | ✅ | Upload ID and selfie |
| 3 | Check crop prices | ✅ | ✅ | ✅ | View current market prices |
| 4 | View price trends | ❌ | ✅ | ✅ | See historical price charts |
| 5 | Create listing | ✅ | ✅ | ✅ | List crops with quantity, price, grade |
| 6 | Add photos to listing | ❌ | ✅ | ✅ | Upload crop photos |
| 7 | Edit listing | ❌ | ✅ | ✅ | Modify price, quantity, or details |
| 8 | Delete listing | ✅ | ✅ | ✅ | Remove active listing |
| 9 | View my listings | ✅ | ✅ | ✅ | See all active listings |
| 10 | Receive offers | ✅ | ✅ | ✅ | Get notified when buyer makes offer |
| 11 | Accept offer | ✅ | ✅ | ✅ | Agree to buyer's price |
| 12 | Reject offer | ✅ | ✅ | ✅ | Decline buyer's offer |
| 13 | Counter offer | ❌ | ✅ | ✅ | Propose different price |
| 14 | Track orders | ✅ | ✅ | ✅ | See status of accepted offers |
| 15 | Confirm delivery | ✅ | ✅ | ✅ | Mark goods as delivered |
| 16 | Upload delivery proof | ❌ | ✅ | ✅ | Add photos of delivered goods |
| 17 | Receive payment | ✅ | ✅ | ✅ | Get paid via escrow to wallet |
| 18 | View wallet balance | ✅ | ✅ | ✅ | Check available funds |
| 19 | Withdraw funds | ✅ | ✅ | ✅ | Transfer to EcoCash/OneMoney |
| 20 | View transaction history | ❌ | ✅ | ✅ | See all past sales |
| 21 | Rate buyer | ❌ | ✅ | ✅ | Leave feedback after transaction |
| 22 | Raise dispute | ✅ | ✅ | ✅ | Report issues with buyer |
| 23 | Upload dispute evidence | ❌ | ✅ | ✅ | Add photos as proof |
| 24 | Check trust score | ✅ | ✅ | ✅ | View personal reliability score |
| 25 | View trust score breakdown | ❌ | ✅ | ✅ | See how score is calculated |
| 26 | Apply for loan | ❌ | ✅ | ✅ | Request agricultural loan |
| 27 | Check loan status | ❌ | ✅ | ✅ | Track loan application |
| 28 | View farming tips | ❌ | ✅ | ✅ | Read agricultural advice |
| 29 | View weather forecast | ❌ | ✅ | ✅ | Check farming conditions |
| 30 | Contact support | ✅ | ✅ | ✅ | Get help from platform |

### Farmer Trust Score Impact

| Action | Score Change | Who Verifies |
|--------|--------------|--------------|
| Phone verified | +5 | System |
| ID verified | +15 | Admin |
| Farm verified (agent visit) | +20 | Agent |
| Successful transaction | +2 per transaction | System |
| Positive rating from buyer | +5 per rating | Buyer |
| 10 successful transactions | +10 (bonus) | System |
| Dispute raised against farmer | -15 (temporary) | System |
| Dispute ruled against farmer | -25 (permanent) | Admin |
| Fake listing detected | -50 | AI + Admin |
| No activity for 60 days | -10 | System |

---

## 🛒 PART 5: BUYER – Complete Core Functions (27 Total)

### Access Methods: USSD (*123#) + Mobile App + Web Portal

| # | Function | USSD | App | Web | Description |
|---|----------|------|-----|-----|-------------|
| 1 | Register account | ✅ | ✅ | ✅ | Sign up with phone number |
| 2 | Verify identity | ❌ | ✅ | ✅ | Upload ID for higher limits |
| 3 | Verify business | ❌ | ✅ | ✅ | Upload company registration |
| 4 | Browse listings | ✅ | ✅ | ✅ | Search crops by type, location |
| 5 | Filter listings | ❌ | ✅ | ✅ | Apply filters for grade, price, quantity |
| 6 | Sort listings | ❌ | ✅ | ✅ | Order by price, date, trust score |
| 7 | Save favorite listings | ❌ | ✅ | ✅ | Bookmark for later |
| 8 | View listing details | ✅ | ✅ | ✅ | See full listing with photos |
| 9 | View seller trust score | ✅ | ✅ | ✅ | See farmer reliability rating |
| 10 | View price history | ❌ | ✅ | ✅ | See crop price trends |
| 11 | Make offer | ✅ | ✅ | ✅ | Submit price offer on listing |
| 12 | Negotiate price | ❌ | ✅ | ✅ | Counter-offer with farmer |
| 13 | View my offers | ❌ | ✅ | ✅ | See all offers made |
| 14 | Cancel offer | ❌ | ✅ | ✅ | Withdraw offer before acceptance |
| 15 | Pay into escrow | ✅ | ✅ | ✅ | Send payment to platform |
| 16 | View wallet balance | ✅ | ✅ | ✅ | Check available funds |
| 17 | Deposit funds | ❌ | ✅ | ✅ | Add money to wallet |
| 18 | Track orders | ✅ | ✅ | ✅ | See status of purchases |
| 19 | Confirm delivery | ✅ | ✅ | ✅ | Mark goods as received |
| 20 | Request delivery | ❌ | ✅ | ✅ | Arrange transport from farm |
| 21 | Track delivery in real-time | ❌ | ✅ | ✅ | See driver location on map |
| 22 | Rate farmer | ❌ | ✅ | ✅ | Leave feedback after transaction |
| 23 | Raise dispute | ✅ | ✅ | ✅ | Report issues with farmer |
| 24 | Upload dispute evidence | ❌ | ✅ | ✅ | Add photos as proof |
| 25 | View transaction history | ❌ | ✅ | ✅ | See all past purchases |
| 26 | Download receipts | ❌ | ✅ | ✅ | Get PDF proof of purchase |
| 27 | Contact support | ✅ | ✅ | ✅ | Get help from platform |

### Buyer Trust Score Impact

| Action | Score Change | Who Verifies |
|--------|--------------|--------------|
| Phone verified | +5 | System |
| ID verified | +15 | Admin |
| Business verified | +25 | Admin |
| Successful purchase | +2 per transaction | System |
| Positive rating from farmer | +5 per rating | Farmer |
| On-time payment (always) | +2 per transaction | System |
| Dispute raised against buyer | -15 (temporary) | System |
| Dispute ruled against buyer | -25 (permanent) | Admin |
| Payment failure | -10 | System |
| False dispute raised | -30 | Admin |

---

## 🚚 PART 6: DRIVER – Core Functions (15 Total)

### Access Method: Mobile App ONLY

| # | Function | Description |
|---|----------|-------------|
| 1 | Self-register | Download app, create account |
| 2 | Upload documents | ID, license, vehicle registration, live selfie |
| 3 | Get verified | Wait for admin approval (24-48 hours) |
| 4 | Go online | Set availability status |
| 5 | View available jobs | See deliveries on map |
| 6 | Accept job | Choose delivery to perform |
| 7 | Negotiate fare | Counter-offer buyer's proposed price |
| 8 | Navigate to pickup | GPS directions to farm |
| 9 | Confirm pickup | Take photo of loaded goods |
| 10 | Navigate to delivery | GPS directions to buyer |
| 11 | Confirm delivery | Take photo of delivered goods, get signature |
| 12 | View earnings | See daily/weekly totals |
| 13 | Withdraw earnings | Transfer to EcoCash |
| 14 | View rating | See customer feedback |
| 15 | Go offline | Stop receiving job requests |

### Driver Tiers & Commission

| Tier | Deliveries | Rating | On-Time | Commission | Driver Keeps |
|------|------------|--------|---------|------------|--------------|
| New | 0-49 | Any | Any | 20% | 80% |
| Standard | 50-199 | 4.5+ | 90%+ | 15% | 85% |
| Premium | 200-499 | 4.7+ | 95%+ | 12% | 88% |
| Platinum | 500+ | 4.9+ | 98%+ | 10% | 90% |

---

## 👨‍💼 PART 7: AGENT – Core Functions (15 Total)

### Access Method: Web Portal ONLY

| # | Function | Description |
|---|----------|-------------|
| 1 | Apply to be agent | Submit application via web portal |
| 2 | Complete training | 10 modules, 377 questions |
| 3 | Pass certification | Final exam (200 questions, 80% required) |
| 4 | Receive task assignments | Get notified of listings to verify |
| 5 | Accept/reject tasks | Choose which verifications to perform |
| 6 | Navigate to farm | GPS directions to farmer location |
| 7 | Verify farmer identity | Check ID matches profile |
| 8 | Inspect crops | Confirm existence, quantity, grade |
| 9 | Take verification photos | Upload GPS-tagged, timestamped photos |
| 10 | Submit verification report | Send findings to platform |
| 11 | Witness delivery | Confirm handover for high-value transactions |
| 12 | Investigate disputes | Collect evidence, interview parties |
| 13 | Recommend resolution | Propose refund or payment |
| 14 | View earnings | See commission from verifications |
| 15 | Track performance | Monitor accuracy, rating, response time |

### Agent Verification Payments

| Task Type | Payment |
|-----------|---------|
| Basic listing verification | $3-5 |
| Large listing (>$500) | $8-12 |
| Premium crop | $10-15 |
| Delivery confirmation | $2-4 |
| Dispute resolution | $10-25 |
| Farmer onboarding | $2-3 |

---

## 👑 PART 8: ADMIN – Core Functions (15 Total)

### Access Method: Web Portal ONLY + MFA

| # | Function | Description |
|---|----------|-------------|
| 1 | Monitor platform health | Check API, database, services status |
| 2 | Verify user documents | Approve/reject ID uploads |
| 3 | Approve agents | Review and approve agent applications |
| 4 | Approve drivers | Review and approve driver applications |
| 5 | Manage users | Suspend, verify, or ban users |
| 6 | Monitor transactions | View all platform transactions |
| 7 | Freeze transactions | Temporarily hold suspicious payments |
| 8 | Override disputes | Make final decisions on appealed cases |
| 9 | Adjust platform fees | Change commission percentages |
| 10 | Send broadcast messages | Notify all users |
| 11 | Generate reports | Daily, weekly, monthly platform analytics |
| 12 | Manage ML models | Trigger retraining of price/risk models |
| 13 | View audit logs | See all admin actions for compliance |
| 14 | Manage backups | Configure and restore database backups |
| 15 | Configure system settings | Update thresholds, limits, features |

---

## 📊 PART 9: ACCESS METHOD COMPARISON

| Feature | USSD | Mobile App | Web Portal |
|---------|------|------------|------------|
| **Works on any phone** | ✅ Yes | ❌ No (smartphone only) | ❌ No (computer only) |
| **Requires internet** | ❌ No | ✅ Yes | ✅ Yes |
| **Can upload photos** | ❌ No | ✅ Yes | ✅ Yes |
| **Can view maps** | ❌ No | ✅ Yes | ✅ Yes |
| **Real-time tracking** | ❌ No | ✅ Yes | ✅ Yes |
| **Best for** | Quick transactions | Full features | Management |

---

## 🏛️ PART 10: INSTITUTIONAL GOVERNANCE CHARTER

*Aligned with the National Development Strategy 1 (NDS1) Protocols*

*Last Updated: April 18, 2026 | Document ID: AT-GOV-2026-V4.3.1*

### 1. Preamble & Mandate

ZimAgritrust serves as the authoritative digital twin and national command infrastructure for the agricultural trade sector of Zimbabwe. Accessing the Command Center, Market Terminal, Logistics Network, or Field Agent Bridge constitutes a legally binding operational contract governed by the National Escrow Registry and Ministry guidelines. Use of this platform signifies total institutional compliance.

### 2. Professional Conduct & AI Integrity

The platform utilizes Sovereign AI, an **AI Price Oracle**, and **Regional Yield Telemetry** to stabilize national markets. All platform stakeholders ("Users") must acknowledge that:

* **Algorithmic Neutrality:** Automated price deviations exceeding 20% from the National Commodity Index will trigger a Mandatory Audit. Refusal of audit leads to immediate suspension.
* **Non-Interference:** Manipulating scraping metrics, market trend data, or institutional risk scores is classified as a Tier-1 security violation and federal offense.
* **USSD / Terminal Integrity:** Access via unstructured supplementary service data (USSD) channels is monitored; spamming or overloading telecom bridges will result in temporary lockouts.

### 3. The National Escrow & Logistics Protocol

ZimAgritrust utilizes a high-friction, zero-trust financial architecture to ensure total trade security:

* **Funds Commitment:** Buyers are strictly required to securely commit 100% of the trade value to the multisig escrow vault before any production movement is authorized.
* **Logistics & Handover Verification:** Production must be transported by registered logistics partners. Producers and Logistics Operators must provide 'Grade-A' certificates, matched by Secure Handover Codes at delivery, to trigger escrow release.
* **Irreversible Settlement:** Once a 'Release Handshake' and logistics delivery confirmation are executed, the transaction is finalized on the ledger. Reversals are only permitted during the 'Dispute Adjudication' phase by an authorized Lead Governance Administrator.

### 4. Account Suspension & Absolute Revocation

ZimAgritrust maintains a strict, zero-tolerance policy against system-wide trust erosion. Platform access is a sovereign privilege, not a right.

#### 4.1 Tiered Disciplinary Triggers

* **Trust Index Breach:** Any account whose AI-computed Trust Score falls below the **40% Critical Floor** is subject to immediate algorithmic suspension.
* **Synthetic Listing Fraud:** Falsifying inventory levels, grade certificates, or grain moisture content will result in permanent identity revocation and referral to law enforcement.
* **Identity Falsification:** Mismatches between the National ID Registry and platform biometrics/KYC will result in an automatic platform block and financial asset freeze.
* **Escrow Collusion:** Colluding with field agents or logistics carriers to release funds without physical delivery of sovereign assets leads to immediate platform blacklisting.

### 5. Dispute Resolution & Arbitration Waitlist

In the event of a commercial dispute, the **Regional Adjudication Hub** serves as the primary arbiter.

1. **Direct Settlement Proposals:** Parties are required to attempt dispute de-escalation via the Direct Settlement offering system (e.g., initiating a discount percentage).
2. **Institutional Arbitration (Escalation):** If parties cannot reach an accord, an ZimAgritrust Lead Agent or HQ Admin will be dispatched for binding adjudication. The administrator's decision regarding escrow allocation (refund vs. release) is final.

### 6. Data Governance & Sovereignty

ZimAgritrust is the primary custodian of sensitive agricultural, geographic, and financial metadata.

* **Encryption:** All identity files, financial holdings, and transport manifests are encrypted-at-rest using AES-256 protocols.
* **Persistent Auditability:** Every keystroke, trade execution, and status change within the Command Center is indelibly logged in the **Persistent System Audit Ledger**.
* **Data Sovereignty:** All regional telemetry and yield data remain the exclusive property of the sovereign network for macroeconomic planning (NDS1 directives).

---

**By continuing to use the ZimAgritrust Command Center, Mobile Interface, or USSD services, you affirm your absolute commitment to the National Agricultural Code of Ethics.**
