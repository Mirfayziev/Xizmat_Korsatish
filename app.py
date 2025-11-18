import os
import requests
from flask import (
    Flask, request, jsonify, render_template, redirect,
    url_for, session, flash
)
from werkzeug.utils import secure_filename

from config import Config
from models import db, Category, Service, Order, OrderStatus, Message, AIReview
from ai_service import analyze_audio_file


# ------------------------------------------------------------
#  APP INITIALIZATION
# ------------------------------------------------------------

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()


# ------------------------------------------------------------
#  HELPERS
# ------------------------------------------------------------

def send_user_message(chat_id, text, reply_markup=None):
    token = app.config["TELEGRAM_BOT_TOKEN"]
    if not token: return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}

    if reply_markup:
        payload["reply_markup"] = reply_markup

    requests.post(url, json=payload)


def send_master_message(chat_id, text, reply_markup=None):
    token = app.config["TELEGRAM_MASTER_BOT_TOKEN"]
    if not token: return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}

    if reply_markup:
        payload["reply_markup"] = reply_markup

    requests.post(url, json=payload)


def admin_notify(text):
    admin_id = app.config["TELEGRAM_ADMIN_CHAT_ID"]
    if admin_id:
        send_user_message(admin_id, f"📢 Admin xabari:\n{text}")


# ------------------------------------------------------------
# AUTH (ADMIN PANEL)
# ------------------------------------------------------------

