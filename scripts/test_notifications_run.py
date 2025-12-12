import time

# Use package imports and the backend app directly
from backend import app as backend_app
from backend.models import db, User, Notification

with backend_app.app_context():
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
    
    # Use Flask test client to perform HTTP requests without external server
    client = backend_app.test_client()
    
    # Login as admin via test client
    login = client.post('/api/auth/login', json={'username': 'admin_test', 'password': 'Admin@123'})
    print('admin login', login.status_code, login.get_data(as_text=True))
    if login.status_code != 200:
        raise SystemExit('Admin login failed')
    admin_token = login.get_json().get('access_token')
    headers = {'Authorization': 'Bearer ' + admin_token}
    
    # Register a student user via API (if already exists the endpoint may return 400)
    reg = client.post('/api/auth/register', json={'username':'student_test','email':'student_test@example.com','password':'Student@123','full_name':'Student Test'})
    print('register student', reg.status_code, reg.get_data(as_text=True))
    
    # If registration failed because user exists, ensure password is set to known value
    if reg.status_code not in (200, 201):
        student = User.query.filter_by(username='student_test').first()
        if student:
            student.set_password('Student@123')
            db.session.commit()

    # Login as student
    slogin = client.post('/api/auth/login', json={'username':'student_test','password':'Student@123'})
    print('student login', slogin.status_code, slogin.get_data(as_text=True))
    if slogin.status_code != 200:
        raise SystemExit('Student login failed')
    student_token = slogin.get_json().get('access_token')
    
    # Send notification via admin endpoint
    send = client.post('/api/admin/notifications/send', headers=headers, json={'title':'Test Notice','message':'Hello students','target':'all'})
    print('send notif', send.status_code, send.get_data(as_text=True))
    
    # Student fetch notifications
    getn = client.get('/api/notifications?unread=true', headers={'Authorization':'Bearer '+student_token})
    print('student notifications', getn.status_code, getn.get_data(as_text=True))



# Inspect notifications table directly via backend app context for debugging
with backend_app.app_context():
    notes = Notification.query.order_by(Notification.created_at.desc()).limit(20).all()
    print('DB total notifications:', Notification.query.count())
    for n in notes:
        print('DB:', n.notification_id, n.user_id, n.title, n.is_read, n.created_at)
