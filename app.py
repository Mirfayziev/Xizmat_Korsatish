import os
import time
import requests
from flask import Flask, request, jsonify, render_template, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy

from config import Config
from models import db, Category, Service, Order, OrderStatus, Message, AIReview
from ai_service import analyze_audio_file

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


# =============================
#   HELPERS
# =============================

def send_user_message(chat_id, text, reply_markup=None):
    data = {
        "chat_id": chat_id,
        "text": text
    }
    if reply_markup:
        data["reply_markup"] = reply_markup

    requests.post(
        f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage",
        json=data
    )


def send_master_message(chat_id, text, reply_markup=None):
    data = {
        "chat_id": chat_id,
        "text": text
    }
    if reply_markup:
        data["reply_markup"] = reply_markup

    requests.post(
        f"https://api.telegram.org/bot{Config.TELEGRAM_MASTER_BOT_TOKEN}/sendMessage",
        json=data
    )


# =============================
#   HOME REDIRECT
# =============================

@app.route("/")
def home():
    return redirect("/admin/login")


# =============================
#   ADMIN LOGIN
# =============================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["username"] == Config.ADMIN_USERNAME and \
           request.form["password"] == Config.ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin/dashboard")
        flash("Noto‘g‘ri login yoki parol", "danger")
    return render_template("login.html")


@app.route("/admin/logout")
def logout():
    session.pop("admin", None)
    return redirect("/admin/login")


# =============================
#   ADMIN PAGES
# =============================

@app.route("/admin/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect("/admin/login")
    orders = Order.query.order_by(Order.id.desc()).limit(10).all()
    return render_template("dashboard.html", orders=orders)


@app.route("/admin/categories", methods=["GET"])
def categories_page():
    if "admin" not in session:
        return redirect("/admin/login")
    cats = Category.query.all()
    return render_template("categories.html", categories=cats)


@app.post("/admin/categories/add")
def add_category():
    name = request.form["name"]
    icon = request.form.get("icon", "")

    c = Category(name=name, icon=icon)
    db.session.add(c)
    db.session.commit()
    return redirect("/admin/categories")


@app.post("/admin/categories/<int:id>/delete")
def delete_category(id):
    Category.query.filter_by(id=id).delete()
    db.session.commit()
    return redirect("/admin/categories")


@app.route("/admin/services")
def services_page():
    if "admin" not in session:
        return redirect("/admin/login")
    return render_template(
        "services.html",
        services=Service.query.all(),
        categories=Category.query.all()
    )


@app.post("/admin/services/add")
def add_service():
    s = Service(
        name=request.form["name"],
        price=request.form.get("price"),
        description=request.form.get("description"),
        category_id=request.form["category_id"]
    )
    db.session.add(s)
    db.session.commit()
    return redirect("/admin/services")


@app.post("/admin/services/<int:id>/delete")
def delete_service(id):
    Service.query.filter_by(id=id).delete()
    db.session.commit()
    return redirect("/admin/services")


@app.route("/admin/orders")
def orders_page():
    if "admin" not in session:
        return redirect("/admin/login")

    status = request.args.get("status")
    if status:
        orders = Order.query.filter_by(status=status).all()
    else:
        orders = Order.query.order_by(Order.id.desc()).all()

    return render_template("orders.html", orders=orders)


@app.route("/admin/orders/<int:id>", methods=["GET", "POST"])
def order_details(id):
    if "admin" not in session:
        return redirect("/admin/login")

    order = Order.query.get(id)

    if request.method == "POST":
        action = request.form["action"]

        if action == "status":
            order.status = OrderStatus(request.form["status"])
            db.session.commit()

        if action == "send_message":
            m = Message(
                order_id=id,
                text=request.form["text"],
                from_admin=True
            )
            db.session.add(m)
            db.session.commit()

            # To user
            send_user_message(order.user_chat_id, "Admin: " + request.form["text"])

        return redirect(f"/admin/orders/{id}")

    return render_template(
        "order_detail.html",
        order=order,
        messages=Message.query.filter_by(order_id=id).all(),
        ai_data=AIReview.query.filter_by(order_id=id).order_by(AIReview.id.desc()).all(),
        OrderStatus=OrderStatus
    )


# =============================
#   UPLOAD AUDIO (ADMIN)
# =============================

@app.post("/admin/upload_audio/<int:order_id>/<audio_type>")
def upload_audio(order_id, audio_type):
    file = request.files["audio"]
    filename = f"{audio_type}_{order_id}_{int(time.time())}.ogg"
    path = os.path.join(Config.UPLOAD_FOLDER, filename)
    file.save(path)

    analyze_audio_file(order_id, path, audio_type, db, AIReview)

    flash("AI tahlil bajarildi!", "success")
    return redirect(f"/admin/orders/{order_id}")


# =============================
#   AI Tahlillar
# =============================

@app.route("/admin/analytics")
def analytics():
    if "admin" not in session:
        return redirect("/admin/login")

    total_orders = Order.query.count()
    done_orders = Order.query.filter_by(status=OrderStatus.DONE).count()

    revenue = sum([o.service.price for o in Order.query.filter_by(status=OrderStatus.DONE).all() if o.service])
    profit = revenue * (100 - Config.MASTER_SHARE_PERCENT) / 100

    from sqlalchemy import func
    top_services = db.session.query(Service.name, func.count(Order.id))\
        .join(Order, Order.service_id == Service.id)\
        .group_by(Service.name)\
        .order_by(func.count(Order.id).desc())\
        .limit(5).all()

    return render_template(
        "analytics.html",
        total_orders=total_orders,
        done_orders=done_orders,
        revenue=revenue,
        profit=int(profit),
        top_services=top_services
    )


@app.route("/admin/ai")
def ai_page():
    return render_template(
        "ai_analysis.html",
        ai_list=AIReview.query.order_by(AIReview.id.desc()).all()
    )


# =============================
#   TELEGRAM — USER BOT
# =============================

@app.post("/telegram/user_webhook")
def user_webhook():
    update = request.json

    # No message
    if not update:
        return jsonify({"ok": True})

    # Callback
    if "callback_query" in update:
        cb = update["callback_query"]
        chat_id = cb["from"]["id"]
        data = cb["data"]

        # Category select
        if data.startswith("cat_"):
            cat_id = int(data.split("_")[1])
            services = Service.query.filter_by(category_id=cat_id).all()

            keyboard = [
                [{"text": s.name, "callback_data": f"serv_{s.id}"}]
                for s in services
            ]

            send_user_message(
                chat_id,
                "Xizmatni tanlang:",
                {"inline_keyboard": keyboard}
            )

        # Service selected
        if data.startswith("serv_"):
            serv_id = int(data.split("_")[1])
            serv = Service.query.get(serv_id)

            new = Order(
                service_id=serv_id,
                category_id=serv.category_id,
                status=OrderStatus.NEW,
                user_chat_id=chat_id
            )
            db.session.add(new)
            db.session.commit()

            send_user_message(chat_id, "📞 Telefon raqamingizni yuboring.")
        return jsonify({"ok": True})

    # Messages
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]

        # ========================
        #  VOICE = AI ANALYZE
        # ========================
        if "voice" in msg:

            file_id = msg["voice"]["file_id"]

            file_info = requests.get(
                f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
            ).json()

            file_path = file_info["result"]["file_path"]
            file_url = f"https://api.telegram.org/file/bot{Config.TELEGRAM_BOT_TOKEN}/{file_path}"

            audio_data = requests.get(file_url).content

            filename = f"voice_{chat_id}_{int(time.time())}.ogg"
            save_path = os.path.join(Config.UPLOAD_FOLDER, filename)

            with open(save_path, "wb") as f:
                f.write(audio_data)

            order = Order.query.filter_by(user_chat_id=chat_id).order_by(Order.id.desc()).first()

            analyze_audio_file(order.id, save_path, "client", db, AIReview)

            send_user_message(chat_id, "🎧 Ovoz qabul qilindi!\nAI tahlil qildi.")
            return jsonify({"ok": True})

        # Text messages
        text = msg.get("text")

        order = Order.query.filter_by(user_chat_id=chat_id).order_by(Order.id.desc()).first()

        if order and not order.phone:
            order.phone = text
            db.session.commit()
            send_user_message(chat_id, "📍 Lokatsiyani yuboring.")
            return jsonify({"ok": True})

        if order and not order.location_lat and "location" in msg:
            order.location_lat = msg["location"]["latitude"]
            order.location_lng = msg["location"]["longitude"]
            db.session.commit()
            send_user_message(chat_id, "✍️ Izoh yozing.")
            return jsonify({"ok": True})

        if order and not order.comment:
            order.comment = text
            db.session.commit()
            send_user_message(
                chat_id,
                "💳 To‘lov turini tanlang:",
                {
                    "inline_keyboard": [
                        [{"text": "Click", "callback_data": "pay_click"}],
                        [{"text": "Payme", "callback_data": "pay_payme"}]
                    ]
                }
            )
            return jsonify({"ok": True})

    return jsonify({"ok": True})


