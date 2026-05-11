# KDE

Ứng dụng Django dự đoán thành phố khả nghi nhất từ nội dung bài đăng X/Twitter bằng cách:

- đọc nội dung bài đăng từ URL X/Twitter
- rút trích term địa lý từ tweet
- tính điểm KDE trên tập dữ liệu thành phố toàn cầu
- hiển thị kết quả trên bản đồ thế giới

Project này hiện dùng dataset `GeoNames cities500` đã được build thành file JSON để phục vụ suy luận nhanh trong app.

## Công nghệ

- Python
- Django 4.2.7
- NumPy
- D3.js + TopoJSON
- SQLite

## Tính năng chính

- nhập trực tiếp nội dung tweet hoặc dán URL bài đăng X/Twitter
- autocomplete thành phố để áp dụng `city bias`
- dự đoán vị trí từ tập dữ liệu hơn 200k thành phố toàn cầu
- hiển thị toàn bộ cloud điểm thành phố trên bản đồ
- trả về top city scores để so sánh kết quả

## Cấu trúc chính

- `tweet_locator/`: Django project settings và URL root
- `location_app/`: app chính cho prediction, views, utils, tests
- `location_app/data/world_cities.json`: dataset thành phố toàn cầu đã build
- `location_app/management/commands/build_world_city_dataset.py`: command build dataset
- `static/location_app/`: CSS và JavaScript cho giao diện

## Yêu cầu môi trường

- Python 3.10+ khuyến nghị
- Windows PowerShell hoặc shell tương đương

## Cài đặt

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Mở trình duyệt tại:

```text
http://127.0.0.1:8000/
```

## Chạy test

```powershell
.\venv\Scripts\python.exe manage.py test location_app
```

## Dataset thành phố toàn cầu

App cần file:

```text
location_app/data/world_cities.json
```

Nếu file này chưa có, bạn có thể build lại từ raw `GeoNames cities500`:

1. Tải `cities500.zip` từ GeoNames
2. Giải nén `cities500.txt` vào:

```text
location_app/data/cities500_raw/cities500.txt
```

3. Chạy command:

```powershell
.\venv\Scripts\python.exe manage.py build_world_city_dataset
```

Lưu ý:

- `world_cities.json` nên được commit nếu bạn muốn clone repo là chạy ngay
- `cities500_raw/cities500.txt` là raw source lớn, không nên commit

## API chính

- `POST /api/predict/`: dự đoán thành phố từ tweet
- `GET /api/city-search/?q=...`: gợi ý tên thành phố
- `GET /api/world-cities/`: trả dữ liệu điểm thành phố cho bản đồ
- `POST /api/resolve-tweet/`: đọc nội dung tweet từ URL X/Twitter

## Push lên GitHub

Repo đích:

```text
https://github.com/nekooo2404/KDE
```

Các lệnh cơ bản:

```powershell
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/nekooo2404/KDE.git
git push -u origin main
```

Nếu repo local đã có remote `origin`, chỉ cần cập nhật URL:

```powershell
git remote set-url origin https://github.com/nekooo2404/KDE.git
git push -u origin main
```
