-- One-time: populate question_text for all blank classroom_quiz_questions
-- Run: docker exec agric-postgres-1 psql -U postgres -d zimagritrust -f /tmp/populate_questions.sql

UPDATE classroom_quiz_questions SET question_text = 'What is the core mission of ZimAgritrust?'
  WHERE options @> '["Sovereign Trust in Trade"]' AND options @> '["Profit Maximization"]';

UPDATE classroom_quiz_questions SET question_text = 'Which digital channel does ZimAgritrust primarily use for farmer interactions in rural Zimbabwe?'
  WHERE options @> '["USSD / WhatsApp"]' AND options @> '["React Native Pro"]';

UPDATE classroom_quiz_questions SET question_text = 'Who initiates a KYC verification request for a new farmer on the platform?'
  WHERE options @> '["The Field Agent"]' AND options @> '["The Warehouse Manager"]' AND NOT (options @> '["The Bank Manager"]');

UPDATE classroom_quiz_questions SET question_text = 'When does a farmer receive payment after a completed trade on ZimAgritrust?'
  WHERE options @> '["After Agent verification and delivery"]' AND options @> '["Before planting"]';

UPDATE classroom_quiz_questions SET question_text = 'What happens to an agent found guilty of faking a quality report?'
  WHERE options @> '["Immediate and permanent ban"]' AND options @> '["A small fine"]';

UPDATE classroom_quiz_questions SET question_text = 'What type of ledger does ZimAgritrust use to store all verified transactions?'
  WHERE options @> '["Blockchain-inspired Immutable Ledger"]' AND options @> '["Excel Spreadsheets"]';

UPDATE classroom_quiz_questions SET question_text = 'How quickly must a Field Agent respond to a newly assigned task?'
  WHERE options @> '["24 Hours"]' AND options @> '["12 Hours"]' AND options @> '["1 Week"]';

UPDATE classroom_quiz_questions SET question_text = 'Who or what authorizes fund release in a ZimAgritrust Smart Contract?'
  WHERE options @> '["The Smart Contract Logic"]' AND options @> '["The Bank Manager"]';

UPDATE classroom_quiz_questions SET question_text = 'What is the minimum Trust Score a farmer needs to list produce on ZimAgritrust?'
  WHERE options @> '["50"]' AND options @> '["60"]' AND options @> '["70"]' AND options @> '["80"]';

UPDATE classroom_quiz_questions SET question_text = 'What does GPS geo-tagging prove during a farm verification visit?'
  WHERE options @> '["To prove you are physically at the farm location"]' AND options @> '["To navigate to the farm"]';

UPDATE classroom_quiz_questions SET question_text = 'Why must a Field Agent keep their mobile device locked and secure?'
  WHERE options @> '["It contains sensitive farmer data including GPS locations and financial earnings"]' AND options @> '["It looks more professional"]';

UPDATE classroom_quiz_questions SET question_text = 'How should a Field Agent handle an insurance claim from a farmer who experienced crop damage?'
  WHERE options @> '["Visit the field and document conditions accurately"]' AND options @> '["Approve it without visiting"]';

UPDATE classroom_quiz_questions SET question_text = 'What happens to Escrow funds when a trade dispute is raised?'
  WHERE options @> '["Funds stay in Escrow until resolved"]' AND options @> '["Funds are split 50/50 immediately"]';

UPDATE classroom_quiz_questions SET question_text = 'What real-time data does the ZimAgritrust app provide to Field Agents during a verification?'
  WHERE options @> '["Current regional crop prices"]' AND options @> '["Stock market trends"]';

UPDATE classroom_quiz_questions SET question_text = 'What is the primary identity document required for farmer KYC on ZimAgritrust?'
  WHERE options @> '["The farmer''s physical National ID"]' AND options @> '["The farmer''s favorite color"]';

UPDATE classroom_quiz_questions SET question_text = 'What data is stored in the ZimAgritrust Agent app for audit purposes?'
  WHERE options @> '["Chat history, media, verification reports, and tracking data"]' AND options @> '["Social media posts"]';

