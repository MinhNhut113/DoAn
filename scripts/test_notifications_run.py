import os
import sys
import time
import requests

# change cwd to backend so imports like `from config import Config` work
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BACKEND_DIR = os.path.join(BASE, 'backend')
os.chdir(BACKEND_DIR)
sys.path.insert(0, BACKEND_DIR)

import app as backend_app
from models import db, User

with backend_app.app.app_context():
    admin_username = 'admin_test'
    admin = User.query.filter_by(username=admin_username).first()
    if not admin:
        admin = User(username=admin_username, email='admin_test@example.com', full_name='Admin Test', role='admin')
        admin.set_password('Admin@123')
        db.session.add(admin)
        db.session.commit()
        print('Created admin', admin.user_id)
    else:
        print('Admin exists', admin.user_id)

# Give server a moment
time.sleep(1)

# Login as admin via HTTP
login = requests.post('http://127.0.0.1:5000/api/auth/login', json={'username': 'admin_test', 'password': 'Admin@123'})
print('admin login', login.status_code, login.text)
if login.status_code != 200:
    raise SystemExit('Admin login failed')
admin_token = login.json().get('access_token')
headers = {'Authorization': 'Bearer ' + admin_token}

# Register a student user via API
reg = requests.post('http://127.0.0.1:5000/api/auth/register', json={'username':'student_test','email':'student_test@example.com','password':'Student@123','full_name':'Student Test'})
print('register student', reg.status_code, reg.text)
if reg.status_code not in (200,201):
    # if already exists, try login
    pass

# Login as student
slogin = requests.post('http://127.0.0.1:5000/api/auth/login', json={'username':'student_test','password':'Student@123'})
print('student login', slogin.status_code, slogin.text)
if slogin.status_code != 200:
    raise SystemExit('Student login failed')
student_token = slogin.json().get('access_token')

# Send notification via admin endpoint
send = requests.post('http://127.0.0.1:5000/api/admin/notifications/send', headers=headers, json={'title':'Test Notice','message':'Hello students','target':'all'})
print('send notif', send.status_code, send.text)

# Student fetch notifications
getn = requests.get('http://127.0.0.1:5000/api/admin/notifications?unread=true', headers={'Authorization':'Bearer '+student_token})
print('student notifications', getn.status_code, getn.text)

# Inspect notifications table directly via backend app context for debugging
import app as backend_app
from models import Notification
with backend_app.app.app_context():
    notes = Notification.query.order_by(Notification.created_at.desc()).limit(20).all()
    print('DB total notifications:', Notification.query.count())
    for n in notes:
        print('DB:', n.notification_id, n.user_id, n.title, n.is_read, n.created_at)
