from decimal import Decimal
from datetime import date
from app.amortization import (
    calcular_cuota_frances,
    generar_tabla_frances,
    generar_tabla_aleman,
    calcular_mora,
    proyectar_prestamo,
)


class TestCalcularCuotaFrances:
    def test_cuota_normal(self):
        cuota = calcular_cuota_frances(Decimal('1000'), Decimal('36'), 12)
        assert cuota == Decimal('100.46')

    def test_cuota_monto_cero(self):
        cuota = calcular_cuota_frances(Decimal('0'), Decimal('36'), 12)
        assert cuota == Decimal('0.00')

    def test_cuota_plazo_cero(self):
        cuota = calcular_cuota_frances(Decimal('1000'), Decimal('36'), 0)
        assert cuota == Decimal('0.00')

    def test_cuota_tasa_cero(self):
        cuota = calcular_cuota_frances(Decimal('1200'), Decimal('0'), 12)
        assert cuota == Decimal('100.00')

    def test_cuota_monto_negativo(self):
        cuota = calcular_cuota_frances(Decimal('-500'), Decimal('36'), 12)
        assert cuota == Decimal('0.00')

    def test_cuota_plazo_grande(self):
        cuota = calcular_cuota_frances(Decimal('50000'), Decimal('24'), 60)
        assert cuota > Decimal('0')


class TestGenerarTablaFrances:
    def test_tabla_completa(self):
        tabla, cuota = generar_tabla_frances(Decimal('1000'), Decimal('36'), 6)
        assert len(tabla) == 6
        assert cuota == Decimal('184.60')

    def test_ultima_cuota_cierra_saldo(self):
        tabla, cuota = generar_tabla_frances(Decimal('1000'), Decimal('36'), 6)
        assert tabla[-1]['saldo_final'] == Decimal('0.00')

    def test_suma_amortizaciones_igual_monto(self):
        tabla, _ = generar_tabla_frances(Decimal('1000'), Decimal('36'), 6)
        total_amort = sum(item['amortizacion'] for item in tabla)
        assert total_amort == Decimal('1000.00')

    def test_interes_decreciente(self):
        tabla, _ = generar_tabla_frances(Decimal('1000'), Decimal('36'), 6)
        intereses = [item['interes'] for item in tabla]
        assert intereses[0] > intereses[-1]

    def test_monto_cero(self):
        tabla, cuota = generar_tabla_frances(Decimal('0'), Decimal('36'), 6)
        assert tabla == []
        assert cuota == Decimal('0.00')

    def test_fecha_desembolso_personalizada(self):
        fecha = date(2026, 1, 15)
        tabla, _ = generar_tabla_frances(Decimal('1000'), Decimal('36'), 3, fecha)
        assert tabla[0]['fecha_vencimiento'] == date(2026, 2, 15)
        assert tabla[1]['fecha_vencimiento'] == date(2026, 3, 15)
        assert tabla[2]['fecha_vencimiento'] == date(2026, 4, 15)


class TestGenerarTablaAleman:
    def test_tabla_completa(self):
        tabla = generar_tabla_aleman(Decimal('1000'), Decimal('36'), 6)
        assert len(tabla) == 6

    def test_amortizacion_constante(self):
        tabla = generar_tabla_aleman(Decimal('1000'), Decimal('36'), 6)
        amortizaciones = [item['amortizacion'] for item in tabla[:-1]]
        for am in amortizaciones:
            assert am == Decimal('166.67')

    def test_ultima_cuota_ajusta_saldo(self):
        tabla = generar_tabla_aleman(Decimal('1000'), Decimal('36'), 6)
        assert tabla[-1]['saldo_final'] == Decimal('0.00')

    def test_monto_cero(self):
        tabla = generar_tabla_aleman(Decimal('0'), Decimal('36'), 6)
        assert tabla == []


class TestCalcularMora:
    def test_mora_normal(self):
        mora = calcular_mora(Decimal('100.00'), 5)
        assert mora == Decimal('2.50')

    def test_mora_sin_dias(self):
        mora = calcular_mora(Decimal('100.00'), 0)
        assert mora == Decimal('0.00')

    def test_mora_dias_negativos(self):
        mora = calcular_mora(Decimal('100.00'), -3)
        assert mora == Decimal('0.00')

    def test_mora_monto_cero(self):
        mora = calcular_mora(Decimal('0'), 10)
        assert mora == Decimal('0.00')

    def test_mora_tasa_personalizada(self):
        mora = calcular_mora(Decimal('200.00'), 10, Decimal('0.001'))
        assert mora == Decimal('2.00')


class TestProyectarPrestamo:
    def test_proyeccion_normal(self):
        res = proyectar_prestamo(Decimal('1000'), Decimal('36'), 12)
        assert res['monto'] == Decimal('1000')
        assert res['cuota_mensual'] == Decimal('100.46')
        assert res['total_pagar'] > Decimal('1000')
        assert res['total_interes'] == res['total_pagar'] - res['monto']

    def test_proyeccion_monto_cero(self):
        res = proyectar_prestamo(Decimal('0'), Decimal('36'), 12)
        assert res['cuota_mensual'] == Decimal('0.00')

    def test_proyeccion_plazo_cero(self):
        res = proyectar_prestamo(Decimal('1000'), Decimal('36'), 0)
        assert res['cuota_mensual'] == Decimal('0.00')
