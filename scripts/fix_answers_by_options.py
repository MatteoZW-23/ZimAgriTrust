"""
Sets correct_answer AND question_text for all quiz questions by matching options.
Run: docker exec agric-backend-1 python /app/fix_answers_by_options.py
"""
import sys
sys.path.insert(0, "/app")

# Each entry: (unique_option_substring, correct_answer, question_text)
# unique_option_substring must appear in only ONE question's options
QUESTIONS = [
    # options fingerprint (unique substring)        correct_answer                                                  question_text
    ("Sovereign Trust in Trade",                    "Sovereign Trust in Trade",                                     "What is the core mission of ZimAgritrust?"),
    ("React Native Pro",                            "USSD / WhatsApp",                                              "Which digital channel does ZimAgritrust primarily use for farmer interactions?"),
    ("The Warehouse Manager",                       "The Field Agent",                                              "Who initiates a KYC verification request for a new farmer on the platform?"),
    ("Before planting",                             "After Agent verification and delivery",                        "When does a farmer receive payment after a completed trade on ZimAgritrust?"),
    ("Immediate and permanent ban",                 "Immediate and permanent ban",                                  "What is the consequence for an Agent found faking a quality report?"),
    ("Blockchain-inspired Immutable Ledger",        "Blockchain-inspired Immutable Ledger",                         "What type of ledger does ZimAgritrust use for all verified transactions?"),
    ("12 Hours",                                    "24 Hours",                                                     "How quickly must a Field Agent respond to a newly assigned task?"),
    ("The Smart Contract Logic",                    "The Smart Contract Logic",                                     "Who or what authorises fund release in a ZimAgritrust Smart Contract?"),
    ("60",                                          "80",                                                           "What is the minimum Trust Score a farmer needs to list produce on ZimAgritrust?"),
    ("To prove you are physically",                 "To prove you are physically at the farm location",             "What does GPS geo-tagging prove during a farm verification visit?"),
    ("sensitive farmer data including GPS",         "It contains sensitive farmer data including GPS locations and financial earnings", "Why must a Field Agent keep their mobile device locked and secure?"),
    ("Approve it without visiting",                 "Visit the field and document conditions accurately",           "How should a Field Agent handle an insurance claim from a farmer who experienced crop damage?"),
    ("Funds stay in Escrow until resolved",         "Funds stay in Escrow until resolved",                         "What happens to Escrow funds when a trade dispute is raised?"),
    ("Current regional crop prices",                "Current regional crop prices",                                 "What real-time data does the ZimAgritrust app provide during a verification?"),
    ("farmer's physical National ID",               "The farmer's physical National ID",                            "What is the primary identity document required for farmer KYC on ZimAgritrust?"),
    ("Chat history, media, verification reports",   "Chat history, media, verification reports, and tracking data", "What data is stored in the ZimAgritrust Agent app for audit purposes?"),
    ("verified data that banks use to issue loans", "It provides verified data that banks use to issue loans",      "How does ZimAgritrust verification help farmers access loans?"),
    ("Only during an active dispute",               "Only during an active dispute with Admin approval",            "Under what condition can a dispute conversation log be reviewed?"),
    ("Sentinel-2 Satellite Imagery",                "Sentinel-2 Satellite Imagery",                                 "What satellite imagery does ZimAgritrust use for land verification?"),
    ("demonstrating digital tools like USSD",       "Teaching and demonstrating digital tools like USSD to improve farmer livelihoods", "What is the role of a Field Agent in digital literacy outreach?"),
    ("Show Evidence with technical data",           "Show Evidence with technical data",                            "How should a Field Agent respond to a farmer who disputes a grading result?"),
    ("It is automatically revoked",                 "It is automatically revoked",                                  "What happens to an Agent's certification when they are found guilty of fraud?"),
    ("Send a WhatsApp message via the app to inform","Send a WhatsApp message via the app to inform the farmer",    "What should a Field Agent do if they will arrive late to a scheduled farm visit?"),
    ("Right to use the land for a specific period", "Right to use the land for a specific period",                  "What is a Usufruct land right in the context of ZimAgritrust farmer KYC?"),
    ("Data usage is lower and it works on basic",   "Data usage is lower and it works on basic smartphones",        "Why does ZimAgritrust primarily use USSD for farmer interactions in rural areas?"),
    ("Yes, it must be disclosed to avoid",          "Yes, it must be disclosed to avoid conflicts of interest",     "Must a Field Agent disclose personal business interests related to a farmer they verify?"),
    ("Pay slips and formal employment records",     "Pay slips and formal employment records",                      "What documents does a Field Agent primarily collect during farmer KYC verification?"),
    ("mathematically impossible to forge",          "It proves the data is mathematically impossible to forge",     "Why is cryptographic hashing used for KYC records on ZimAgritrust?"),
    ("System ban and report to local authorities",  "System ban and report to local authorities",                   "What is the consequence for a Field Agent caught falsifying a grade report?"),
    ("70%",                                         "80%",                                                          "What is the minimum passing score for quizzes on ZimAgritrust Academy?"),
    ("50%",                                         "80%",                                                          "What is the minimum passing score for the Mid-Academy Examination?"),
    ("weight display is captured via the agent",    "The weight display is captured via the agent's camera",        "How do digital scales connect to the ZimAgritrust app during weighing?"),
    ("hide poor quality at the bottom",             "Farmers may hide poor quality at the bottom",                  "Why should a Field Agent sample produce from multiple layers of a bag?"),
    ("claiming more land than they actually",       "To prevent farmers from claiming more land than they actually farm", "Why is GPS land measurement important during farm registration?"),
    ("Zero-Commingling",                            "Zero-Commingling compliance",                                  "Why must Escrow funds be kept in a separate account?"),
    ("smooths future verification access",          "It builds community trust and smooths future verification access", "Why is it important for a Field Agent to greet community leaders before a verification?"),
    ("Nitrogen and phosphorous levels",             "Nitrogen and phosphorous levels",                              "What soil data does a Field Agent record during a farm visit?"),
    ("Recuse",                                      "Click 'Recuse' in the app and let the task be reassigned",     "What must a Field Agent do if they have a personal relationship with a farmer they are assigned?"),
    ("GPS logs and photos as evidence",             "By providing GPS logs and photos as evidence",                 "How can a Field Agent appeal a negative performance review?"),
    ("2.5%",                                        "2.5%",                                                         "What commission rate does a Field Agent earn per verified listing on ZimAgritrust?"),
    ("End-to-End Encryption",                       "End-to-End Encryption (E2EE)",                                 "What encryption standard does ZimAgritrust use for all data in transit?"),
    ("Lead Auditor",                                "Senior Agent",                                                 "What career level comes after Certified Agent in the ZimAgritrust progression?"),
    ("500 goes to the bank and",                    "$500 goes to the bank and $500 to the farmer",                 "If a farmer has $1000 crop inventory and a 50% Warehouse Receipt loan, how much do they receive?"),
    ("Refund to Buyer",                             "Refund to Buyer",                                              "What is the correct action when a delivered crop fails quality check at the warehouse?"),
    ("Good for processing or animal feed only",     "Good for processing or animal feed only",                      "What does a Grade-B classification mean for maize on ZimAgritrust?"),
    ("moisture meter evidence and propose",         "Show the moisture meter evidence and propose a re-verification after drying", "How should a Field Agent handle a farmer who argues their crop is damp but moisture reading is high?"),
    ("The Collateral Officer",                      "The Collateral Officer",                                       "Who manages the physical crop collateral in a Warehouse Receipt Financing arrangement?"),
    ("Acknowledge the farmer",                      "Acknowledge the farmer's expectations",                        "What is the first step when de-escalating a tense KYC situation with a farmer?"),
    ("different depths",                            "5 from different depths",                                      "How many grain samples should a Field Agent collect for moisture and aflatoxin testing?"),
    ("Legal Witness",                               "It makes the Agent a 'Legal Witness' to the quality",         "What is the legal significance of a Field Agent's digital signature on a grade report?"),
    ("dispute is logged for parties to settle",     "24 hours after a dispute is logged for parties to settle privately", "What is the 'Cool-Down Period' on ZimAgritrust disputes?"),
    ("ML-Camera",                                   "The Agent Portal's ML-Camera",                                 "What tool does a Field Agent use to identify crop diseases using AI on ZimAgritrust?"),
    ("secondary tool immediately and flag",         "Use a secondary tool immediately and flag the report",         "What should a Field Agent do if their moisture meter gives an erratic reading?"),
    ("National Credit Bureau",                      "It is recorded on the blockchain and shared with the National Credit Bureau", "What happens to a farmer's record after a fraudulent transaction is confirmed?"),
    ("A Title Deed",                                "A Title Deed",                                                 "Which document best proves a farmer's ownership of land during KYC?"),
    ("Deposits full amount into Escrow",            "Deposits full amount into Escrow",                             "What does a Buyer do first to initiate a trade on ZimAgritrust?"),
    ("Repayment Rate",                              "Repayment Rate",                                               "Which farmer metric most influences their ZimAgritrust Trust Score?"),
    ("transparency and build trust",                "To maintain transparency and build trust",                     "Why does a Field Agent explain every verification step to the farmer in real time?"),
    ("Verifying a crop owned by the Agent",         "Verifying a crop owned by the Agent's own family business without disclosure", "Which action constitutes a Conflict of Interest for a ZimAgritrust Field Agent?"),
    ("Vegetation Index",                            "Normalized Difference Vegetation Index - measures plant health","What does NDVI stand for in the ZimAgritrust satellite monitoring context?"),
    ("Aflatoxin (Aspergillus)",                     "Aflatoxin (Aspergillus)",                                     "Which contamination causes automatic Grade-F rejection for maize on ZimAgritrust?"),
    ("Every 14 days",                               "Every 14 days",                                                "How often must a Field Agent recalibrate their moisture meter?"),
    ("Neutral Auditors appointed by the platform",  "Neutral Auditors appointed by the platform",                   "Who resolves escalated disputes on the ZimAgritrust platform?"),
    ("No, this is a side-trade conflict",           "No, this is a side-trade conflict of interest",               "Can a Field Agent purchase produce from a farmer they have just graded?"),
    ("Grading Accuracy",                            "Grading Accuracy",                                             "Which KPI carries the highest weight in a Field Agent's quarterly performance review?"),
    ("Grading",                                     "Grading",                                                      "Which step in the ZimAgritrust workflow requires a Field Agent's digital signature?"),
    ("Instantly (via Mobile Money)",                "2-5 Days",                                                     "How quickly are funds released to a farmer after a ZimAgritrust trade is confirmed?"),
    ("An interconnected device that collects",      "An interconnected device that collects and transmits data in real-time", "What does 'IoT device' mean in the context of ZimAgritrust?"),
    ("Loans secured by verified crops",             "Loans secured by verified crops currently held in escrow/warehouse", "What is Warehouse Receipt Financing on ZimAgritrust?"),
    ("A decentralized pool holding funds",          "A decentralized pool holding funds until contract terms are met", "What is an Escrow Smart Wallet on ZimAgritrust?"),
    ("A legal agreement enforceable by law",        "A legal agreement enforceable by law once signed digitally via the platform", "What is a Digital Smart Contract on the ZimAgritrust platform?"),
    ("Building trust and delivering professional",  "Building trust and delivering professional verification service", "What is the primary role of a ZimAgritrust Field Agent?"),
    ("Strict prohibition of any gifts",             "Strict prohibition of any gifts or payments to influence grading", "What is the ZimAgritrust policy on grading bribes?"),
    ("An independent certified professional",       "An independent certified professional appointed by the platform", "Who is a Neutral Auditor on the ZimAgritrust platform?"),
    ("10%",                                         "12.5%",                                                        "What percentage commission does a Field Agent earn per verified transaction on ZimAgritrust?"),
    ("Installing WiFi towers",                      "Teaching and demonstrating digital tools like USSD to improve farmer livelihoods", "What does 'Digital Inclusion' mean for a ZimAgritrust Field Agent?"),
]

