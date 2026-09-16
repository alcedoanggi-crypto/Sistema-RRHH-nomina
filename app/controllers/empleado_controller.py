from datetime import datetime, date

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, abort
)
from flask_login import login_required, current_user

from app.extensions import db
from app.models import (
    Empleado, Departamento, Cargo, Contrato, Documento, Usuario, RolEnum,
    TipoContratoEnum, EstadoContratoEnum,
)
from app.utils.decorators import admin_rrhh_required
from app.utils.files import save_upload

empleado_bp = Blueprint("empleado", __name__, url_prefix="/empleados")


def _puede_ver(empleado):
    if current_user.rol in (RolEnum.ADMIN_RRHH, RolEnum.JEFE_AREA):
        return True
    return current_user.empleado_id == empleado.id


@empleado_bp.route("/")
@login_required
def listar():
    q = request.args.get("q", "").strip()
    depto_id = request.args.get("departamento", type=int)
    query = Empleado.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(Empleado.nombres.ilike(like), Empleado.apellidos.ilike(like),
                   Empleado.cedula.ilike(like))
        )
    if depto_id:
        query = query.filter_by(departamento_id=depto_id)

    if current_user.rol == RolEnum.EMPLEADO:
        query = query.filter_by(id=current_user.empleado_id or -1)

    empleados = query.order_by(Empleado.apellidos).all()
    departamentos = Departamento.query.order_by(Departamento.nombre).all()
    return render_template(
        "empleados/listar.html", empleados=empleados, departamentos=departamentos, q=q
    )


@empleado_bp.route("/<int:id>")
@login_required
def detalle(id):
    empleado = db.get_or_404(Empleado, id)
    if not _puede_ver(empleado):
        abort(403)
    return render_template("empleados/detalle.html", empleado=empleado)


@empleado_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@admin_rrhh_required
def crear():
    if request.method == "POST":
        emp = Empleado(
            cedula=request.form["cedula"].strip(),
            nombres=request.form["nombres"].strip(),
            apellidos=request.form["apellidos"].strip(),
            email=request.form.get("email"),
            telefono=request.form.get("telefono"),
            direccion=request.form.get("direccion"),
            genero=request.form.get("genero"),
            fecha_nacimiento=_parse_date(request.form.get("fecha_nacimiento")),
            fecha_ingreso=_parse_date(request.form.get("fecha_ingreso")) or date.today(),
            departamento_id=request.form.get("departamento_id", type=int),
            cargo_id=request.form.get("cargo_id", type=int),
        )
        foto = request.files.get("foto")
        if foto and foto.filename:
            emp.foto = save_upload(foto, "fotos")

        db.session.add(emp)
        db.session.flush()

        # Usuario asociado opcional
        if request.form.get("crear_usuario"):
            u = Usuario(
                username=request.form["username"].strip(),
                email=request.form.get("email") or f"{emp.cedula}@empresa.local",
                rol=RolEnum(request.form.get("rol", RolEnum.EMPLEADO.value)),
                empleado_id=emp.id,
            )
            u.set_password(request.form.get("password") or emp.cedula)
            db.session.add(u)

        db.session.commit()
        flash("Empleado creado correctamente.", "success")
        return redirect(url_for("empleado.detalle", id=emp.id))

    return render_template(
        "empleados/form.html",
        empleado=None,
        departamentos=Departamento.query.order_by(Departamento.nombre).all(),
        cargos=Cargo.query.order_by(Cargo.nombre).all(),
        roles=list(RolEnum),
    )


@empleado_bp.route("/<int:id>/editar", methods=["GET", "POST"])
@login_required
@admin_rrhh_required
def editar(id):
    emp = db.get_or_404(Empleado, id)
    if request.method == "POST":
        emp.nombres = request.form["nombres"].strip()
        emp.apellidos = request.form["apellidos"].strip()
        emp.email = request.form.get("email")
        emp.telefono = request.form.get("telefono")
        emp.direccion = request.form.get("direccion")
        emp.genero = request.form.get("genero")
        emp.fecha_nacimiento = _parse_date(request.form.get("fecha_nacimiento"))
        emp.departamento_id = request.form.get("departamento_id", type=int)
        emp.cargo_id = request.form.get("cargo_id", type=int)

        salida = _parse_date(request.form.get("fecha_salida"))
        emp.fecha_salida = salida
        emp.activo = salida is None

        foto = request.files.get("foto")
        if foto and foto.filename:
            emp.foto = save_upload(foto, "fotos")

        db.session.commit()
        flash("Datos actualizados.", "success")
        return redirect(url_for("empleado.detalle", id=emp.id))

    return render_template(
        "empleados/form.html",
        empleado=emp,
        departamentos=Departamento.query.order_by(Departamento.nombre).all(),
        cargos=Cargo.query.order_by(Cargo.nombre).all(),
        roles=list(RolEnum),
    )


# ---------- Contratos ----------

@empleado_bp.route("/<int:id>/contratos/nuevo", methods=["POST"])
@login_required
@admin_rrhh_required
def agregar_contrato(id):
    emp = db.get_or_404(Empleado, id)
    contrato = Contrato(
        empleado_id=emp.id,
        tipo=TipoContratoEnum(request.form.get("tipo", TipoContratoEnum.INDEFINIDO.value)),
        fecha_inicio=_parse_date(request.form.get("fecha_inicio")) or date.today(),
        fecha_fin=_parse_date(request.form.get("fecha_fin")),
        salario=request.form.get("salario", type=float) or 0,
        jornada_horas=request.form.get("jornada_horas", type=int) or 160,
        observaciones=request.form.get("observaciones"),
    )
    archivo = request.files.get("archivo")
    if archivo and archivo.filename:
        contrato.archivo = save_upload(archivo, "contratos")
    db.session.add(contrato)
    db.session.commit()
    flash("Contrato registrado.", "success")
    return redirect(url_for("empleado.detalle", id=emp.id))


# ---------- Documentos ----------

@empleado_bp.route("/<int:id>/documentos/nuevo", methods=["POST"])
@login_required
@admin_rrhh_required
def agregar_documento(id):
    emp = db.get_or_404(Empleado, id)
    archivo = request.files.get("archivo")
    if not archivo or not archivo.filename:
        flash("Selecciona un archivo.", "warning")
        return redirect(url_for("empleado.detalle", id=emp.id))
    doc = Documento(
        empleado_id=emp.id,
        nombre=request.form.get("nombre") or archivo.filename,
        tipo=request.form.get("tipo", "otro"),
        archivo=save_upload(archivo, "documentos"),
    )
    db.session.add(doc)
    db.session.commit()
    flash("Documento subido.", "success")
    return redirect(url_for("empleado.detalle", id=emp.id))


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None
