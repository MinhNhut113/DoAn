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
