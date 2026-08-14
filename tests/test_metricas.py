import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from leitura_csv import Observacao
from metricas import (
    MetricasGrupo,
    alertas_margem_nao_positiva,
    alertas_outliers_liquido,
    alertas_taxa_instavel,
    calcular_metricas,
    resumir_grupos,
)


def obs(dia: int, grupo: str, comissao: float, cashback: float, vendas: float) -> Observacao:
    return Observacao(
        data=date(2011, 1, 1) + timedelta(days=dia),
        grupo=grupo,
        parceiro="Parceiro X",
        compradores=10,
        comissao=comissao,
        cashback=cashback,
        vendas=vendas,
    )


class CalcularMetricasTest(unittest.TestCase):
    def setUp(self):
        self.obs = [
            obs(0, "Grupo 1", comissao=1000, cashback=400, vendas=10000),
            obs(1, "Grupo 1", comissao=2000, cashback=800, vendas=20000),
        ]

    def test_agregados(self):
        m = calcular_metricas("Grupo 1", self.obs)
        self.assertEqual(m.dias, 2)
        self.assertEqual(m.compradores_dia, 10)
        self.assertEqual(m.gmv_dia, 15000)
        self.assertEqual(m.liquido_dia, 900)  # (600 + 1200) / 2

    def test_taxas_e_margem(self):
        m = calcular_metricas("Grupo 1", self.obs)
        self.assertAlmostEqual(m.taxa_cashback, 1200 / 30000)
        self.assertAlmostEqual(m.taxa_comissao, 3000 / 30000)
        self.assertAlmostEqual(m.margem, 1800 / 3000)

    def test_serie_liquido_diaria(self):
        m = calcular_metricas("Grupo 1", self.obs)
        self.assertEqual(
            m.serie_liquido,
            ((date(2011, 1, 1), 600), (date(2011, 1, 2), 1200)),
        )

    def test_resumir_ordena_por_grupo(self):
        observacoes = self.obs + [obs(0, "Grupo 2", 500, 100, 5000)]
        grupos = [m.grupo for m in resumir_grupos(observacoes)]
        self.assertEqual(grupos, ["Grupo 1", "Grupo 2"])


class AlertasTaxaInstavelTest(unittest.TestCase):
    def test_taxa_constante_sem_alerta(self):
        observacoes = [obs(d, "Grupo 1", 1100, 400, 10000) for d in range(10)]
        self.assertEqual(alertas_taxa_instavel(observacoes), [])

    def test_taxa_variavel_gera_alerta(self):
        # taxas diárias alternando entre 3% e 10% do GMV
        observacoes = [
            obs(d, "Grupo 1", 1100, 300 if d % 2 == 0 else 1000, 10000)
            for d in range(10)
        ]
        alertas = alertas_taxa_instavel(observacoes)
        self.assertEqual(len(alertas), 1)
        self.assertIn("instável", alertas[0])


class AlertasOutliersTest(unittest.TestCase):
    def test_sem_outliers(self):
        observacoes = [obs(d, "Grupo 1", 1000 + d, 400, 10000) for d in range(10)]
        self.assertEqual(alertas_outliers_liquido(observacoes), [])

    def test_outlier_em_um_grupo(self):
        observacoes = [obs(d, "Grupo 1", 1000, 400, 10000) for d in range(10)]
        observacoes += [obs(d, "Grupo 2", 1000, 400, 10000) for d in range(10)]
        observacoes.append(obs(10, "Grupo 1", 50000, 400, 100000))
        alertas = alertas_outliers_liquido(observacoes)
        self.assertEqual(len(alertas), 1)
        self.assertIn("Grupo 1", alertas[0])

    def test_outlier_em_todos_os_grupos_vira_evento_externo(self):
        observacoes = [obs(d, "Grupo 1", 1000, 400, 10000) for d in range(10)]
        observacoes += [obs(d, "Grupo 2", 2000, 800, 20000) for d in range(10)]
        observacoes.append(obs(10, "Grupo 1", 50000, 400, 100000))
        observacoes.append(obs(10, "Grupo 2", 90000, 800, 200000))
        alertas = alertas_outliers_liquido(observacoes)
        self.assertEqual(len(alertas), 1)
        self.assertIn("evento externo", alertas[0])


class AlertasMargemTest(unittest.TestCase):
    def _metricas(self, margem: float) -> MetricasGrupo:
        return MetricasGrupo(
            grupo="Grupo 9", dias=10, compradores_dia=10.0, gmv_dia=1000.0,
            comissao_dia=100.0, cashback_dia=100.0, liquido_dia=0.0,
            taxa_cashback=0.1, taxa_comissao=0.1, margem=margem,
            serie_liquido=(),
        )

    def test_margem_zero_gera_alerta(self):
        alertas = alertas_margem_nao_positiva([self._metricas(0.0)])
        self.assertEqual(len(alertas), 1)
        self.assertIn("inviável", alertas[0])

    def test_margem_positiva_sem_alerta(self):
        self.assertEqual(alertas_margem_nao_positiva([self._metricas(0.3)]), [])


if __name__ == "__main__":
    unittest.main()
