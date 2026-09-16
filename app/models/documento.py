from datetime import datetime
from app.extensions import db


class Documento(db.Model):
    __tablename__ = "documentos"

    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey("empleados.id"), nullable=False)
    empleado = db.relationship("Empleado", back_populates="documentos")

    nombre = db.Column(db.String(150), nullable=False)
    tipo = db.Column(db.String(50))  # contrato, certificado, cedula, titulo, otro
    archivo = db.Column(db.String(255), nullable=False)  # ruta en static/uploads
    subido_en = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Documento {self.nombre} emp={self.empleado_id}>"