def login_required(fn):
    def wrap(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    wrap.__name__ = fn.__name__
    return wrap


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        name = request.form["username"]
        pwd = request.form["password"]

        if name == Config.ADMIN_USERNAME and pwd == Config.ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect("/admin/dashboard")

        flash("❌ Login yoki parol noto‘g‘ri!", "danger")

    return render_template("login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


# ------------------------------------------------------------
# ADMIN PANEL
# ------------------------------------------------------------

@app.route("/")
def home():
    return redirect("/admin/dashboard")


@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    orders = Order.query.order_by(Order.created_at.desc()).limit(20).all()
    return render_template("dashboard.html", orders=orders, OrderStatus=OrderStatus)


@app.route("/admin/categories")
@login_required
def admin_categories():
    categories = Category.query.all()
    return render_template("categories.html", categories=categories)


@app.route("/admin/categories/add", methods=["POST"])
@login_required
def admin_add_category():
    name = request.form["name"]
    icon = request.form.get("icon")

    db.session.add(Category(name=name, icon=icon))
    db.session.commit()

    return redirect("/admin/categories")


@app.route("/admin/categories/<int:id>/delete", methods=["POST"])
@login_required
def admin_delete_category(id):
    cat = Category.query.get(id)
    db.session.delete(cat)
    db.session.commit()
    return redirect("/admin/categories")


@app.route("/admin/services")
@login_required
def admin_services():
    services = Service.query.all()
    categories = Category.query.all()
    return render_template("services.html", services=services, categories=categories)


@app.route("/admin/services/add", methods=["POST"])
@login_required
def admin_add_service():
    srv = Service(
        name=request.form["name"],
        price=float(request.form.get("price") or 0),
        description=request.form.get("description"),
        category_id=int(request.form["category_id"])
    )
    db.session.add(srv)
    db.session.commit()
    return redirect("/admin/services")


@app.route("/admin/services/<int:id>/delete", methods=["POST"])
@login_required
def admin_delete_service(id):
    srv = Service.query.get(id)
    db.session.delete(srv)
    db.session.commit()
    return redirect("/admin/services")


@app.route("/admin/orders")
@login_required
def admin_orders():
    status = request.args.get("status")
    query = Order.query

    if status:
        query = query.filter_by(status=OrderStatus(status))

    orders = query.order_by(Order.created_at.desc()).all()
    return render_template("orders.html", orders=orders, OrderStatus=OrderStatus)


@app.route("/admin/orders/<int:id>", methods=["GET", "POST"])
@login_required
def admin_order_detail(id):
    order = Order.query.get(id)

    if request.method == "POST":
        action = request.form["action"]

        # ADMIN → FOYDALANUVCHI XABAR
        if action == "send_message":
            msg = Message(
                order_id=order.id,
                from_admin=True,
                text=request.form["text"]
            )
            db.session.add(msg)
            db.session.commit()

            send_user_message(order.chat_id, f"👨‍💼 Admin:\n{msg.text}")
            return redirect(f"/admin/orders/{order.id}")

        # STATUS O‘ZGARTIRISH
        if action == "status":
            new_status = request.form["status"]
            order.status = OrderStatus(new_status)
            db.session.commit()

            admin_notify(f"Buyurtma #{order.id} yangi status: {new_status}")

            return redirect(f"/admin/orders/{order.id}")

    messages = Message.query.filter_by(order_id=id).order_by(Message.created_at).all()

    ai_data = AIReview.query.filter_by(order_id=id).all()

    return render_template(
        "order_detail.html",
        order=order,
        messages=messages,
        ai_data=ai_data,
        OrderStatus=OrderStatus
    )


# ------------------------------------------------------------
#  ANALYTIKA PANELI
# ------------------------------------------------------------

from sqlalchemy import func

@app.route("/admin/analytics")
@login_required
def admin_analytics():
    total_orders = Order.query.count()
    done_orders = Order.query.filter(Order.status == OrderStatus.DONE).count()

    # Daromad
    revenue = (
        db.session.query(func.sum(Service.price))
        .join(Order, Order.service_id == Service.id)
        .filter(Order.status.in_([OrderStatus.DONE, OrderStatus.PAYMENT_PENDING]))
        .scalar() or 0
    )

    master_percent = Config.MASTER_SHARE_PERCENT
    master_cost = revenue * (master_percent / 100)
    profit = revenue - master_cost

    top_services = (
        db.session.query(Service.name, func.count(Order.id))
        .join(Order)
        .group_by(Service.id)
        .order_by(func.count(Order.id).desc())
        .limit(5)
        .all()
    )

    return render_template(
        "analytics.html",
        total_orders=total_orders,
        done_orders=done_orders,
        revenue=int(revenue),
        master_cost=int(master_cost),
        profit=int(profit),
        top_services=top_services
    )


# ------------------------------------------------------------
#  AI AUDIO YUKLASH (FOYDALANUVCHI + USTA)
# ------------------------------------------------------------

@app.route("/admin/upload_audio/<int:order_id>/<string:user_type>", methods=["POST"])
@login_required
def upload_audio(order_id, user_type):
    if "audio" not in request.files:
        flash("Audio topilmadi!", "danger")
        return redirect(f"/admin/orders/{order_id}")

    file = request.files["audio"]
    filename = secure_filename(file.filename)
    save_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    file.save(save_path)

    # AI orqali tahlil
    ai_review = analyze_audio_file(order_id, save_path, user_type, db, AIReview)

    flash("AI tahlili tayyor!", "success")
    return redirect(f"/admin/orders/{order_id}")


# ------------------------------------------------------------
# BOT WEBHOOK — CLIENT BOT
# ------------------------------------------------------------

@app.route("/telegram/user_webhook", methods=["POST"])
def user_webhook():
    update = request.get_json()

    if not update:
        return jsonify({"ok": True})

    # MESSAGE HANDLER
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        user_id = msg["from"]["id"]
        text = msg.get("text")
        contact = msg.get("contact")
        location = msg.get("location")

        # Get/create order
        order = Order.query.filter_by(
            user_id=str(user_id),
            chat_id=str(chat_id)
        ).order_by(Order.id.desc()).first()

        if not order:
            order = Order(
                user_id=str(user_id),
                chat_id=str(chat_id),
                step="category",
                status=OrderStatus.NEW
            )
            db.session.add(order)
            db.session.commit()

        # START
        if text == "/start":
            order.step = "category"
            order.status = OrderStatus.NEW
            db.session.commit()

            categories = Category.query.all()
            kb = {"inline_keyboard": [
                [{"text": f"{c.icon or ''} {c.name}", "callback_data": f"cat_{c.id}"}]
                for c in categories
            ]}

            send_user_message(chat_id, "Xizmat turini tanlang:", kb)
            return jsonify({"ok": True})

        # CONTACT
        if order.step == "phone":
            if contact:
                order.phone = contact["phone_number"]
            elif text:
                order.phone = text

            order.step = "location"
            db.session.commit()

            kb = {
                "keyboard": [[{"text": "📍 Lokatsiyani ulashish", "request_location": True}]],
                "resize_keyboard": True
            }
            send_user_message(chat_id, "Lokatsiyani yuboring:", kb)
            return jsonify({"ok": True})

        # LOCATION
        if order.step == "location":
            if location:
                order.location_lat = location["latitude"]
                order.location_lng = location["longitude"]
            else:
                order.address_text = text

            order.step = "comment"
            db.session.commit()

            send_user_message(
                chat_id,
                "Ustaga izoh qoldiring:",
                {"remove_keyboard": True}
            )
            return jsonify({"ok": True})

        # COMMENT
        if order.step == "comment" and text:
            order.comment = text
            order.step = "payment"
            db.session.commit()

            kb = {
                "inline_keyboard": [
                    [{"text": "CLICK", "callback_data": "pay_CLICK"},
                     {"text": "PAYME", "callback_data": "pay_PAYME"}],
                    [{"text": "Naqd", "callback_data": "pay_CASH"},
                     {"text": "QR", "callback_data": "pay_QR"}]
                ]
            }
            send_user_message(chat_id, "To‘lov turini tanlang:", kb)
            return jsonify({"ok": True})

        # CHAT WITH ADMIN
        if order.step == "chat" and text:
            db.session.add(Message(order_id=order.id, from_admin=False, text=text))
            db.session.commit()

            admin_notify(f"Mijozdan xabar (#{order.id}):\n{text}")
            return jsonify({"ok": True})


    # CALLBACK HANDLER
    if "callback_query" in update:
        cq = update["callback_query"]
        data = cq["data"]
        chat_id = cq["message"]["chat"]["id"]
        user_id = cq["from"]["id"]

        order = Order.query.filter_by(
            user_id=str(user_id),
            chat_id=str(chat_id)
        ).order_by(Order.id.desc()).first()

        # CATEGORY
        if data.startswith("cat_"):
            cat_id = int(data.split("_")[1])
            order.category_id = cat_id
            order.step = "service"
            db.session.commit()

            services = Service.query.filter_by(category_id=cat_id).all()
            kb = {"inline_keyboard": [
                [{"text": s.name, "callback_data": f"srv_{s.id}"}] for s in services
            ]}

            send_user_message(chat_id, "Xizmatni tanlang:", kb)
            return jsonify({"ok": True})

        # SERVICE
        if data.startswith("srv_"):
            srv_id = int(data.split("_")[1])
            order.service_id = srv_id
            order.step = "phone"
            order.status = OrderStatus.PENDING
            db.session.commit()

            kb = {
                "keyboard": [[{"text": "📱 Kontakt ulashish", "request_contact": True}]],
                "resize_keyboard": True
            }
            send_user_message(chat_id, "Telefon raqamingizni yuboring:", kb)
            return jsonify({"ok": True})

        # PAYMENT
        if data.startswith("pay_"):
            order.payment_method = data.replace("pay_", "")
            order.step = "done"
            order.status = OrderStatus.IN_PROGRESS
            db.session.commit()

            send_user_message(
                chat_id,
                "Buyurtma qabul qilindi!",
                {"remove_keyboard": True}
            )

            admin_notify(f"Yangi buyurtma #{order.id}")
            return jsonify({"ok": True})

    return jsonify({"ok": True})


# ------------------------------------------------------------
# BOT WEBHOOK — MASTER (USTA) BOT
# ------------------------------------------------------------

@app.route("/telegram/master_webhook", methods=["POST"])
def master_webhook():
    update = request.get_json()
    if not update:
        return jsonify({"ok": True})

    # MESSAGE
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text")

        # /start
        if text == "/start":
            send_master_message(chat_id,
                "Assalomu alaykum, Usta!\n"
                "Buyurtmalar ro‘yxati: /orders"
            )
            return jsonify({"ok": True})

        # /orders
        if text == "/orders":
            orders = Order.query.filter(
                Order.status.in_([OrderStatus.PENDING, OrderStatus.IN_PROGRESS])
            ).all()

            if not orders:
                send_master_message(chat_id, "Hozircha faol buyurtmalar yo‘q.")
                return jsonify({"ok": True})

            kb = {"inline_keyboard": [
                [{"text": f"#{o.id} - {o.service.name}", "callback_data": f"ord_{o.id}"}]
                for o in orders
            ]}
            send_master_message(chat_id, "Buyurtmalar:", kb)
            return jsonify({"ok": True})

    # CALLBACK
    if "callback_query" in update:
        cq = update["callback_query"]
        data = cq["data"]
        chat_id = cq["message"]["chat"]["id"]

        if data.startswith("ord_"):
            order_id = int(data.replace("ord_", ""))
            order = Order.query.get(order_id)

            text = (
                f"Buyurtma #{order.id}\n"
                f"Xizmat: {order.service.name}\n"
                f"Telefon: {order.phone}\n"
                f"Izoh: {order.comment}\n"
                f"To‘lov: {order.payment_method}\n"
                "\nStatusni tanlang:"
            )

            kb = {
                "inline_keyboard": [
                    [{"text": "🚀 Ishni boshladim",
                      "callback_data": f"st_{order_id}_start"}],
                    [{"text": "🏁 Tugatdim",
                      "callback_data": f"st_{order_id}_done"}]
                ]
            }

            send_master_message(chat_id, text, kb)
            return jsonify({"ok": True})

        if data.startswith("st_"):
            _, order_id, status = data.split("_")
            order = Order.query.get(int(order_id))

            if status == "start":
                order.status = OrderStatus.IN_PROGRESS
                db.session.commit()

                send_master_message(chat_id, "Ishni boshladingiz!")
                send_user_message(order.chat_id, "Usta ishni boshladi 🚀")
                admin_notify(f"Usta #{order.id} ishni boshladi")

            if status == "done":
                order.status = OrderStatus.DONE
                db.session.commit()

                send_master_message(chat_id, "Ish tugatildi! 🏁")
                send_user_message(order.chat_id, "Ish tugatildi! 💳 To‘lov kutilmoqda.")
                admin_notify(f"Usta #{order.id} ishni tugatdi")

            return jsonify({"ok": True})

    return jsonify({"ok": True})


# ------------------------------------------------------------
# RUN APP
# ------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
