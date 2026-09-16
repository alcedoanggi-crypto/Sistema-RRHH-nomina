from datetime import date, datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Evaluacion, Empleado, RolEnum
from app.utils.decorators import jefe_o_admin_required

evaluacion_bp = Blueprint("evaluacion", __name__, url_prefix="/evaluaciones")


@evaluacion_bp.route("/")
@login_required
def index():
    query = Evaluacion.query
    if current_user.rol == RolEnum.EMPLEADO:
        query = query.filter_by(empleado_id=current_user.empleado_id or -1)
    elif current_user.rol == RolEnum.JEFE_AREA:
        emp = current_user.empleado
        ids = [e.id for e in emp.departamento.empleados] if emp and emp.departamento else []
        query = query.filter(Evaluacion.empleado_id.in_(ids or [-1]))

    evaluaciones = query.order_by(Evaluacion.fecha.desc()).all()
    return render_template("evaluaciones/index.html", evaluaciones=evaluaciones)


@evaluacion_bp.route("/nueva", methods=["GET", "POST"])
@login_required
@jefe_o_admin_required
def crear():
    if request.method == "POST":
        ev = Evaluacion(
            empleado_id=request.form.get("empleado_id", type=int),
            evaluador_id=current_user.empleado_id,
            periodo=request.form["periodo"].strip(),
            fecha=date.today(),
            productividad=request.form.get("productividad", 3, type=int),
            calidad_trabajo=request.form.get("calidad_trabajo", 3, type=int),
            trabajo_equipo=request.form.get("trabajo_equipo", 3, type=int),
            puntualidad=request.form.get("puntualidad", 3, type=int),
            iniciativa=request.form.get("iniciativa", 3, type=int),
            fortalezas=request.form.get("fortalezas"),
            areas_mejora=request.form.get("areas_mejora"),
        )
        db.session.add(ev)
        db.session.commit()
        flash("Evaluación registrada.", "success")
        return redirect(url_for("evaluacion.detalle", id=ev.id))

    empleados = Empleado.query.filter_by(activo=True).order_by(Empleado.apellidos)
    if current_user.rol == RolEnum.JEFE_AREA and current_user.empleado and current_user.empleado.departamento:
        empleados = empleados.filter_by(departamento_id=current_user.empleado.departamento_id)
    return render_template(
        "evaluaciones/form.html",
        empleados=empleados.all(),
        criterios=Evaluacion.CRITERIOS,
    )


@evaluacion_bp.route("/<int:id>")
@login_required
def detalle(id):
    ev = db.get_or_404(Evaluacion, id)
    if current_user.rol == RolEnum.EMPLEADO and ev.empleado_id != current_user.empleado_id:
        abort(403)
    return render_template("evaluaciones/detalle.html", ev=ev)


@evaluacion_bp.route("/<int:id>/comentar", methods=["POST"])
@login_required
def comentar(id):
    ev = db.get_or_404(Evaluacion, id)
    if ev.empleado_id != current_user.empleado_id:
        abort(403)
    ev.comentario_empleado = request.form.get("comentario_empleado", "").strip()
    db.session.commit()
    flash("Comentario guardado.", "success")
    return redirect(url_for("evaluacion.detalle", id=ev.id))
