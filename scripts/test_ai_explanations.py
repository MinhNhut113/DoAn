import time
import json

# Import backend as package so relative imports work consistently
from backend import app as backend_app
from backend.models import Quiz, QuizQuestion, QuizQuestionMapping, db

# Ensure DB tables exist and seed a minimal quiz if none present
with backend_app.app_context():
    db.create_all()
    quiz = Quiz.query.first()
    if not quiz:
        quiz = Quiz(quiz_name='Auto Test Quiz')
        db.session.add(quiz)
        db.session.flush()
        # create 3 simple multiple-choice questions
        questions = []
        for i in range(1, 4):
            q = QuizQuestion(question_text=f'Sample question {i}?', question_type='multiple_choice', options='["A","B","C","D"]', correct_answer=1, explanation='Sample explanation')
            db.session.add(q)
            db.session.flush()
            questions.append(q)
            m = QuizQuestionMapping(quiz_id=quiz.quiz_id, question_id=q.question_id, question_order=i)
            db.session.add(m)
        db.session.commit()
    quiz_id = quiz.quiz_id

client = backend_app.test_client()

# Login as student (password used in tests is 'Student@123')
login = client.post('/api/auth/login', json={'username': 'student_test', 'password': 'Student@123'})
if login.status_code != 200:
    print('Student login failed:', login.get_data(as_text=True))
    raise SystemExit(1)

student_token = login.get_json().get('access_token')
headers = {'Authorization': f'Bearer {student_token}'}

# Fetch quiz
quiz_resp = client.get(f'/api/quizzes/{quiz_id}', headers=headers)
print('Quiz fetch:', quiz_resp.status_code)
if quiz_resp.status_code != 200:
    print('Failed to fetch quiz')
    raise SystemExit(1)

# Get actual question IDs and answers from the quiz to trigger wrong answers
with backend_app.app_context():
    mappings = QuizQuestionMapping.query.filter_by(quiz_id=quiz_id).all()
    if not mappings:
        print(f'No questions in quiz {quiz_id}')
        raise SystemExit(1)

    # Build answers: intentionally select wrong answers to trigger AI explanations
    submit_data = {
        'answers': [
            {'question_id': m.question_id, 'selected_answer': 2}
            for m in mappings[:3]
        ],
        'time_taken_minutes': 5
    }

submit_resp = client.post(f'/api/quizzes/{quiz_id}/submit', headers=headers, json=submit_data)
print('Submit quiz:', submit_resp.status_code)
result = submit_resp.get_json()
print(json.dumps(result, indent=2, ensure_ascii=False))

# Check for AI explanations in response
if submit_resp.status_code == 200:
    answers = result.get('result', {}).get('answers', [])
    ai_explanations_found = [ans for ans in answers if ans.get('ai_explanation')]
    print(f'\n✓ Found {len(ai_explanations_found)} AI explanations out of {len(answers)} answers')
    if ai_explanations_found:
        print('Sample AI explanation:')
        print(ai_explanations_found[0].get('ai_explanation'))
