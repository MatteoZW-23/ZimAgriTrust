-- Populate correct_answer for all classroom_quiz_questions
-- Matches by question_text (now populated). Run once.
-- docker exec agric-postgres-1 psql -U postgres -d agri_trust -f /tmp/set_correct_answers.sql

UPDATE classroom_quiz_questions SET correct_answer = 'Sovereign Trust in Trade'
  WHERE question_text ILIKE '%core mission of ZimAgritrust%';

UPDATE classroom_quiz_questions SET correct_answer = 'USSD / WhatsApp'
  WHERE question_text ILIKE '%digital channel%primarily use%farmer interactions%';

UPDATE classroom_quiz_questions SET correct_answer = 'The Field Agent'
  WHERE question_text ILIKE '%initiates a KYC verification request%';

UPDATE classroom_quiz_questions SET correct_answer = 'After Agent verification and delivery'
  WHERE question_text ILIKE '%farmer receive payment%completed trade%';

UPDATE classroom_quiz_questions SET correct_answer = 'Immediate and permanent ban'
  WHERE question_text ILIKE '%found guilty of faking%quality report%';

UPDATE classroom_quiz_questions SET correct_answer = 'Blockchain-inspired Immutable Ledger'
  WHERE question_text ILIKE '%type of ledger%ZimAgritrust use%verified transactions%';

UPDATE classroom_quiz_questions SET correct_answer = '24 Hours'
  WHERE question_text ILIKE '%Field Agent respond%newly assigned task%';

UPDATE classroom_quiz_questions SET correct_answer = 'The Smart Contract Logic'
  WHERE question_text ILIKE '%authorizes fund release%Smart Contract%';

UPDATE classroom_quiz_questions SET correct_answer = '80'
  WHERE question_text ILIKE '%minimum Trust Score%farmer%list produce%';

UPDATE classroom_quiz_questions SET correct_answer = 'To prove you are physically at the farm location'
  WHERE question_text ILIKE '%GPS geo-tagging prove%farm verification visit%';

UPDATE classroom_quiz_questions SET correct_answer = 'It contains sensitive farmer data including GPS locations and financial earnings'
  WHERE question_text ILIKE '%Field Agent keep their mobile device locked%';

UPDATE classroom_quiz_questions SET correct_answer = 'Visit the field and document conditions accurately'
  WHERE question_text ILIKE '%insurance claim%farmer%crop damage%';

UPDATE classroom_quiz_questions SET correct_answer = 'Funds stay in Escrow until resolved'
  WHERE question_text ILIKE '%Escrow funds%trade dispute%raised%';

UPDATE classroom_quiz_questions SET correct_answer = 'Current regional crop prices'
  WHERE question_text ILIKE '%real-time data%ZimAgritrust app%verification%';

UPDATE classroom_quiz_questions SET correct_answer = 'The farmer''s physical National ID'
  WHERE question_text ILIKE '%primary identity document%farmer KYC%';

UPDATE classroom_quiz_questions SET correct_answer = 'Chat history, media, verification reports, and tracking data'
  WHERE question_text ILIKE '%data is stored in the ZimAgritrust Agent app%audit%';

UPDATE classroom_quiz_questions SET correct_answer = 'It provides verified data that banks use to issue loans'
  WHERE question_text ILIKE '%verification help farmers access loans%';

UPDATE classroom_quiz_questions SET correct_answer = 'Only during an active dispute with Admin approval'
  WHERE question_text ILIKE '%dispute conversation log be reviewed%';

UPDATE classroom_quiz_questions SET correct_answer = 'Sentinel-2 Satellite Imagery'
  WHERE question_text ILIKE '%satellite imagery%ZimAgritrust use%land verification%';

UPDATE classroom_quiz_questions SET correct_answer = 'Teaching and demonstrating digital tools like USSD to improve farmer livelihoods'
  WHERE question_text ILIKE '%Field Agent%digital literacy outreach%';

UPDATE classroom_quiz_questions SET correct_answer = 'Show Evidence with technical data'
  WHERE question_text ILIKE '%farmer who disputes a quality grading result%';

UPDATE classroom_quiz_questions SET correct_answer = 'It is automatically revoked'
  WHERE question_text ILIKE '%Agent%certification%found guilty of fraud%';

