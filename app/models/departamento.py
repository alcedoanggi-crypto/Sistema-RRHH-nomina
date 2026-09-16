from app.extensions import db


class Departamento(db.Model):
    __tablename__ = "departamentos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), unique=True, nullable=False)
    descripcion = db.Column(db.String(255))

    # Jefe del departamento (autorreferencia a empleados)
    jefe_id = db.Column(db.Integer, db.ForeignKey("empleados.id"))
    jefe = db.relationship("Empleado", foreign_keys=[jefe_id])

    empleados = db.relationship(
        "Empleado",
        back_populates="departamento",
        foreign_keys="Empleado.departamento_id",
    )
    cargos = db.relationship("Cargo", back_populates="departamento")

    @property
    def total_empleados(self):
        return len([e for e in self.empleados if e.activo])

    def __repr__(self):
        return f"<Departamento {self.nombre}>"
