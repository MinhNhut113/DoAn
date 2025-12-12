from backend import app as backend_app
from backend.models import Notification, User

with backend_app.app_context():
    notes = Notification.query.order_by(Notification.created_at.desc()).limit(50).all()
    print('total notes:', Notification.query.count())
    for n in notes:
        print(n.notification_id, n.user_id, n.title, n.is_read, n.created_at)
