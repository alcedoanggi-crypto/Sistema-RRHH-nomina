from app.extensions import db


class Cargo(db.Model):
    __tablename__ = "cargos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.String(255))
    salario_base = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    departamento_id = db.Column(db.Integer, db.ForeignKey("departamentos.id"), nullable=False)
    departamento = db.relationship("Departamento", back_populates="cargos")

    empleados = db.relationship("Empleado", back_populates="cargo")

    __table_args__ = (
        db.UniqueConstraint("nombre", "departamento_id", name="uq_cargo_departamento"),
    )

    def __repr__(self):
        return f"<Cargo {self.nombre}>"
