from backend import app as backend_app
from backend.models import db
from sqlalchemy import text

with backend_app.app_context():
    print('Executing ALTER TABLE to add learning_goal column if missing...')
    conn = db.engine.connect()
    try:
        conn.execute(text("ALTER TABLE users ADD learning_goal TEXT NULL"))
        print('✓ Added learning_goal column to users table')
    except Exception as e:
        if 'already exists' in str(e).lower() or 'duplicate column name' in str(e).lower():
            print('✓ learning_goal column already exists')
        else:
            print(f'Error: {e}')
    finally:
        conn.close()
    print('Done')
