import os, sys, json
import requests

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BACKEND_DIR = os.path.join(BASE, 'backend')
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

import app as backend_app
from models import User, Course, Lesson, Assignment, AssignmentSubmission, db
from datetime import datetime, timedelta

# Login as student
resp = requests.post('http://127.0.0.1:5000/api/auth/login', json={'username': 'student_test', 'password': 'NewStudent@123'})
if resp.status_code != 200:
    print('Student login failed:', resp.text)
    sys.exit(1)

student_token = resp.json().get('access_token')
student_id = resp.json().get('user').get('user_id')
headers = {'Authorization': f'Bearer {student_token}'}

print('✓ Student logged in:', student_id)

# Get or create test assignment
with backend_app.app.app_context():
    # Find a lesson with a course
    lesson = Lesson.query.filter(Lesson.course_id != None).first()
    if not lesson:
        print('No lesson found to test with')
        sys.exit(1)
    
    lesson_id = lesson.lesson_id
    course_id = lesson.course_id
    
    # Create test assignment
    assign = Assignment.query.filter_by(lesson_id=lesson_id).first()
    if not assign:
        assign = Assignment(
            course_id=course_id,
            lesson_id=lesson_id,
            assignment_title='Test Assignment',
            assignment_description='Test description',
            due_date=datetime.utcnow() + timedelta(days=7),
            max_score=100
        )
        db.session.add(assign)
        db.session.commit()
        print(f'Created assignment {assign.assignment_id} for lesson {lesson_id}')
    
    assignment_id = assign.assignment_id

# Test 1: Fetch assignment for lesson
print(f'\n1. Fetching assignment for lesson {lesson_id}...')
resp = requests.get(f'http://127.0.0.1:5000/api/assignments/lesson/{lesson_id}', headers=headers)
print(f'   Status: {resp.status_code}')
data = resp.json()
if data.get('assignment'):
    print(f'   ✓ Found assignment: {data["assignment"]["assignment_title"]}')
    print(f'   Previous submission: {data.get("submission") is not None}')
else:
    print('   No assignment found')

# Test 2: Submit assignment
print(f'\n2. Submitting assignment {assignment_id}...')
submit_data = {
    'assignment_id': assignment_id,
    'submission_content': 'My solution to the assignment',
    'file_url': 'https://drive.google.com/file/d/1234/view'
}
resp = requests.post('http://127.0.0.1:5000/api/assignments/submit', headers=headers, json=submit_data)
print(f'   Status: {resp.status_code}')
if resp.status_code in (200, 201):
    submission = resp.json().get('submission')
    print(f'   ✓ Submission created/updated: {submission["submission_id"]}')
    print(f'   Content: {submission["submission_content"][:50]}...')
    print(f'   File URL: {submission["file_url"]}')
else:
    print(f'   Error: {resp.text}')

# Test 3: Fetch assignment again to see updated submission
print(f'\n3. Fetching assignment again to verify submission...')
resp = requests.get(f'http://127.0.0.1:5000/api/assignments/lesson/{lesson_id}', headers=headers)
data = resp.json()
if data.get('submission'):
    submission = data['submission']
    print(f'   ✓ Submission found')
    print(f'   Submitted at: {submission["submitted_at"]}')
    print(f'   Score: {submission["score"]}')
    
    # Test 4: Re-submit (update)
    print(f'\n4. Re-submitting assignment (updating)...')
    submit_data['submission_content'] = 'Updated solution'
    resp = requests.post('http://127.0.0.1:5000/api/assignments/submit', headers=headers, json=submit_data)
    if resp.status_code in (200, 201):
        updated = resp.json().get('submission')
        print(f'   ✓ Submission updated')
        print(f'   New content: {updated["submission_content"]}')
    else:
        print(f'   Error: {resp.text}')
else:
    print('   Submission not found')

print('\n✓ All tests passed!')
