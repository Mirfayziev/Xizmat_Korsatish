import os
import requests
from functools import wraps

from flask import (
    Flask,
    request,
    render_template,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
)

from sqlalchemy import func

from config import Config
from models import db, Category, Service, Order, Message, OrderStatus


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # ---------------- HELPERS ----------------

    def send_user_message(chat_id, text, reply_markup=None):
        """Foydalanuvchi botidan xabar yuborish."""
        token = app.config.get("TELEGRAM_BOT_TOKEN")
        if not token or not chat_id:
            return
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print("Error sending user telegram message:", e)

    def send_master_message(chat_id, text, reply_markup=None):
        """Usta botidan xabar yuborish."""
        token = app.config.get("TELEGRAM_MASTER_BOT_TOKEN")
        if not token or not chat_id:
            return
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print("Error sending master telegram message:", e)

    def build_categories_keyboard():
        categories = Category.query.order_by(Category.id).all()
        keyboard = []
        row = []
        for i, cat in enumerate(categories, start=1):
            text = f"{cat.icon} {cat.name}" if cat.icon else cat.name
            row.append(
                {
                    "text": text,
                    "callback_data": f"cat_{cat.id}",
                }
            )
            if i % 2 == 0:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        # Admin bilan bog'lanish tugmasi
        keyboard.append(
            [
                {
                    "text": "📞 Admin bilan bog'lanish",
                    "callback_data": "contact_admin",
                }
            ]
        )

        return {"inline_keyboard": keyboard} if keyboard else None

    def build_services_keyboard(category_id):
        services = (
            Service.query.filter_by(category_id=category_id)
            .order_by(Service.id)
            .all()
        )
        keyboard = []
        row = []
        for i, srv in enumerate(services, start=1):
            price_txt = f" ({srv.price:.0f})" if srv.price is not None else ""
            text = f"{srv.name}{price_txt}"
            row.append(
                {
                    "text": text,
                    "callback_data": f"srv_{srv.id}",
                }
            )
            if i % 1 == 0:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        return {"inline_keyboard": keyboard} if keyboard else None

    def build_payment_keyboard():
        keyboard = [
            [
                {"text": "CLICK", "callback_data": "pay_click"},
                {"text": "PAYME", "callback_data": "pay_payme"},
            ],
            [
                {"text": "Naqd", "callback_data": "pay_cash"},
                {"text": "QR orqali", "callback_data": "pay_qr"},
            ],
        ]
        return {"inline_keyboard": keyboard}

    def build_share_contact_keyboard():
        return {
            "keyboard": [
                [
                    {
                        "text": "📱 Telefon raqamni ulashish",
                        "request_contact": True,
                    }
                ]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": True,
        }

    def build_share_location_keyboard():
        return {
            "keyboard": [
                [
                    {
                        "text": "📍 Lokatsiyani ulashish",
                        "request_location": True,
                    }
                ]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": True,
        }

    def get_or_create_active_order(user_id, chat_id):
        order = (
            Order.query.filter(
                Order.user_id == user_id,
                Order.chat_id == chat_id,
                Order.status.in_(
                    [
                        OrderStatus.NEW,
                        OrderStatus.PENDING,
                        OrderStatus.IN_PROGRESS,
                        OrderStatus.PAYMENT_PENDING,
                    ]
                ),
            )
            .order_by(Order.id.desc())
            .first()
        )
        if not order:
            order = Order(user_id=user_id, chat_id=chat_id)
            db.session.add(order)
            db.session.commit()
        return order

    # ---------------- AUTH HELPERS ----------------

    def login_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get("admin_logged_in"):
                return redirect(url_for("admin_login"))
            return f(*args, **kwargs)

        return decorated

    # ---------------- ADMIN ROUTES ----------------

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            if (
                username == app.config["ADMIN_USERNAME"]
                and password == app.config["ADMIN_PASSWORD"]
            ):
                session["admin_logged_in"] = True
                return redirect(url_for("admin_dashboard"))
            else:
                flash("Login yoki parol noto'g'ri", "danger")
        return render_template("login.html")

    @app.route("/admin/logout")
    def admin_logout():
        session.pop("admin_logged_in", None)
        return redirect(url_for("admin_login"))

    @app.route("/")
    def home():
        if session.get("admin_logged_in"):
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("admin_login"))

    @app.route("/admin/dashboard")
    @login_required
    def admin_dashboard():
        orders = Order.query.order_by(Order.created_at.desc()).limit(20).all()
        return render_template(
            "dashboard.html", orders=orders, OrderStatus=OrderStatus
        )

    @app.route("/admin/categories")
    @login_required
    def admin_categories():
        categories = Category.query.order_by(Category.id).all()
        return render_template("categories.html", categories=categories)

    @app.route("/admin/categories/add", methods=["POST"])
    @login_required
    def admin_add_category():
        name = request.form.get("name")
        icon = request.form.get("icon")
        if name:
            cat = Category(name=name, icon=icon or None)
            db.session.add(cat)
            db.session.commit()
        return redirect(url_for("admin_categories"))

    @app.route("/admin/categories/<int:cat_id>/delete", methods=["POST"])
    @login_required
    def admin_delete_category(cat_id):
        cat = Category.query.get_or_404(cat_id)
        db.session.delete(cat)
        db.session.commit()
        return redirect(url_for("admin_categories"))

    @app.route("/admin/services")
    @login_required
    def admin_services():
        services = Service.query.order_by(Service.id).all()
        categories = Category.query.order_by(Category.id).all()
        return render_template(
            "services.html",
            services=services,
            categories=categories,
        )

    @app.route("/admin/services/add", methods=["POST"])
    @login_required
    def admin_add_service():
        name = request.form.get("name")
        price = request.form.get("price")
        description = request.form.get("description")
        category_id = request.form.get("category_id")
        if name and category_id:
            price_value = float(price) if price else None
            srv = Service(
                name=name,
                price=price_value,
                description=description,
                category_id=int(category_id),
            )
            db.session.add(srv)
            db.session.commit()
        return redirect(url_for("admin_services"))

    @app.route("/admin/services/<int:srv_id>/delete", methods=["POST"])
    @login_required
    def admin_delete_service(srv_id):
        srv = Service.query.get_or_404(srv_id)
        db.session.delete(srv)
        db.session.commit()
        return redirect(url_for("admin_services"))

    @app.route("/admin/orders")
    @login_required
    def admin_orders():
        status_filter = request.args.get("status")
        query = Order.query
        if status_filter:
            try:
                status_enum = OrderStatus(status_filter)
                query = query.filter_by(status=status_enum)
            except ValueError:
                pass
        orders = query.order_by(Order.created_at.desc()).all()
        return render_template(
            "orders.html",
            orders=orders,
            OrderStatus=OrderStatus,
            status_filter=status_filter,
        )

    @app.route("/admin/orders/<int:order_id>", methods=["GET", "POST"])
    @login_required
    def admin_order_detail(order_id):
        order = Order.query.get_or_404(order_id)
        if request.method == "POST":
            action = request.form.get("action")

            if action == "set_status":
                new_status = request.form.get("status")
                try:
                    order.status = OrderStatus(new_status)
                    db.session.commit()
                except ValueError:
                    pass

                # Ish bajarilganda foydalanuvchiga xabar
                if order.status in [
                    OrderStatus.DONE,
                    OrderStatus.PAYMENT_PENDING,
                ]:
                    text = (
                        "✅ Ish bajarildi.\n"
                        "💳 To'lov kutilmoqda."
                    )
                    send_user_message(order.chat_id, text)

                # Adminga xabar
                admin_chat_id = app.config.get("TELEGRAM_ADMIN_CHAT_ID")
                if admin_chat_id:
                    send_user_message(
                        admin_chat_id,
                        f"ℹ️ Buyurtma #{order.id} statusi yangilandi: {order.status.value}",
                    )

            if action == "send_message":
                text = request.form.get("text")
                if text:
                    msg = Message(order_id=order.id, from_admin=True, text=text)
                    db.session.add(msg)
                    db.session.commit()
                    # Foydalanuvchiga yuboramiz
                    send_user_message(
                        order.chat_id,
                        f"👨‍💼 Admin: {text}",
                    )

            return redirect(url_for("admin_order_detail", order_id=order.id))

        messages = (
            Message.query.filter_by(order_id=order.id)
            .order_by(Message.created_at.asc())
            .all()
        )
        return render_template(
            "order_detail.html",
            order=order,
            messages=messages,
            OrderStatus=OrderStatus,
        )

    # ---------------- ANALYTICS ----------------

    @app.route("/admin/analytics")
    @login_required
    def admin_analytics():
        # Umumiy statistika
        total_orders = Order.query.count()
        total_done = (
            Order.query.filter(
                Order.status.in_(
                    [
                        OrderStatus.DONE,
                        OrderStatus.PAYMENT_PENDING,
                        OrderStatus.CLOSED,
                    ]
                )
            ).count()
        )
        total_in_progress = (
            Order.query.filter(Order.status == OrderStatus.IN_PROGRESS).count()
        )

        # Xizmatlar bo'yicha buyurtmalar soni
        services_stats = (
            db.session.query(Service.name, func.count(Order.id))
            .join(Order, Order.service_id == Service.id)
            .group_by(Service.id)
            .order_by(func.count(Order.id).desc())
            .all()
        )

        # Kategoriyalar bo'yicha buyurtmalar
        categories_stats = (
            db.session.query(Category.name, func.count(Order.id))
            .join(Order, Order.category_id == Category.id)
            .group_by(Category.id)
            .order_by(func.count(Order.id).desc())
            .all()
        )

        # To'lov turlari bo'yicha
        payment_stats = (
            db.session.query(Order.payment_method, func.count(Order.id))
            .group_by(Order.payment_method)
            .all()
        )

        # Kunlik buyurtmalar
        daily_stats = (
            db.session.query(
                func.date(Order.created_at),
                func.count(Order.id),
            )
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at))
            .all()
        )

        # Daromad / xarajat / foyda
        revenue_q = (
            db.session.query(func.coalesce(func.sum(Service.price), 0))
            .join(Order, Order.service_id == Service.id)
            .filter(
                Order.status.in_(
                    [
                        OrderStatus.DONE,
                        OrderStatus.PAYMENT_PENDING,
                        OrderStatus.CLOSED,
                    ]
                )
            )
        )
        total_revenue = revenue_q.scalar() or 0

        master_percent = app.config.get("MASTER_SHARE_PERCENT", 70.0)
        try:
            master_percent = float(master_percent)
        except ValueError:
            master_percent = 70.0

        total_master_cost = total_revenue * (master_percent / 100.0)
        total_profit = total_revenue - total_master_cost

        return render_template(
            "analytics.html",
            total_orders=total_orders,
            total_done=total_done,
            total_in_progress=total_in_progress,
            services_stats=services_stats,
            categories_stats=categories_stats,
            payment_stats=payment_stats,
            daily_stats=daily_stats,
            total_revenue=total_revenue,
            total_master_cost=total_master_cost,
            total_profit=total_profit,
            master_percent=master_percent,
        )

    # ---------------- WEBHOOK ROUTES ----------------

    @app.route("/telegram/webhook", methods=["POST"])
    def telegram_webhook_compat():
        # Eski webhook manzil bilan moslik uchun
        data = request.get_json(force=True)
        handle_user_update(data)
        return jsonify({"ok": True})

    @app.route("/telegram/user_webhook", methods=["POST"])
    def telegram_user_webhook():
        data = request.get_json(force=True)
        handle_user_update(data)
        return jsonify({"ok": True})

    @app.route("/telegram/master_webhook", methods=["POST"])
    def telegram_master_webhook():
        data = request.get_json(force=True)
        handle_master_update(data)
        return jsonify({"ok": True})

    # ---------------- USER BOT LOGIC ----------------

    def handle_user_update(update):
        # message
        if "message" in update:
            message = update["message"]
            chat_id = message["chat"]["id"]
            user_id = message["from"]["id"]
            text = message.get("text")
            contact = message.get("contact")
            location = message.get("location")

            order = get_or_create_active_order(user_id, chat_id)

            # START
            if text == "/start":
                order.step = "category"
                order.status = OrderStatus.NEW
                db.session.commit()
                welcome_text = (
                    "Assalomu alaykum! 👋\n"
                    "Xizmat turini tanlang:"
                )
                reply_markup = build_categories_keyboard()
                send_user_message(
                    chat_id,
                    welcome_text,
                    reply_markup=reply_markup,
                )
                return

            # Admin bilan chatda bo'lsa
            if order.step == "chat" and text:
                msg = Message(order_id=order.id, from_admin=False, text=text)
                db.session.add(msg)
                db.session.commit()

                admin_chat_id = app.config.get("TELEGRAM_ADMIN_CHAT_ID")
                if admin_chat_id:
                    send_user_message(
                        admin_chat_id,
                        f"💬 Yangi xabar (Order #{order.id}):\n{text}",
                    )
                return

            # Telefon bosqichi
            if order.step == "phone":
                if contact and contact.get("phone_number"):
                    order.phone = contact["phone_number"]
                elif text:
                    order.phone = text
                order.step = "location"
                db.session.commit()
                send_user_message(
                    chat_id,
                    "📍 Lokatsiyani yuboring (Share Location tugmasidan foydalanib) yoki manzilni matn ko'rinishida yozing.",
                    reply_markup=build_share_location_keyboard(),
                )
                return

            # Lokatsiya bosqichi
            if order.step == "location":
                if location:
                    order.location_lat = location.get("latitude")
                    order.location_lng = location.get("longitude")
                    order.step = "comment"
                    db.session.commit()
                    send_user_message(
                        chat_id,
                        "✍️ Usta o'zi bilan nima olib kelishi kerak? Izoh qoldiring:",
                        reply_markup={"remove_keyboard": True},
                    )
                    return
                elif text:
                    order.address_text = text
                    order.step = "comment"
                    db.session.commit()
                    send_user_message(
                        chat_id,
                        "✍️ Usta o'zi bilan nima olib kelishi kerak? Izoh qoldiring:",
                        reply_markup={"remove_keyboard": True},
                    )
                    return

            # Izoh bosqichi
            if order.step == "comment":
                if text:
                    order.comment = text
                    order.step = "payment"
                    db.session.commit()
                    send_user_message(
                        chat_id,
                        "💳 To'lov turini tanlang:",
                        reply_markup=build_payment_keyboard(),
                    )
                    return

            # Agar alohida step bo'lmasa – oddiy chat sifatida saqlaymiz
            if text:
                msg = Message(order_id=order.id, from_admin=False, text=text)
                db.session.add(msg)
                db.session.commit()

                admin_chat_id = app.config.get("TELEGRAM_ADMIN_CHAT_ID")
                if admin_chat_id:
                    send_user_message(
                        admin_chat_id,
                        f"📩 Yangi xabar (Order #{order.id}):\n{text}",
                    )

        # callback query (inline keyboard)
        if "callback_query" in update:
            cq = update["callback_query"]
            data = cq.get("data")
            chat_id = cq["message"]["chat"]["id"]
            user_id = cq["from"]["id"]

            order = get_or_create_active_order(user_id, chat_id)

            # Admin bilan bog'lanish
            if data == "contact_admin":
                order.step = "chat"
                db.session.commit()
                admin_chat_id = app.config.get("TELEGRAM_ADMIN_CHAT_ID")
                if admin_chat_id:
                    send_user_message(
                        admin_chat_id,
                        f"📞 Foydalanuvchi siz bilan bog'lanmoqchi. Order #{order.id}",
                    )
                send_user_message(
                    chat_id,
                    "✍️ Xabaringizni yozing. Admin sizga javob qaytaradi.",
                )
                return

            # Orqaga menyuga qaytish (agar kerak bo'lsa)
            if data == "back_to_menu":
                order.step = "category"
                db.session.commit()
                send_user_message(
                    chat_id,
                    "Xizmat turini tanlang:",
                    reply_markup=build_categories_keyboard(),
                )
                return

            # Kategoriya tanlash
            if data.startswith("cat_"):
                cat_id = int(data.split("_")[1])
                category = Category.query.get(cat_id)
                if not category:
                    send_user_message(chat_id, "Kategoriya topilmadi.")
                    return
                order.category_id = cat_id
                order.step = "service"
                db.session.commit()

                services_keyboard = build_services_keyboard(cat_id)
                if not services_keyboard:
                    send_user_message(
                        chat_id,
                        "Bu kategoriyada xizmatlar topilmadi.",
                    )
                    return
                text = (
                    f"{category.icon or ''} <b>{category.name}</b> kategoriyasi.\n"
                    "Xizmat turini tanlang:"
                )
                send_user_message(
                    chat_id,
                    text,
                    reply_markup=services_keyboard,
                )
                return

            # Xizmat tanlash
            if data.startswith("srv_"):
                srv_id = int(data.split("_")[1])
                service = Service.query.get(srv_id)
                if not service:
                    send_user_message(chat_id, "Xizmat topilmadi.")
                    return
                order.service_id = srv_id
                order.step = "phone"
                order.status = OrderStatus.PENDING
                db.session.commit()

                summary = f"✅ Xizmat tanlandi:\n<b>{service.name}</b>\n"
                if service.price is not None:
                    summary += f"Narx: {service.price:.0f}\n"
                if service.description:
                    summary += f"\n{service.description}\n"
                summary += "\n📱 Telefon raqamingizni yuboring:"
                send_user_message(
                    chat_id,
                    summary,
                    reply_markup=build_share_contact_keyboard(),
                )
                return

            # To'lov tanlash
            if data.startswith("pay_"):
                pay_code = data.split("_")[1]
                mapping = {
                    "click": "CLICK",
                    "payme": "PAYME",
                    "cash": "Naqd",
                    "qr": "QR orqali",
                }
                order.payment_method = mapping.get(pay_code, pay_code)
                order.status = OrderStatus.IN_PROGRESS
                order.step = "done"
                db.session.commit()

                # Lokatsiya / kontakt keyboardlarini yopamiz
                send_user_message(
                    chat_id,
                    "🎉 Buyurtmangiz qabul qilindi!",
                    reply_markup={"remove_keyboard": True},
                )

                text_lines = [
                    "✅ Buyurtmangiz qabul qilindi!",
                    "",
                ]
                if order.service:
                    text_lines.append(f"Xizmat: {order.service.name}")
                if order.payment_method:
                    text_lines.append(
                        f"To'lov turi: {order.payment_method}"
                    )
                text_lines.append("")
                text_lines.append(
                    "Usta tez orada siz bilan bog'lanadi yoki keladi."
                )
                send_user_message(chat_id, "\n".join(text_lines))

                # Adminga ham xabar
                admin_chat_id = app.config.get("TELEGRAM_ADMIN_CHAT_ID")
                if admin_chat_id:
                    send_user_message(
                        admin_chat_id,
                        f"🆕 Yangi buyurtma #{order.id}\n"
                        f"Xizmat: {order.service.name if order.service else ''}\n"
                        f"To'lov: {order.payment_method or '-'}",
                    )
                return

    # ---------------- MASTER BOT LOGIC ----------------

    def handle_master_update(update):
        """
        Usta bot logikasi.
        Hozircha soddaroq variant: usta buyurtmalar ro'yxatini ko'radi va statusni yangilaydi.
        Keyin shu yerga audio + AI tahlilni qo'shsa bo'ladi.
        """
        # message
        if "message" in update:
            message = update["message"]
            chat_id = message["chat"]["id"]
            text = message.get("text")

            if text == "/start":
                send_master_message(
                    chat_id,
                    "Assalomu alaykum, usta! 👷\n"
                    "Siz uchun biriktirilgan buyurtmalar ro'yxatini ko'rish uchun /orders buyrug'ini bosing.",
                )
                return

            if text == "/orders":
                # Hozircha barcha PENDING va IN_PROGRESS buyurtmalarni ko'rsatamiz
                orders = (
                    Order.query.filter(
                        Order.status.in_(
                            [OrderStatus.PENDING, OrderStatus.IN_PROGRESS]
                        )
                    )
                    .order_by(Order.created_at.asc())
                    .limit(20)
                    .all()
                )
                if not orders:
                    send_master_message(
                        chat_id,
                        "Hozir siz uchun faol buyurtmalar yo'q.",
                    )
                    return

                keyboard = []
                for o in orders:
                    title = o.service.name if o.service else f"Order #{o.id}"
                    keyboard.append(
                        [
                            {
                                "text": f"#{o.id} - {title}",
                                "callback_data": f"mord_{o.id}",
                            }
                        ]
                    )
                send_master_message(
                    chat_id,
                    "Faol buyurtmalar:",
                    reply_markup={"inline_keyboard": keyboard},
                )
                return

            # Hozircha: usta matn yozsa – admin'ga uzatiladi
            if text:
                admin_chat_id = app.config.get("TELEGRAM_ADMIN_CHAT_ID")
                if admin_chat_id:
                    send_user_message(
                        admin_chat_id,
                        f"👷 Ustadan xabar:\n{text}",
                    )
                send_master_message(
                    chat_id,
                    "Xabaringiz qabul qilindi, rahmat.",
                )
                return

        # callback query
        if "callback_query" in update:
            cq = update["callback_query"]
            data = cq.get("data")
            chat_id = cq["message"]["chat"]["id"]

            if data.startswith("mord_"):
                order_id = int(data.split("_")[1])
                order = Order.query.get(order_id)
                if not order:
                    send_master_message(chat_id, "Buyurtma topilmadi.")
                    return

                text_lines = [
                    f"📝 Buyurtma #{order.id}",
                ]
                if order.service:
                    text_lines.append(f"Xizmat: {order.service.name}")
                if order.phone:
                    text_lines.append(f"Telefon: {order.phone}")
                if order.comment:
                    text_lines.append(f"Izoh: {order.comment}")
                if order.payment_method:
                    text_lines.append(f"To'lov: {order.payment_method}")
                text_lines.append(f"Status: {order.status.value}")
                text_lines.append("")
                text_lines.append("Statusni tanlang:")

                keyboard = [
                    [
                        {
                            "text": "🚀 Ishni boshladim",
                            "callback_data": f"mstatus_{order.id}_in_progress",
                        }
                    ],
                    [
                        {
                            "text": "🏁 Ish tugadi",
                            "callback_data": f"mstatus_{order.id}_done",
                        }
                    ],
                ]
                send_master_message(
                    chat_id,
                    "\n".join(text_lines),
                    reply_markup={"inline_keyboard": keyboard},
                )
                return

            if data.startswith("mstatus_"):
                parts = data.split("_")
                if len(parts) != 3:
                    return
                order_id = int(parts[1])
                new_st = parts[2]
                order = Order.query.get(order_id)
                if not order:
                    send_master_message(chat_id, "Buyurtma topilmadi.")
                    return

                if new_st == "in_progress":
                    order.status = OrderStatus.IN_PROGRESS
                    db.session.commit()
                    send_master_message(
                        chat_id,
                        f"Buyurtma #{order.id} statusi: IN_PROGRESS",
                    )
                    # Adminga info
                    admin_chat_id = app.config.get("TELEGRAM_ADMIN_CHAT_ID")
                    if admin_chat_id:
                        send_user_message(
                            admin_chat_id,
                            f"👷 Usta buyurtma #{order.id} ishini boshladi.",
                        )
                    return

                if new_st == "done":
                    order.status = OrderStatus.DONE
                    db.session.commit()
                    send_master_message(
                        chat_id,
                        f"Buyurtma #{order.id} statusi: DONE",
                    )
                    # Foydalanuvchiga
                    send_user_message(
                        order.chat_id,
                        "✅ Ish bajarildi.\n💳 To'lov kutilmoqda.",
                    )
                    # Adminga
                    admin_chat_id = app.config.get("TELEGRAM_ADMIN_CHAT_ID")
                    if admin_chat_id:
                        send_user_message(
                            admin_chat_id,
                            f"👷 Usta buyurtma #{order.id} ishini tugatdi.",
                        )
                    return

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
