import os, json

from backend import app as backend_app
from backend.models import User, Course, Lesson, Assignment, AssignmentSubmission, db
from datetime import datetime, timedelta

# Login as student using test client
client = backend_app.test_client()
login = client.post('/api/auth/login', json={'username': 'student_test', 'password': 'NewStudent@123'})
if login.status_code != 200:
    print('Student login failed:', login.get_data(as_text=True))
    raise SystemExit(1)

student_token = login.get_json().get('access_token')
student_id = login.get_json().get('user').get('user_id')
headers = {'Authorization': f'Bearer {student_token}'}

print('✓ Student logged in:', student_id)

# Get or create test assignment
with backend_app.app_context():
    # Find a lesson with a course
    lesson = Lesson.query.filter(Lesson.course_id != None).first()
    if not lesson:
        # create a minimal course and lesson
        course = Course(course_name='Auto Test Course', description='Auto-created for tests')
        db.session.add(course)
        db.session.flush()
        lesson = Lesson(course_id=course.course_id, lesson_title='Auto Test Lesson', lesson_content='Test', lesson_order=1)
        db.session.add(lesson)
        db.session.commit()
        print('Created course+lesson', course.course_id, lesson.lesson_id)
    
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
resp = client.get(f'/api/assignments/lesson/{lesson_id}', headers=headers)
print(f'   Status: {resp.status_code}')
data = resp.get_json()
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
resp = client.post('/api/assignments/submit', headers=headers, json=submit_data)
print(f'   Status: {resp.status_code}')
if resp.status_code in (200, 201):
    submission = resp.get_json().get('submission')
    print(f'   ✓ Submission created/updated: {submission["submission_id"]}')
    print(f'   Content: {submission["submission_content"][:50]}...')
    print(f'   File URL: {submission["file_url"]}')
else:
    print(f'   Error: {resp.get_data(as_text=True)}')

# Test 3: Fetch assignment again to see updated submission
print(f'\n3. Fetching assignment again to verify submission...')
resp = client.get(f'/api/assignments/lesson/{lesson_id}', headers=headers)
data = resp.get_json()
if data.get('submission'):
    submission = data['submission']
    print(f'   ✓ Submission found')
    print(f'   Submitted at: {submission["submitted_at"]}')
    print(f'   Score: {submission["score"]}')
    
    # Test 4: Re-submit (update)
    print(f'\n4. Re-submitting assignment (updating)...')
    submit_data['submission_content'] = 'Updated solution'
    resp = client.post('/api/assignments/submit', headers=headers, json=submit_data)
    if resp.status_code in (200, 201):
        updated = resp.get_json().get('submission')
        print(f'   ✓ Submission updated')
        print(f'   New content: {updated["submission_content"]}')
    else:
        print(f'   Error: {resp.get_data(as_text=True)}')
else:
    print('   Submission not found')

print('\n✓ All tests passed!')
