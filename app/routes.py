from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, Queue, QueueEntry, ContentOption
from . import db
from .forms import RegistrationForm

main = Blueprint('main', __name__)

@main.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("main.login"))

@main.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        # Проверка, существует ли пользователь
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered.', 'danger')
            return redirect(url_for('main.register'))

        # Создание нового пользователя
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password, method='pbkdf2:sha256')
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html', form=form)

@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Найти пользователя по email
        user = User.query.filter_by(email=email).first()

        print(f"Email entered: {email}")
        print(f"User found: {user}")

        # Проверка, существует ли пользователь
        if not user:
            flash("Invalid email or password.", "danger")
            return redirect(url_for("main.login"))

        # Проверка пароля
        if not check_password_hash(user.password_hash, password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("main.login"))

        # Авторизовать пользователя
        login_user(user)
        flash("You have been logged in successfully!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("login.html")

@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))

@main.route("/dashboard")
@login_required
def dashboard():
    # Получить все очереди текущего пользователя
    queues = Queue.query.filter_by(creator_id=current_user.id).order_by(Queue.priority).all()
    return render_template("dashboard.html", queues=queues)

@main.route("/public")
def public_page():
    queue_id = request.args.get("queue_id")
    if queue_id:
        queue = Queue.query.get(queue_id)
        if queue:
            return render_template("public_table.html", queue=queue)
        else:
            return "Queue not found.", 404
    return "Please provide a queue ID.", 400

@main.route("/public_all/<int:user_id>")
def public_all(user_id):
    user = User.query.get_or_404(user_id)
    queues = Queue.query.filter_by(creator_id=user.id).order_by(Queue.priority).all()
    return render_template("public_all.html", user=user, queues=queues)

@main.route("/create_queue", methods=["GET", "POST"])
@login_required
def create_queue():
    if request.method == "POST":
        name = request.form.get("name")
        priority = request.form.get("priority")

        # Создать очередь
        new_queue = Queue(name=name, priority=int(priority), creator_id=current_user.id)
        db.session.add(new_queue)
        db.session.commit()
        flash(f'Queue "{name}" created successfully!', "success")
        return redirect(url_for("main.dashboard"))

    return render_template("create_queue.html")


@main.route("/delete_queue/<int:queue_id>")
@login_required
def delete_queue(queue_id):
    queue = Queue.query.get_or_404(queue_id)
    if queue.creator_id != current_user.id:
        flash("You do not have permission to delete this queue.", "danger")
        return redirect(url_for("main.dashboard"))

    db.session.delete(queue)
    db.session.commit()
    flash(f'Queue "{queue.name}" deleted successfully!', "success")
    return redirect(url_for("main.dashboard"))


@main.route("/manage_queue/<int:queue_id>", methods=["GET", "POST"])
@login_required
def manage_queue(queue_id):
    queue = Queue.query.get_or_404(queue_id)
    if queue.creator_id != current_user.id:
        flash("You do not have permission to manage this queue.", "danger")
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        new_name = request.form.get("name")
        new_priority = request.form.get("priority")

        # Обновляем данные очереди
        queue.name = new_name
        queue.priority = int(new_priority)
        db.session.commit()

        flash(f'Queue "{queue.name}" updated successfully!', "success")
        return redirect(url_for("main.manage_queue", queue_id=queue.id))

    return render_template("manage_queue.html", queue=queue)

@main.route("/manage_all_queues")
@login_required
def manage_all_queues():
    queues = Queue.query.filter_by(creator_id=current_user.id).order_by(Queue.priority).all()
    content_options = ContentOption.query.all()  # Получаем все варианты контента
    return render_template("manage_all_queues.html", queues=queues, content_options=content_options)


@main.route("/add_participant", methods=["POST"])
@login_required
def add_participant():
    # Получение данных из формы
    username = request.form.get("username")
    content = request.form.get("content")
    comment = request.form.get("comment")
    queue_id = request.form.get("queue_id")

    # Лог для отладки
    print(f"Received data: username={username}, content={content}, comment={comment}, queue_id={queue_id}")

    # Проверка, существует ли очередь
    queue = Queue.query.get(queue_id)
    if not queue:
        flash("Queue not found.", "danger")
        return redirect(url_for('main.manage_all_queues'))

    # Создание нового участника
    new_entry = QueueEntry(
        username=username,
        status='waiting',
        content=content,
        comment=comment,
        queue_id=queue.id
    )
    db.session.add(new_entry)
    db.session.commit()

    flash("Participant added successfully!", "success")
    return redirect(url_for('main.manage_all_queues'))

