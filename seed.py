"""Crea las tablas y carga datos de demostración.

Uso:
    python seed.py            # crea tablas + datos demo
    python seed.py --reset    # BORRA todo y vuelve a cargar
"""
import sys
import random
from datetime import date, datetime, timedelta

from app import create_app
from app.extensions import db
from app.models import (
    Usuario, RolEnum, Departamento, Cargo, Empleado, Contrato,
    TipoContratoEnum, Asistencia, Permiso, TipoPermisoEnum, EstadoSolicitudEnum,
    Evaluacion,
)
from app.services.nomina_service import generar_nomina_masiva

app = create_app("development")

NOMBRES = ["Andrea", "Carlos", "María", "José", "Lucía", "Diego", "Valentina", "Fernando",
           "Camila", "Roberto", "Paula", "Andrés", "Daniela", "Miguel", "Sofía", "Javier"]
APELLIDOS = ["García", "Rodríguez", "Martínez", "López", "Pérez", "Gómez", "Sánchez",
             "Ramírez", "Torres", "Flores", "Vásquez", "Castro", "Ortiz", "Núñez"]


def run(reset=False):
    with app.app_context():
        if reset:
            db.drop_all()
        db.create_all()

        if Usuario.query.first():
            print("La base ya tiene datos. Usa --reset para recargar.")
            return

        # ----- Departamentos -----
        deptos_data = [
            ("Recursos Humanos", "Gestión del talento humano"),
            ("Tecnología", "Desarrollo y soporte de sistemas"),
            ("Finanzas", "Contabilidad y tesorería"),
            ("Operaciones", "Producción y logística"),
            ("Comercial", "Ventas y atención al cliente"),
        ]
        deptos = []
        for nombre, desc in deptos_data:
            d = Departamento(nombre=nombre, descripcion=desc)
            db.session.add(d)
            deptos.append(d)
        db.session.flush()

        # ----- Cargos -----
        cargos_data = {
            "Recursos Humanos": [("Analista de RRHH", 1100), ("Jefe de RRHH", 2200)],
            "Tecnología": [("Desarrollador", 1600), ("Soporte técnico", 1000), ("Líder de TI", 2600)],
            "Finanzas": [("Contador", 1400), ("Asistente contable", 950), ("Jefe Financiero", 2800)],
            "Operaciones": [("Operario", 700), ("Supervisor de planta", 1500)],
            "Comercial": [("Ejecutivo de ventas", 900), ("Gerente Comercial", 2700)],
        }
        cargos = {}
        for d in deptos:
            for nombre, salario in cargos_data[d.nombre]:
                c = Cargo(nombre=nombre, salario_base=salario, departamento_id=d.id)
                db.session.add(c)
                cargos[(d.nombre, nombre)] = c
        db.session.flush()

        # ----- Empleados -----
        empleados = []
        usados = set()
        for i in range(24):
            nom = random.choice(NOMBRES)
            ape = f"{random.choice(APELLIDOS)} {random.choice(APELLIDOS)}"
            ced = f"17{random.randint(10000000, 99999999)}"
            while ced in usados:
                ced = f"17{random.randint(10000000, 99999999)}"
            usados.add(ced)
            depto = random.choice(deptos)
            cargo = random.choice([c for (dn, _), c in cargos.items() if dn == depto.nombre])
            ingreso = date.today() - timedelta(days=random.randint(30, 2200))
            nac = date(random.randint(1975, 2001), random.randint(1, 12), random.randint(1, 28))
            e = Empleado(
                cedula=ced, nombres=nom, apellidos=ape, fecha_nacimiento=nac,
                genero=random.choice(["Masculino", "Femenino"]),
                telefono=f"09{random.randint(10000000, 99999999)}",
                email=f"{nom.lower()}.{ape.split()[0].lower()}@empresa.com",
                direccion="Av. Principal y calle secundaria",
                fecha_ingreso=ingreso, departamento_id=depto.id, cargo_id=cargo.id,
            )
            db.session.add(e)
            empleados.append(e)
        db.session.flush()

        # Ajustar algunos cumpleaños/aniversarios al mes actual para el dashboard
        hoy = date.today()
        for e in empleados[:3]:
            e.fecha_nacimiento = e.fecha_nacimiento.replace(month=hoy.month)
        for e in empleados[3:6]:
            e.fecha_ingreso = date(hoy.year - random.randint(1, 5), hoy.month, random.randint(1, 28))

        # Bajas (para rotación)
        for e in empleados[-2:]:
            e.fecha_salida = hoy - timedelta(days=random.randint(5, 90))
            e.activo = False

        # ----- Contratos -----
        for e in empleados:
            db.session.add(Contrato(
                empleado_id=e.id,
                tipo=random.choice(list(TipoContratoEnum)),
                fecha_inicio=e.fecha_ingreso,
                salario=e.cargo.salario_base,
                jornada_horas=160,
            ))

        # ----- Jefes de departamento + usuarios -----
        for d in deptos:
            candidatos = [e for e in empleados if e.departamento_id == d.id and e.activo]
            if candidatos:
                d.jefe_id = candidatos[0].id

        # Usuario admin RRHH
        admin_emp = next(e for e in empleados if e.departamento.nombre == "Recursos Humanos" and e.activo)
        admin = Usuario(username="admin", email="admin@empresa.com", rol=RolEnum.ADMIN_RRHH,
                        empleado_id=admin_emp.id)
        admin.set_password("admin123")
        db.session.add(admin)

        # Un jefe de área
        jefe_emp = deptos[1].jefe_id
        jefe = Usuario(username="jefe", email="jefe@empresa.com", rol=RolEnum.JEFE_AREA,
                       empleado_id=jefe_emp)
        jefe.set_password("jefe123")
        db.session.add(jefe)

        # Un empleado normal
        emp_emp = next(e for e in empleados if e.activo and e.id not in (admin_emp.id, jefe_emp))
        empu = Usuario(username="empleado", email="empleado@empresa.com", rol=RolEnum.EMPLEADO,
                       empleado_id=emp_emp.id)
        empu.set_password("empleado123")
        db.session.add(empu)

        # ----- Asistencias (últimos 40 días hábiles) -----
        for e in [x for x in empleados if x.activo]:
            for delta in range(40):
                f = hoy - timedelta(days=delta)
                if f.weekday() >= 5:
                    continue
                r = random.random()
                if r < 0.05:
                    a = Asistencia(empleado_id=e.id, fecha=f, estado="ausente")
                else:
                    hora_in = 8 if r > 0.15 else 9
                    entrada = datetime.combine(f, datetime.min.time()).replace(hour=hora_in, minute=random.randint(0, 30))
                    salida = entrada + timedelta(hours=8, minutes=random.randint(0, 40))
                    a = Asistencia(empleado_id=e.id, fecha=f, hora_entrada=entrada, hora_salida=salida)
                    a.calcular_estado()
                db.session.add(a)

        # ----- Permisos -----
        for e in random.sample([x for x in empleados if x.activo], 8):
            ini = hoy - timedelta(days=random.randint(-10, 30))
            p = Permiso(
                empleado_id=e.id,
                tipo=random.choice(list(TipoPermisoEnum)),
                fecha_inicio=ini, fecha_fin=ini + timedelta(days=random.randint(1, 5)),
                motivo="Solicitud de ejemplo generada automáticamente.",
                estado=random.choice(list(EstadoSolicitudEnum)),
            )
            db.session.add(p)

        # ----- Evaluaciones -----
        for e in random.sample([x for x in empleados if x.activo], 12):
            db.session.add(Evaluacion(
                empleado_id=e.id, evaluador_id=e.departamento.jefe_id,
                periodo=f"{hoy.year}-S1",
                productividad=random.randint(2, 5), calidad_trabajo=random.randint(2, 5),
                trabajo_equipo=random.randint(3, 5), puntualidad=random.randint(2, 5),
                iniciativa=random.randint(2, 5),
                fortalezas="Compromiso y buena actitud.", areas_mejora="Gestión del tiempo.",
            ))

        db.session.commit()

        # ----- Nómina de los 3 últimos meses -----
        for i in range(3):
            m = hoy.month - i
            y = hoy.year
            if m <= 0:
                m += 12
                y -= 1
            generar_nomina_masiva(y, m)

        print("=" * 50)
        print(" Datos de demostración cargados correctamente")
        print("=" * 50)
        print(" Usuarios:")
        print("   admin     / admin123      (Administrador RRHH)")
        print("   jefe      / jefe123       (Jefe de Área)")
        print("   empleado  / empleado123   (Empleado)")
        print("=" * 50)


if __name__ == "__main__":
    run(reset="--reset" in sys.argv)
