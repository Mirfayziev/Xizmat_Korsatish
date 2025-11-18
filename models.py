from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum

db = SQLAlchemy()

# ---------------- ORDER STATUS ENUM ----------------

class OrderStatus(Enum):
    NEW = "NEW"                    # xolat yaratildi
    PENDING = "PENDING"            # telefon / lokatsiya olinyapti
    IN_PROGRESS = "IN_PROGRESS"    # usta ish boshladi
    DONE = "DONE"                  # usta ish tugatdi
    PAYMENT_PENDING = "PAYMENT_PENDING"  # to'lov kutilmoqda
    CLOSED = "CLOSED"              # yopildi


# ---------------- CATEGORY MODEL ----------------

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    icon = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------- SERVICE MODEL ----------------

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship("Category", backref="services")


# ---------------- ORDER MODEL ----------------

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.String(50))    # Telegram User ID
    chat_id = db.Column(db.String(50))    # Telegram chat ID

    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    service_id = db.Column(db.Integer, db.ForeignKey("service.id"))

    phone = db.Column(db.String(50))
    address_text = db.Column(db.Text)

    location_lat = db.Column(db.Float)
    location_lng = db.Column(db.Float)

    comment = db.Column(db.Text)
    payment_method = db.Column(db.String(50))

    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.NEW)
    step = db.Column(db.String(30), default="category")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # relations
    category = db.relationship("Category")
    service = db.relationship("Service")

    ai_reviews = db.relationship("AIReview", backref="order", lazy=True)
    messages = db.relationship("Message", backref="order", lazy=True)


# ---------------- CHAT MESSAGES ----------------

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    
    from_admin = db.Column(db.Boolean, default=False)
    text = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------- AI REVIEW MODEL ----------------
"""
AI 2 turdagi audio tahlillarni saqlaydi:
1) Foydalanuvchi ovozli review
2) Usta ovozli hisobot

AI natija:
- sentiment
- quality score
- difficulty
- materials
- extra cost
- recommended actions
- cleaned text (matn ko'rinishida)
"""
class AIReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)

    # audio haqida
    audio_file = db.Column(db.String(300))
    audio_type = db.Column(db.String(20))  # "client" yoki "master"

    # AI natijalari
    transcript = db.Column(db.Text)  # whisper matni
    ai_summary = db.Column(db.Text)  # GPT generatsiya
    sentiment_score = db.Column(db.Float)  # 0–100
    quality_score = db.Column(db.Float)  # 0–100
    difficulty = db.Column(db.Integer)  # 1–10
    materials_used = db.Column(db.Text)
    extra_cost = db.Column(db.Float)
    recommended = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
