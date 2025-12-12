import os, sys
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BACKEND_DIR = os.path.join(BASE, 'backend')
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

import app as backend_app
from sqlalchemy import text

with backend_app.app.app_context():
    print('Executing ALTER TABLE to add reset_token columns if missing...')
    try:
        backend_app.db.session.execute(text("ALTER TABLE users ADD reset_token VARCHAR(10) NULL"))
        backend_app.db.session.commit()
        print('Added reset_token column')
    except Exception as e:
        backend_app.db.session.rollback()
        print('reset_token add skipped or failed:', e)
    try:
        backend_app.db.session.execute(text("ALTER TABLE users ADD reset_token_expiry DATETIME NULL"))
        backend_app.db.session.commit()
        print('Added reset_token_expiry column')
    except Exception as e:
        backend_app.db.session.rollback()
        print('reset_token_expiry add skipped or failed:', e)
    print('Done')
