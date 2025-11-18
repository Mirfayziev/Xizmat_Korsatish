import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-key")

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///imperiya.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Admin login
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

    # Telegram bots
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_MASTER_BOT_TOKEN = os.environ.get("TELEGRAM_MASTER_BOT_TOKEN", "")

    # Admin chat ID
    TELEGRAM_ADMIN_CHAT_ID = os.environ.get("TELEGRAM_ADMIN_CHAT_ID", "")

    # AI – Whisper + GPT-4o-mini
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

    # Usta ulushi (%)
    MASTER_SHARE_PERCENT = float(os.environ.get("MASTER_SHARE_PERCENT", 70))

    # Audio fayllarni yuklash papkasi
    UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