UPDATE classroom_quiz_questions SET question_text = 'How does ZimAgritrust verification help farmers access loans?'
  WHERE options @> '["It provides verified data that banks use to issue loans"]' AND options @> '["It reduces their taxes"]';

UPDATE classroom_quiz_questions SET question_text = 'Under what condition can a dispute conversation log be reviewed?'
  WHERE options @> '["Only during an active dispute with Admin approval"]' AND options @> '["Always"]';

UPDATE classroom_quiz_questions SET question_text = 'What satellite imagery technology does ZimAgritrust use for land verification?'
  WHERE options @> '["Sentinel-2 Satellite Imagery"]' AND options @> '["Google Street View"]';

UPDATE classroom_quiz_questions SET question_text = 'What is the role of a Field Agent in digital literacy outreach?'
  WHERE options @> '["Teaching and demonstrating digital tools like USSD to improve farmer livelihoods"]' AND options @> '["Installing WiFi towers"]';

UPDATE classroom_quiz_questions SET question_text = 'How should a Field Agent respond to a farmer who disputes a quality grading result?'
  WHERE options @> '["Show Evidence with technical data"]' AND options @> '["Offer a bribe"]';

UPDATE classroom_quiz_questions SET question_text = 'What happens to an Agent''s certification when they are found guilty of fraud?'
  WHERE options @> '["It is automatically revoked"]' AND options @> '["It remains active for future reference"]';

UPDATE classroom_quiz_questions SET question_text = 'What should a Field Agent do if they will arrive late to a scheduled farm visit?'
  WHERE options @> '["Send a WhatsApp message via the app to inform the farmer"]' AND options @> '["Ignore it"]';

UPDATE classroom_quiz_questions SET question_text = 'What is a Usufruct land right in the context of ZimAgritrust farmer KYC?'
  WHERE options @> '["Right to use the land for a specific period"]' AND options @> '["Full ownership forever"]';

UPDATE classroom_quiz_questions SET question_text = 'Why does ZimAgritrust primarily use USSD for farmer interactions in rural areas?'
  WHERE options @> '["Data usage is lower and it works on basic smartphones"]' AND options @> '["Apps are too expensive"]';

UPDATE classroom_quiz_questions SET question_text = 'Must a Field Agent disclose any personal business interests related to a farmer they are verifying?'
  WHERE options @> '["Yes, it must be disclosed to avoid conflicts of interest"]' AND options @> '["No, it is private"]';

UPDATE classroom_quiz_questions SET question_text = 'What documents does a Field Agent primarily collect during farmer KYC verification?'
  WHERE options @> '["Pay slips and formal employment records"]' AND options @> '["GPS coordinates"]' AND options @> '["Crop photos"]';

UPDATE classroom_quiz_questions SET question_text = 'Why is cryptographic hashing used for KYC records on ZimAgritrust?'
  WHERE options @> '["It proves the data is mathematically impossible to forge"]' AND options @> '["It makes data look fancy"]';

UPDATE classroom_quiz_questions SET question_text = 'What is the consequence for a Field Agent caught falsifying a grade report?'
  WHERE options @> '["System ban and report to local authorities"]' AND options @> '["Warning"]' AND options @> '["A retry"]';

UPDATE classroom_quiz_questions SET question_text = 'What is the minimum passing score for the Final Certification Examination?'
  WHERE options @> '["70%"]' AND options @> '["80%"]' AND options @> '["90%"]' AND options @> '["100%"]';

UPDATE classroom_quiz_questions SET question_text = 'What is the minimum passing score for the Mid-Academy Examination?'
  WHERE options @> '["50%"]' AND options @> '["75%"]' AND options @> '["80%"]' AND options @> '["100%"]';

-- Additional questions from remaining unmatched options

UPDATE classroom_quiz_questions SET question_text = 'How do digital scales connect to the ZimAgritrust app during produce weighing?'
  WHERE options @> '["The weight display is captured via the agent''s camera"]' AND options @> '["By using voice commands"]';

UPDATE classroom_quiz_questions SET question_text = 'Why should a Field Agent sample produce from multiple layers of a bag or silo?'
  WHERE options @> '["Farmers may hide poor quality at the bottom"]' AND options @> '["It is too dusty"]';

