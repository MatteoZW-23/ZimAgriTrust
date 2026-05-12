# 🌾 ZimAgriTrust – Canonical System Specification

> **Status:** Authoritative reference. All implementation work must trace back to a function/endpoint/screen listed here.
> **Last updated:** 2026-05-05
> **Total functions:** 348 across 15 categories

---

## PART 1: SYSTEM ARCHITECTURE OVERVIEW

### 1.1 Core System Components

| Component | Description | Technology Stack |
|-----------|-------------|------------------|
| Backend API | Central server handling all logic | Python FastAPI + PostgreSQL + Redis |
| Public Website | Marketing and entry point | React + Tailwind CSS |
| Unified App | Farmer + Buyer mobile/web app | React Native + React Web |
| Driver App | Delivery personnel mobile app | React Native |
| Agent Portal | Verification specialists web portal | React + Tailwind CSS |
| Admin Portal | Platform management web portal | React + Tailwind CSS |
| USSD Gateway | Text-based interface for any phone | Integration with Econet/NetOne/Telecel |
| WhatsApp Bot | Conversational interface | WhatsApp Business API |
| SMS Service | Critical alerts and OTP | Africa's Talking API |
| Database | All platform data | PostgreSQL |
| Cache | Real-time data and sessions | Redis |
| File Storage | Photos and documents | AWS S3 / Cloudinary |

### 1.2 Access Methods Matrix

