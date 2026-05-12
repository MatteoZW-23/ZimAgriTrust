import uuid
import os
import json
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.academy import AcademyModule

TRAINING_MATERIALS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "training-materials")
)

MODULE_MATERIAL_DIRS = {
    1: "module_1_platform_operations",
    2: "module_2_escrow_and_payment",
    3: "module_3_crop_verification_quality",
    4: "module_4_dispute_resolution",
    5: "module_5_trust_reputation",
    6: "module_6_ethics_integrity",
    7: "module_7_rural_finance_credit",
    8: "module_8_legal_regulatory",
    9: "module_9_agtech_iot",
    10: "module_10_customer_excellence",
}


def _module_material_paths(module_number: int) -> tuple[str, str]:
    module_dir = MODULE_MATERIAL_DIRS[module_number]
    handbook_path = os.path.join(TRAINING_MATERIALS_DIR, module_dir, f"handbook_m{module_number}.txt")
    quiz_path = os.path.join(TRAINING_MATERIALS_DIR, module_dir, f"quiz_m{module_number}.json")
    return handbook_path, quiz_path


def _load_module_quiz(module_number: int) -> dict | None:
    _, quiz_path = _module_material_paths(module_number)
    if not os.path.exists(quiz_path):
        return None
    with open(quiz_path, "r", encoding="utf-8") as quiz_file:
        quiz_data = json.load(quiz_file)
    return {"questions": quiz_data.get("questions", [])}

