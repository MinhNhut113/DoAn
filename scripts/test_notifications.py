import os
import requests

os.environ['PYTHONPATH'] = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

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

# login
try:
    r = requests.post('http://127.0.0.1:5000/api/auth/login', json={'username':'admin_test','password':'Admin@123'})
    print('login status', r.status_code)
    print(r.text)
    token = r.json().get('access_token')
    h = {'Authorization': 'Bearer '+token}
    r2 = requests.post('http://127.0.0.1:5000/api/admin/notifications/send', headers=h, json={'title':'Test','message':'Hello all','target':'all'})
    print('send notif', r2.status_code, r2.text)
except Exception as e:
    print('HTTP error', e)
