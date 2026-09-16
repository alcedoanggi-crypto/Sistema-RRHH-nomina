from datetime import datetime, date

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models import (
    Permiso, Empleado, RolEnum, TipoPermisoEnum, EstadoSolicitudEnum,
)
from app.utils.decorators import jefe_o_admin_required, admin_rrhh_required
from app.utils.files import save_upload

permiso_bp = Blueprint("permiso", __name__, url_prefix="/permisos")


@permiso_bp.route("/")
@login_required
def index():
    estado = request.args.get("estado")
    query = Permiso.query

    if current_user.rol == RolEnum.EMPLEADO:
        query = query.filter_by(empleado_id=current_user.empleado_id or -1)
    elif current_user.rol == RolEnum.JEFE_AREA:
        # Ve las de su departamento
        emp = current_user.empleado
        ids = [e.id for e in emp.departamento.empleados] if emp and emp.departamento else []
        query = query.filter(Permiso.empleado_id.in_(ids or [-1]))

    if estado:
        query = query.filter_by(estado=EstadoSolicitudEnum(estado))

    solicitudes = query.order_by(Permiso.solicitado_en.desc()).all()
    return render_template(
        "permisos/index.html", solicitudes=solicitudes,
        tipos=list(TipoPermisoEnum), estados=list(EstadoSolicitudEnum), estado_sel=estado,
    )


@permiso_bp.route("/nueva", methods=["GET", "POST"])
@login_required
def crear():
    if not current_user.empleado_id:
        flash("Tu usuario no está vinculado a un empleado.", "warning")
        return redirect(url_for("permiso.index"))

    if request.method == "POST":
        ini = datetime.strptime(request.form["fecha_inicio"], "%Y-%m-%d").date()
        fin = datetime.strptime(request.form["fecha_fin"], "%Y-%m-%d").date()
        if fin < ini:
            flash("La fecha fin no puede ser anterior a la de inicio.", "danger")
            return redirect(url_for("permiso.crear"))

        p = Permiso(
            empleado_id=current_user.empleado_id,
            tipo=TipoPermisoEnum(request.form["tipo"]),
            fecha_inicio=ini,
            fecha_fin=fin,
            motivo=request.form["motivo"].strip(),
        )
        adjunto = request.files.get("adjunto")
        if adjunto and adjunto.filename:
            p.adjunto = save_upload(adjunto, "permisos")

        db.session.add(p)
        db.session.commit()
        flash("Solicitud enviada. Queda pendiente de aprobación.", "success")
        return redirect(url_for("permiso.index"))

    return render_template("permisos/form.html", tipos=list(TipoPermisoEnum))


@permiso_bp.route("/<int:id>")
@login_required
def detalle(id):
    p = db.get_or_404(Permiso, id)
    return render_template("permisos/detalle.html", p=p)


@permiso_bp.route("/<int:id>/aprobar", methods=["POST"])
@login_required
@jefe_o_admin_required
def aprobar(id):
    p = db.get_or_404(Permiso, id)
    comentario = request.form.get("comentario", "")

    if current_user.rol == RolEnum.JEFE_AREA:
        if p.estado != EstadoSolicitudEnum.PENDIENTE:
            flash("Esta solicitud ya fue procesada.", "info")
        else:
            p.estado = EstadoSolicitudEnum.APROBADO_JEFE
            p.aprobado_jefe_id = current_user.empleado_id
            p.comentario_aprobacion = comentario
            flash("Aprobada por jefatura. Pasa a RRHH para aprobación final.", "success")
    else:  # ADMIN_RRHH: aprobación final
        p.estado = EstadoSolicitudEnum.APROBADO
        p.aprobado_rrhh_id = current_user.id
        p.comentario_aprobacion = comentario or p.comentario_aprobacion
        p.resuelto_en = datetime.utcnow()
        flash("Solicitud aprobada definitivamente.", "success")

    db.session.commit()
    return redirect(url_for("permiso.detalle", id=p.id))


@permiso_bp.route("/<int:id>/rechazar", methods=["POST"])
@login_required
@jefe_o_admin_required
def rechazar(id):
    p = db.get_or_404(Permiso, id)
    p.estado = EstadoSolicitudEnum.RECHAZADO
    p.comentario_aprobacion = request.form.get("comentario", "")
    p.resuelto_en = datetime.utcnow()
    if current_user.rol == RolEnum.JEFE_AREA:
        p.aprobado_jefe_id = current_user.empleado_id
    else:
        p.aprobado_rrhh_id = current_user.id
    db.session.commit()
    flash("Solicitud rechazada.", "info")
    return redirect(url_for("permiso.detalle", id=p.id))


@permiso_bp.route("/<int:id>/cancelar", methods=["POST"])
@login_required
def cancelar(id):
    p = db.get_or_404(Permiso, id)
    if p.empleado_id != current_user.empleado_id and current_user.rol != RolEnum.ADMIN_RRHH:
        abort(403)
    if p.estado in (EstadoSolicitudEnum.APROBADO, EstadoSolicitudEnum.RECHAZADO):
        flash("No se puede cancelar una solicitud ya resuelta.", "warning")
    else:
        p.estado = EstadoSolicitudEnum.CANCELADO
        db.session.commit()
        flash("Solicitud cancelada.", "info")
    return redirect(url_for("permiso.index"))
