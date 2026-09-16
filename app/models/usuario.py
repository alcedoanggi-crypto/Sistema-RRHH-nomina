import enum
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class RolEnum(str, enum.Enum):
    ADMIN_RRHH = "admin_rrhh"
    JEFE_AREA = "jefe_area"
    EMPLEADO = "empleado"

    @property
    def label(self):
        return {
            "admin_rrhh": "Administrador RRHH",
            "jefe_area": "Jefe de Área",
            "empleado": "Empleado",
        }[self.value]


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.Enum(RolEnum), nullable=False, default=RolEnum.EMPLEADO)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    empleado_id = db.Column(db.Integer, db.ForeignKey("empleados.id"), unique=True)
    empleado = db.relationship("Empleado", back_populates="usuario")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Helpers de rol
    @property
    def es_admin_rrhh(self):
        return self.rol == RolEnum.ADMIN_RRHH

    @property
    def es_jefe(self):
        return self.rol == RolEnum.JEFE_AREA

    @property
    def es_empleado(self):
        return self.rol == RolEnum.EMPLEADO

    def __repr__(self):
        return f"<Usuario {self.username} ({self.rol.value})>"
