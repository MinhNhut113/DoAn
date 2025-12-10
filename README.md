# Nền Tảng Học Trực Tuyến với AI

## Mô Tả
Hệ thống học trực tuyến sử dụng Trí tuệ nhân tạo để cá nhân hóa nội dung học tập và theo dõi tiến độ học tập của sinh viên.

## Công Nghệ Sử Dụng
- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python (Flask)
- **Database**: SQL Server
- **AI**: TensorFlow/PyTorch, API calls

## Cài Đặt

### Backend
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Database
1. Tạo database trong SQL Server
2. Chạy script trong thư mục `database/schema.sql`

### Frontend
Mở `frontend/index.html` trong trình duyệt hoặc sử dụng local server.

## Cấu Trúc Dự Án
```
├── backend/          # Python Flask API
├── frontend/         # HTML/CSS/JavaScript
├── database/         # SQL Server scripts
└── ai_models/        # AI models và utilities
```

## Chức Năng

### Sinh Viên
- Đăng nhập, đăng ký, quản lý hồ sơ
- Xem và tham gia khóa học
- Làm bài kiểm tra trắc nghiệm
- Theo dõi tiến độ học tập
- Nhận gợi ý cá nhân hóa từ AI

### Quản Trị Viên
- Quản lý người dùng
- Quản lý khóa học và bài giảng
- Quản lý ngân hàng câu hỏi
- Xem thống kê và báo cáo

## Cấu Hình Kết Nối Cơ Sở Dữ Liệu
```ini
USE_WINDOWS_AUTH=False
SQL_USERNAME=sa
SQL_PASSWORD=YourStrongPassword
```

