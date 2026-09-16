from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Inicia sesión para acceder a esta página."
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    from app.models.usuario import Usuario

    return db.session.get(Usuario, int(user_id))
