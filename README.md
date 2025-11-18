# shopKME - D'Dream Clinic Coupon System

ระบบจัดการคูปองและแต้มสะสมสำหรับคลินิกความงาม

## 🚀 Features

- ระบบสมาชิกและแต้มสะสม
- จัดการคูปองส่วนลด
- คูปองสไลด์แบบ carousel
- QR Code สำหรับแลกของรางวัล
- ระบบพาร์ทเนอร์
- Dashboard สำหรับ staff

## 📋 Requirements

- Python 3.10+
- PostgreSQL 12+
- Django 5.2.7

## 🛠️ Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/shopKME.git
cd shopKME
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables

สร้างไฟล์ `.env` (copy จาก `.env.example`):

```bash
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac
```

แก้ไขไฟล์ `.env`:

```
DEBUG=True
SECRET_KEY=your-secret-key-here
PG_NAME=ddreamPJ
PG_USER=postgres
PG_PASSWORD=your_password
PG_HOST=localhost
PG_PORT=5432
ALLOWED_HOSTS=127.0.0.1,localhost
```

### 5. Setup PostgreSQL Database

```sql
CREATE DATABASE ddreamPJ;
```

### 6. Run Migrations

```bash
python manage.py migrate
```

### 7. Create Superuser

```bash
python manage.py createsuperuser
```

### 8. Collect Static Files

```bash
python manage.py collectstatic
```

### 9. Run Development Server

```bash
python manage.py runserver
```

เปิด browser: `http://127.0.0.1:8000`

## 🌐 Production Deployment (Render)

### 1. Push to GitHub

```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Create PostgreSQL on Render

- Dashboard → New → PostgreSQL
- Copy **Internal Database URL**

### 3. Create Web Service on Render

- Dashboard → New → Web Service
- Connect GitHub repository
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn shopKME.wsgi:application`

### 4. Environment Variables on Render

```
DEBUG=False
SECRET_KEY=<new-secret-key>
DATABASE_URL=<internal-database-url>
ALLOWED_HOSTS=yourapp.onrender.com
```

### 5. Deploy

Click **Create Web Service** → รอ ~5-10 นาที

## 📁 Project Structure

```
shopKME/
├── account/              # แอปหลัก
├── shopKME/             # การตั้งค่า
├── templates/           # HTML templates
├── static/              # CSS, JS, Images
├── media/               # User uploads (ไม่อัพ GitHub)
├── staticfiles/         # Collected static (ไม่อัพ GitHub)
├── manage.py
├── requirements.txt
├── build.sh             # Build script สำหรับ Render
├── .env.example         # ตัวอย่าง environment variables
└── .gitignore
```

## 🔒 Security Notes

- ไฟล์ `.env` ถูกเพิ่มใน `.gitignore` แล้ว
- ห้ามอัพ `db.sqlite3` และ `media/` ขึ้น GitHub
- เปลี่ยน `SECRET_KEY` ใหม่สำหรับ production
- ตั้งค่า `DEBUG=False` ใน production

## 🧪 Testing

```bash
python manage.py test
```

## 📝 License

Private Project - All Rights Reserved

## 👥 Contributors

- Your Name

## 📞 Contact

- Email: your-email@example.com
- Website: https://yourapp.onrender.com
