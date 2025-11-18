import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Admin login
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

    # 1-bot (foydalanuvchi bot) tokeni
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

    # 2-bot (usta bot) tokeni – hozircha placeholder, keyin ishlatamiz
    TELEGRAM_MASTER_BOT_TOKEN = os.environ.get("TELEGRAM_MASTER_BOT_TOKEN", "")

    # Adminga bot orqali xabar yuborish uchun chat_id (ixtiyoriy)
    TELEGRAM_ADMIN_CHAT_ID = os.environ.get("TELEGRAM_ADMIN_CHAT_ID", "")

    # Usta ulushi (foizda) – xarajat hisoblash uchun
    # Masalan: 70 degani 70% ustaniki, 30% seniki profit
    MASTER_SHARE_PERCENT = float(os.environ.get("MASTER_SHARE_PERCENT", "30"))
