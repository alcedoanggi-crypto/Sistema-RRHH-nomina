"""Cálculo automático de nómina.

Reglas simplificadas (ejemplo Ecuador). Ajusta los porcentajes y conceptos
según la legislación de tu país en config.py y aquí.
"""
from calendar import monthrange
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from flask import current_app
from app.extensions import db
from app.models import Nomina, DetalleNomina, Empleado, Asistencia, Permiso, EstadoSolicitudEnum


def _q(valor):
    return Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular_nomina(empleado: Empleado, anio: int, mes: int, bonos=None, commit=True) -> Nomina:
    """Genera (o regenera) la nómina de un empleado para un período.

    bonos: lista de dicts {"concepto": str, "monto": float}
    """
    bonos = bonos or []
    dias_mes = monthrange(anio, mes)[1]
    salario_base = Decimal(str(empleado.salario_actual))

    # --- Ausencias no remuneradas dentro del período ---
    inicio_periodo = date(anio, mes, 1)
    fin_periodo = date(anio, mes, dias_mes)
    dias_no_remunerados = 0
    for p in empleado.permisos:
        if p.estado != EstadoSolicitudEnum.APROBADO or p.es_remunerado:
            continue
        ini = max(p.fecha_inicio, inicio_periodo)
        fin = min(p.fecha_fin, fin_periodo)
        if ini <= fin:
            dias_no_remunerados += (fin - ini).days + 1

    dias_trabajados = max(dias_mes - dias_no_remunerados, 0)
    salario_proporcional = _q(salario_base / dias_mes * dias_trabajados)

    # --- INGRESOS ---
    ingresos = [{"concepto": "Sueldo", "monto": salario_proporcional}]

    # Bono por antigüedad (ejemplo: 2 % del sueldo por año, tope 20 %)
    factor_antig = min(Decimal(str(empleado.antiguedad_anios)) * Decimal("0.02"), Decimal("0.20"))
    if factor_antig > 0:
        ingresos.append({
            "concepto": "Bono antigüedad",
            "monto": _q(salario_proporcional * factor_antig),
        })

    for b in bonos:
        if b.get("monto"):
            ingresos.append({"concepto": b["concepto"], "monto": _q(b["monto"])})

    total_ingresos = _q(sum(i["monto"] for i in ingresos))

    # --- DEDUCCIONES ---
    aporte_iess_pct = Decimal(str(current_app.config["APORTE_IESS_PERSONAL"]))
    deducciones = [{
        "concepto": f"Aporte IESS ({aporte_iess_pct * 100:.2f} %)",
        "monto": _q(total_ingresos * aporte_iess_pct),
    }]

    if dias_no_remunerados:
        deducciones.append({
            "concepto": f"Descuento {dias_no_remunerados} día(s) permiso no remunerado",
            "monto": Decimal("0.00"),  # ya está descontado en el proporcional; informativo
        })

    total_deducciones = _q(sum(d["monto"] for d in deducciones))
    neto = _q(total_ingresos - total_deducciones)

    # --- Persistencia ---
    nomina = Nomina.query.filter_by(empleado_id=empleado.id, anio=anio, mes=mes).first()
    if nomina:
        for d in list(nomina.detalles):
            db.session.delete(d)
    else:
        nomina = Nomina(empleado_id=empleado.id, anio=anio, mes=mes)
        db.session.add(nomina)

    nomina.salario_base = salario_base
    nomina.dias_trabajados = dias_trabajados
    nomina.total_ingresos = total_ingresos
    nomina.total_deducciones = total_deducciones
    nomina.neto_pagar = neto
    nomina.estado = "generada"

    for i in ingresos:
        db.session.add(DetalleNomina(nomina=nomina, concepto=i["concepto"], tipo="ingreso", monto=i["monto"]))
    for d in deducciones:
        db.session.add(DetalleNomina(nomina=nomina, concepto=d["concepto"], tipo="deduccion", monto=d["monto"]))

    if commit:
        db.session.commit()
    return nomina


def generar_nomina_masiva(anio: int, mes: int) -> list[Nomina]:
    resultado = []
    empleados = Empleado.query.filter_by(activo=True).all()
    for emp in empleados:
        resultado.append(calcular_nomina(emp, anio, mes, commit=False))
    db.session.commit()
    return resultado
