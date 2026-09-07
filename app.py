import os
from datetime import datetime

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_, and_

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("UCHAT_SECRET_KEY", "dev-secret-key-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'uchat.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to continue."
login_manager.login_message_category = "info"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar_color = db.Column(db.String(7), default="#00a884")
    status = db.Column(db.String(140), default="Hey there! I am using UChat.")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def initials(self):
        parts = self.display_name.strip().split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return self.display_name[:2].upper()


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_read = db.Column(db.Boolean, default=False)

    sender = db.relationship("User", foreign_keys=[sender_id])
    recipient = db.relationship("User", foreign_keys=[recipient_id])

    def to_dict(self):
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "body": self.body,
            "timestamp": self.timestamp.strftime("%H:%M"),
            "full_timestamp": self.timestamp.strftime("%d %b %Y, %H:%M"),
            "is_mine": self.sender_id == current_user.id if current_user.is_authenticated else False,
        }


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_conversation_partners():
    """Return list of users the current user has exchanged messages with,
    plus every other registered user (so new chats can be started),
    ordered by most recent activity."""
    all_users = User.query.filter(User.id != current_user.id).all()

    partners = []
    for user in all_users:
        last_msg = (
            Message.query.filter(
                or_(
                    and_(Message.sender_id == current_user.id, Message.recipient_id == user.id),
                    and_(Message.sender_id == user.id, Message.recipient_id == current_user.id),
                )
            )
            .order_by(Message.timestamp.desc())
            .first()
        )
        unread_count = Message.query.filter_by(
            sender_id=user.id, recipient_id=current_user.id, is_read=False
        ).count()

        partners.append({
            "user": user,
            "last_message": last_msg,
            "unread_count": unread_count,
            "sort_key": last_msg.timestamp if last_msg else datetime.min,
        })

    partners.sort(key=lambda p: p["sort_key"], reverse=True)
    return partners


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        display_name = request.form.get("display_name", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not username or not display_name or not password:
            flash("Please fill in all fields.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
        elif User.query.filter_by(username=username).first():
            flash("That username is already taken.", "error")
        else:
            colors = ["#00a884", "#7986cb", "#f06292", "#ffa726", "#4dd0e1", "#9575cd"]
            user = User(
                username=username,
                display_name=display_name,
                avatar_color=colors[User.query.count() % len(colors)],
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for("index"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            user.last_seen = datetime.utcnow()
            db.session.commit()
            next_page = request.args.get("next")
            return redirect(next_page or url_for("index"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    current_user.last_seen = datetime.utcnow()
    db.session.commit()
    logout_user()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Main chat routes
# ---------------------------------------------------------------------------

@app.route("/")
@login_required
def index():
    partners = get_conversation_partners()
    return render_template("index.html", partners=partners, active_chat=None)


@app.route("/chat/<int:user_id>")
@login_required
def chat(user_id):
    other_user = User.query.get_or_404(user_id)
    partners = get_conversation_partners()

    messages = (
        Message.query.filter(
            or_(
                and_(Message.sender_id == current_user.id, Message.recipient_id == other_user.id),
                and_(Message.sender_id == other_user.id, Message.recipient_id == current_user.id),
            )
        )
        .order_by(Message.timestamp.asc())
        .all()
    )

    # mark incoming messages as read
    Message.query.filter_by(
        sender_id=other_user.id, recipient_id=current_user.id, is_read=False
    ).update({"is_read": True})
    db.session.commit()

    return render_template(
        "index.html",
        partners=partners,
        active_chat=other_user,
        messages=messages,
    )


@app.route("/api/send/<int:user_id>", methods=["POST"])
@login_required
def send_message(user_id):
    other_user = User.query.get_or_404(user_id)
    body = request.form.get("body", "").strip()

    if not body:
        return jsonify({"error": "Message cannot be empty"}), 400

    message = Message(sender_id=current_user.id, recipient_id=other_user.id, body=body)
    db.session.add(message)
    db.session.commit()

    return jsonify(message.to_dict())


@app.route("/api/messages/<int:user_id>")
@login_required
def poll_messages(user_id):
    """Return messages newer than the given message id, for lightweight polling."""
    since_id = request.args.get("since", 0, type=int)
    other_user = User.query.get_or_404(user_id)

    messages = (
        Message.query.filter(
            or_(
                and_(Message.sender_id == current_user.id, Message.recipient_id == other_user.id),
                and_(Message.sender_id == other_user.id, Message.recipient_id == current_user.id),
            ),
            Message.id > since_id,
        )
        .order_by(Message.timestamp.asc())
        .all()
    )

    unread_ids = [m.id for m in messages if m.recipient_id == current_user.id]
    if unread_ids:
        Message.query.filter(Message.id.in_(unread_ids)).update(
            {"is_read": True}, synchronize_session=False
        )
        db.session.commit()

    return jsonify([m.to_dict() for m in messages])


@app.route("/api/sidebar")
@login_required
def sidebar_data():
    """Lightweight endpoint the sidebar polls for unread counts / last messages."""
    partners = get_conversation_partners()
    data = []
    for p in partners:
        data.append({
            "user_id": p["user"].id,
            "last_message": p["last_message"].body if p["last_message"] else None,
            "last_time": p["last_message"].timestamp.strftime("%H:%M") if p["last_message"] else None,
            "unread_count": p["unread_count"],
        })
    return jsonify(data)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip()
        status = request.form.get("status", "").strip()
        if display_name:
            current_user.display_name = display_name
        if status:
            current_user.status = status
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html")


# ---------------------------------------------------------------------------
# CLI helper to (re)create the database
# ---------------------------------------------------------------------------

@app.cli.command("init-db")
def init_db():
    """Create all database tables."""
    db.create_all()
    print("Database initialized.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)
