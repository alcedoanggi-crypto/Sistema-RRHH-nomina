from datetime import date, timedelta
from calendar import monthrange

from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, extract

from app.extensions import db
from app.models import (
    Empleado, Departamento, Nomina, Permiso, Asistencia,
    EstadoSolicitudEnum,
)

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def index():
    hoy = date.today()

    total_activos = Empleado.query.filter_by(activo=True).count()
    solicitudes_pendientes = Permiso.query.filter(
        Permiso.estado.in_([EstadoSolicitudEnum.PENDIENTE, EstadoSolicitudEnum.APROBADO_JEFE])
    ).count()

    nomina_mes = db.session.query(func.coalesce(func.sum(Nomina.neto_pagar), 0)).filter(
        Nomina.anio == hoy.year, Nomina.mes == hoy.month
    ).scalar()

    # Ausentismo del mes: días 'ausente' / días laborables registrados
    ausencias = Asistencia.query.filter(
        extract("year", Asistencia.fecha) == hoy.year,
        extract("month", Asistencia.fecha) == hoy.month,
        Asistencia.estado == "ausente",
    ).count()

    # Empleados destacados
    cumpleanieros = [e for e in Empleado.query.filter_by(activo=True).all() if e.cumple_este_mes]
    aniversarios = [
        e for e in Empleado.query.filter_by(activo=True).all()
        if e.fecha_ingreso.month == hoy.month and e.fecha_ingreso.year < hoy.year
    ]

    kpis = {
        "nomina_total": float(nomina_mes or 0),
        "empleados_activos": total_activos,
        "solicitudes_pendientes": solicitudes_pendientes,
        "ausencias_mes": ausencias,
    }

    permisos_recientes = (
        Permiso.query.order_by(Permiso.solicitado_en.desc()).limit(6).all()
    )

    return render_template(
        "dashboard/index.html",
        kpis=kpis,
        cumpleanieros=cumpleanieros,
        aniversarios=aniversarios,
        permisos_recientes=permisos_recientes,
    )


# ---------- Endpoints JSON para los gráficos ----------

@dashboard_bp.route("/api/chart/empleados-por-departamento")
@login_required
def chart_empleados_departamento():
    filas = (
        db.session.query(Departamento.nombre, func.count(Empleado.id))
        .outerjoin(Empleado, (Empleado.departamento_id == Departamento.id) & (Empleado.activo.is_(True)))
        .group_by(Departamento.nombre)
        .order_by(Departamento.nombre)
        .all()
    )
    return jsonify(labels=[f[0] for f in filas], data=[f[1] for f in filas])


@dashboard_bp.route("/api/chart/nomina-mensual")
@login_required
def chart_nomina_mensual():
    hoy = date.today()
    labels, data = [], []
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    for i in range(11, -1, -1):
        anio = hoy.year if hoy.month - i > 0 else hoy.year - 1
        mes = (hoy.month - i - 1) % 12 + 1
        total = db.session.query(func.coalesce(func.sum(Nomina.neto_pagar), 0)).filter(
            Nomina.anio == anio, Nomina.mes == mes
        ).scalar()
        labels.append(f"{meses[mes - 1]} {str(anio)[2:]}")
        data.append(float(total or 0))
    return jsonify(labels=labels, data=data)


@dashboard_bp.route("/api/chart/rotacion")
@login_required
def chart_rotacion():
    """Rotación de personal: ingresos vs. salidas por mes (últimos 6 meses)."""
    hoy = date.today()
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    labels, ingresos, salidas = [], [], []
    for i in range(5, -1, -1):
        anio = hoy.year if hoy.month - i > 0 else hoy.year - 1
        mes = (hoy.month - i - 1) % 12 + 1
        ini = date(anio, mes, 1)
        fin = date(anio, mes, monthrange(anio, mes)[1])
        ingresos.append(Empleado.query.filter(Empleado.fecha_ingreso.between(ini, fin)).count())
        salidas.append(Empleado.query.filter(Empleado.fecha_salida.between(ini, fin)).count())
        labels.append(f"{meses[mes - 1]} {str(anio)[2:]}")
    return jsonify(labels=labels, ingresos=ingresos, salidas=salidas)


@dashboard_bp.route("/api/chart/ausentismo")
@login_required
def chart_ausentismo():
    hoy = date.today()
    filas = (
        db.session.query(Departamento.nombre, func.count(Asistencia.id))
        .select_from(Asistencia)
        .join(Empleado, Empleado.id == Asistencia.empleado_id)
        .join(Departamento, Departamento.id == Empleado.departamento_id)
        .filter(
            Asistencia.estado.in_(["ausente", "tardanza"]),
            extract("year", Asistencia.fecha) == hoy.year,
        )
        .group_by(Departamento.nombre)
        .all()
    )
    return jsonify(labels=[f[0] for f in filas], data=[f[1] for f in filas])
