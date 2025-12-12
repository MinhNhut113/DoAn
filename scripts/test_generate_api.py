from backend import app as backend_app

client = backend_app.test_client()
# ensure student has known password
from backend.models import User, db
with backend_app.app_context():
    u = User.query.filter_by(username='student_test').first()
    if u:
        u.set_password('Student@123')
        db.session.commit()

# login as student
login = client.post('/api/auth/login', json={'username':'student_test','password':'Student@123'})
print('login', login.status_code, login.get_data(as_text=True))
if login.status_code!=200:
    raise SystemExit(1)
token = login.get_json()['access_token']
headers = {'Authorization': 'Bearer '+token}
# call generate (compat endpoint)
resp = client.post('/api/ai/generate', headers=headers, json={'lesson_content':'Short text about testing', 'num_questions':2})
print('generate', resp.status_code, resp.get_data(as_text=True))
