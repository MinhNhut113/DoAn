import time

from backend import app as backend_app
from backend.models import User, db

EMAIL = 'student_test@example.com'
NEW_PW = 'NewStudent@123'

client = backend_app.test_client()

# call forgot-password via test client
resp = client.post('/api/auth/forgot-password', json={'email': EMAIL})
print('forgot-password', resp.status_code, resp.get_data(as_text=True))

# give server a moment then read token from DB
with backend_app.app_context():
    u = User.query.filter_by(email=EMAIL).first()
    if not u:
        print('User not found in DB')
        raise SystemExit(1)
    token = u.reset_token
    print('token from DB:', token)

if not token:
    print('No token present; abort')
    raise SystemExit(1)

# call reset-password
r2 = client.post('/api/auth/reset-password', json={'email': EMAIL, 'token': token, 'new_password': NEW_PW})
print('reset-password', r2.status_code, r2.get_data(as_text=True))

# try login with new password
r3 = client.post('/api/auth/login', json={'username': 'student_test', 'password': NEW_PW})
print('login after reset', r3.status_code, r3.get_data(as_text=True))
