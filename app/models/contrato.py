import enum
from datetime import date
from app.extensions import db


class TipoContratoEnum(str, enum.Enum):
    INDEFINIDO = "indefinido"
    PLAZO_FIJO = "plazo_fijo"
    EVENTUAL = "eventual"
    PASANTIA = "pasantia"
    SERVICIOS = "servicios_profesionales"

    @property
    def label(self):
        return self.value.replace("_", " ").title()


class EstadoContratoEnum(str, enum.Enum):
    ACTIVO = "activo"
    FINALIZADO = "finalizado"
    SUSPENDIDO = "suspendido"


class Contrato(db.Model):
    __tablename__ = "contratos"

    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey("empleados.id"), nullable=False)
    empleado = db.relationship("Empleado", back_populates="contratos")

    tipo = db.Column(db.Enum(TipoContratoEnum), nullable=False, default=TipoContratoEnum.INDEFINIDO)
    estado = db.Column(db.Enum(EstadoContratoEnum), nullable=False, default=EstadoContratoEnum.ACTIVO)
    fecha_inicio = db.Column(db.Date, nullable=False, default=date.today)
    fecha_fin = db.Column(db.Date)  # NULL para indefinido
    salario = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    jornada_horas = db.Column(db.Integer, default=160)
    archivo = db.Column(db.String(255))  # PDF del contrato firmado
    observaciones = db.Column(db.Text)

    @property
    def esta_vigente(self):
        if self.estado != EstadoContratoEnum.ACTIVO:
            return False
        if self.fecha_fin and self.fecha_fin < date.today():
            return False
        return self.fecha_inicio <= date.today()

    def __repr__(self):
        return f"<Contrato {self.tipo.value} emp={self.empleado_id}>"
