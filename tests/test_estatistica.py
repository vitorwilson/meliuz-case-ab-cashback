import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from estatistica import (
    _beta_regularizada,
    ic_bootstrap_diferenca,
    ic_bootstrap_media,
    t_pareado_pvalor,
    welch_pvalor,
)


class BetaRegularizadaTest(unittest.TestCase):
    def test_beta_1_1_eh_identidade(self):
        self.assertAlmostEqual(_beta_regularizada(1, 1, 0.3), 0.3)
        self.assertAlmostEqual(_beta_regularizada(1, 1, 0.7), 0.7)

    def test_beta_simetrica_no_meio(self):
        self.assertAlmostEqual(_beta_regularizada(2, 2, 0.5), 0.5)

    def test_extremos(self):
        self.assertEqual(_beta_regularizada(2, 2, 0.0), 0.0)
        self.assertEqual(_beta_regularizada(2, 2, 1.0), 1.0)


class WelchTest(unittest.TestCase):
    def test_valor_conhecido_t1_gl8(self):
        # t = 1,0 com 8 graus de liberdade -> p bicaudal ≈ 0,3466
        x = [10, 12, 14, 16, 18]
        y = [8, 10, 12, 14, 16]
        self.assertAlmostEqual(welch_pvalor(x, y), 0.3466, places=3)

    def test_amostras_distantes_significativo(self):
        x = [20, 22, 24, 26, 28]
        y = [8, 10, 12, 14, 16]
        self.assertLess(welch_pvalor(x, y), 0.001)

    def test_series_identicas_constantes(self):
        self.assertEqual(welch_pvalor([5.0] * 10, [5.0] * 10), 1.0)

    def test_series_constantes_diferentes(self):
        self.assertEqual(welch_pvalor([5.0] * 10, [7.0] * 10), 0.0)

    def test_amostra_minima_nao_quebra(self):
        self.assertEqual(welch_pvalor([1.0], [2.0, 3.0]), 1.0)


class TPareadoTest(unittest.TestCase):
    def test_valor_conhecido(self):
        # diferenças [1..5]: t = 4,243 com 4 graus de liberdade -> 0,01 < p < 0,02
        p = t_pareado_pvalor([1, 2, 3, 4, 5])
        self.assertGreater(p, 0.01)
        self.assertLess(p, 0.02)

    def test_diferencas_constantes_positivas(self):
        self.assertEqual(t_pareado_pvalor([2.0] * 10), 0.0)

    def test_diferencas_constantes_nulas(self):
        self.assertEqual(t_pareado_pvalor([0.0] * 10), 1.0)

    def test_amostra_minima_nao_quebra(self):
        self.assertEqual(t_pareado_pvalor([3.0]), 1.0)


class BootstrapMediaTest(unittest.TestCase):
    def test_ic_contem_media_real(self):
        valores = [100 + i % 7 for i in range(30)]
        baixo, alto = ic_bootstrap_media(valores)
        self.assertLessEqual(baixo, 103)
        self.assertLessEqual(103, alto)

    def test_deterministico_com_seed_fixa(self):
        valores = [100 + i % 7 for i in range(30)]
        self.assertEqual(ic_bootstrap_media(valores), ic_bootstrap_media(valores))


class BootstrapTest(unittest.TestCase):
    def test_ic_contem_diferenca_real(self):
        x = [100 + i % 7 for i in range(30)]
        y = [80 + i % 5 for i in range(30)]
        baixo, alto = ic_bootstrap_diferenca(x, y)
        diferenca = 103 - 82
        self.assertLessEqual(baixo, diferenca)
        self.assertLessEqual(diferenca, alto)

    def test_ic_exclui_zero_quando_separado(self):
        x = [100 + i % 7 for i in range(30)]
        y = [10 + i % 5 for i in range(30)]
        baixo, _ = ic_bootstrap_diferenca(x, y)
        self.assertGreater(baixo, 0)

    def test_deterministico_com_seed_fixa(self):
        x = [100 + i % 7 for i in range(30)]
        y = [80 + i % 5 for i in range(30)]
        self.assertEqual(ic_bootstrap_diferenca(x, y), ic_bootstrap_diferenca(x, y))


if __name__ == "__main__":
    unittest.main()