import json as _json

def run():
    from app.db.session import SessionLocal
    from app.models.classroom import QuizQuestion

    db = SessionLocal()
    try:
        all_qs = db.query(QuizQuestion).all()
        updated = 0
        no_match = []

        for fingerprint, correct_answer, question_text in QUESTIONS:
            matched = [q for q in all_qs if q.options and any(fingerprint in opt for opt in q.options)]
            if len(matched) == 1:
                q = matched[0]
                q.correct_answer = correct_answer
                q.question_text = question_text
                updated += 1
            elif len(matched) == 0:
                no_match.append(f"NO MATCH: {fingerprint[:50]}")
            else:
                # Multiple matches — use question_text to disambiguate
                best = [q for q in matched if question_text[:20].lower() in (q.question_text or "").lower()]
                if len(best) == 1:
                    best[0].correct_answer = correct_answer
                    best[0].question_text = question_text
                    updated += 1
                else:
                    no_match.append(f"AMBIGUOUS ({len(matched)}): {fingerprint[:50]}")

        db.commit()
        print(f"✅ Updated {updated} questions with correct answers and text.")
        if no_match:
            print(f"⚠️  {len(no_match)} issues:")
            for m in no_match:
                print(f"   {m}")

        remaining = db.query(QuizQuestion).filter(
            (QuizQuestion.correct_answer == None) | (QuizQuestion.correct_answer == "")
        ).count()
        print(f"📊 Questions still without correct_answer: {remaining}")
    finally:
        db.close()

if __name__ == "__main__":
    run()
