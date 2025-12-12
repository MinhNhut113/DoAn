import os, sys, time
import requests

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BACKEND_DIR = os.path.join(BASE, 'backend')
# ensure imports work
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

import app as backend_app
from models import User

EMAIL = 'student_test@example.com'
NEW_PW = 'NewStudent@123'

# call forgot-password via HTTP
resp = requests.post('http://127.0.0.1:5000/api/auth/forgot-password', json={'email': EMAIL})
print('forgot-password', resp.status_code, resp.text)

# give server a moment then read token from DB
with backend_app.app.app_context():
    u = User.query.filter_by(email=EMAIL).first()
    if not u:
        print('User not found in DB')
        sys.exit(1)
    token = u.reset_token
    print('token from DB:', token)

if not token:
    print('No token present; abort')
    sys.exit(1)

# call reset-password
r2 = requests.post('http://127.0.0.1:5000/api/auth/reset-password', json={'email': EMAIL, 'token': token, 'new_password': NEW_PW})
print('reset-password', r2.status_code, r2.text)

# try login with new password
r3 = requests.post('http://127.0.0.1:5000/api/auth/login', json={'username': 'student_test', 'password': NEW_PW})
print('login after reset', r3.status_code, r3.text)
