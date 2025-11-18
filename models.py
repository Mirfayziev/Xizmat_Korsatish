from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import enum

db = SQLAlchemy()

class OrderStatus(enum.Enum):
    NEW = "new"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    PAYMENT_PENDING = "payment_pending"
    CLOSED = "closed"

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    icon = db.Column(db.String(10), nullable=True)  # emoji

    services = db.relationship("Service", backref="category", lazy=True)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=True)
    description = db.Column(db.Text, nullable=True)

    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, nullable=False)   # telegram user id
    chat_id = db.Column(db.BigInteger, nullable=False)   # telegram chat id

    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey("service.id"), nullable=True)

    phone = db.Column(db.String(50), nullable=True)
    location_lat = db.Column(db.Float, nullable=True)
    location_lng = db.Column(db.Float, nullable=True)
    address_text = db.Column(db.String(255), nullable=True)
    comment = db.Column(db.Text, nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)

    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.NEW, nullable=False)
    step = db.Column(db.String(50), default="category", nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = db.relationship("Category", lazy=True)
    service = db.relationship("Service", lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    from_admin = db.Column(db.Boolean, default=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order = db.relationship("Order", backref="messages")