# =============================
#   TELEGRAM — MASTER BOT
# =============================

@app.post("/telegram/master_webhook")
def master_webhook():
    update = request.json

    if not update or "message" not in update:
        return jsonify({"ok": True})

    msg = update["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")

    # Start
    if text == "/start":
        send_master_message(chat_id, "Assalomu alaykum, usta!\nBuyurtmalar: /orders")
        return jsonify({"ok": True})

    # Orders
    if text == "/orders":
        orders = Order.query.filter(Order.status.in_([
            OrderStatus.NEW, OrderStatus.PENDING, OrderStatus.IN_PROGRESS
        ])).all()

        if not orders:
            send_master_message(chat_id, "Buyurtmalar yo‘q.")
            return jsonify({"ok": True})

        msg_text = "🔧 Buyurtmalar:\n\n"
        for o in orders:
            msg_text += f"#{o.id} — {o.service.name}\n/order_{o.id}\n\n"

        send_master_message(chat_id, msg_text)
        return jsonify({"ok": True})

    # One order
    if text.startswith("/order_"):
        id = int(text.split("_")[1])
        order = Order.query.get(id)

        t = f"🧾 Buyurtma #{order.id}\n"
        t += f"Xizmat: {order.service.name}\n"
        t += f"Telefon: {order.phone}\n"
        t += f"Holat: {order.status.value}\n\n"
        t += f"Ishni boshlash: /startwork_{id}\n"
        t += f"Ish tugatish: /finish_{id}"

        send_master_message(chat_id, t)
        return jsonify({"ok": True})

    # Start work
    if text.startswith("/startwork_"):
        id = int(text.split("_")[1])
        order = Order.query.get(id)
        order.status = OrderStatus.IN_PROGRESS
        db.session.commit()

        send_master_message(chat_id, "Ish boshlandi!")
        send_user_message(order.user_chat_id, "🧑‍🔧 Usta ishni boshladi!")
        return jsonify({"ok": True})

    # Finish work
    if text.startswith("/finish_"):
        id = int(text.split("_")[1])
        order = Order.query.get(id)
        order.status = OrderStatus.DONE
        db.session.commit()

        send_master_message(chat_id, "Ish tugadi!")
        send_user_message(order.user_chat_id, "Ish tugatildi! Iltimos, to‘lovni amalga oshiring.")
        return jsonify({"ok": True})

    return jsonify({"ok": True})


# =============================
#   RUN
# =============================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000)
