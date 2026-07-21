from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch


class TestActualizarMora:
    def test_actualiza_cuotas_vencidas(self, db, prestamo_activo, amortizaciones):
        from app.scheduler import actualizar_mora
        with patch('app.scheduler.date') as mock_date:
            futuro = date.today() + timedelta(days=10)
            mock_date.today.return_value = futuro
            actualizar_mora()
        from app.models import Amortizacion
        cuotas = Amortizacion.query.filter_by(prestamo_id=prestamo_activo.id).all()
        for c in cuotas:
            if c.fecha_vencimiento < futuro:
                assert c.dias_atraso > 0

    def test_sin_cuotas_vencidas(self, db, prestamo_activo, amortizaciones):
        from app.scheduler import actualizar_mora
        with patch('app.scheduler.date') as mock_date:
            mock_date.today.return_value = prestamo_activo.fecha_desembolso.date()
            actualizar_mora()
        from app.models import Amortizacion
        cuotas = Amortizacion.query.filter_by(prestamo_id=prestamo_activo.id).all()
        for c in cuotas:
            assert c.dias_atraso == 0
            assert c.mora == Decimal('0.00')


class TestGenerarRecordatorios:
    def test_genera_recordatorio_cuota_proxima(self, db, prestamo_activo, amortizaciones):
        from app.scheduler import generar_recordatorios
        from app.models import Notificacion

        Notificacion.query.delete()
        db.session.commit()

        with patch('app.scheduler.date') as mock_date:
            mock_date.today.return_value = amortizaciones[0].fecha_vencimiento - timedelta(days=3)
            generar_recordatorios()

        notifs = Notificacion.query.filter_by(tipo='recordatorio').all()
        for n in notifs:
            assert 'Recordatorio' in n.mensaje

    def test_sin_cuotas_proximas(self, db, prestamo_activo, amortizaciones):
        from app.scheduler import generar_recordatorios
        from app.models import Notificacion

        Notificacion.query.delete()
        db.session.commit()

        with patch('app.scheduler.date') as mock_date:
            mock_date.today.return_value = date(2020, 1, 1)
            generar_recordatorios()

        notifs = Notificacion.query.filter_by(tipo='recordatorio').all()
        assert len(notifs) == 0


class TestCastigarPrestamosMora:
    def test_castiga_prestamo_mora_extrema(self, db, prestamo_activo, amortizaciones):
        from app.scheduler import castigar_prestamos_mora
        from app.models import Amortizacion, Prestamo

        real_today = date.today()
        fecha_pasada = real_today - timedelta(days=45)

        Amortizacion.query.filter_by(prestamo_id=prestamo_activo.id).update({
            'fecha_vencimiento': fecha_pasada,
            'estado': 'pendiente'
        })
        db.session.commit()

        with patch('app.scheduler.date') as mock_date:
            mock_date.today.return_value = real_today
            castigar_prestamos_mora()

        p = Prestamo.query.get(prestamo_activo.id)
        assert p.estado == 'castigado'

    def test_no_castiga_sin_mora(self, db, prestamo_activo, amortizaciones):
        from app.scheduler import castigar_prestamos_mora
        from app.models import Prestamo

        castigar_prestamos_mora()
        p = Prestamo.query.get(prestamo_activo.id)
        assert p.estado == 'activo'
