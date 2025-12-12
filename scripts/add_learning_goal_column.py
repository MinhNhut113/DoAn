import os, sys
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BACKEND_DIR = os.path.join(BASE, 'backend')
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

import app as backend_app
from sqlalchemy import text

with backend_app.app.app_context():
    print('Executing ALTER TABLE to add learning_goal column if missing...')
    try:
        backend_app.db.session.execute(text("ALTER TABLE users ADD learning_goal TEXT NULL"))
        backend_app.db.session.commit()
        print('✓ Added learning_goal column to users table')
    except Exception as e:
        backend_app.db.session.rollback()
        if 'already exists' in str(e).lower() or 'invalid column name' not in str(e).lower():
            print('✓ learning_goal column already exists')
        else:
            print(f'Error: {e}')
    print('Done')
