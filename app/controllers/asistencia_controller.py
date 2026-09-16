from datetime import date, datetime
from calendar import monthrange

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import extract

from app.extensions import db
from app.models import Asistencia, Empleado, RolEnum
from app.utils.decorators import jefe_o_admin_required

asistencia_bp = Blueprint("asistencia", __name__, url_prefix="/asistencias")


@asistencia_bp.route("/")
@login_required
def index():
    hoy = date.today()
    mi_asistencia = None
    if current_user.empleado_id:
        mi_asistencia = Asistencia.query.filter_by(
            empleado_id=current_user.empleado_id, fecha=hoy
        ).first()

    anio = request.args.get("anio", hoy.year, type=int)
    mes = request.args.get("mes", hoy.month, type=int)

    query = Asistencia.query.filter(
        extract("year", Asistencia.fecha) == anio,
        extract("month", Asistencia.fecha) == mes,
    )
    if current_user.rol == RolEnum.EMPLEADO:
        query = query.filter_by(empleado_id=current_user.empleado_id or -1)

    registros = query.order_by(Asistencia.fecha.desc()).all()

    resumen = {"presente": 0, "tardanza": 0, "ausente": 0}
    for r in registros:
        resumen[r.estado] = resumen.get(r.estado, 0) + 1

    return render_template(
        "asistencias/index.html",
        registros=registros, mi_asistencia=mi_asistencia,
        anio=anio, mes=mes, resumen=resumen, hoy=hoy,
    )


@asistencia_bp.route("/marcar", methods=["POST"])
@login_required
def marcar():
    if not current_user.empleado_id:
        flash("Tu usuario no está vinculado a un empleado.", "warning")
        return redirect(url_for("asistencia.index"))

    hoy = date.today()
    ahora = datetime.now()
    registro = Asistencia.query.filter_by(
        empleado_id=current_user.empleado_id, fecha=hoy
    ).first()

    if registro is None:
        registro = Asistencia(empleado_id=current_user.empleado_id, fecha=hoy, hora_entrada=ahora)
        registro.calcular_estado()
        db.session.add(registro)
        flash(f"Entrada registrada a las {ahora.strftime('%H:%M')}.", "success")
    elif registro.hora_salida is None:
        registro.hora_salida = ahora
        flash(f"Salida registrada a las {ahora.strftime('%H:%M')}. "
              f"Horas: {registro.horas_trabajadas}.", "success")
    else:
        flash("Ya registraste entrada y salida hoy.", "info")

    db.session.commit()
    return redirect(url_for("asistencia.index"))


@asistencia_bp.route("/manual", methods=["POST"])
@login_required
@jefe_o_admin_required
def registro_manual():
    empleado_id = request.form.get("empleado_id", type=int)
    fecha = datetime.strptime(request.form["fecha"], "%Y-%m-%d").date()
    registro = Asistencia.query.filter_by(empleado_id=empleado_id, fecha=fecha).first()
    if registro is None:
        registro = Asistencia(empleado_id=empleado_id, fecha=fecha)
        db.session.add(registro)

    entrada = request.form.get("hora_entrada")
    salida = request.form.get("hora_salida")
    if entrada:
        registro.hora_entrada = datetime.combine(fecha, datetime.strptime(entrada, "%H:%M").time())
    if salida:
        registro.hora_salida = datetime.combine(fecha, datetime.strptime(salida, "%H:%M").time())
    registro.observacion = request.form.get("observacion")
    registro.estado = request.form.get("estado") or registro.calcular_estado()

    db.session.commit()
    flash("Registro de asistencia guardado.", "success")
    return redirect(url_for("asistencia.index"))


@asistencia_bp.route("/reporte")
@login_required
@jefe_o_admin_required
def reporte():
    hoy = date.today()
    anio = request.args.get("anio", hoy.year, type=int)
    mes = request.args.get("mes", hoy.month, type=int)
    dias_mes = monthrange(anio, mes)[1]

    empleados = Empleado.query.filter_by(activo=True).order_by(Empleado.apellidos).all()
    data = []
    for e in empleados:
        regs = Asistencia.query.filter(
            Asistencia.empleado_id == e.id,
            extract("year", Asistencia.fecha) == anio,
            extract("month", Asistencia.fecha) == mes,
        ).all()
        presentes = sum(1 for r in regs if r.estado == "presente")
        tardanzas = sum(1 for r in regs if r.estado == "tardanza")
        ausentes = sum(1 for r in regs if r.estado == "ausente")
        horas = round(sum(r.horas_trabajadas for r in regs), 1)
        data.append({
            "empleado": e, "presentes": presentes, "tardanzas": tardanzas,
            "ausentes": ausentes, "horas": horas,
            "pct_asistencia": round(presentes / dias_mes * 100, 1) if dias_mes else 0,
        })

    return render_template("asistencias/reporte.html", data=data, anio=anio, mes=mes)
