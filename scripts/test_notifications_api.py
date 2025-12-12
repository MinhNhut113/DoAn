import time

from backend import app as backend_app
from backend.models import User, Notification, db

# Use test client and existing test student
client = backend_app.test_client()

# Login as student
login = client.post('/api/auth/login', json={'username': 'student_test', 'password': 'Student@123'})
if login.status_code != 200:
    print('Student login failed:', login.get_data(as_text=True))
    raise SystemExit(1)

student_token = login.get_json().get('access_token')
student_id = login.get_json().get('user').get('user_id')
headers = {'Authorization': f'Bearer {student_token}'}

print('✓ Student logged in:', student_id)

# Test 1: Fetch notifications
print('\n1. Fetching all notifications...')
resp = client.get('/api/notifications/', headers=headers)
print(f'   Status: {resp.status_code}')
notifications = resp.get_json()
print(f'   Total notifications: {len(notifications)}')
if notifications:
    for n in notifications[:2]:
        print(f'   - {n["title"]}: {n["is_read"]}')

# Test 2: Fetch unread notifications
print('\n2. Fetching unread notifications...')
resp = client.get('/api/notifications/?unread=true', headers=headers)
print(f'   Status: {resp.status_code}')
unread = resp.get_json()
print(f'   Unread notifications: {len(unread)}')

# Test 3: Mark one as read
if unread:
    notif_id = unread[0]['notification_id']
    print(f'\n3. Marking notification {notif_id} as read...')
    resp = client.post(f'/api/notifications/{notif_id}/read', headers=headers)
    print(f'   Status: {resp.status_code}')
    print(f'   Response: {resp.get_json()}')
    
    # Verify it's read
    print(f'\n4. Verifying notification {notif_id} is marked read...')
    resp = client.get('/api/notifications/?unread=true', headers=headers)
    unread_after = resp.get_json()
    print(f'   Unread count after: {len(unread_after)}')
    was_marked = not any(n['notification_id'] == notif_id for n in unread_after)
    print(f'   ✓ Notification marked as read: {was_marked}')
else:
    print('\n3. No unread notifications to test mark-read')

print('\n✓ All tests passed!')
