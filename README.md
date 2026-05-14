# KDE AI Predictor - Enterprise SaaS Dashboard

Hệ thống phân tích và dự đoán vị trí địa lý từ nội dung văn bản/Tweet ứng dụng AI (AI-powered Location Prediction).
Hệ thống kết hợp nhiều phương pháp nội suy tiên tiến (KDE, TF-IDF, Semantic FAISS) với giao diện người dùng Next.js hiện đại, mang lại trải nghiệm tra cứu tức thời.

## 🌟 Kiến trúc Hệ thống (Architecture)

Project được cấu trúc theo mô hình **Monorepo (Backend Django + Frontend Next.js)**:

- **Frontend (`frontend/`)**: 
  - Next.js 15 (App Router) + React 19.
  - TailwindCSS v4 + `shadcn/ui` + Framer Motion (Hiệu ứng UI mượt mà, Dark Theme).
  - Bản đồ tương tác với `react-simple-maps` và thông báo toàn cục `sonner`.
  - Tối ưu hiệu năng: Code Splitting, Lazy Loading cho Biểu đồ (Recharts).

- **Backend (`location_app/`)**: 
  - Django 4.2 RESTful API.
  - Xử lý pipeline dự đoán với 3 tầng thông minh:
    1. **KDE Model (Kernel Density Estimation)**: Mật độ thực thể địa lý (<10ms).
    2. **TF-IDF Fallback**: So sánh cosine similarity vector (<20ms).
    3. **FAISS Semantic**: Phân tích ngữ nghĩa sâu bằng `sentence-transformers` (<500ms).
  - Global Exception Handling (Middleware bắt lỗi và trả về chuẩn JSON).
  - RAM Caching (LocMemCache) giúp lưu kết quả đã tra cứu.

## 🚀 Tính năng nổi bật
- **Sub-second Prediction**: Pipeline dự đoán phản hồi cực nhanh (phần lớn <100ms).
- **Interactive Global Map**: Hiển thị chính xác toạ độ thành phố dự đoán trên bản đồ địa lý với hiệu ứng Radar.
- **Smart Debounce Search**: Tự động trích xuất từ khoá địa lý (Geographic Markers) khi người dùng đang nhập liệu.
- **Mobile Responsive Navigation**: Thanh điều hướng dạng Hamburger Menu hoạt động mượt mà trên di động.
- **Data Analytics Dashboard**: Thống kê mức độ tự tin (Confidence score) và so sánh xếp hạng các thành phố.

## 📦 Yêu cầu Môi trường

- Node.js 18.17+ (Cho Frontend)
- Python 3.10+ (Cho Backend)
- Redis (Optional, dùng nếu muốn chạy Asynchronous Logging qua Celery)

## 🛠 Hướng dẫn Cài đặt & Khởi chạy

### 1. Backend (Django)

Mở terminal và trỏ vào thư mục gốc của project:

```powershell
# Tạo và kích hoạt môi trường ảo
python -m venv venv
.\venv\Scripts\activate

# Cài đặt thư viện Python
pip install -r requirements.txt

# Migrate DB và chạy server
python manage.py migrate
python manage.py runserver
```
Backend sẽ chạy tại: `http://127.0.0.1:8000/`

**Tạo Dataset thành phố (Bắt buộc nếu chưa có)**
```powershell
# Chạy script để build file world_cities.json từ cities500
python manage.py build_world_city_dataset
```

### 2. Frontend (Next.js)

Mở một terminal mới và trỏ vào thư mục `frontend/`:

```powershell
cd frontend
npm install
npm run dev
```
Frontend sẽ chạy tại: `http://localhost:3000/` (Giao diện chính dành cho Người dùng)

## 📡 API Endpoints chính

- `POST /api/predict/`: Core pipeline dự đoán thành phố từ nội dung văn bản. Hỗ trợ caching tự động.
- `POST /api/predict/batch/`: Batch inference siêu tốc sử dụng FAISS cho nhiều đoạn văn bản cùng lúc.
- `GET /api/city-search/?q=...`: Autocomplete gợi ý tên thành phố.
- `POST /api/extract-keywords/`: Trích xuất thực thể địa lý thời gian thực từ chuỗi.

## 🤝 Contribution & Deployment

- Đảm bảo thiết lập đầy đủ file `.env` trước khi đưa lên môi trường Production.
- Tắt chế độ `DEBUG = True` trong Django Settings trước khi deploy.
- Sử dụng lệnh `npm run build` ở Frontend để tối ưu hoá bundle tĩnh của Next.js.
