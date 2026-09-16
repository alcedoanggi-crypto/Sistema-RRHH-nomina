import enum
from datetime import datetime
from app.extensions import db


class TipoPermisoEnum(str, enum.Enum):
    VACACIONES = "vacaciones"
    MEDICO = "permiso_medico"
    PERSONAL = "asunto_personal"
    MATERNIDAD = "maternidad_paternidad"
    CALAMIDAD = "calamidad_domestica"
    NO_REMUNERADO = "no_remunerado"

    @property
    def label(self):
        return self.value.replace("_", " ").title()


class EstadoSolicitudEnum(str, enum.Enum):
    PENDIENTE = "pendiente"
    APROBADO_JEFE = "aprobado_jefe"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
    CANCELADO = "cancelado"

    @property
    def label(self):
        return self.value.replace("_", " ").title()

    @property
    def badge(self):
        return {
            "pendiente": "warning",
            "aprobado_jefe": "info",
            "aprobado": "success",
            "rechazado": "danger",
            "cancelado": "secondary",
        }[self.value]


class Permiso(db.Model):
    __tablename__ = "permisos"

    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey("empleados.id"), nullable=False)
    empleado = db.relationship("Empleado", back_populates="permisos", foreign_keys=[empleado_id])

    tipo = db.Column(db.Enum(TipoPermisoEnum), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.Text, nullable=False)
    adjunto = db.Column(db.String(255))
    estado = db.Column(db.Enum(EstadoSolicitudEnum), nullable=False, default=EstadoSolicitudEnum.PENDIENTE)

    solicitado_en = db.Column(db.DateTime, default=datetime.utcnow)

    aprobado_jefe_id = db.Column(db.Integer, db.ForeignKey("empleados.id"))
    aprobado_jefe = db.relationship("Empleado", foreign_keys=[aprobado_jefe_id])
    aprobado_rrhh_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    comentario_aprobacion = db.Column(db.String(255))
    resuelto_en = db.Column(db.DateTime)

    @property
    def dias(self):
        return (self.fecha_fin - self.fecha_inicio).days + 1

    @property
    def es_remunerado(self):
        return self.tipo != TipoPermisoEnum.NO_REMUNERADO

    def __repr__(self):
        return f"<Permiso {self.tipo.value} emp={self.empleado_id} [{self.estado.value}]>"