| User Role | USSD (*123#) | Mobile App | Web App | SMS | WhatsApp |
|-----------|:---:|:---:|:---:|:---:|:---:|
| Farmer | ✅ | ✅ | ✅ | ✅ | ✅ |
| Buyer | ✅ | ✅ | ✅ | ✅ | ✅ |
| Driver | ❌ | ✅ | ❌ | ✅ | ❌ |
| Agent | ❌ | ❌ | ✅ | ✅ | ❌ |
| Admin | ❌ | ❌ | ✅ | ✅ | ❌ |
| Public | ❌ | ❌ | ✅ (limited) | ❌ | ❌ |

---

## PART 2: USER ROLES & RESPONSIBILITIES

### 2.1 Farmer
- **Primary purpose:** Sell agricultural produce
- **Access:** USSD, Mobile App, Web, SMS, WhatsApp
- **Trust score:** 0–100 (impacts listing limits and loan eligibility)
- **Verification:** Phone, ID, Farm location
- **Earning model:** Sales revenue minus 2.5% platform fee

### 2.2 Buyer
- **Primary purpose:** Purchase agricultural produce
- **Access:** USSD, Mobile App, Web, SMS, WhatsApp
- **Trust score:** 0–100 (impacts offer limits and payment terms)
- **Verification:** Phone, ID (Business verification for bulk)
- **Spending model:** Pays goods + 0.5% escrow fee

### 2.3 Driver
- **Primary purpose:** Deliver goods from farms to buyers
- **Access:** Mobile App only
- **Tiers:** New, Standard, Premium, Platinum
- **Commission:** 10–20% depending on tier
- **Verification:** Phone, ID, License, Vehicle registration, Live selfie

### 2.4 Agent
- **Primary purpose:** Verify listings, resolve disputes
- **Access:** Web Portal only
- **Training:** 10 modules + certification exam
- **Payment:** $3–25 per task + monthly bonuses
- **Verification:** ID, Background check, Training completion

### 2.5 Admin
- **Primary purpose:** Platform management and oversight
- **Access:** Web Portal only + MFA
- **Permissions:** Full system access
- **Responsibilities:** User management, transaction monitoring, dispute override
- **Verification:** Internal hiring, MFA

---

## PART 3: COMPLETE FUNCTION LIST (348)

### 3.1 System-Wide (34)

**Authentication & Account Management (1–15)**
1. Phone verification (OTP) via SMS/WhatsApp
2. Register account via USSD/App/Web
3. Login via USSD/App/Web
4. Logout via USSD/App/Web
5. Forgot password via SMS/WhatsApp
6. Change password via App/Web
7. Change PIN via USSD
8. View profile via USSD/App/Web
9. Edit profile via App/Web
10. Upload profile photo via App/Web
11. Delete account via App/Web
12. Select language (English, Shona, Ndebele) via USSD/App/Web
13. View notifications via App/Web/WhatsApp
14. Mark notifications read via App/Web
15. Notification preferences via App/Web

**Verification (16–23)**
16. Phone verification via SMS OTP
17. Identity verification (ID front + back) via App/Web
18. Selfie verification via App/Web
19. Live selfie with handwritten date (drivers only)
20. Farm location verification via Agent visit
21. Business verification via Admin
22. Driver license verification via Admin
23. Vehicle registration verification via Admin

**Trust Score System (24–31)**
24. View trust score via USSD/App/Web
25. View trust score breakdown via App/Web
26. Trust +5 (phone verified)
27. Trust +15 (ID verified)
28. Trust +20 (farm verified)
29. Trust +2 per successful transaction
30. Trust −25 (dispute lost)
31. Trust −50 (fake listing)

**Notification Channels (32–34)**
32. SMS notifications (critical alerts, OTP, payments)
33. WhatsApp notifications (rich messages, offers, disputes)
34. Email notifications (reports, certificates, legal)

### 3.2 Public Website (35–46)
35. View homepage (scroll storytelling)
36. View market snapshot
37. View trending crops
38. View featured listings
39. View how it works
40. View pricing
41. View about us
42. View help center (FAQs)
43. View terms of service
44. View privacy policy
45. Sign up
46. Log in

### 3.3 Farmer Functions (47–81)

**Market & Prices (47–50)**
47. Check crop prices via USSD/App/Web
48. View price trends via App/Web
49. Set price alert via App/Web
50. View demand forecast via App/Web

**Listing Management (51–58)**
51. Create listing via USSD/App/Web
52. Add listing photos via App/Web
53. Edit listing via App/Web
54. Delete listing via USSD/App/Web
55. View my listings via USSD/App/Web
56. View listing stats via App/Web
57. Boost listing (premium $2) via App/Web
58. Expire listing via App/Web

**Offer Management (59–63)**
59. Receive offer notification via SMS/WhatsApp/App
60. View received offers via USSD/App/Web
61. Accept offer via USSD/App/Web
62. Reject offer via USSD/App/Web
63. Counter offer via App/Web

**Order & Delivery (64–68)**
64. View my orders via USSD/App/Web
65. Track order status via USSD/App/Web
66. Confirm delivery via USSD/App/Web
67. Upload delivery proof via App/Web
68. Arrange transport via App/Web

**Wallet & Payments (69–73)**
69. View wallet balance via USSD/App/Web
70. Receive payment (automatic)
71. Withdraw funds via USSD/App/Web
72. View transaction history via App/Web
73. Download receipt via Web

**Trust & Disputes (74–77)**
74. View trust score via USSD/App/Web
75. View trust score breakdown via App/Web
76. Raise dispute via USSD/App/Web
77. Rate buyer via App/Web

**Farming Tools (78–81)**
78. View farming tips via App/Web
79. View weather forecast via App/Web
80. View planting calendar via App/Web
81. Calculate fertilizer needs via App/Web

### 3.4 Buyer Functions (82–113)

**Market & Search (82–88)**
82. Browse listings via USSD/App/Web
83. Search by crop via USSD/App/Web
84. Filter by location via App/Web
85. Filter by price range via App/Web
86. Filter by grade via App/Web
87. Filter by quantity via App/Web
88. Sort listings via App/Web

**Listing Interaction (89–94)**
89. View listing details via USSD/App/Web
90. View seller trust score via USSD/App/Web
91. View seller verification badges via USSD/App/Web
92. Save listing via App/Web
93. Share listing via App/Web
94. Report listing via App/Web

**Offer Management (95–99)**
95. Make offer via USSD/App/Web
96. Negotiate price (counter) via App/Web
97. View my offers via App/Web
98. Cancel offer via App/Web
99. Accept counter-offer via USSD/App/Web

**Order & Delivery (100–105)**
100. View my orders via USSD/App/Web
101. Track order status via USSD/App/Web
102. Confirm delivery via USSD/App/Web
103. Request delivery via App/Web
104. Track delivery in real-time via App
105. View delivery history via App/Web

**Payment & Wallet (106–110)**
106. Pay into escrow via USSD/App/Web
107. View wallet balance via USSD/App/Web
108. Deposit funds via App/Web
109. View transaction history via App/Web
110. Download receipt via Web

**Trust & Disputes (111–113)**
111. View trust score via USSD/App/Web
112. Raise dispute via USSD/App/Web
113. Rate farmer via App/Web

### 3.5 Driver Functions (114–138)

**Registration & Verification (114–119)**
114. Self-register via App
115. Upload National ID via App
116. Upload driver's license via App
117. Upload vehicle registration via App
118. Upload vehicle photo via App
119. Take live selfie with date via App

**Account Management (120–123)**
120. Login via App
121. View profile via App
122. Edit profile via App
123. View verification status via App

**Job Management (124–129)**
124. Go online via App
125. View available jobs (map view) via App
126. Accept job via App
127. Negotiate fare via App
128. Decline job via App
129. Go offline via App

**Navigation & Delivery (130–134)**
130. Navigate to pickup via App
131. Call farmer via App
132. Confirm pickup (photo) via App
133. Navigate to delivery via App
134. Confirm delivery (photo + signature) via App

**Earnings & Performance (135–138)**
135. View earnings (daily/weekly/monthly) via App
136. View transaction history via App
137. Withdraw earnings via App
138. View rating via App

### 3.6 Agent Functions (139–162)

**Application & Certification (139–145)**
139. Apply to be agent via Web
140. Upload documents via Web
141. Complete training modules (10) via Web
142. Take module quizzes via Web
143. Take mid-exam (100 questions) via Web
144. Take final exam (200 questions) via Web
145. View certification status via Web

**Task Management (146–150)**
146. Receive task assignments via SMS + Web
147. View task list via Web
148. Accept task via Web
149. Reject task via Web
150. View task details via Web

**Verification (151–155)**
151. Navigate to farm via Web (GPS)
152. Verify farmer identity via Web
153. Inspect crops via Web
154. Take verification photos (GPS-tagged) via Web
155. Submit verification report via Web

**Dispute Resolution (156–159)**
156. Receive dispute assignment via Web
157. Review evidence via Web
158. Interview parties via Web (phone)
159. Recommend resolution via Web

**Earnings & Performance (160–162)**
160. View earnings via Web
161. View performance stats via Web
162. View ranking via Web

### 3.7 Admin Functions (163–197)

**Dashboard & Monitoring (163–167)**
163. View platform health
164. View real-time metrics
165. View system logs
166. View audit trail
167. View daily summary report

**User Management (168–172)**
168. View all users
169. Verify user documents
170. Suspend user
171. Ban user
172. Reinstate user

**Agent Management (173–176)**
173. View agent applications
174. Approve agent
175. Reject agent
176. Suspend agent

**Driver Management (177–180)**
177. View driver applications
178. Approve driver
179. Reject driver
180. Suspend driver

**Transaction Management (181–184)**
181. View all transactions
182. Freeze transaction
183. Release frozen transaction
184. Process refund

**Dispute Management (185–188)**
185. View all disputes
186. Assign agent to dispute
187. Override agent decision
188. Close dispute

**Platform Configuration (189–193)**
189. Adjust platform fee
190. Adjust escrow fee
191. Adjust agent commission
192. Update system settings
193. Send broadcast (SMS + WhatsApp + Email)

**Reporting (194–197)**
194. Generate daily report
195. Generate weekly report
196. Generate monthly report
197. Export report as PDF

### 3.8 USSD Interface (198–219)

**Main Menu (198–207)**
198. Access main menu (*123#)
199. Check prices (1)
200. Sell crops (2)
201. My listings (3)
202. My orders (4)
203. Make offer (5)
204. My wallet (6)
205. Dispute help (7)
206. My profile (8)
207. Help (0)

**Price Check Sub-menu (208–213)**
208. Maize price
209. Soybeans price
210. Wheat price
211. Sugar beans price
212. Groundnuts price
213. Back to main menu

**Sell Crops Flow (214–219)**
214. Enter crop type
215. Enter quantity (kg)
216. Enter price per kg
217. Enter grade (A/B/C)
218. Enter location
219. Confirm listing

### 3.9 WhatsApp Bot (220–244)

**Market (220–224)**
220. `prices` – current crop prices
221. `forecast` – 7-day prediction
222. `trending` – most-viewed crops
223. `weather [location]`
224. `news` – agriculture headlines

**Listing (225–229)**
225. `sell` – start listing flow
226. `my listings`
227. `edit [id] [field] [value]`
228. `delete [id]`
229. `boost [id]` – $2 premium

**Offer & Order (230–234)**
230. `my offers`
231. `accept [id]`
232. `reject [id]`
233. `counter [id] [price]`
234. `my orders`

**Account (235–239)**
235. `profile`
236. `wallet`
237. `trust`
238. `verify`
239. `withdraw [amount]`

**Support (240–244)**
240. `dispute [id]`
241. `evidence [id]`
242. `agent`
243. `help`
244. `menu`

### 3.10 Notifications (245–287)

**SMS (245–262)** OTP, Welcome, ID approved/rejected/resubmit, Offer received/accepted/rejected, Payment confirmation, Delivery arranged/reminder/confirmed, Payment released, Dispute opened/resolved, Agent assigned, Withdrawal complete, Low balance.

**WhatsApp (263–277)** Offer received (buttons), Offer accepted (payment link), Payment confirmation (receipt), Delivery tracking (live location), Delivery confirmed (photo), Payment released (PDF), Dispute opened (evidence upload), Dispute update (agent contact), Dispute resolved (summary), Agent assignment, Verification report (photo gallery), Price alert (chart), Weather alert, Loan approval, Loan reminder.

**Email (278–287)** Welcome, Weekly summary (PDF), Monthly statement, Transaction receipt, Dispute resolution, Agent certification, Training reminder, Driver approval, Platform update, Security alert.

### 3.11 Escrow & Payment (288–305)

**Payments (288–297)**
288. Initiate payment
289. Select method (EcoCash/OneMoney/Bank)
290. Confirm payment
291. View payment status
292. Receive payment confirmation (webhook)
293. Hold funds in escrow
294. Release funds (after delivery)
295. Process refund (after dispute)
296. Calculate fees (2.5% platform + 0.5% escrow)
297. Generate receipt via email

**Wallet (298–305)**
298. View balance
299. Deposit
300. Withdraw
301. Transaction history
302. Pending transactions
303. Download statement
304. Set auto-withdrawal
305. View fee breakdown

### 3.12 Agent Training Academy (306–320)

**Modules (306–315)**
306. M1 Platform Operations (35q, 80%)
307. M2 Escrow & Payment (35q, 80%)
308. M3 Crop Verification & Quality (46q, 85%)
309. M4 Dispute Resolution (46q, 85%)
310. M5 Trust & Reputation (27q, 80%)
311. M6 Code of Conduct & Ethics (42q, 90%)
312. M7 Financial Services & Loans (35q, 80%)
313. M8 Legal & Regulatory (38q, 80%)
314. M9 Technology & Tools (33q, 85%)
315. M10 Customer Service (40q, 85%)

**Exams (316–320)**
316. Mid-exam (100q)
317. Final exam (200q, 80%)
318. View results
319. Retake (max 2)
320. Download certificate (PDF)

### 3.13 Driver Tiers & Bonuses (321–328)

**Tiers (321–324)**
321. New (0–49 deliveries, 20% commission)
322. Standard (50–199, 4.5⭐, 90% on-time, 15%)
323. Premium (200–499, 4.7⭐, 95% on-time, 12%)
324. Platinum (500+, 4.9⭐, 98% on-time, 10%)

**Bonuses (325–328)**
325. Peak hour +20% (6–9 AM, 4–7 PM)
326. Weekly volume bonus ($5–100)
327. Tier weekly bonus ($10–50)
328. Rating bonus (+$1 per 5⭐)

### 3.14 Logistics & Delivery (329–336)

**Options (329–332)**
329. Farmer delivers
330. Buyer collects
331. Platform driver
332. Cooperative transport

**Tracking (333–336)**
333. Share live location
334. View ETA
335. Receive delay alerts
336. Confirm delivery

### 3.15 Financial Services (337–348)

**Loans (337–344)**
337. Check eligibility
338. Apply for loan
339. View products (input/equipment/expansion/emergency)
340. Calculate repayment
341. View status
342. Make repayment
343. View history
344. Receive disbursement

**Loan Verification (345–348)**
345. Verify purpose (Agent)
346. Assess viability (Agent)
347. Approve (Admin)
348. Reject (Admin)

---

## PART 4: WHAT MUST BE DESIGNED

### 4.1 Database Tables (12)
`users`, `listings`, `transactions`, `disputes`, `drivers`, `agents`, `admin_users`, `training_modules`, `agent_progress`, `notifications`, `audit_logs`, `price_history`.

### 4.2 API Endpoints (45)
- **Auth (5):** `POST /auth/register|login|logout|refresh|forgot-password`
- **Users (5):** `GET /users/me`, `PUT /users/me`, `POST /users/verify-id`, `GET /users/trust-score`, `DELETE /users/me`
- **Listings (6):** `GET /listings`, `GET /listings/{id}`, `POST /listings`, `PUT /listings/{id}`, `DELETE /listings/{id}`, `GET /listings/my`
- **Offers (4):** `POST /listings/{id}/offers`, `GET /offers/received`, `POST /offers/{id}/accept|reject`
- **Transactions (5):** `GET /transactions`, `GET /transactions/{id}`, `POST /transactions/{id}/confirm-delivery|dispute`, `GET /transactions/{id}/status`
- **Wallet (4):** `GET /wallet`, `POST /wallet/deposit|withdraw`, `GET /wallet/transactions`
- **Payments (4):** `POST /payments/initiate`, `GET /payments/{id}/status`, `POST /payments/callback|refund`
- **Agents (5):** `GET /agents/tasks`, `POST /agents/tasks/{id}/accept`, `POST /agents/verification/submit`, `GET /agents/earnings|performance`
- **Admin (7):** `GET /admin/users`, `PUT /admin/users/{id}/suspend`, `GET /admin/agents/pending`, `POST /admin/agents/{id}/approve`, `GET /admin/transactions`, `POST /admin/transactions/{id}/freeze`, `GET /admin/disputes`

### 4.3 Frontend Screens (36)
- **Public Website (6):** Home, How it works, Pricing, About, Help center, Login/Signup
- **Farmer (8):** Dashboard, Create Listing, My Listings, Offers Received, My Orders, Wallet, Profile, Disputes
- **Buyer (7):** Marketplace, Listing Details, My Offers, My Orders, Wallet, Profile, Disputes
- **Driver (5):** Dashboard (map+jobs), Job Details, Navigation, Earnings, Profile
- **Agent (4):** Dashboard, Verification Form, Dispute Resolution, Training Academy
- **Admin (6):** Dashboard, User Mgmt, Agent Mgmt, Transaction Monitor, Dispute Oversight, Platform Settings

### 4.4 USSD Menu Tree
Main menu (1–9, 0 exit) → Price sub-menu, Sell flow.

### 4.5 WhatsApp Intent Flows (20)
Prices, listings, offers, orders, account, support — see §3.9.

### 4.6 Notification Templates (43)
SMS (18) + WhatsApp (15) + Email (10).

### 4.7 Security (8)
- JWT (access 1h, refresh 7d)
- Password ≥8, letters+numbers
- Rate limits: unauth 10/min, farmers/buyers 30/min, admins 120/min
- MFA for Admin
- TLS 1.3 in transit, AES-256 at rest
- Audit log all admin actions, payment events, role changes
- Sessions: USSD 2-min timeout, agent 8h
- OTP: 5-min expiry, 3 attempts max

### 4.8 Integrations (6)
USSD gateway (Econet/NetOne/Telecel) · SMS (Africa's Talking) · WhatsApp Business API · EcoCash · OneMoney · Email (SendGrid/AWS SES).

---

## PART 5: PRIORITY MATRIX

| Priority | Component | Reason |
|---|---|---|
| **P0** | Database schema | Foundation |
| **P0** | Backend API | Core logic |
| **P0** | Authentication | Security |
| **P0** | USSD interface | Core innovation for Zimbabwe |
| **P1** | Public website | User acquisition |
| **P1** | Farmer app screens | Core marketplace |
| **P1** | Buyer app screens | Core marketplace |
| **P1** | SMS notifications | Critical alerts |
| **P2** | Driver app | Logistics |
| **P2** | Agent portal | Verification |
| **P2** | WhatsApp bot | Supplementary channel |
| **P3** | Admin portal | Platform management |
| **P3** | Email notifications | Reports |
| **P3** | Financial services | Loans |

---

## TRACEABILITY

Every PR must reference a function ID from §3 (e.g. `feat(ussd): implement F#214 enter crop type`). Gap analysis lives in `docs/SYSTEM_GAP_ANALYSIS.md`. Roadmap lives in `docs/SYSTEM_ROADMAP.md`.
