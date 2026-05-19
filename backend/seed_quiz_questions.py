"""
One-time script: populate question_text for all classroom_quiz_questions
where question_text is blank, by matching known option sets.
Run inside the backend container:
  docker exec agric-backend-1 python /app/scripts/seed_quiz_questions.py
"""
import os, sys
sys.path.insert(0, "/app")

from app.db.session import SessionLocal

# Map: tuple(sorted options) -> question_text
QUESTION_MAP = {
    # ── Platform Operations ──────────────────────────────────────────────────
    ("A friendly promise", "A legal agreement enforceable by law once signed digitally via the platform", "An email", "A handshake"):
        "What is a Digital Smart Contract on the ZimAgritrust platform?",
    ("A smartphone", "An interconnected device that collects and transmits data in real-time", "A laptop", "A satellite"):
        "What does 'IoT device' mean in the context of ZimAgritrust?",
    ("A decentralized pool holding funds until contract terms are met", "A government tax fund", "A private bank account", "An insurance policy"):
        "What is an Escrow Smart Wallet on ZimAgritrust?",
    ("A friendly promise", "A legal agreement once signed", "An email", "A handshake"):
        "What is a Digital Smart Contract on the ZimAgritrust platform?",
    ("Building trust and delivering professional verification service", "Getting paid", "Taking photos only", "Talking to neighbors"):
        "What is the primary role of a ZimAgritrust Field Agent?",
    ("Profit Maximization", "Sovereign Trust in Trade", "Data Harvesting", "Government Surveillance"):
        "What is the core mission of ZimAgritrust?",
    ("Strict prohibition of any gifts or payments to influence grading", "Only cash is forbidden", "Payment for speed is allowed", "Small gifts are okay"):
        "What is the ZimAgritrust policy on grading bribes?",
    ("The Farmer's relative", "An independent certified professional appointed by the platform", "The original Field Agent", "The Buyer's employee"):
        "Who is a Neutral Auditor on the ZimAgritrust platform?",
    ("0", "100", "50", "85"):
        "What is the minimum Trust Score required for a farmer to list produce on ZimAgritrust?",
    ("10%", "12.5%", "14%", "15%"):
        "What percentage commission does a Field Agent earn per verified transaction on ZimAgritrust?",
    ("Lending based on a farmer's house", "Loans secured by verified crops currently held in escrow/warehouse", "Loans based on future promises", "Giving away money"):
        "What is Warehouse Receipt Financing on ZimAgritrust?",
    # ── KYC & Verification ───────────────────────────────────────────────────
    ("GPS coordinates", "Pay slips and formal employment records", "Crop photos", "Phone numbers"):
        "What documents does a Field Agent primarily collect during farmer KYC verification?",
    ("It proves the data is mathematically impossible to forge", "It makes data look fancy", "It reduces server costs", "It is required by the government"):
        "Why is cryptographic hashing used for KYC records on ZimAgritrust?",
    ("Ignore it", "Send a WhatsApp message via the app to inform the farmer", "Ask a friend to go instead", "Cancel the visit"):
        "What should a Field Agent do if they will be late to a scheduled farm visit?",
    ("Show Evidence with technical data", "Call the police", "Offer a bribe", "Walk away"):
        "How should a Field Agent respond to a farmer who disputes a quality grading result?",
    ("Yes, it must be disclosed to avoid conflicts of interest", "No, it is private", "Only for full-time jobs", "Only if asked directly"):
        "Must a Field Agent disclose any personal business interests related to a farmer they are verifying?",
    # ── Produce Grading ──────────────────────────────────────────────────────
    ("Aflatoxin (Aspergillus)", "Large Grain Borer", "Maize Lethal Necrosis", "Minor discoloration"):
        "Which of the following is a Grade-F (automatic rejection) contaminant for maize on ZimAgritrust?",
    ("Every 14 days", "Every 30 days", "Every 7 days", "Only when it breaks"):
        "How often should a Field Agent recalibrate their moisture meter?",
    ("It is automatically revoked", "It expires after 30 days", "It remains active for future reference", "The Agent keeps it permanently"):
        "What happens to a Grade Certificate when a dispute is upheld against it?",
    ("Right to use the land for a specific period", "Abandoned land", "Full ownership forever", "Government-owned land"):
        "What is a 'Usufruct' land right in the context of ZimAgritrust farmer KYC?",
    ("System ban and report to local authorities", "Warning", "A retry", "Loss of 10 points"):
        "What is the consequence for a Field Agent who is caught falsifying a grade report?",
    # ── Disputes & Mediation ─────────────────────────────────────────────────
    ("Neutral Auditors appointed by the platform", "Community voting", "Coin flips", "Local court trials"):
        "Who resolves escalated disputes on the ZimAgritrust platform?",
    ("No, this is a side-trade conflict of interest", "Only if the price is fair", "Yes, after 30 days", "Yes, with Admin approval"):
        "Can a Field Agent purchase produce from a farmer they have just graded?",
    ("Grading", "Listing", "Payment", "Verification"):
        "Which step in the ZimAgritrust workflow requires a Field Agent's digital signature?",
    ("Grading Accuracy", "Response Time", "System Integrity", "User Feedback"):
        "Which KPI carries the highest weight in a Field Agent's quarterly performance review?",
    # ── Digital Tools ────────────────────────────────────────────────────────
    ("Data usage is lower and it works on basic smartphones", "Apps are too expensive", "There is no app", "WhatsApp is more secure"):
        "Why does ZimAgritrust primarily use USSD for farmer interactions in rural areas?",
    ("Teaching and demonstrating digital tools like USSD to improve farmer livelihoods", "Installing WiFi towers", "Posting on social media", "Selling gadgets"):
        "What does 'Digital Inclusion' mean for a ZimAgritrust Field Agent?",
    ("2-5 Days", "Instantly (via Mobile Money)", "14 Days", "Upon buyer's secondary approval"):
        "How quickly are funds released to a farmer after a ZimAgritrust trade is confirmed?",
    # ── Exam thresholds ──────────────────────────────────────────────────────
    ("70%", "75%", "80%", "85%"):
        "What is the minimum passing score required to complete a module quiz on ZimAgritrust Academy?",
    ("50%", "75%", "80%", "100%"):
        "What is the minimum score required to pass the Mid-Academy Examination?",
    ("70%", "80%", "90%", "100%"):
        "What is the minimum score required to pass the Final Certification Examination?",
    ("80%", "85%", "90%", "95%"):
        "What is the passing threshold for the Field Agent Certification Final Exam?",
}

def key(options):
    return tuple(sorted(options)) if options else ()

def run():
    db = SessionLocal()
    try:
        from app.models.classroom import QuizQuestion
        questions = db.query(QuizQuestion).all()
        updated = 0
        no_match = []

        for q in questions:
            if not q.question_text:
                k = key(q.options)
                text = QUESTION_MAP.get(k)
                if text:
                    q.question_text = text
                    updated += 1
                else:
                    no_match.append((str(q.id), q.options))

        db.commit()
        print(f"✅ Updated {updated} questions.")
        if no_match:
            print(f"⚠️  {len(no_match)} questions had no match:")
            for qid, opts in no_match[:10]:
                print(f"   {qid}: {opts}")
    finally:
        db.close()

if __name__ == "__main__":
    run()