@main.route("/delete_participant/<int:participant_id>", methods=["POST"])
@login_required
def delete_participant(participant_id):
    participant = QueueEntry.query.get_or_404(participant_id)

    # Проверяем, принадлежит ли очередь текущему пользователю
    queue = Queue.query.get(participant.queue_id)
    if queue.creator_id != current_user.id:
        flash("You do not have permission to delete this participant.", "danger")
        return redirect(url_for("main.manage_all_queues"))

    # Удаляем участника
    db.session.delete(participant)
    db.session.commit()
    flash(f'Participant "{participant.username}" has been removed.', "success")
    return redirect(url_for("main.manage_all_queues"))


@main.route("/edit_participant/<int:participant_id>", methods=["GET", "POST"])
@login_required
def edit_participant(participant_id):
    participant = QueueEntry.query.get_or_404(participant_id)

    # Проверяем, принадлежит ли очередь текущему пользователю
    queue = Queue.query.get(participant.queue_id)
    if queue.creator_id != current_user.id:
        flash("You do not have permission to edit this participant.", "danger")
        return redirect(url_for("main.manage_all_queues"))

    if request.method == "POST":
        participant.username = request.form.get("username")
        participant.status = request.form.get("status")
        participant.content = request.form.get("content")
        participant.comment = request.form.get("comment")
        db.session.commit()
        flash(f'Participant "{participant.username}" has been updated.', "success")
        return redirect(url_for("main.manage_all_queues"))

    return render_template("edit_participant.html", participant=participant)


@main.route("/add_content_option", methods=["POST"])
@login_required
def add_content_option():
    new_content = request.form.get("new_content")

    # Проверяем, существует ли уже вариант
    if ContentOption.query.filter_by(name=new_content).first():
        flash("This content option already exists.", "danger")
        return redirect(url_for("main.manage_all_queues"))

    # Добавляем новый вариант
    db.session.add(ContentOption(name=new_content))
    db.session.commit()
    flash(f'Content option "{new_content}" added successfully.', "success")
    return redirect(url_for("main.manage_all_queues"))

@main.route("/delete_content_option/<int:content_id>", methods=["POST"])
@login_required
def delete_content_option(content_id):
    content_option = ContentOption.query.get_or_404(content_id)

    # Удаляем вариант контента
    db.session.delete(content_option)
    db.session.commit()
    flash(f'Content option "{content_option.name}" has been removed.', "success")
    return redirect(url_for("main.manage_all_queues"))

@main.route("/toggle_status/<int:participant_id>", methods=["POST"])
@login_required
def toggle_status(participant_id):
    participant = QueueEntry.query.get_or_404(participant_id)

    # Проверяем, принадлежит ли очередь текущему пользователю
    queue = Queue.query.get(participant.queue_id)
    if queue.creator_id != current_user.id:
        return jsonify({"success": False}), 403

    # Переключаем статус
    status_order = ["waiting", "completed", "postponed"]
    current_index = status_order.index(participant.status)
    next_index = (current_index + 1) % len(status_order)
    participant.status = status_order[next_index]

    db.session.commit()
    return jsonify({"success": True, "new_status": participant.status})

@main.route("/update_participant_queue/<int:participant_id>", methods=["POST"])
@login_required
def update_participant_queue(participant_id):
    data = request.get_json()
    new_queue_id = data.get("queue_id")
    order = data.get("order", [])

    # Проверяем существование новой очереди
    new_queue = Queue.query.get(new_queue_id)
    if not new_queue or new_queue.creator_id != current_user.id:
        return jsonify({"success": False, "message": "Invalid queue."}), 400

    # Обновляем очередь участника
    participant = QueueEntry.query.get(participant_id)
    if not participant or participant.queue.creator_id != current_user.id:
        return jsonify({"success": False, "message": "Invalid participant."}), 400

    participant.queue_id = new_queue_id
    db.session.commit()

    # Обновляем порядок участников
    for index, pid in enumerate(order):
        entry = QueueEntry.query.get(int(pid))
        if entry and entry.queue_id == int(new_queue_id):
            entry.priority = index
            db.session.commit()

    return jsonify({"success": True})