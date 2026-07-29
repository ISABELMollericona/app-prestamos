from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


def calcular_cuota_frances(monto, tasa_anual, plazo_meses):
    """
    Calcula cuota fija mensual - Método Francés
    Fórmula: C = P * [i(1+i)^n] / [(1+i)^n - 1]
    """
    if monto <= 0 or plazo_meses <= 0:
        return Decimal('0.00')

    i = tasa_anual / Decimal('12') / Decimal('100')

    if i == 0:
        cuota = monto / plazo_meses
        return cuota.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    factor = (1 + i) ** plazo_meses
    cuota = monto * (i * factor) / (factor - 1)
    return cuota.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def generar_tabla_frances(monto, tasa_anual, plazo_meses, fecha_desembolso=None):
    """
    Genera tabla de amortización completa - Método Francés
    Retorna lista de dicts con cada cuota
    """
    if monto <= 0 or plazo_meses <= 0:
        return [], Decimal('0.00')

    if fecha_desembolso is None:
        fecha_desembolso = date.today()

    i = tasa_anual / Decimal('12') / Decimal('100')
    cuota_fija = calcular_cuota_frances(monto, tasa_anual, plazo_meses)
    saldo = monto
    tabla = []

    for num in range(1, plazo_meses + 1):
        interes = (saldo * i).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        if num == plazo_meses:
            amortizacion = saldo
            cuota = amortizacion + interes
        else:
            amortizacion = cuota_fija - interes
            cuota = cuota_fija

        saldo_final = saldo - amortizacion
        if saldo_final < Decimal('0.01'):
            saldo_final = Decimal('0.00')

        fecha_venc = fecha_desembolso + relativedelta(months=num)

        seguro_desgravamen = (saldo * Decimal('0.0003')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_cuota = cuota + seguro_desgravamen

        tabla.append({
            'numero': num,
            'fecha_vencimiento': fecha_venc,
            'saldo_inicial': saldo,
            'monto_cuota': cuota,
            'interes': interes,
            'amortizacion': amortizacion,
            'saldo_final': saldo_final,
            'seguro_desgravamen': seguro_desgravamen,
            'total_cuota': total_cuota,
            'estado': 'pendiente'
        })

        saldo = saldo_final

    return tabla, cuota_fija


def generar_tabla_aleman(monto, tasa_anual, plazo_meses, fecha_desembolso=None):
    """
    Genera tabla de amortización - Método Alemán (amortización constante)
    """
    if monto <= 0 or plazo_meses <= 0:
        return []

    if fecha_desembolso is None:
        fecha_desembolso = date.today()

    i = tasa_anual / Decimal('12') / Decimal('100')
    amortizacion_fija = (monto / plazo_meses).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    saldo = monto
    tabla = []

    for num in range(1, plazo_meses + 1):
        if num == plazo_meses:
            amortizacion = saldo
        else:
            amortizacion = amortizacion_fija

        interes = (saldo * i).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        cuota = amortizacion + interes
        saldo_final = saldo - amortizacion

        if saldo_final < Decimal('0.01'):
            saldo_final = Decimal('0.00')

        fecha_venc = fecha_desembolso + relativedelta(months=num)

        seguro_desgravamen = (saldo * Decimal('0.0003')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_cuota = cuota + seguro_desgravamen

        tabla.append({
            'numero': num,
            'fecha_vencimiento': fecha_venc,
            'saldo_inicial': saldo,
            'monto_cuota': cuota,
            'interes': interes,
            'amortizacion': amortizacion,
            'saldo_final': saldo_final,
            'seguro_desgravamen': seguro_desgravamen,
            'total_cuota': total_cuota,
            'estado': 'pendiente'
        })

        saldo = saldo_final

    return tabla


def generar_tabla_americano(monto, tasa_anual, plazo_meses, fecha_desembolso=None):
    """
    Genera tabla de amortizacion - Metodo Americano (solo intereses)
    El deudor paga solo intereses cada periodo y el capital total al vencimiento
    """
    if monto <= 0 or plazo_meses <= 0:
        return [], Decimal('0.00')

    if fecha_desembolso is None:
        fecha_desembolso = date.today()

    i = tasa_anual / Decimal('12') / Decimal('100')
    interes_mensual = (monto * i).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    saldo = monto
    tabla = []

    for num in range(1, plazo_meses + 1):
        if num == plazo_meses:
            amortizacion = saldo
            cuota = interes_mensual + saldo
        else:
            amortizacion = Decimal('0.00')
            cuota = interes_mensual

        interes = interes_mensual if num < plazo_meses else (saldo * i).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        saldo_final = saldo - amortizacion
        if saldo_final < Decimal('0.01'):
            saldo_final = Decimal('0.00')

        fecha_venc = fecha_desembolso + relativedelta(months=num)

        seguro_desgravamen = (saldo * Decimal('0.0003')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_cuota = cuota + seguro_desgravamen

        tabla.append({
            'numero': num,
            'fecha_vencimiento': fecha_venc,
            'saldo_inicial': saldo,
            'monto_cuota': cuota,
            'interes': interes,
            'amortizacion': amortizacion,
            'saldo_final': saldo_final,
            'seguro_desgravamen': seguro_desgravamen,
            'total_cuota': total_cuota,
            'estado': 'pendiente'
        })

        saldo = saldo_final

    return tabla, interes_mensual


def calcular_mora(monto_cuota, dias_atraso, tasa_mora_diaria=Decimal('0.005')):
    """Calcula mora por días de atraso (0.5% diario sobre la cuota)"""
    if dias_atraso <= 0 or monto_cuota <= 0:
        return Decimal('0.00')
    mora = monto_cuota * tasa_mora_diaria * dias_atraso
    return mora.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def recalcular_plan_pagos(prestamo, monto_amortizado, database, fecha_recalculo=None):
    """
    Recalcula el plan de pagos tras una amortizacion extraordinaria.
    Elimina las cuotas pendientes y genera nuevas desde el saldo restante.
    """
    if fecha_recalculo is None:
        fecha_recalculo = date.today()

    from app.models import Amortizacion
    cuotas_pendientes = Amortizacion.query.filter_by(
        prestamo_id=prestamo.id, estado='pendiente'
    ).order_by(Amortizacion.numero_cuota).all()

    if not cuotas_pendientes:
        return False

    saldo_actual = cuotas_pendientes[0].saldo_inicial
    nuevo_saldo = saldo_actual - Decimal(str(monto_amortizado))
    if nuevo_saldo < 0:
        nuevo_saldo = Decimal('0.00')

    plazo_restante = len(cuotas_pendientes)
    tasa = prestamo.tasa_interes_valor or Decimal('0.03')
    tipo = prestamo.tipo_tasa or 'mensual'
    if tipo == 'anual':
        tasa_decimal = Decimal(str(tasa)) * Decimal('100')
    elif tipo == 'mensual':
        tasa_decimal = Decimal(str(tasa)) * Decimal('100') * Decimal('12')
    elif tipo == 'diaria':
        tasa_decimal = Decimal(str(tasa)) * Decimal('100') * Decimal('365')
    else:
        tasa_decimal = Decimal(str(tasa)) * Decimal('100') * Decimal('12')

    for cuota in cuotas_pendientes:
        database.session.delete(cuota)

    if prestamo.metodo_amortizacion == 'frances':
        nuevas_cuotas, cuota = generar_tabla_frances(
            nuevo_saldo, tasa_decimal, plazo_restante, fecha_recalculo
        )
    elif prestamo.metodo_amortizacion == 'americano':
        nuevas_cuotas, cuota = generar_tabla_americano(
            nuevo_saldo, tasa_decimal, plazo_restante, fecha_recalculo
        )
    else:
        nuevas_cuotas = generar_tabla_aleman(
            nuevo_saldo, tasa_decimal, plazo_restante, fecha_recalculo
        )
        cuota = nuevas_cuotas[0]['monto_cuota'] if nuevas_cuotas else Decimal('0')

    for item in nuevas_cuotas:
        am = Amortizacion(
            prestamo_id=prestamo.id,
            numero_cuota=item['numero'],
            fecha_vencimiento=item['fecha_vencimiento'],
            saldo_inicial=item['saldo_inicial'],
            monto_cuota=item['monto_cuota'],
            interes=item['interes'],
            amortizacion=item['amortizacion'],
            saldo_final=item['saldo_final'],
            seguro_desgravamen=item['seguro_desgravamen'],
            total_cuota=item['total_cuota'],
            estado='pendiente'
        )
        database.session.add(am)

    prestamo.monto_cuota = cuota
    prestamo.saldo_pendiente = nuevo_saldo
    prestamo.total_interes = sum(a['interes'] for a in nuevas_cuotas)
    prestamo.total_a_pagar = sum(a['total_cuota'] for a in nuevas_cuotas)
    if nuevas_cuotas:
        prestamo.fecha_vencimiento = nuevas_cuotas[-1]['fecha_vencimiento']

    return True


def proyectar_prestamo(monto, tasa_anual, plazo_meses):
    """Proyección rápida de préstamo para cotizaciones"""
    if monto <= 0 or plazo_meses <= 0:
        return {
            'monto': monto,
            'tasa_anual': tasa_anual,
            'plazo_meses': plazo_meses,
            'cuota_mensual': Decimal('0.00'),
            'total_interes': Decimal('0.00'),
            'total_pagar': Decimal('0.00')
        }

    cuota = calcular_cuota_frances(monto, tasa_anual, plazo_meses)
    total_pagar = cuota * plazo_meses
    total_interes = total_pagar - monto

    return {
        'monto': monto,
        'tasa_anual': tasa_anual,
        'plazo_meses': plazo_meses,
        'cuota_mensual': cuota,
        'total_interes': total_interes,
        'total_pagar': total_pagar
    }
