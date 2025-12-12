import os, sys
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BACKEND_DIR = os.path.join(BASE, 'backend')
# ensure backend package importable
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)
import app as backend_app
from models import Notification, User
with backend_app.app.app_context():
    notes = Notification.query.order_by(Notification.created_at.desc()).limit(50).all()
    print('total notes:', Notification.query.count())
    for n in notes:
        print(n.notification_id, n.user_id, n.title, n.is_read, n.created_at)
