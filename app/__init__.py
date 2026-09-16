import os
from flask import Flask, render_template
from config import config
from app.extensions import db, migrate, login_manager


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config["default"]))

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Modelos (para que Flask-Migrate los detecte)
    from app import models  # noqa: F401

    # Blueprints (controladores / rutas)
    from app.controllers.auth_controller import auth_bp
    from app.controllers.dashboard_controller import dashboard_bp
    from app.controllers.empleado_controller import empleado_bp
    from app.controllers.asistencia_controller import asistencia_bp
    from app.controllers.permiso_controller import permiso_bp
    from app.controllers.nomina_controller import nomina_bp
    from app.controllers.evaluacion_controller import evaluacion_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(empleado_bp)
    app.register_blueprint(asistencia_bp)
    app.register_blueprint(permiso_bp)
    app.register_blueprint(nomina_bp)
    app.register_blueprint(evaluacion_bp)

    # Manejo de errores
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    # Filtros de plantilla
    @app.template_filter("money")
    def money(value):
        try:
            return "${:,.2f}".format(float(value or 0))
        except (TypeError, ValueError):
            return "$0.00"

    return app