UPDATE classroom_quiz_questions SET correct_answer = 'Send a WhatsApp message via the app to inform the farmer'
  WHERE question_text ILIKE '%late%scheduled farm visit%';

UPDATE classroom_quiz_questions SET correct_answer = 'Right to use the land for a specific period'
  WHERE question_text ILIKE '%Usufruct land right%';

UPDATE classroom_quiz_questions SET correct_answer = 'Data usage is lower and it works on basic smartphones'
  WHERE question_text ILIKE '%primarily use USSD%rural areas%';

UPDATE classroom_quiz_questions SET correct_answer = 'Yes, it must be disclosed to avoid conflicts of interest'
  WHERE question_text ILIKE '%disclose any personal business interests%';

UPDATE classroom_quiz_questions SET correct_answer = 'Pay slips and formal employment records'
  WHERE question_text ILIKE '%documents%Field Agent%collect%farmer KYC verification%';

UPDATE classroom_quiz_questions SET correct_answer = 'It proves the data is mathematically impossible to forge'
  WHERE question_text ILIKE '%cryptographic hashing%KYC records%';

UPDATE classroom_quiz_questions SET correct_answer = 'System ban and report to local authorities'
  WHERE question_text ILIKE '%consequence%Field Agent caught falsifying%grade report%';

UPDATE classroom_quiz_questions SET correct_answer = '80%'
  WHERE question_text ILIKE '%minimum passing score%Final Certification%';

UPDATE classroom_quiz_questions SET correct_answer = '80%'
  WHERE question_text ILIKE '%minimum passing score%Mid-Academy%';

UPDATE classroom_quiz_questions SET correct_answer = '80%'
  WHERE question_text ILIKE '%minimum passing score%module quiz%';

UPDATE classroom_quiz_questions SET correct_answer = 'The weight display is captured via the agent''s camera'
  WHERE question_text ILIKE '%digital scales connect%ZimAgritrust app%weighing%';

UPDATE classroom_quiz_questions SET correct_answer = 'Farmers may hide poor quality at the bottom'
  WHERE question_text ILIKE '%sample produce from multiple layers%';

UPDATE classroom_quiz_questions SET correct_answer = 'To prevent farmers from claiming more land than they actually farm'
  WHERE question_text ILIKE '%GPS land measurement important%farm registration%';

UPDATE classroom_quiz_questions SET correct_answer = 'Zero-Commingling compliance'
  WHERE question_text ILIKE '%Escrow funds%kept in a separate account%';

UPDATE classroom_quiz_questions SET correct_answer = 'It builds community trust and smooths future verification access'
  WHERE question_text ILIKE '%greet community leaders%before starting verification%';

UPDATE classroom_quiz_questions SET correct_answer = 'Nitrogen and phosphorous levels'
  WHERE question_text ILIKE '%soil data%Field Agent record%farm visit%';

UPDATE classroom_quiz_questions SET correct_answer = 'Click ''Recuse'' in the app and let the task be reassigned'
  WHERE question_text ILIKE '%personal relationship with a farmer%assigned to verify%';

UPDATE classroom_quiz_questions SET correct_answer = 'By providing GPS logs and photos as evidence'
  WHERE question_text ILIKE '%Field Agent appeal%negative performance review%';

UPDATE classroom_quiz_questions SET correct_answer = '2.5%'
  WHERE question_text ILIKE '%commission rate%Field Agent earns per verified listing%';

UPDATE classroom_quiz_questions SET correct_answer = 'End-to-End Encryption (E2EE)'
  WHERE question_text ILIKE '%encryption standard%ZimAgritrust%data in transit%';

UPDATE classroom_quiz_questions SET correct_answer = 'Senior Agent'
  WHERE question_text ILIKE '%career level comes after Certified Agent%';

UPDATE classroom_quiz_questions SET correct_answer = '$500 goes to the bank and $500 to the farmer'
  WHERE question_text ILIKE '%crop inventory worth%1000%50% Warehouse Receipt loan%';

UPDATE classroom_quiz_questions SET correct_answer = 'Refund to Buyer'
  WHERE question_text ILIKE '%delivered crop fails quality check%warehouse%';

UPDATE classroom_quiz_questions SET correct_answer = 'Good for processing or animal feed only'
  WHERE question_text ILIKE '%Grade-B classification%maize%';

