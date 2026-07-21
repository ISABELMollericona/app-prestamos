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


def calcular_mora(monto_cuota, dias_atraso, tasa_mora_diaria=Decimal('0.005')):
    """Calcula mora por días de atraso (0.5% diario sobre la cuota)"""
    if dias_atraso <= 0 or monto_cuota <= 0:
        return Decimal('0.00')
    mora = monto_cuota * tasa_mora_diaria * dias_atraso
    return mora.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


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
