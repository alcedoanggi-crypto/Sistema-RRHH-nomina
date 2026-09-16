from datetime import date

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, Response, abort
)
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Nomina, Empleado, RolEnum
from app.services.nomina_service import calcular_nomina, generar_nomina_masiva
from app.services.pdf_service import recibo_pago_pdf
from app.utils.decorators import admin_rrhh_required

nomina_bp = Blueprint("nomina", __name__, url_prefix="/nomina")


@nomina_bp.route("/")
@login_required
def index():
    hoy = date.today()
    anio = request.args.get("anio", hoy.year, type=int)
    mes = request.args.get("mes", hoy.month, type=int)

    query = Nomina.query.filter_by(anio=anio, mes=mes)
    if current_user.rol == RolEnum.EMPLEADO:
        query = query.filter_by(empleado_id=current_user.empleado_id or -1)

    nominas = query.join(Empleado).order_by(Empleado.apellidos).all()
    totales = {
        "ingresos": sum(float(n.total_ingresos) for n in nominas),
        "deducciones": sum(float(n.total_deducciones) for n in nominas),
        "neto": sum(float(n.neto_pagar) for n in nominas),
    }
    return render_template(
        "nomina/index.html", nominas=nominas, anio=anio, mes=mes, totales=totales
    )


@nomina_bp.route("/generar", methods=["POST"])
@login_required
@admin_rrhh_required
def generar():
    anio = request.form.get("anio", type=int)
    mes = request.form.get("mes", type=int)
    empleado_id = request.form.get("empleado_id", type=int)

    if empleado_id:
        emp = db.get_or_404(Empleado, empleado_id)
        bonos = []
        if request.form.get("bono_monto", type=float):
            bonos.append({
                "concepto": request.form.get("bono_concepto") or "Bono",
                "monto": request.form.get("bono_monto", type=float),
            })
        calcular_nomina(emp, anio, mes, bonos=bonos)
        flash(f"Nómina de {emp.nombre_completo} generada.", "success")
    else:
        res = generar_nomina_masiva(anio, mes)
        flash(f"Nómina generada para {len(res)} empleados.", "success")

    return redirect(url_for("nomina.index", anio=anio, mes=mes))


@nomina_bp.route("/nueva")
@login_required
@admin_rrhh_required
def form():
    hoy = date.today()
    return render_template(
        "nomina/form.html",
        empleados=Empleado.query.filter_by(activo=True).order_by(Empleado.apellidos).all(),
        anio=hoy.year, mes=hoy.month,
    )


@nomina_bp.route("/<int:id>")
@login_required
def detalle(id):
    n = db.get_or_404(Nomina, id)
    if current_user.rol == RolEnum.EMPLEADO and n.empleado_id != current_user.empleado_id:
        abort(403)
    return render_template("nomina/detalle.html", n=n)


@nomina_bp.route("/<int:id>/pagar", methods=["POST"])
@login_required
@admin_rrhh_required
def marcar_pagada(id):
    from datetime import datetime
    n = db.get_or_404(Nomina, id)
    n.estado = "pagada"
    n.pagada_en = datetime.utcnow()
    db.session.commit()
    flash("Nómina marcada como pagada.", "success")
    return redirect(url_for("nomina.detalle", id=n.id))


@nomina_bp.route("/<int:id>/recibo.pdf")
@login_required
def recibo(id):
    n = db.get_or_404(Nomina, id)
    if current_user.rol == RolEnum.EMPLEADO and n.empleado_id != current_user.empleado_id:
        abort(403)
    pdf = recibo_pago_pdf(n)
    filename = f"recibo_{n.empleado.cedula}_{n.anio}_{n.mes:02d}.pdf"
    return Response(
        pdf, mimetype="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )
