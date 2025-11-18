# Xizmat_Korsatish
# 🏛️ Xizmat AI Imperiya — Full AI + 2 Bot + Admin Panel

Bu loyiha — xizmat ko‘rsatish platformasi uchun to‘liq **AI bilan ishlaydigan ekotizim**:

- Telegram **Foydalanuvchi Bot**
- Telegram **Usta Bot**
- **Admin Panel** (web)
- AI (Whisper + GPT-4o-mini) — **audio tahlil**
- Buyurtmalar boshqaruvi
- Servislar, Kategoriyalar, Statuslar
- Chat (Admin ↔ Mijoz)
- Analytics Dashboard
- Profit / Daromad / Xarajat
- Usta KPI tahlili

---

# 🚀 Texnologiyalar

- **Flask 3** — Backend
- **SQLAlchemy** — Database ORM
- **OpenAI (Whisper + GPT-4o-mini)** — Audio tahlil
- **Telegram Bot API**
- **Bootstrap 5** — Admin panel dizayni
- **Chart.js** — Analitika grafiklari
- **Gunicorn** — Render serveri

---

# 📁 Loyha tuzilmasi
xizmat_ai_imperiya/
│
├── app.py
├── ai_service.py
├── config.py
├── models.py
├── requirements.txt
├── README.md
│
├── templates/
│ ├── base.html
│ ├── login.html
│ ├── dashboard.html
│ ├── categories.html
│ ├── services.html
│ ├── orders.html
│ ├── order_detail.html
│ ├── analytics.html
│ ├── ai_analysis.html
│ ├── reviews.html
│
└── static/
├── css/style.css
└── js/charts.js

---

# 🔧 O‘rnatish (LOCAL)

Terminalda:


Admin panel:
👉 http://localhost:5000/admin/login

Default login:
- Login: `admin`
- Parol: `admin123`

---

# 🔑 ENV (TOKENLAR)

Render / .env faylga:

SECRET_KEY=supersecretkey

TELEGRAM_BOT_TOKEN=xxxxx
TELEGRAM_MASTER_BOT_TOKEN=xxxxx
TELEGRAM_ADMIN_CHAT_ID=xxxxx

OPENAI_API_KEY=sk-xxxxxx

MASTER_SHARE_PERCENT=70
DATABASE_URL=sqlite:///imperiya.db
SECRET_KEY=supersecretkey

TELEGRAM_BOT_TOKEN=xxxxx
TELEGRAM_MASTER_BOT_TOKEN=xxxxx
TELEGRAM_ADMIN_CHAT_ID=xxxxx

OPENAI_API_KEY=sk-xxxxxx

MASTER_SHARE_PERCENT=70
DATABASE_URL=sqlite:///imperiya.db
https://api.telegram.org/bot
<token>/setWebhook?url=https://<domain>/telegram/user_webhook


### 2) Usta bot:


https://api.telegram.org/bot
<token>/setWebhook?url=https://<domain>/telegram/master_webhook


---

# ☁️ Render’da Deploy qilish

1. GitHub repo oching
2. Loyhani yuklang
3. Render.com → "New Web Service"
4. Build Command:


pip install -r requirements.txt

5. Start Command:


gunicorn app:app


6. Environment Variables’ga tokenlarni qo‘ying
7. Deploy

---

# 📦 AI Audio Tahlil (Whisper + GPT-4o-mini)

- Admin panelda “Buyurtma” sahifasida audio fayl yuklanadi
- Whisper audio → matn qiladi
- GPT-4o-mini:
  - sentiment
  - sifat
  - qiyinchilik (ustaga)
  - materiallar
  - extra cost
  - recommended fix
  - AI summary
- Natija AIReview jadvaliga tushadi
- Admin panelda ko‘rinadi

---

# 🧰 Funksiyalar

## 👤 Foydalanuvchi Bot
- Kategoriya tanlash
- Xizmat tanlash
- Telefon / lokatsiya yuborish
- To‘lov turi tanlash
- Admin bilan chat
- Buyurtma holatini ko‘rish

## 🧑‍🔧 Usta Bot
- Buyurtmalar ro‘yxati
- Buyurtma tafsiloti
- Ishni boshlash
- Ishni tugatish
- Buyurtma statusi o‘zgaradi

## 🧠 AI
- Mijoz ovozini tahlil qilish
- Usta hisobotini tahlil qilish
- AI rating + sentiment
- Materiallar + extra cost
- Full transcript
- KPI dashboard

## 🖥 Admin Panel
- Category CRUD
- Service CRUD
- Buyurtmalar boshqaruvi
- Chat (admin ↔ mijoz)
- Analytics dashboard
- AI natijalari sahifasi
- Audio upload tahlil

---

# 🎉 Tayyor!

Bu loyiha hoziroq ishga tushishga **100% tayyor**.

- Telegram botlar
- AI tahlil
- Admin panel
- Analitika

Hammasi bitta backendda.



🚀 Xizmat AI Imperiya — Ishga tushirishga tayyor!


---

Agar yordam kerak bo‘lsa — aytishingiz kifoya.
