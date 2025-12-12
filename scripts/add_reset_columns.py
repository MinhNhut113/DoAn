from backend import app as backend_app
from backend.models import db
from sqlalchemy import text

with backend_app.app_context():
    print('Executing ALTER TABLE to add reset_token columns if missing...')
    conn = db.engine.connect()
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN reset_token VARCHAR(10) NULL"))
        print('Added reset_token column')
    except Exception as e:
        print('reset_token add skipped or failed:', e)
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN reset_token_expiry DATETIME NULL"))
        print('Added reset_token_expiry column')
    except Exception as e:
        print('reset_token_expiry add skipped or failed:', e)
    conn.close()
    print('Done')
