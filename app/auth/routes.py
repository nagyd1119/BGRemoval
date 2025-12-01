from flask import (
    render_template, request, redirect, url_for,
    flash, session, g
)
from . import auth_bp
from ..models import User
from .. import db
from functools import wraps


@auth_bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)


def login_user(user: User):
    session["user_id"] = user.id


def logout_user():
    session.pop("user_id", None)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            flash("Sign in first.")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


def can_edit_resource(owner_id: int, current_user: User) -> bool:
    if current_user is None:
        return False
    if current_user.is_admin:
        return True
    return current_user.id == owner_id


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]

        if not username or not email or not password:
            flash("All fields are required.")
            return redirect(url_for("auth.register"))

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Username or email already exists.")
            return redirect(url_for("auth.register"))

        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash("Successfully registered.")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash("Username or password is incorrect.")
            return redirect(url_for("auth.login"))

        login_user(user)
        flash("Successfully logged in.")
        return redirect(url_for("gallery.gallery"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("Successfully logged out.")
    return redirect(url_for("gallery.gallery"))
