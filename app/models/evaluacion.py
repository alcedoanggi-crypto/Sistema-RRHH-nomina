from datetime import date, datetime
from app.extensions import db


class Evaluacion(db.Model):
    __tablename__ = "evaluaciones"

    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey("empleados.id"), nullable=False)
    empleado = db.relationship("Empleado", back_populates="evaluaciones", foreign_keys=[empleado_id])

    evaluador_id = db.Column(db.Integer, db.ForeignKey("empleados.id"))
    evaluador = db.relationship("Empleado", foreign_keys=[evaluador_id])

    periodo = db.Column(db.String(30), nullable=False)  # p.ej. "2026-S1"
    fecha = db.Column(db.Date, default=date.today, nullable=False)

    # Criterios 1-5
    productividad = db.Column(db.Integer, default=3)
    calidad_trabajo = db.Column(db.Integer, default=3)
    trabajo_equipo = db.Column(db.Integer, default=3)
    puntualidad = db.Column(db.Integer, default=3)
    iniciativa = db.Column(db.Integer, default=3)

    fortalezas = db.Column(db.Text)
    areas_mejora = db.Column(db.Text)
    comentario_empleado = db.Column(db.Text)

    creada_en = db.Column(db.DateTime, default=datetime.utcnow)

    CRITERIOS = ["productividad", "calidad_trabajo", "trabajo_equipo", "puntualidad", "iniciativa"]

    @property
    def puntaje_total(self):
        vals = [getattr(self, c) or 0 for c in self.CRITERIOS]
        return round(sum(vals) / len(vals), 2)

    @property
    def calificacion(self):
        p = self.puntaje_total
        if p >= 4.5:
            return "Excelente"
        if p >= 3.5:
            return "Muy bueno"
        if p >= 2.5:
            return "Satisfactorio"
        if p >= 1.5:
            return "Necesita mejorar"
        return "Deficiente"

    def __repr__(self):
        return f"<Evaluacion emp={self.empleado_id} {self.periodo}>"
