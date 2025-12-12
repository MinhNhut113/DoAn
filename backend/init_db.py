from flask import Flask
from models import db, User
from config import Config
from werkzeug.security import generate_password_hash
import sys
import os
import secrets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_database():
    """Initializes the database, creates tables, and adds the admin user."""
    # 1. Tạo một instance Flask hoàn toàn mới, chỉ dùng cho việc này.
    app = Flask(__name__)
    
    # 2. Tải cấu hình (quan trọng để có chuỗi kết nối DB).
    app.config.from_object(Config)
    
    # 3. Gắn SQLAlchemy vào instance tạm thời này.
    db.init_app(app)

    # 4. Thực hiện các thao tác DB trong "application context".
    with app.app_context():
        logger.info("Checking and creating tables if needed...")
        db.create_all()
        logger.info("Tables created (if not already present).")

        # Thêm admin user nếu chưa có
        if not db.session.execute(db.select(User).where(User.username == 'admin')).scalar_one_or_none():
            logger.info("Creating admin account...")
            # Prefer ADMIN_PASSWORD from environment. If missing, generate a strong temporary password.
            admin_password = os.getenv('ADMIN_PASSWORD')
            generated = False
            if not admin_password:
                admin_password = secrets.token_urlsafe(16)
                generated = True
                logger.warning("[WARNING] ADMIN_PASSWORD not set. A temporary admin password was generated below. Change it immediately.")
                logger.warning(admin_password)

            admin_user = User(
                username='admin',
                email='admin@learning-platform.local',
                full_name='Administrator',
                password_hash=generate_password_hash(admin_password),
                role='admin',
                is_active=True
            )
            db.session.add(admin_user)
            db.session.commit()
            if not generated:
                logger.info("Admin account created. (Password provided via ADMIN_PASSWORD env var)")
            else:
                logger.info("Admin account created with temporary password (must change).")

if __name__ == '__main__':
    try:
        logger.info("--- Starting database initialization process ---")
        initialize_database()
        logger.info("--- Database initialization process completed ---")
    except Exception as e:
        logger.error(f"[❌] Critical error during database initialization: {e}", exc_info=True)
        logger.error("[ℹ]  Please check the connection string in .env file and ensure SQL Server is running.")
        sys.exit(1)