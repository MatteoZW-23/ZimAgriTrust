UPDATE classroom_quiz_questions SET correct_answer = '80%', question_text = 'What is the minimum passing score for quizzes on ZimAgritrust Academy?'
  WHERE options::text LIKE '%"70%"%' AND options::text LIKE '%"75%"%' AND options::text LIKE '%"80%"%' AND options::text LIKE '%"85%"%';

UPDATE classroom_quiz_questions SET correct_answer = '80%', question_text = 'What is the minimum passing score for the Mid-Academy Examination?'
  WHERE options::text LIKE '%"50%"%' AND options::text LIKE '%"75%"%' AND options::text LIKE '%"80%"%' AND options::text LIKE '%"100%"%';

UPDATE classroom_quiz_questions SET correct_answer = '2.5%', question_text = 'What percentage commission does a Field Agent earn per verified transaction?'
  WHERE options::text LIKE '%"1%"%' AND options::text LIKE '%"2.5%"%' AND options::text LIKE '%"5%"%' AND options::text LIKE '%"10%"%';

UPDATE classroom_quiz_questions SET correct_answer = '85%', question_text = 'What is the passing threshold for the Field Agent Certification Final Exam?'
  WHERE options::text LIKE '%"80%"%' AND options::text LIKE '%"85%"%' AND options::text LIKE '%"90%"%' AND options::text LIKE '%"95%"%';

UPDATE classroom_quiz_questions SET correct_answer = 'Temporary suspension', question_text = 'What is the penalty for a first-time minor violation by a Field Agent?'
  WHERE options::text LIKE '%Temporary suspension%' AND options::text LIKE '%Score reset%';

UPDATE classroom_quiz_questions SET correct_answer = 'Upon delivery confirmation', question_text = 'When does a ZimAgritrust smart contract release payment to the farmer?'
  WHERE options::text LIKE '%Upon delivery confirmation%';

UPDATE classroom_quiz_questions SET correct_answer = 'Cancellation fee is deducted from the deposit', question_text = 'What happens if a Buyer cancels a confirmed trade on ZimAgritrust?'
  WHERE options::text LIKE '%Cancellation fee is deducted%';

UPDATE classroom_quiz_questions SET correct_answer = 'Stones, dirt, and chaff', question_text = 'What are the primary physical impurities tested for in grain grading?'
  WHERE options::text LIKE '%Stones, dirt, and chaff%';

UPDATE classroom_quiz_questions SET correct_answer = '7 days', question_text = 'How long does a farmer have to respond to a dispute resolution decision?'
  WHERE options::text LIKE '%"7 days"%' AND options::text LIKE '%"24 hours"%';

UPDATE classroom_quiz_questions SET correct_answer = 'Encouraging farmers to trade off-platform to avoid fees', question_text = 'Which action would result in immediate termination of a Field Agent?'
  WHERE options::text LIKE '%off-platform to avoid fees%';

UPDATE classroom_quiz_questions SET correct_answer = 'Sharing a farmer''s warehouse photo on social media', question_text = 'Which action by a Field Agent would violate farmer data privacy rules?'
  WHERE options::text LIKE '%warehouse photo on social media%';

UPDATE classroom_quiz_questions SET correct_answer = 'Automatically when satellite data meets predefined conditions', question_text = 'How is parametric crop insurance triggered on ZimAgritrust?'
  WHERE options::text LIKE '%satellite data meets predefined conditions%';

UPDATE classroom_quiz_questions SET correct_answer = 'Anti-Money Laundering', question_text = 'What does AML stand for in the context of ZimAgritrust compliance?'
  WHERE options::text LIKE '%Anti-Money Laundering%';

UPDATE classroom_quiz_questions SET correct_answer = '$10,000', question_text = 'What is the maximum single-transaction value a Trainee Agent can process on ZimAgritrust?'
  WHERE options::text LIKE '%$10,000%' AND options::text LIKE '%$50,000%';

UPDATE classroom_quiz_questions SET correct_answer = 'It ensures immutability and prevents tampering with transaction records', question_text = 'Why does ZimAgritrust use a blockchain-inspired ledger for all transactions?'
  WHERE options::text LIKE '%ensures immutability%';

UPDATE classroom_quiz_questions SET correct_answer = 'It can never be deleted or altered, but a correction can be appended', question_text = 'What happens to a verified record that was found to contain an error?'
  WHERE options::text LIKE '%correction can be appended%';

UPDATE classroom_quiz_questions SET correct_answer = 'Demonstrate it step-by-step on their own phone', question_text = 'What is the best way for a Field Agent to teach a farmer how to use USSD?'
  WHERE options::text LIKE '%step-by-step on their own phone%';

SELECT COUNT(*) as total, COUNT(NULLIF(correct_answer,'')) as with_answer, COUNT(*) FILTER (WHERE question_text NOT ILIKE 'Question%') as named FROM classroom_quiz_questions;
