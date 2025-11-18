Xizmatlar Telegram Bot + Admin Panel
====================================

1) Lokal ishga tushirish
------------------------
- Python o'rnating (3.10+ tavsiya).
- Virtual environment yarating (ixtiyoriy).
- Kutubxonalarni o'rnating:

    pip install -r requirements.txt

- Muhit o'zgaruvchilarini (environment variables) sozlang:

    TELEGRAM_BOT_TOKEN=...
    ADMIN_USERNAME=admin
    ADMIN_PASSWORD=admin123
    TELEGRAM_ADMIN_CHAT_ID=  (ixtiyoriy)

- Bazani avtomatik yaratadi.
- Serverni ishga tushiring:

    python app.py

- Brauzerda oching: http://localhost:5000/admin/login

2) Telegram webhook o'rnatish
-----------------------------
Render'ga deploy qilgandan keyin, servis URL manzilingiz masalan:

    https://sening-servising.onrender.com

Telegramga webhook o'rnating (browser yoki Postman orqali):

    https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook?url=https://sening-servising.onrender.com/telegram/webhook

3) Render'da deploy qilish
--------------------------
- Git repo oching va ushbu fayllarni push qiling.
- Render'da "New Web Service" tanlang.
- Python versiyasi 3.10+ bo'lsin.
- Start command:  gunicorn app:app
- Environment bo'limida quyidagilarni kiriting:
    TELEGRAM_BOT_TOKEN
    ADMIN_USERNAME
    ADMIN_PASSWORD
    TELEGRAM_ADMIN_CHAT_ID (ixtiyoriy)
    SECRET_KEY (ixtiyoriy, xavfsizlik uchun)

4) Foydalanish
--------------
- Admin paneldan kategoriyalar va xizmatlarni qo'shing.
- Telegram botga /start yozing.
- Foydalanuvchi:
    - kategoriya tanlaydi
    - xizmat tanlaydi
    - telefon, lokatsiya, izohni yuboradi
    - to'lov turini tanlaydi
- Admin paneldan buyurtma statusini "DONE" yoki "PAYMENT_PENDING" qilganda,
  bot foydalanuvchiga avtomatik: "Ish bajarildi, to'lov kutilmoqda." degan xabar yuboradi.
