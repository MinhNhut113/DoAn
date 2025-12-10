from flask import Flask
from models import db, User
from config import Config
from werkzeug.security import generate_password_hash
import sys
import os
import secrets

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
        print("Kiểm tra và tạo bảng nếu cần...")
        db.create_all()
        print("Bảng đã được tạo (nếu chưa tồn tại).")

        # Thêm admin user nếu chưa có
        if not db.session.execute(db.select(User).where(User.username == 'admin')).scalar_one_or_none():
            print("Tạo tài khoản admin...")
            # Prefer ADMIN_PASSWORD from environment. If missing, generate a strong temporary password.
            admin_password = os.getenv('ADMIN_PASSWORD')
            generated = False
            if not admin_password:
                admin_password = secrets.token_urlsafe(16)
                generated = True
                print("[WARNING] ADMIN_PASSWORD not set. A temporary admin password was generated below. Change it immediately.")
                print(admin_password)

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
                print("Tài khoản admin đã được tạo. (Password provided via ADMIN_PASSWORD env var)")
            else:
                print("Tài khoản admin đã được tạo với mật khẩu tạm thời (bắt buộc đổi).")

if __name__ == '__main__':
    try:
        print("--- Bắt đầu quá trình khởi tạo Database ---")
        initialize_database()
        print("--- Quá trình khởi tạo Database hoàn tất ---")
    except Exception as e:
        print(f"[❌] Lỗi nghiêm trọng khi khởi tạo database: {e}", file=sys.stderr)
        print("[ℹ]  Vui lòng kiểm tra chuỗi kết nối trong file .env và đảm bảo SQL Server đang chạy.", file=sys.stderr)
        sys.exit(1)