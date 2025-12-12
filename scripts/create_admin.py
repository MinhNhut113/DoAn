import sys, os
# Ensure workspace root is on sys.path so package imports resolve
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, workspace_root)
from backend.models import db, User
from backend import app

with app.app_context():
    u = User.query.filter_by(username='admin_test').first()
    if not u:
        u = User(username='admin_test', email='admin_test@example.com', full_name='Admin Test', role='admin')
        u.set_password('Admin@123')
        db.session.add(u)
        db.session.commit()
        print('created', u.user_id)
    else:
        print('exists', u.user_id)
