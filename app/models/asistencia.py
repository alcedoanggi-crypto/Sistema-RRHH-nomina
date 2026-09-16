from datetime import date, datetime
from app.extensions import db


class Asistencia(db.Model):
    __tablename__ = "asistencias"

    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey("empleados.id"), nullable=False)
    empleado = db.relationship("Empleado", back_populates="asistencias")

    fecha = db.Column(db.Date, nullable=False, default=date.today, index=True)
    hora_entrada = db.Column(db.DateTime)
    hora_salida = db.Column(db.DateTime)
    observacion = db.Column(db.String(255))
    # estado calculado: presente, tardanza, ausente, permiso
    estado = db.Column(db.String(20), default="presente")

    __table_args__ = (
        db.UniqueConstraint("empleado_id", "fecha", name="uq_asistencia_empleado_fecha"),
    )

    HORA_LIMITE_ENTRADA = 8  # 08:00; después es tardanza

    @property
    def horas_trabajadas(self):
        if self.hora_entrada and self.hora_salida:
            delta = self.hora_salida - self.hora_entrada
            return round(delta.total_seconds() / 3600, 2)
        return 0.0

    def calcular_estado(self):
        if not self.hora_entrada:
            self.estado = "ausente"
        elif self.hora_entrada.hour >= self.HORA_LIMITE_ENTRADA and self.hora_entrada.minute > 0:
            self.estado = "tardanza"
        elif self.hora_entrada.hour > self.HORA_LIMITE_ENTRADA:
            self.estado = "tardanza"
        else:
            self.estado = "presente"
        return self.estado

    def __repr__(self):
        return f"<Asistencia emp={self.empleado_id} {self.fecha}>"
