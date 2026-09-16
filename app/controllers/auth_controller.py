from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse

from app.extensions import db
from app.models import Usuario

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        identificador = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        usuario = Usuario.query.filter(
            (Usuario.username == identificador) | (Usuario.email == identificador)
        ).first()

        if usuario is None or not usuario.check_password(password):
            flash("Usuario o contraseña incorrectos.", "danger")
        elif not usuario.activo:
            flash("Tu cuenta está desactivada. Contacta a RRHH.", "warning")
        else:
            login_user(usuario, remember=bool(request.form.get("remember")))
            flash(f"Bienvenido, {usuario.username}.", "success")
            next_page = request.args.get("next")
            if not next_page or urlparse(next_page).netloc != "":
                next_page = url_for("dashboard.index")
            return redirect(next_page)

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/")
def root():
    return redirect(url_for("dashboard.index"))