def seed_academy_modules():
    db = SessionLocal()
    modules = [
        {
            "module_number": 1,
            "title": "Platform Operations (Core)",
            "description": "50 pages | 10 quiz questions | Passing Score: 80%",
            "duration_hours": 4.0,
            "order": 1,
            "passing_score": 80.0,
            "topics": [
                {"id": "1.1", "title": "Welcome to ZimAgritrust", "pages": 5, "content": "Welcome to ZimAgritrust. Our mission is to eliminate the trust deficit in rural agricultural markets. Farmers lack access to fair markets due to unreliable yield verification. ZimAgritrust provides sovereign identity, verifiable proof through field agents, and smart escrow for secure payments." },
                {"id": "1.2", "title": "System Architecture Overview", "pages": 8, "content": "System Architecture: ZimAgritrust uses multi-layered infrastructure for low-connectivity environments. Core backend handles ledger and escrow. Agent portal for mobile field use. Farmer interface via USSD and WhatsApp. IoT gateway for warehouse sensors. AI models analyze crop photos." },
                {"id": "1.3", "title": "User Roles & Responsibilities", "pages": 6, "content": "Roles and Responsibilities: Farmers produce and list crops. Agents verify and provide ground truth. Buyers purchase crops. Administrators handle disputes globally." },
                {"id": "1.4", "title": "Transaction Lifecycle", "pages": 10, "content": "Trade steps: 1. Farmer lists crops via WhatsApp. 2. Buyer deposits full value into escrow. 3. Agent visits farm for verification. 4. Agent grades based on moisture and purity. 5. Crop moves to certified warehouse. 6. Escrow releases funds automatically." },
                {"id": "1.5", "title": "Platform Policies", "pages": 6, "content": "Platform policies: No bribery - immediate permanent ban for gifts. Protect farmer data privacy. Action verification requests within 24 hours. Accurate reporting required - misreporting weight is fraud." },
                {"id": "1.6", "title": "Core Agent Functions", "pages": 8, "content": "Agents verify listings, confirm deliveries, resolve disputes, support farmers, and verify loans." },
                {"id": "1.7", "title": "Agent Functions Summary", "pages": 8, "content": "Agent functions summary: 2. Confirm deliveries: witness handover, verify quantity, check quality, take photos, mark as delivered. 3. Resolve disputes: review evidence, interview parties, inspect goods, determine fault, recommend resolution. 4. Support farmers: help register, teach USSD usage, assist with first listing, help reset PINs. 5. Verify loans: confirm identity, assess farm viability, submit verification for approval. Summary: Listing verification (high priority), delivery confirmation (high), dispute resolution (high), farmer support (medium), loan verification (low)."},
                {"id": "1.8", "title": "WhatsApp AI Agent Assistant", "pages": 8, "content": "WhatsApp AI Assistant: The bot is your field support AI agent. Key capabilities: instant alerts for new tasks, verification checklists for ground truth visits, earnings query by sending 'earnings', automatic dispute setup with photo collection. The bot uses intent detection to support thousands of users, understanding if you're an agent looking for tasks or farmer looking for prices. Remember: bot handles digital data, you handle physical reality." }
            ],
            "quiz_questions": {
                "questions": [
                    {"id": "q1_1", "text": "What is the primary mission of ZimAgritrust?", "options": ["Profit Maximization", "Sovereign Trust in Trade", "Data Harvesting", "Government Surveillance"], "correct_index": 1},
                    {"id": "q1_2", "text": "Which interface is the primary tool for Farmers?", "options": ["USSD / WhatsApp", "React Native Pro", "Python Scripting", "Desktop Dashboard"], "correct_index": 0},
                    {"id": "q1_3", "text": "Who is considered the 'Point of Truth' in the field?", "options": ["The Farmer", "The Buyer", "The Field Agent", "The Warehouse Manager"], "correct_index": 2},
                    {"id": "q1_4", "text": "At what stage are funds released to the Farmer?", "options": ["Before planting", "When the buyer orders", "After Agent verification and delivery", "6 months after sale"], "correct_index": 2},
                    {"id": "q1_5", "text": "What happens if an Agent accepts a bribe to inflate a crop grade?", "options": ["A small fine", "A warning email", "Immediate and permanent ban", "Nothing"], "correct_index": 2},
                    {"id": "q1_6", "text": "Which technology ensures that the ledger cannot be tampered with?", "options": ["Excel Spreadsheets", "Blockchain-inspired Immutable Ledger", "Centralized SQL Trigger", "Manual Paper Records"], "correct_index": 1},
                    {"id": "q1_7", "text": "What is the maximum time allowed for a Verification request to be actioned?", "options": ["12 Hours", "24 Hours", "48 Hours", "1 Week"], "correct_index": 1},
                    {"id": "q1_8", "text": "What is the first step of an ZimAgritrust trade?", "options": ["Payment", "Listing", "Verification", "Grading"], "correct_index": 1},
                    {"id": "q1_9", "text": "Why do farmers primarily use WhatsApp instead of a dedicated mobile app?", "options": ["Apps are too expensive", "Data usage is lower and it works on basic smartphones", "WhatsApp is more secure", "There is no app"], "correct_index": 1},
                    {"id": "q1_10", "text": "What is the passing score for Module 1?", "options": ["50%", "75%", "80%", "100%"], "correct_index": 2}
                ]
            }
        },
        {
            "module_number": 2,
            "title": "Escrow & Payment System",
            "description": "40 pages | 10 quiz questions | Passing Score: 80%",
            "duration_hours": 5.0,
            "order": 2,
            "passing_score": 80.0,
            "topics": [
                {"id": "2.1", "title": "Escrow Storage & Legal Flow", "pages": 12, "content": "Escrow storage: Money held in separate trust accounts at partner banks, not company operating accounts. USD transactions in USD trust account, ZiG in ZiG trust account, EcoCash in segregated merchant wallet. Legal principle: we act as fiduciary trustee, funds protected if company fails. Four-stage money movement: payment to escrow, holding frozen, delivery, release to seller wallet. Withdrawal process: system checks ledger, instructs bank transfer, money leaves ecosystem." },
                {"id": "2.2", "title": "Payment Methods", "pages": 8, "content": "Payment methods: All transactions are digital, no cash used. Supported methods in Zimbabwe: EcoCash mobile money nationwide, OneMoney mobile money nationwide, Innbucks mobile money nationwide, bank transfer digital RTGS. Payout flows from platform trust account to farmer/agent mobile wallet. No physical bank visits required." },
                {"id": "2.3", "title": "Fee Structure", "pages": 6, "content": "Fee structure: Platform fee 2.5% of gross trade value. Agent commission deducted from platform fee or added as service charge. Network fees are standard mobile money or bank fees per transaction." },
                {"id": "2.4", "title": "Payment Disputes", "pages": 8, "content": "Payment disputes: If dispute raised for poor quality or wrong quantity, escrow is immediately frozen. Dispute timeline: dispute raised by buyer/farmer, funds frozen in escrow, agent investigates evidence, resolution either refund to buyer if farmer at fault or release to farmer if buyer at fault." },
                {"id": "2.5", "title": "Regulatory Framework", "pages": 6, "content": "Regulatory framework: Trust account owned by Trust, not company, we act as trustee. Funds legally protected if company goes bankrupt, partner banks monitor suspicious activity. RBZ compliance: zero commingling of operating expenses and escrow, mandatory KYC verification for all traders, audit trail for 7 years, suspicious transactions over $1000 flagged." },
                {"id": "2.6", "title": "How Agents Get Paid", "pages": 4, "content": "Agent payments: Earn through per-task commissions, monthly performance bonuses, travel reimbursement. All digital payments, no cash. Task pay ranges: basic verification $3-5, large verification $8-12, premium verification $10-15, delivery confirmation $2-4, dispute resolution $10-25, farmer onboarding $2-3. Monthly bonus tiers: bronze 85% accuracy 50 tasks $15, silver 90% accuracy 80 tasks $35, gold 95% accuracy 120 tasks $75, platinum 98% accuracy 150 tasks $150. Funds released to mobile wallet."}
            ],
            "quiz_questions": {
                "questions": [
                    {"id": "q2_1", "text": "What is the 'Sovereign Escrow Pool'?", "options": ["A private bank account", "A decentralized pool holding funds until contract terms are met", "A government tax fund", "An insurance policy"], "correct_index": 1},
                    {"id": "q2_2", "text": "Who is the 'Escrow Custodian' in the ZimAgritrust system?", "options": ["The Bank Manager", "The Smart Contract Logic", "The Field Agent", "The Farmer"], "correct_index": 1},
                    {"id": "q2_3", "text": "What does a Buyer do to initiate an order?", "options": ["Sends cash to the agent", "Deposits full amount into Escrow", "Promises to pay later", "Sends a check to the farmer"], "correct_index": 1},
                    {"id": "q2_4", "text": "When is the Escrow released to the Farmer?", "options": ["Upon delivery confirmation", "When the order is placed", "After 30 days regardless of quality", "When the Agent starts traveling"], "correct_index": 0},
                    {"id": "q2_5", "text": "What happens if a Buyer cancels an order after verification but before delivery?", "options": ["Full refund automatically", "Cancellation fee is deducted from the deposit", "Buyer loses 100% of the funds", "No refund possible"], "correct_index": 1},
                    {"id": "q2_6", "text": "What is the standard ZimAgritrust platform fee percentage?", "options": ["1%", "2.5%", "5%", "10%"], "correct_index": 1},
                    {"id": "q2_7", "text": "What happens in a 'Payment Dispute'?", "options": ["Funds stay in Escrow until resolved", "Funds are split 50/50 immediately", "Funds return to Buyer immediately", "Funds go to the Agent"], "correct_index": 0},
                    {"id": "q2_8", "text": "How long does a Farmer have to wait for funds after Agent 'Seals' the deal?", "options": ["Instantly (via Mobile Money)", "2-5 Days", "14 Days", "Upon buyer's secondary approval"], "correct_index": 0},
                    {"id": "q2_9", "text": "Fraudulent payment attempts result in...", "options": ["Warning", "System ban and report to local authorities", "Loss of 10 points", "A retry"], "correct_index": 1},
                    {"id": "q2_10", "text": "What is the passing score for Module 2?", "options": ["70%", "80%", "90%", "100%"], "correct_index": 1}
                ]
            }
        },
        {
            "module_number": 3,
            "title": "Crop Verification & Quality Standards",
            "description": "55 pages | 10 quiz questions | Passing Score: 85%",
            "duration_hours": 6.0,
            "order": 3,
            "passing_score": 85.0,
            "topics": [
                {"id": "3.1", "title": "Crop Grading Standards", "pages": 15, "content": "Crop grading standards: ZimAgritrust uses standardized grading, agent grading is final word. Maize grading: Grade A moisture under 12.5%, broken grains under 2%, foreign matter under 0.5%, zero infestation. Grade B moisture 12.5-14%, broken grains 2-5%, foreign matter 0.5-1.5%, zero infestation. Grade C moisture 14.1-15.5%, broken grains 5-10%, foreign matter 1.5-3%, trace infestation allowed. Reject crops with aflatoxins, chemical residue, or internal heat."},
                {"id": "3.2", "title": "Sampling Techniques", "pages": 10, "content": "Sampling techniques: Use representative sampling for 10-tonne trucks. 5-point probe method: bottom-left probe to base, top-right diagonal probe, center core sample, opposite corners to complete pattern. Guidelines: mix 5 samples in clean bucket, take test sample from composite, never sample only top layer as farmers may hide poor quality at bottom."},
                {"id": "3.3", "title": "Visual Disease Detection", "pages": 12, "content": "Visual disease detection: Eyes are first line of defense, use agent app AI lens to confirm issues. Common pathogens: aflatoxin yellow-green mold extremely toxic requiring quarantine, maize lethal necrosis with leaf streaking and shriveled cobs, large grain borer with visible holes and flour inside bags. Protocol: take 3 high-resolution macro photos and flag for senior audit review if disease suspected."},
                {"id": "3.4", "title": "Using Verification Hardware", "pages": 8, "content": "Verification hardware: Every agent gets sovereign verification kit. Tools include digital moisture meter must be calibrated every 30 days, Bluetooth platform scale automatically syncs weight to ledger to prevent errors, GPS geotagger built into tablet ensures you are at farm location. Pro-tip: low battery causes false high readings, sync hardware status daily."},
                {"id": "3.5", "title": "Batch Tagging & Sealing", "pages": 10, "content": "Batch tagging and sealing: Once verified, crop must be sealed to prevent tampering. Sealing process: generate QR code with unique batch ID, attach physical tamper-evident tag, take seal photo of tag on bags, digital handover where driver scans QR code to accept responsibility."}
            ],
            "quiz_questions": {
                 "questions": [
                    {"id": "q3_1", "text": "What is the maximum moisture threshold for Grade A Maize?", "options": ["10%", "12.5%", "14%", "15%"], "correct_index": 1},
                    {"id": "q3_2", "text": "How many samples should be taken from a 1-ton listing using the 5-Point Probe Method?", "options": ["1", "3", "5 from different depths", "None"], "correct_index": 2},
                    {"id": "q3_3", "text": "Which tool is used for visual disease detection in the field?", "options": ["Microscope", "The Agent Portal's ML-Camera", "A magnifying glass", "Flashlight"], "correct_index": 1},
                    {"id": "q3_4", "text": "What constitutes 'Foreign Matter' in a grain sample?", "options": ["Grains from other countries", "Stones, dirt, and chaff", "Different colored grains", "Insects"], "correct_index": 1},
                    {"id": "q3_5", "text": "A 'Grade C' crop classification typically indicates...", "options": ["Premium export quality", "Good for processing or animal feed only", "Unfit for any use", "Medium quality with minor defects"], "correct_index": 1},
                    {"id": "q3_6", "text": "Why should you never take samples only from the top layer of a grain pile?", "options": ["It is too dusty", "Farmers may hide poor quality at the bottom", "Top layer is always the best quality", "It takes too long"], "correct_index": 1},
                    {"id": "q3_7", "text": "What is the primary purpose of the GPS Geotagger during verification?", "options": ["To navigate to the farm", "To prove you are physically at the farm location", "To track the farmer's movements", "To calculate travel reimbursement"], "correct_index": 1},
                    {"id": "q3_8", "text": "How often must a Digital Moisture Meter be calibrated?", "options": ["Every 7 days", "Every 14 days", "Every 30 days", "Only when it breaks"], "correct_index": 2},
                    {"id": "q3_9", "text": "Which of these pathogens requires immediate quarantine?", "options": ["Large Grain Borer", "Maize Lethal Necrosis", "Aflatoxin (Aspergillus)", "Minor discoloration"], "correct_index": 2},
                    {"id": "q3_10", "text": "What is the passing score for Module 3?", "options": ["70%", "75%", "80%", "85%"], "correct_index": 3}
                 ]
            }
        },
        {
            "module_number": 4,
            "title": "Dispute Resolution",
            "description": "50 pages | 10 quiz questions | Passing Score: 85%",
            "duration_hours": 6.0,
            "order": 4,
            "passing_score": 85.0,
            "topics": [
                {"id": "4.1", "title": "Negotiation Hub & Encryption", "pages": 12, "content": "Negotiation hub is heart of buyer-seller relationship with end-to-end encryption by default. Privacy first: encrypted state means agents and admins cannot read chat normally, dispute override allows admin to grant temporary decryption access during active dispute, audit logging records all access on immutable ledger for accountability." },
                {"id": "4.2", "title": "Dispute Access Protocol", "pages": 10, "content": "Dispute access protocol: when dispute raised, workflow triggered. Raise dispute by buyer/farmer flagging transaction, admin review by global admin assessing sensitivity, grant access with temporary key valid 7 days, agent investigation with access to chat logs and media, revocation automatically blocks access once case resolved." },
                {"id": "4.3", "title": "Evidence Analysis", "pages": 15, "content": "Evidence analysis: during investigation review chat history for promises about grade price timing, media with photos and videos of crop before and after shipping, verification reports with original field notes from farm visit, tracking data with GPS logs of transport route." },
                {"id": "4.4", "title": "Conflict Resolution Workflow", "pages": 8, "content": "Conflict resolution workflow: based on evidence recommend one of following: refund funds return to buyer, release funds move to farmer, partial settlement funds split based on compromised quality grade, escalation move to senior auditor if evidence inconclusive." }
            ],
            "quiz_questions": {
                "questions": [
                    {"id": "q4_1", "text": "Who is a 'Neutral Auditor' in a resolution case?", "options": ["The Farmer's relative", "An independent certified professional appointed by the platform", "The original Field Agent", "The Buyer's employee"], "correct_index": 1},
                    {"id": "q4_2", "text": "What triggers a 'Dispute' status on an order?", "options": ["A formal disagreement logged by either Buyer or Farmer via the portal", "A late payment only", "A bad weather report", "The Agent being busy"], "correct_index": 0},
                    {"id": "q4_3", "text": "What is the 'Cooling-off Period'?", "options": ["24 hours after a dispute is logged for parties to settle privately", "Time to wait for rain", "The Agent's vacation", "A server maintenance window"], "correct_index": 0},
                    {"id": "q4_4", "text": "How long is a temporary decryption access key valid during a dispute?", "options": ["24 hours", "3 days", "7 days", "30 days"], "correct_index": 2},
                    {"id": "q4_5", "text": "Which of the following is NOT a valid resolution decision?", "options": ["Refund to Buyer", "Release to Farmer", "Partial Settlement", "Destroy the crop"], "correct_index": 3},
                    {"id": "q4_6", "text": "What type of encryption is used in the Negotiation Hub by default?", "options": ["AES-128", "End-to-End Encryption (E2EE)", "SSL only", "No encryption"], "correct_index": 1},
                    {"id": "q4_7", "text": "During an investigation, which evidence should you review first?", "options": ["Social media posts", "Chat history, media, verification reports, and tracking data", "News articles about the farmer", "Your personal notes from memory"], "correct_index": 1},
                    {"id": "q4_8", "text": "When is an Agent granted access to encrypted negotiation chats?", "options": ["Always", "Only during an active dispute with Admin approval", "When the Agent requests it", "Every Monday"], "correct_index": 1},
                    {"id": "q4_9", "text": "What happens to decryption access once a dispute case is resolved?", "options": ["It remains active for future reference", "It is automatically revoked", "The Agent keeps it permanently", "It expires after 30 days"], "correct_index": 1},
                    {"id": "q4_10", "text": "What is the passing score for Module 4?", "options": ["70%", "75%", "80%", "85%"], "correct_index": 3}
                ]
            }
        },
        {
            "module_number": 5,
            "title": "Trust & Reputation System",
            "description": "30 pages | 10 quiz questions | Passing Score: 80%",
            "duration_hours": 4.0,
            "order": 5,
            "passing_score": 80.0,
            "topics": [
                {"id": "5.1", "title": "The Trust Score Algorithm", "pages": 10, "content": "Trust score algorithm: Real-time reflection of professionalism and accuracy. Calculation weights: grading accuracy 40% checking if grade holds up during warehouse audits, response time 30% visiting farms within 24 hours, user feedback 20% professionalism ratings from farmers, system integrity 10% proper tool usage and sync frequency. Score below 70/100 results in temporary suspension, below 40/100 permanent ban."},
                {"id": "5.2", "title": "Review & Rating Management", "pages": 10, "content": "Review and rating management: After every trade, farmer rates you publicly to other farmers. High-performance tips: explain the grade with reasons like moisture percentage, be punctual with WhatsApp updates if delayed, provide support helping farmers list next crop. Note: can appeal bad-faith reviews with evidence like GPS logs and photos."},
                {"id": "5.3", "title": "Career Progression Levels", "pages": 10, "content": "Career progression levels: ZimAgritrust is career path not just gig. Levels: field trainee with supervised verification, certified agent with independent verification rights, senior agent handling high-value listings over $10k and MFI loan verification, lead auditor investigating disputes from other agents. Each level unlocked increases base commission percentage."}
            ],
            "quiz_questions": {
                "questions": [
                    {"id": "q5_1", "text": "What is the 'Base Trust Score' for a new certified Agent?", "options": ["50", "85", "100", "0"], "correct_index": 1},
                    {"id": "q5_2", "text": "How many successful trades are needed to reach 'Gold' status?", "options": ["10", "50", "100", "500"], "correct_index": 2},
                    {"id": "q5_3", "text": "What percentage of the Trust Score is based on Grading Accuracy?", "options": ["20%", "30%", "40%", "50%"], "correct_index": 2},
                    {"id": "q5_4", "text": "What happens if an Agent's Trust Score drops below 40/100?", "options": ["Temporary suspension", "Permanent ban", "Warning email", "Score reset to 50"], "correct_index": 1},
                    {"id": "q5_5", "text": "Which level unlocks high-value listing verification ($10k+)?", "options": ["Field Trainee", "Certified Agent", "Senior Agent", "Lead Auditor"], "correct_index": 2},
                    {"id": "q5_6", "text": "How can an Agent appeal a 'bad-faith' review from a farmer?", "options": ["By calling the farmer", "By providing GPS logs and photos as evidence", "By asking an admin to delete it", "Reviews cannot be appealed"], "correct_index": 1},
                    {"id": "q5_7", "text": "What is the minimum Trust Score that triggers temporary suspension?", "options": ["50", "60", "70", "80"], "correct_index": 2},
                    {"id": "q5_8", "text": "Which factor contributes the LEAST to the Trust Score calculation?", "options": ["Grading Accuracy", "Response Time", "User Feedback", "System Integrity"], "correct_index": 3},
                    {"id": "q5_9", "text": "What should you do if delayed for a farm visit?", "options": ["Ignore it", "Send a WhatsApp message via the app to inform the farmer", "Ask a friend to go instead", "Cancel the visit"], "correct_index": 1},
                    {"id": "q5_10", "text": "What is the passing score for Module 5?", "options": ["70%", "75%", "80%", "85%"], "correct_index": 2}
                ]
            }
        },
        {
            "module_number": 6,
            "title": "Marketplace Ethics & Integrity",
            "description": "35 pages | 10 quiz questions | Passing Score: 80%",
            "duration_hours": 4.0,
            "order": 6,
            "passing_score": 80.0,
            "topics": [
                {"id": "6.1", "title": "Professional Ethics", "pages": 10, "content": "Professional ethics: ZimAgritrust built on sovereign protocol, corruption is enemy of prosperity. Zero tolerance policies: no bribery accepting any gift results in immediate dismissal, no collusion artificially inflating grades is fraud, no poaching never encourage farmers to trade off-platform. Sanctions recorded on blockchain and shared with National Credit Bureau."},
                {"id": "6.2", "title": "Data Privacy & Security", "pages": 10, "content": "Data privacy and security: Handle sensitive farmer data including GPS locations, IDs, financial earnings. Need to know rule: confidentiality never share warehouse photos on social media, security device must be PIN-protected at all times, E2EE all chats encrypted only gain access during dispute."},
                {"id": "6.3", "title": "Conflict of Interest", "pages": 15, "content": "Conflict of interest: Must remain neutral point of truth. Common scenarios: family farms cannot verify crop owned by relative, side trades cannot act as buyer for verified crop, competing platforms require disclosure if work for other ag-tech firms. Rule: if suspect conflict, click recuse in app for task reassignment."}
            ],
            "quiz_questions": {
                "questions": [
                    {"id": "q6_1", "text": "What is the 'Zero-Bribe' policy?", "options": ["Small gifts are okay", "Strict prohibition of any gifts or payments to influence grading", "Payment for speed is allowed", "Only cash is forbidden"], "correct_index": 1},
                    {"id": "q6_2", "text": "What constitutes a 'Conflict of Interest' for an Agent?", "options": ["Knowing the farmer", "Verifying a crop owned by the Agent's own family business without disclosure", "Working on weekends", "Using a personal phone"], "correct_index": 1},
                    {"id": "q6_3", "text": "What happens if an Agent is caught in collusion to inflate a grade?", "options": ["A warning", "Temporary suspension", "It is recorded on the blockchain and shared with the National Credit Bureau", "A small fine"], "correct_index": 2},
                    {"id": "q6_4", "text": "What is 'poaching' in the ZimAgritrust context?", "options": ["Hunting wildlife on farms", "Encouraging farmers to trade off-platform to avoid fees", "Stealing crops", "Taking competitor agents"], "correct_index": 1},
                    {"id": "q6_5", "text": "Which of the following is a violation of the 'Need to Know' data privacy rule?", "options": ["Sharing a farmer's warehouse photo on social media", "Reporting crop quality to the platform", "Sending a WhatsApp update to the farmer", "Uploading verification photos to the app"], "correct_index": 0},
                    {"id": "q6_6", "text": "What should an Agent do if they suspect a conflict of interest?", "options": ["Continue with the verification", "Click 'Recuse' in the app and let the task be reassigned", "Ask the farmer to hide the relationship", "Complete the task quickly"], "correct_index": 1},
                    {"id": "q6_7", "text": "Why must your verification device always be PIN-protected?", "options": ["To prevent theft", "It contains sensitive farmer data including GPS locations and financial earnings", "It looks more professional", "Company policy only"], "correct_index": 1},
                    {"id": "q6_8", "text": "Can an Agent act as a Buyer for a crop they previously verified?", "options": ["Yes, after 30 days", "Yes, with Admin approval", "No, this is a side-trade conflict of interest", "Only if the price is fair"], "correct_index": 2},
                    {"id": "q6_9", "text": "Is disclosure required if an Agent works for another ag-tech firm?", "options": ["No, it is private", "Yes, it must be disclosed to avoid conflicts of interest", "Only if asked directly", "Only for full-time jobs"], "correct_index": 1},
                    {"id": "q6_10", "text": "What is the passing score for Module 6?", "options": ["70%", "75%", "80%", "85%"], "correct_index": 2}
                ]
            }
        },
        {
            "module_number": 7,
            "title": "Rural Finance & Credit Access",
            "description": "45 pages | 10 quiz questions | Passing Score: 80%",
            "duration_hours": 5.0,
            "order": 7,
            "passing_score": 80.0,
            "topics": [
                {"id": "7.1", "title": "Inventory-Backed Lending", "pages": 15, "content": "Inventory-backed lending: Farmers have crops but no cash, solved through collateralized verification. Flow: seal by verifying and tagging 10 tonnes maize, lock listing in system, lend bank issues $500 loan instantly, settlement when buyer pays $1000 with $500 to bank and $500 to farmer. Your role as collateral officer: misreporting weight makes bank lose money and you liable."},
                {"id": "7.2", "title": "Credit Scoring for Smallholders", "pages": 15, "content": "Credit scoring for smallholders: Traditional banks use pay slips, ZimAgritrust uses ledger history. Data points: yield growth check if farmer produces more each year, repayment rate check if they fulfill trade commitments, quality consistency check if maize always grade A. Providing this data enables farmers to buy tractors and better seeds."},
                {"id": "7.3", "title": "Insurance & Risk", "pages": 15, "content": "Insurance and risk: Drought and pests are real risks. Integrated insurance: parametric triggers automatically trigger payouts when satellite data shows zero rain for 30 days, verification audits may send you to verify field conditions for total crop loss claims. Insurance ensures farmer and commission survive bad seasons."}
            ],
            "quiz_questions": {
                "questions": [
                    {"id": "q7_1", "text": "What is 'Inventory-Backed Lending'?", "options": ["Lending based on a farmer's house", "Loans secured by verified crops currently held in escrow/warehouse", "Loans based on future promises", "Giving away money"], "correct_index": 1},
                    {"id": "q7_2", "text": "What is the Agent's role in a collateralized loan?", "options": ["The Borrower", "The Collateral Officer", "The Bank Manager", "The Insurance Agent"], "correct_index": 1},
                    {"id": "q7_3", "text": "Which data point is NOT used in ZimAgritrust's Sovereign Credit Scoring?", "options": ["Yield Growth", "Repayment Rate", "Quality Consistency", "Farmer's Political Affiliation"], "correct_index": 3},
                    {"id": "q7_4", "text": "How are insurance payouts triggered under parametric insurance?", "options": ["By filing a paper claim", "Automatically when satellite data meets predefined conditions", "After a court ruling", "By agent recommendation only"], "correct_index": 1},
                    {"id": "q7_5", "text": "What happens to the bank's $500 loan when a buyer pays $1000 for the crop?", "options": ["The farmer keeps all $1000", "$500 goes to the bank and $500 to the farmer", "The bank takes $800", "The agent takes a $200 fee"], "correct_index": 1},
                    {"id": "q7_6", "text": "Why is verifying farm size with satellite imagery important for insurance?", "options": ["To calculate travel distance", "To prevent farmers from claiming more land than they actually farm", "For mapping roads", "To estimate crop prices"], "correct_index": 1},
                    {"id": "q7_7", "text": "What should an Agent do if asked to verify a total crop loss for an insurance claim?", "options": ["Approve it without visiting", "Visit the field and document conditions accurately", "Ask the farmer for a bribe", "Decline all insurance claims"], "correct_index": 1},
                    {"id": "q7_8", "text": "How does accurate verification help farmers access credit?", "options": ["It reduces their taxes", "It provides verified data that banks use to issue loans", "It increases crop prices", "It reduces insurance costs"], "correct_index": 1},
                    {"id": "q7_9", "text": "What type of data does traditional banking use that rural farmers often lack?", "options": ["GPS coordinates", "Pay slips and formal employment records", "Crop photos", "Phone numbers"], "correct_index": 1},
                    {"id": "q7_10", "text": "What is the passing score for Module 7?", "options": ["70%", "75%", "80%", "85%"], "correct_index": 2}
                ]
            }
        },
        {
            "module_number": 8,
            "title": "Legal & Regulatory Framework",
            "description": "40 pages | 10 quiz questions | Passing Score: 80%",
            "duration_hours": 5.0,
            "order": 8,
            "passing_score": 80.0,
            "topics": [
                {"id": "8.1", "title": "The Trust Deed & Terms", "pages": 10, "content": "Trust deed and terms: Every user signs global trust deed upon registration as legal foundation. Key clauses: escrow finality funds legally irreversible once delivery confirmed, agent signatory digital signature makes you legal witness to quality, arbitration disputes settled by neutral auditors not local courts for speed."},
                {"id": "8.2", "title": "Land Tenure & Rights", "pages": 15, "content": "Land tenure and rights: Verifying land ownership as important as crop. Verification types: title deeds for formal ownership, leasehold for right to use land specific period, communal allotment traditional leader verification. Your job: use app to capture photo of land permit/deed to ensure buyer not buying stolen goods."},
                {"id": "8.3", "title": "RBZ & Regulatory Compliance", "pages": 15, "content": "RBZ and regulatory compliance: Operate under Reserve Bank of Zimbabwe fintech sandbox. Compliance rules: AML flag transactions over $10000 suspicious, KYC verify farmer physical national ID, zero-commingling corporate and escrow money stored in different bank accounts."}
            ],
            "quiz_questions": {
                "questions": [
                    {"id": "q8_1", "text": "What is a 'Binding Contract' in ZimAgritrust?", "options": ["A friendly promise", "A legal agreement enforceable by law once signed digitally via the platform", "An email", "A handshake"], "correct_index": 1},
                    {"id": "q8_2", "text": "What makes an Agent's digital signature on a report legally significant?", "options": ["It is optional", "It makes the Agent a 'Legal Witness' to the quality", "It is only for internal records", "It has no legal value"], "correct_index": 1},
                    {"id": "q8_3", "text": "Which document proves formal land ownership during verification?", "options": ["A utility bill", "A Title Deed", "A school ID", "A church membership card"], "correct_index": 1},
                    {"id": "q8_4", "text": "Under RBZ Fintech Sandbox rules, what does AML stand for?", "options": ["Automatic Money Lending", "Anti-Money Laundering", "Approved Merchant List", "Agent Management License"], "correct_index": 1},
                    {"id": "q8_5", "text": "What is the minimum transaction amount that must be flagged as suspicious under AML rules?", "options": ["$1,000", "$5,000", "$10,000", "$50,000"], "correct_index": 2},
                    {"id": "q8_6", "text": "Why must corporate money and Escrow money be stored in different bank accounts?", "options": ["To earn more interest", "Zero-Commingling compliance", "To confuse auditors", "Bank preference"], "correct_index": 1},
                    {"id": "q8_7", "text": "What does KYC require an Agent to verify?", "options": ["The farmer's favorite color", "The farmer's physical National ID", "The farmer's shoe size", "The farmer's social media handle"], "correct_index": 1},
                    {"id": "q8_8", "text": "How are disputes settled on the platform to ensure speed?", "options": ["Local court trials", "Neutral Auditors appointed by the platform", "Community voting", "Coin flips"], "correct_index": 1},
                    {"id": "q8_9", "text": "What is 'Leasehold' land tenure?", "options": ["Full ownership forever", "Right to use the land for a specific period", "Government-owned land", "Abandoned land"], "correct_index": 1},
                    {"id": "q8_10", "text": "What is the passing score for Module 8?", "options": ["70%", "75%", "80%", "85%"], "correct_index": 2}
                ]
            }
        },
        {
            "module_number": 9,
            "title": "Advanced Ag-Tech & IoT",
            "description": "50 pages | 10 quiz questions | Passing Score: 85%",
            "duration_hours": 6.0,
            "order": 9,
            "passing_score": 85.0,
            "topics": [
                {"id": "9.1", "title": "IoT & Smart Sensors", "pages": 15, "content": "IoT and smart sensing: Technology is force multiplier. Connected tools: Bluetooth probes measure moisture and protein levels instantly, smart scales capture weight display via camera to prevent manual entry errors, soil sensors analyze nitrogen phosphorous levels to predict future yield. Troubleshooting: if sensor loses calibration app flags report, use secondary tool immediately."},
                {"id": "9.2", "title": "Drone & Satellite Imagery", "pages": 20, "content": "Drone and satellite imagery: Use Sentinel-2 satellite imagery to verify farm size. Drone operations: NDVI maps identify disease hotspots from air before farm arrival, area verification ensures farmer not claiming 10 hectares when only have 2. Your role: interpret NDVI health maps in dashboard, no need to fly drones."},
                {"id": "9.3", "title": "Blockchain & Immutability", "pages": 15, "content": "Blockchain and immutability: ZimAgritrust uses distributed ledger not central database. Immutability matters: no deletions once signed report cannot be deleted or altered, audit trail records every change with timestamp and ID, buyer confidence international buyers trust data as mathematically impossible to forge. Remember: your ID is reputation, false report stays on ledger forever."}
            ],
            "quiz_questions": {
                "questions": [
                    {"id": "q9_1", "text": "What is an 'IoT Sensor'?", "options": ["A smartphone", "An interconnected device that collects and transmits data in real-time", "A satellite", "A laptop"], "correct_index": 1},
                    {"id": "q9_2", "text": "What does NDVI stand for and what does it measure?", "options": ["National Data Verification Index - measures bank balances", "Normalized Difference Vegetation Index - measures plant health", "New Device Verification Interface - measures battery life", "Network Distribution Volume Indicator - measures internet speed"], "correct_index": 1},
                    {"id": "q9_3", "text": "What should an Agent do if a sensor loses calibration during verification?", "options": ["Continue with the faulty reading", "Use a secondary tool immediately and flag the report", "Estimate the value", "Ignore the sensor"], "correct_index": 1},
                    {"id": "q9_4", "text": "Why does ZimAgritrust use a Distributed Ledger instead of a central database?", "options": ["It is cheaper", "It ensures immutability and prevents tampering with transaction records", "It is faster", "It uses less storage"], "correct_index": 1},
                    {"id": "q9_5", "text": "What happens to a signed report on the Sovereign Ledger if an error is discovered?", "options": ["It is deleted immediately", "It can never be deleted or altered, but a correction can be appended", "An admin can edit it", "The agent can request deletion"], "correct_index": 1},
                    {"id": "q9_6", "text": "What do soil sensors primarily analyze to predict future yield?", "options": ["GPS coordinates", "Nitrogen and phosphorous levels", "Farmer's age", "Market prices"], "correct_index": 1},
                    {"id": "q9_7", "text": "How do Smart Scales prevent manual entry errors?", "options": ["By using voice commands", "The weight display is captured via the agent's camera", "They automatically type numbers", "They don't connect to the app"], "correct_index": 1},
                    {"id": "q9_8", "text": "What type of satellite imagery does ZimAgritrust use to verify farm size?", "options": ["Google Street View", "Sentinel-2 Satellite Imagery", "NASA Apollo photos", "Weather radar"], "correct_index": 1},
                    {"id": "q9_9", "text": "Why is immutability important for international buyer confidence?", "options": ["It makes data look fancy", "It proves the data is mathematically impossible to forge", "It reduces server costs", "It is required by the government"], "correct_index": 1},
                    {"id": "q9_10", "text": "What is the passing score for Module 9?", "options": ["70%", "75%", "80%", "85%"], "correct_index": 3}
                ]
            }
        },
        {
            "module_number": 10,
            "title": "Premium Customer Excellence",
            "description": "30 pages | 10 quiz questions | Passing Score: 90%",
            "duration_hours": 4.0,
            "order": 10,
            "passing_score": 90.0,
            "topics": [
                {"id": "10.1", "title": "The Golden Service Rule", "pages": 10, "content": "Golden service rule: As ZimAgritrust agent you are consultant not bureaucrat. Etiquette: always greet farmer and village elders respectfully, show moisture meter reading to farmer for transparency, arrive on time as farmer's time is valuable. Goal: every farmer should want you back for next harvest."},
                {"id": "10.2", "title": "Conflict De-escalation", "pages": 10, "content": "Conflict de-escalation: Sometimes grade not what farmer expected. 3-step de-escalation: acknowledge understanding they expected Grade A, show evidence with moisture meter reading 14.5% meeting Grade B standards, propose action to dry grain 2 more days for re-verification to reach Grade A. Never argue, use technical data to let platform deliver bad news."},
                {"id": "10.3", "title": "Community Leadership", "pages": 10, "content": "Community leadership: You are technology ambassador in village. Your influence: digital literacy teaching farmers USSD usage, market intelligence sharing current regional prices, ethics being known as agent who cannot be bribed. Final thought: when community trusts agent, system prospers. Verify with integrity."}
            ],
            "quiz_questions": {
                "questions": [
                    {"id": "q10_1", "text": "What is the primary goal of an Agent during a farm visit?", "options": ["Getting paid", "Building trust and delivering professional verification service", "Talking to neighbors", "Taking photos only"], "correct_index": 1},
                    {"id": "q10_2", "text": "What is the first step in the 3-Step De-escalation technique?", "options": ["Show evidence", "Acknowledge the farmer's expectations", "Propose action", "Change the subject"], "correct_index": 1},
                    {"id": "q10_3", "text": "Why should an Agent show the moisture meter reading to the farmer?", "options": ["To prove the Agent is smarter", "To maintain transparency and build trust", "It is required by law", "To embarrass the farmer"], "correct_index": 1},
                    {"id": "q10_4", "text": "What is the best way to teach farmers how to use USSD?", "options": ["Give them a long manual", "Demonstrate it step-by-step on their own phone", "Tell them to figure it out", "Only teach the village chief"], "correct_index": 1},
                    {"id": "q10_5", "text": "What should an Agent do when a farmer disputes a Grade B classification?", "options": ["Argue loudly", "Show the moisture meter evidence and propose a re-verification after drying", "Change the grade to please the farmer", "Leave immediately"], "correct_index": 1},
                    {"id": "q10_6", "text": "Why is greeting village elders respectfully important during a farm visit?", "options": ["It is just politeness", "It builds community trust and smooths future verification access", "They control the GPS signal", "It is required by the app"], "correct_index": 1},
                    {"id": "q10_7", "text": "What kind of market intelligence should an Agent share with farmers?", "options": ["Stock market trends", "Current regional crop prices", "Bitcoin prices", "Weather forecasts only"], "correct_index": 1},
                    {"id": "q10_8", "text": "What does it mean to be an 'ambassador of technology in the village'?", "options": ["Selling gadgets", "Teaching and demonstrating digital tools like USSD to improve farmer livelihoods", "Installing WiFi towers", "Posting on social media"], "correct_index": 1},
                    {"id": "q10_9", "text": "In the 3-Step De-escalation, what comes AFTER acknowledging the farmer's expectations?", "options": ["Walk away", "Show Evidence with technical data", "Offer a bribe", "Call the police"], "correct_index": 1},
                    {"id": "q10_10", "text": "What is the passing score for Module 10?", "options": ["80%", "85%", "90%", "95%"], "correct_index": 2}
                ]
            }
        }
    ]

    for m_data in modules:
        handbook_path, _ = _module_material_paths(m_data["module_number"])
        if os.path.exists(handbook_path):
            m_data["content_url"] = os.path.relpath(handbook_path, os.getcwd())
            for topic in m_data.get("topics", []):
                topic["study_source"] = m_data["content_url"]

        quiz_from_materials = _load_module_quiz(m_data["module_number"])
        if quiz_from_materials and quiz_from_materials["questions"]:
            m_data["quiz_questions"] = quiz_from_materials

        # Check if we need to auto-generate questions for modules that are missing them
        if not m_data["quiz_questions"]["questions"] or len(m_data["quiz_questions"]["questions"]) < 10:
            current_questions = m_data["quiz_questions"]["questions"]
            current_q_count = len(current_questions)
            topics = m_data.get("topics", [])
            
            for j in range(current_q_count + 1, 11):
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