UPDATE classroom_quiz_questions SET question_text = 'Why is GPS land measurement important during farm registration?'
  WHERE options @> '["To prevent farmers from claiming more land than they actually farm"]' AND options @> '["To calculate travel distance"]';

UPDATE classroom_quiz_questions SET question_text = 'Why must Escrow funds be kept in a separate account?'
  WHERE options @> '["Zero-Commingling compliance"]' AND options @> '["To earn more interest"]';

UPDATE classroom_quiz_questions SET question_text = 'Why is it important for a Field Agent to greet community leaders before starting verification?'
  WHERE options @> '["It builds community trust and smooths future verification access"]' AND options @> '["It is just politeness"]';

UPDATE classroom_quiz_questions SET question_text = 'What soil data does a Field Agent record during a farm visit?'
  WHERE options @> '["Nitrogen and phosphorous levels"]' AND options @> '["GPS coordinates"]' AND options @> '["Farmer''s age"]';

UPDATE classroom_quiz_questions SET question_text = 'What must a Field Agent do if they have a personal relationship with a farmer they are assigned to verify?'
  WHERE options @> '["Click ''Recuse'' in the app and let the task be reassigned"]' AND options @> '["Continue with the verification"]';

UPDATE classroom_quiz_questions SET question_text = 'How can a Field Agent appeal a negative performance review?'
  WHERE options @> '["By providing GPS logs and photos as evidence"]' AND options @> '["By asking an admin to delete it"]';

UPDATE classroom_quiz_questions SET question_text = 'What is the commission rate a Field Agent earns per verified listing on ZimAgritrust?'
  WHERE options @> '["1%"]' AND options @> '["2.5%"]' AND options @> '["5%"]' AND options @> '["10%"]';

UPDATE classroom_quiz_questions SET question_text = 'What encryption standard does ZimAgritrust use for all data in transit?'
  WHERE options @> '["End-to-End Encryption (E2EE)"]' AND options @> '["AES-128"]';

UPDATE classroom_quiz_questions SET question_text = 'What is the consequence if a Field Agent receives a bribe from a farmer?'
  WHERE options @> '["Nothing"]' AND options @> '["A warning email"]' AND options @> '["Immediate and permanent ban"]' AND NOT (options @> '["A small fine"]' AND options @> '["Immediate and permanent ban"]' AND options @> '["A warning email"]' AND options @> '["Nothing"]' AND NOT EXISTS (SELECT 1));

UPDATE classroom_quiz_questions SET question_text = 'What career level comes after Certified Agent in the ZimAgritrust progression?'
  WHERE options @> '["Senior Agent"]' AND options @> '["Certified Agent"]' AND options @> '["Lead Auditor"]';

UPDATE classroom_quiz_questions SET question_text = 'If a farmer has crop inventory worth $1000 and a 50% Warehouse Receipt loan, how much do they receive?'
  WHERE options @> '["$500 goes to the bank and $500 to the farmer"]' AND options @> '["The farmer keeps all $1000"]';

UPDATE classroom_quiz_questions SET question_text = 'What is the correct action when a delivered crop fails quality check at the warehouse?'
  WHERE options @> '["Refund to Buyer"]' AND options @> '["Release to Farmer"]' AND options @> '["Partial Settlement"]';

UPDATE classroom_quiz_questions SET question_text = 'What is a Grade-B classification for maize on ZimAgritrust?'
  WHERE options @> '["Good for processing or animal feed only"]' AND options @> '["Premium export quality"]';

UPDATE classroom_quiz_questions SET question_text = 'How should a Field Agent handle a farmer who argues their crop is damp but the moisture reading is high?'
  WHERE options @> '["Show the moisture meter evidence and propose a re-verification after drying"]';

-- Set any still-blank questions to a placeholder so the quiz renders something
UPDATE classroom_quiz_questions 
  SET question_text = 'Question ' || order_sequence::text || ': Select the correct answer based on your training.'
  WHERE question_text = '' OR question_text IS NULL;

SELECT COUNT(*) as total, COUNT(NULLIF(question_text,'')) as with_text FROM classroom_quiz_questions;
