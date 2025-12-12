import os

from backend import app
from backend.models import db, User

with app.app_context():
    u = User.query.filter_by(username='admin_test').first()
    if not u:
        u = User(username='admin_test', email='admin_test@example.com', full_name='Admin Test', role='admin')
        u.set_password('Admin@123')
        db.session.add(u); db.session.commit()
        print('created admin', u.user_id)
    else:
        print('admin exists', u.user_id)

# Use test client for requests
client = app.test_client()
login = client.post('/api/auth/login', json={'username':'admin_test','password':'Admin@123'})
print('login status', login.status_code)
print(login.get_data(as_text=True))
if login.status_code == 200:
    token = login.get_json().get('access_token')
    h = {'Authorization': 'Bearer '+token}
    r2 = client.post('/api/admin/notifications/send', headers=h, json={'title':'Test','message':'Hello all','target':'all'})
    print('send notif', r2.status_code, r2.get_data(as_text=True))
else:
    print('login failed')
