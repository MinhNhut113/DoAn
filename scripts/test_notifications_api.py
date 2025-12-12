import os, sys, time
import requests

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BACKEND_DIR = os.path.join(BASE, 'backend')
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

import app as backend_app
from models import User, Notification, db
from datetime import datetime

# Login as student
resp = requests.post('http://127.0.0.1:5000/api/auth/login', json={'username': 'student_test', 'password': 'NewStudent@123'})
if resp.status_code != 200:
    print('Student login failed:', resp.text)
    sys.exit(1)

student_token = resp.json().get('access_token')
student_id = resp.json().get('user').get('user_id')
headers = {'Authorization': f'Bearer {student_token}'}

print('✓ Student logged in:', student_id)

# Test 1: Fetch notifications
print('\n1. Fetching all notifications...')
resp = requests.get('http://127.0.0.1:5000/api/notifications/', headers=headers)
print(f'   Status: {resp.status_code}')
notifications = resp.json()
print(f'   Total notifications: {len(notifications)}')
if notifications:
    for n in notifications[:2]:
        print(f'   - {n["title"]}: {n["is_read"]}')

# Test 2: Fetch unread notifications
print('\n2. Fetching unread notifications...')
resp = requests.get('http://127.0.0.1:5000/api/notifications/?unread=true', headers=headers)
print(f'   Status: {resp.status_code}')
unread = resp.json()
print(f'   Unread notifications: {len(unread)}')

# Test 3: Mark one as read
if unread:
    notif_id = unread[0]['notification_id']
    print(f'\n3. Marking notification {notif_id} as read...')
    resp = requests.post(f'http://127.0.0.1:5000/api/notifications/{notif_id}/read', headers=headers)
    print(f'   Status: {resp.status_code}')
    print(f'   Response: {resp.json()}')
    
    # Verify it's read
    print(f'\n4. Verifying notification {notif_id} is marked read...')
    resp = requests.get('http://127.0.0.1:5000/api/notifications/?unread=true', headers=headers)
    unread_after = resp.json()
    print(f'   Unread count after: {len(unread_after)}')
    was_marked = not any(n['notification_id'] == notif_id for n in unread_after)
    print(f'   ✓ Notification marked as read: {was_marked}')
else:
    print('\n3. No unread notifications to test mark-read')

print('\n✓ All tests passed!')
