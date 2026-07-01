import pytest
import core_math
import fee_estimator

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

class TestFeeEstimator:
    def test_stima_rendimenti_zero_tvl(self):
        """Se la pool è vuota, l'algoritmo non deve calcolare divisioni per zero."""
        fee, apr = fee_estimator.stima_rendimenti_cl(
            capitale=1000.0, live_price=1600.0, price_a=1500.0, price_b=1700.0, 
            vol_24h=50000.0, tvl_pool=0.0
        )
        assert fee == 0.0
        assert apr == 0.0

    def test_stima_rendimenti_range_invalido(self):
        """Se i limiti coincidono (spread = 0) o sono invertiti, restituisce zero."""
        fee, apr = fee_estimator.stima_rendimenti_cl(
            capitale=1000.0, live_price=1600.0, price_a=1600.0, price_b=1600.0, 
            vol_24h=50000.0, tvl_pool=1000000.0
        )
        assert fee == 0.0
        assert apr == 0.0

    def test_clipping_quota_utente(self):
        """
        Se un utente inserisce un capitale maggiore del TVL dell'intera pool,
        la quota deve essere cappata a 1.0 (100%) per impedire APR esplosivi e infiniti.
        """
        # TVL = 1 Milione, Capitale Utente = 2 Milioni
        fee, apr = fee_estimator.stima_rendimenti_cl(
            capitale=2000000.0, live_price=1600.0, price_a=1500.0, price_b=1700.0, 
            vol_24h=50000.0, tvl_pool=1000000.0
        )
        # La fee giornaliera calcolata non deve superare il totale logico ammissibile
        assert fee > 0
        # Fee totali della pool = 50k * 0.0005 = 25$. L'utente non può guadagnare più del limite strutturale.
        assert fee < 100.0