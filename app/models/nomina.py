from datetime import datetime
from app.extensions import db


class Nomina(db.Model):
    __tablename__ = "nominas"

    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey("empleados.id"), nullable=False)
    empleado = db.relationship("Empleado", back_populates="nominas")

    anio = db.Column(db.Integer, nullable=False)
    mes = db.Column(db.Integer, nullable=False)  # 1-12

    salario_base = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    dias_trabajados = db.Column(db.Integer, default=30)
    total_ingresos = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total_deducciones = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    neto_pagar = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    estado = db.Column(db.String(20), default="generada")  # generada, pagada, anulada
    generada_en = db.Column(db.DateTime, default=datetime.utcnow)
    pagada_en = db.Column(db.DateTime)

    detalles = db.relationship(
        "DetalleNomina", back_populates="nomina", cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.UniqueConstraint("empleado_id", "anio", "mes", name="uq_nomina_periodo"),
    )

    @property
    def periodo(self):
        meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        return f"{meses[self.mes]} {self.anio}"

    @property
    def ingresos(self):
        return [d for d in self.detalles if d.tipo == "ingreso"]

    @property
    def deducciones(self):
        return [d for d in self.detalles if d.tipo == "deduccion"]

    def __repr__(self):
        return f"<Nomina emp={self.empleado_id} {self.mes}/{self.anio}>"


class DetalleNomina(db.Model):
    __tablename__ = "detalle_nomina"

    id = db.Column(db.Integer, primary_key=True)
    nomina_id = db.Column(db.Integer, db.ForeignKey("nominas.id"), nullable=False)
    nomina = db.relationship("Nomina", back_populates="detalles")

    concepto = db.Column(db.String(120), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # ingreso | deduccion
    monto = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    def __repr__(self):
        return f"<DetalleNomina {self.concepto} {self.tipo} {self.monto}>"
