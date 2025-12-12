import os, sys, time
import requests
import json

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BACKEND_DIR = os.path.join(BASE, 'backend')
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

import app as backend_app
from models import User, Quiz, QuizQuestion, QuizQuestionMapping, db

# Login as student
resp = requests.post('http://127.0.0.1:5000/api/auth/login', json={'username': 'student_test', 'password': 'NewStudent@123'})
if resp.status_code != 200:
    print('Student login failed:', resp.text)
    sys.exit(1)

student_token = resp.json().get('access_token')
headers = {'Authorization': f'Bearer {student_token}'}

# Get a quiz (assuming quiz exists)
with backend_app.app.app_context():
    quiz = Quiz.query.first()
    if not quiz:
        print('No quiz found in database; run backend/app.py to initialize')
        sys.exit(1)
    
    quiz_id = quiz.quiz_id

# Fetch quiz
quiz_resp = requests.get(f'http://127.0.0.1:5000/api/quizzes/{quiz_id}', headers=headers)
print('Quiz fetch:', quiz_resp.status_code)
if quiz_resp.status_code != 200:
    print('Failed to fetch quiz')
    sys.exit(1)

# Get actual question IDs and answers from the quiz to trigger wrong answers
with backend_app.app.app_context():
    mappings = QuizQuestionMapping.query.filter_by(quiz_id=quiz_id).all()
    if not mappings:
        print(f'No questions in quiz {quiz_id}')
        sys.exit(1)
    
    # Build answers: intentionally select wrong answers to trigger AI explanations
    submit_data = {
        'answers': [
            {'question_id': m.question_id, 'selected_answer': 2}  # Select answer 2 for all (likely wrong)
            for m in mappings[:3]  # Test with first 3 questions
        ],
        'time_taken_minutes': 5
    }

submit_resp = requests.post(f'http://127.0.0.1:5000/api/quizzes/{quiz_id}/submit', headers=headers, json=submit_data)
print('Submit quiz:', submit_resp.status_code)
result = submit_resp.json()
print(json.dumps(result, indent=2, ensure_ascii=False))

# Check for AI explanations in response
if submit_resp.status_code == 200:
    answers = result.get('result', {}).get('answers', [])
    ai_explanations_found = [ans for ans in answers if ans.get('ai_explanation')]
    print(f'\n✓ Found {len(ai_explanations_found)} AI explanations out of {len(answers)} answers')
    if ai_explanations_found:
        print('Sample AI explanation:')
        print(ai_explanations_found[0].get('ai_explanation'))