UPDATE classroom_quiz_questions SET correct_answer = 'Show the moisture meter evidence and propose a re-verification after drying'
  WHERE question_text ILIKE '%farmer%argues%crop is damp%moisture reading is high%';

-- Questions with placeholder text -- set best-guess based on options
-- "The Borrower / Collateral Officer / Bank Manager / Insurance Agent" -> Who does what in a Warehouse Receipt loan
UPDATE classroom_quiz_questions SET correct_answer = 'The Collateral Officer'
  WHERE question_text ILIKE 'Question 1:%' AND options::text ILIKE '%Collateral Officer%';

UPDATE classroom_quiz_questions SET correct_answer = 'Acknowledge the farmer''s expectations'
  WHERE question_text ILIKE 'Question 1:%' AND options::text ILIKE '%Acknowledge the farmer%';

UPDATE classroom_quiz_questions SET correct_answer = '100'
  WHERE question_text ILIKE 'Question 1:%' AND options::text ILIKE '%"100"%' AND options::text ILIKE '%"10"%' AND options::text ILIKE '%"50"%';

UPDATE classroom_quiz_questions SET correct_answer = 'A formal disagreement logged by either Buyer or Farmer via the portal'
  WHERE question_text ILIKE 'Question 1:%' AND options::text ILIKE '%formal disagreement%';

UPDATE classroom_quiz_questions SET correct_answer = 'Normalized Difference Vegetation Index - measures plant health'
  WHERE question_text ILIKE 'Question 1:%' AND options::text ILIKE '%NDVI%' OR (options::text ILIKE '%Vegetation Index%');

UPDATE classroom_quiz_questions SET correct_answer = '5 from different depths'
  WHERE question_text ILIKE 'Question 1:%' AND options::text ILIKE '%different depths%';

UPDATE classroom_quiz_questions SET correct_answer = 'It makes the Agent a ''Legal Witness'' to the quality'
  WHERE question_text ILIKE 'Question 1:%' AND options::text ILIKE '%Legal Witness%';

UPDATE classroom_quiz_questions SET correct_answer = '24 hours after a dispute is logged for parties to settle privately'
  WHERE question_text ILIKE 'Question 2:%' AND options::text ILIKE '%dispute is logged%';

UPDATE classroom_quiz_questions SET correct_answer = '50%'
  WHERE question_text ILIKE 'Question 2:%' AND options::text ILIKE '%20%' AND options::text ILIKE '%50%' AND options::text NOT ILIKE '%80%';

UPDATE classroom_quiz_questions SET correct_answer = 'The Agent Portal''s ML-Camera'
  WHERE question_text ILIKE 'Question 2:%' AND options::text ILIKE '%ML-Camera%';

UPDATE classroom_quiz_questions SET correct_answer = 'Use a secondary tool immediately and flag the report'
  WHERE question_text ILIKE 'Question 2:%' AND options::text ILIKE '%secondary tool%';

UPDATE classroom_quiz_questions SET correct_answer = 'The Field Agent'
  WHERE question_text ILIKE 'Question 2:%' AND options::text ILIKE '%Warehouse Manager%' AND options::text ILIKE '%The Buyer%';

UPDATE classroom_quiz_questions SET correct_answer = 'It is recorded on the blockchain and shared with the National Credit Bureau'
  WHERE question_text ILIKE 'Question 2:%' AND options::text ILIKE '%National Credit Bureau%';

UPDATE classroom_quiz_questions SET correct_answer = 'A Title Deed'
  WHERE question_text ILIKE 'Question 2:%' AND options::text ILIKE '%Title Deed%';

UPDATE classroom_quiz_questions SET correct_answer = 'Deposits full amount into Escrow'
  WHERE question_text ILIKE 'Question 2:%' AND options::text ILIKE '%Deposits full amount into Escrow%';

UPDATE classroom_quiz_questions SET correct_answer = 'Repayment Rate'
  WHERE question_text ILIKE 'Question 2:%' AND options::text ILIKE '%Repayment Rate%';

UPDATE classroom_quiz_questions SET correct_answer = 'To maintain transparency and build trust'
  WHERE question_text ILIKE 'Question 2:%' AND options::text ILIKE '%transparency and build trust%';

-- Final check
SELECT COUNT(*) as total, COUNT(NULLIF(correct_answer,'')) as with_answer FROM classroom_quiz_questions;
