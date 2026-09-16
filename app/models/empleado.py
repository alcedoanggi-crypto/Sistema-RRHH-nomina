from datetime import date, datetime
from app.extensions import db


class Empleado(db.Model):
    __tablename__ = "empleados"

    id = db.Column(db.Integer, primary_key=True)
    cedula = db.Column(db.String(20), unique=True, nullable=False, index=True)
    nombres = db.Column(db.String(120), nullable=False)
    apellidos = db.Column(db.String(120), nullable=False)
    fecha_nacimiento = db.Column(db.Date)
    genero = db.Column(db.String(20))
    telefono = db.Column(db.String(30))
    email = db.Column(db.String(120))
    direccion = db.Column(db.String(255))
    foto = db.Column(db.String(255))  # ruta relativa dentro de static/uploads

    fecha_ingreso = db.Column(db.Date, default=date.today, nullable=False)
    fecha_salida = db.Column(db.Date)  # NULL => activo
    activo = db.Column(db.Boolean, default=True, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    departamento_id = db.Column(db.Integer, db.ForeignKey("departamentos.id"))
    departamento = db.relationship(
        "Departamento", back_populates="empleados", foreign_keys=[departamento_id]
    )

    cargo_id = db.Column(db.Integer, db.ForeignKey("cargos.id"))
    cargo = db.relationship("Cargo", back_populates="empleados")

    usuario = db.relationship("Usuario", back_populates="empleado", uselist=False)
    contratos = db.relationship(
        "Contrato", back_populates="empleado", cascade="all, delete-orphan",
        order_by="Contrato.fecha_inicio.desc()",
    )
    asistencias = db.relationship(
        "Asistencia", back_populates="empleado", cascade="all, delete-orphan"
    )
    permisos = db.relationship(
        "Permiso", back_populates="empleado", cascade="all, delete-orphan",
        foreign_keys="Permiso.empleado_id",
    )
    nominas = db.relationship(
        "Nomina", back_populates="empleado", cascade="all, delete-orphan"
    )
    evaluaciones = db.relationship(
        "Evaluacion", back_populates="empleado", cascade="all, delete-orphan",
        foreign_keys="Evaluacion.empleado_id",
    )
    documentos = db.relationship(
        "Documento", back_populates="empleado", cascade="all, delete-orphan"
    )

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def contrato_vigente(self):
        for c in self.contratos:
            if c.esta_vigente:
                return c
        return None

    @property
    def salario_actual(self):
        c = self.contrato_vigente
        if c and c.salario:
            return float(c.salario)
        if self.cargo and self.cargo.salario_base:
            return float(self.cargo.salario_base)
        return 0.0

    @property
    def antiguedad_anios(self):
        fin = self.fecha_salida or date.today()
        return round((fin - self.fecha_ingreso).days / 365.25, 1)

    @property
    def cumple_este_mes(self):
        return bool(self.fecha_nacimiento) and self.fecha_nacimiento.month == date.today().month

    def __repr__(self):
        return f"<Empleado {self.nombre_completo}>"
