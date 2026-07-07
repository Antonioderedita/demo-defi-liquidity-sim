import pytest
import core_math
import fee_estimator
import range_builder

class TestCoreMath:
    def test_liquidity_standard(self):
        """Testa il calcolo con parametri normali."""
        L = core_math.get_liquidity_for_capital(1000.0, 1600.0, 1500.0, 1700.0)
        assert L > 0

    def test_liquidity_zero_capital(self):
        """Un capitale nullo deve generare liquidità nulla."""
        L = core_math.get_liquidity_for_capital(0.0, 1600.0, 1500.0, 1700.0)
        assert L == 0.0

    def test_out_of_range_low(self):
        """
        Se il prezzo scende sotto il limite inferiore, l'LP resta con 100% WETH e 0 USDC.
        Questo verifica le equazioni di composizione del portafoglio.
        """
        L = core_math.get_liquidity_for_capital(1000.0, 1400.0, 1500.0, 1700.0)
        weth, usdc = core_math.get_amounts_for_liquidity(L, 1400.0, 1500.0, 1700.0)
        assert weth > 0
        assert usdc == 0.0

    def test_range_invertito(self):
        L = core_math.get_liquidity_for_capital(1000.0, 1600.0, 1700.0, 1500.0)
        assert L == 0.0

    def test_out_of_range_high(self):
        """Se il prezzo sale sopra il limite superiore, l'LP resta con 100% USDC e 0 WETH."""
        L = core_math.get_liquidity_for_capital(1000.0, 1800.0, 1500.0, 1700.0)
        weth, usdc = core_math.get_amounts_for_liquidity(L, 1800.0, 1500.0, 1700.0)
        assert weth == 0.0
        assert usdc > 0.0

    def test_impermanent_loss_zero(self):
        """Se il prezzo non si muove (p0 == p1), l'Impermanent Loss deve essere 0%."""
        L = core_math.get_liquidity_for_capital(1000.0, 1600.0, 1500.0, 1700.0)
        il_perc, _, _ = core_math.calculate_impermanent_loss(L, 1600.0, 1600.0, 1500.0, 1700.0)
        assert il_perc == 0.0


class TestFeeEstimator:
    def test_stima_rendimenti_zero_emissioni(self):
        """Se le emissioni sono a zero, l'algoritmo non deve calcolare ritorni."""
        fee, apr = fee_estimator.stima_rendimenti_cl(
            capitale=1000.0, live_price=1600.0, price_a=1500.0, price_b=1700.0, 
            apr_emissioni_base=0.0
        )
        assert fee == 0.0
        assert apr == 0.0

    def test_stima_rendimenti_range_invalido(self):
        """Se i limiti coincidono (spread = 0) o sono invertiti, restituisce zero."""
        fee, apr = fee_estimator.stima_rendimenti_cl(
            capitale=1000.0, live_price=1600.0, price_a=1600.0, price_b=1600.0, 
            apr_emissioni_base=25.0
        )
        assert fee == 0.0
        assert apr == 0.0

    def test_moltiplicatore_concentrazione(self):
        """
        Sostituisce il vecchio test sul TVL. Verifica che a parità di capitale ed emissioni base,
        un range più stretto generi un APR stimato maggiore (effetto concentrazione).
        """
        _, apr_largo = fee_estimator.stima_rendimenti_cl(
            capitale=1000.0, live_price=1600.0, price_a=1000.0, price_b=2200.0, apr_emissioni_base=25.0
        )
        _, apr_stretto = fee_estimator.stima_rendimenti_cl(
            capitale=1000.0, live_price=1600.0, price_a=1500.0, price_b=1700.0, apr_emissioni_base=25.0
        )
        assert apr_stretto > apr_largo

    def test_fee_zero_se_fuori_range(self):
        """Se il prezzo attuale è fuori dal range, le fee devono essere zero assoluto."""
        fee, apr = fee_estimator.stima_rendimenti_cl(
            capitale=1000.0, live_price=2000.0, price_a=1500.0, price_b=1700.0,
            apr_emissioni_base=25.0
        )
        assert fee == 0.0
        assert apr == 0.0


class TestRangeBuilder:
    def test_monotonicita_probabilita(self):
        """Allargando il range, la probabilità di sopravvivenza (no-touch) deve aumentare."""
        prob_stretta = range_builder.calcola_probabilita_no_touch(1600.0, 1590.0, 1610.0, 0.03, 7)
        prob_larga = range_builder.calcola_probabilita_no_touch(1600.0, 1500.0, 1700.0, 0.03, 7)
        assert prob_larga > prob_stretta

    def test_probabilita_fuori_range_iniziale(self):
        """Se il prezzo parte già fuori dal range, la probabilità di restarci dentro è 0."""
        prob = range_builder.calcola_probabilita_no_touch(1800.0, 1500.0, 1700.0, 0.03, 7)
        assert prob == 0.0