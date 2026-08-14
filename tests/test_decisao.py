import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from decisao import (
    ESCALAR,
    INCONCLUSIVO,
    NAO_ESCALAR,
    TESTE_PAREADO,
    TESTE_WELCH,
    decidir,
)
from metricas import MetricasGrupo


def metricas_fake(
    grupo: str,
    valores: list[float],
    margem: float = 0.5,
    inicio: date = date(2011, 1, 1),
) -> MetricasGrupo:
    liquido = sum(valores) / len(valores)
    comissao_dia = liquido / margem if margem > 0 else liquido * 2
    serie = tuple((inicio + timedelta(days=i), v) for i, v in enumerate(valores))
    return MetricasGrupo(
        grupo=grupo,
        dias=len(valores),
        compradores_dia=100.0,
        gmv_dia=50000.0,
        comissao_dia=comissao_dia,
        cashback_dia=comissao_dia - liquido,
        liquido_dia=liquido,
        taxa_cashback=0.05,
        taxa_comissao=0.11,
        margem=margem,
        serie_liquido=serie,
    )


class DecidirTest(unittest.TestCase):
    def test_escalar_quando_vantagem_significativa(self):
        g1 = metricas_fake("Grupo 1", [100 + i % 5 for i in range(30)])
        g2 = metricas_fake("Grupo 2", [50 + i % 5 for i in range(30)])
        decisao = decidir([g1, g2])
        self.assertEqual(decisao.tipo, ESCALAR)
        self.assertEqual(decisao.variante, "Grupo 1")

    def test_datas_alinhadas_usam_teste_pareado(self):
        g1 = metricas_fake("Grupo 1", [100 + i % 5 for i in range(30)])
        g2 = metricas_fake("Grupo 2", [50 + i % 5 for i in range(30)])
        decisao = decidir([g1, g2])
        self.assertEqual(decisao.comparacoes[0].teste, TESTE_PAREADO)

    def test_datas_desalinhadas_caem_para_welch(self):
        g1 = metricas_fake("Grupo 1", [100 + i % 5 for i in range(30)])
        g2 = metricas_fake(
            "Grupo 2", [50 + i % 5 for i in range(30)], inicio=date(2012, 1, 1)
        )
        decisao = decidir([g1, g2])
        self.assertEqual(decisao.comparacoes[0].teste, TESTE_WELCH)

    def test_inconclusivo_quando_diferencas_oscilam(self):
        # diferenças diárias com média pequena e variância alta -> sem significância
        v1 = [100 + (i * 53) % 100 for i in range(15)]
        v2 = [95 + (i * 29 + 7) % 100 for i in range(15)]
        decisao = decidir([
            metricas_fake("Grupo 1", v1),
            metricas_fake("Grupo 2", v2),
        ])
        self.assertEqual(decisao.tipo, INCONCLUSIVO)
        lider = "Grupo 1" if sum(v1) > sum(v2) else "Grupo 2"
        self.assertEqual(decisao.variante, lider)  # líder provisório

    def test_nao_escalar_quando_margem_nao_positiva(self):
        g1 = metricas_fake("Grupo 1", [0.0] * 20, margem=0.0)
        g2 = metricas_fake("Grupo 2", [-100 - i % 10 for i in range(20)], margem=-0.5)
        decisao = decidir([g1, g2])
        self.assertEqual(decisao.tipo, NAO_ESCALAR)
        self.assertIsNone(decisao.variante)

    def test_um_grupo_so_aborta(self):
        with self.assertRaisesRegex(ValueError, "pelo menos 2 grupos"):
            decidir([metricas_fake("Grupo 1", [100] * 10)])

    def test_bonferroni_divide_alfa(self):
        g1 = metricas_fake("Grupo 1", [100 + i % 5 for i in range(30)])
        g2 = metricas_fake("Grupo 2", [50 + i % 5 for i in range(30)])
        g3 = metricas_fake("Grupo 3", [40 + i % 5 for i in range(30)])
        decisao = decidir([g1, g2, g3])
        self.assertAlmostEqual(decisao.alfa_ajustado, 0.025)
        self.assertEqual(len(decisao.comparacoes), 2)


if __name__ == "__main__":
    unittest.main()
