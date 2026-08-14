import csv
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from decisao import ESCALAR, INCONCLUSIVO, NAO_ESCALAR, Comparacao, Decisao
from metricas import MetricasGrupo
from registro import montar_registro, registrar, resumo_resultado, texto_decisao


def metricas_fake(grupo: str, liquido_dia: float) -> MetricasGrupo:
    serie = tuple((date(2011, 1, 1) + timedelta(days=i), liquido_dia) for i in range(30))
    return MetricasGrupo(
        grupo=grupo, dias=30, compradores_dia=100.0, gmv_dia=50000.0,
        comissao_dia=liquido_dia * 2, cashback_dia=liquido_dia,
        liquido_dia=liquido_dia, taxa_cashback=0.05, taxa_comissao=0.11,
        margem=0.5, serie_liquido=serie,
    )


def decisao_fake(tipo: str, variante: str | None) -> Decisao:
    return Decisao(
        tipo=tipo, variante=variante, justificativa="...",
        alfa_ajustado=0.05,
        comparacoes=[Comparacao("Grupo 2", 10.0, 0.01, (5.0, 15.0), "t pareado por dia")],
    )


class RegistrarTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.planilha = str(Path(self.dir.name) / "registro_testes.csv")
        self.registro = montar_registro(
            nome="Teste X", descricao="desc", parceiro="Parceiro X",
            metricas=[metricas_fake("Grupo 1", 100), metricas_fake("Grupo 2", 50)],
            decisao=decisao_fake(ESCALAR, "Grupo 1"),
            inicio=date(2011, 1, 1), fim=date(2011, 1, 30),
            data_analise=date(2026, 8, 14), relatorio="reports/x.md",
        )

    def tearDown(self):
        self.dir.cleanup()

    def _linhas(self) -> list[dict[str, str]]:
        with open(self.planilha, encoding="utf-8") as arq:
            return list(csv.DictReader(arq))

    def test_cria_arquivo_com_cabecalho(self):
        registrar(self.planilha, self.registro)
        with open(self.planilha, encoding="utf-8") as arq:
            primeira = arq.readline()
        self.assertIn("Nome do teste", primeira)

    def test_append_nao_duplica_cabecalho(self):
        registrar(self.planilha, self.registro)
        registrar(self.planilha, self.registro)
        self.assertEqual(len(self._linhas()), 2)

    def test_conteudo_da_linha(self):
        registrar(self.planilha, self.registro)
        linha = self._linhas()[0]
        self.assertEqual(linha["Nome do teste"], "Teste X")
        self.assertEqual(linha["Parceiro"], "Parceiro X")
        self.assertEqual(linha["Decisão"], "Escalar Grupo 1 para 100% do tráfego")
        self.assertEqual(linha["Nº de variantes"], "2")


class TextosTest(unittest.TestCase):
    def test_resumo_resultado_lider_primeiro(self):
        metricas = [metricas_fake("Grupo 2", 50), metricas_fake("Grupo 1", 100)]
        resumo = resumo_resultado(metricas, decisao_fake(ESCALAR, "Grupo 1"))
        self.assertTrue(resumo.index("Grupo 1") < resumo.index("Grupo 2"))

    def test_texto_decisao_tipos(self):
        self.assertIn("Escalar Grupo 1", texto_decisao(decisao_fake(ESCALAR, "Grupo 1")))
        self.assertIn("Inconclusivo", texto_decisao(decisao_fake(INCONCLUSIVO, "Grupo 1")))
        self.assertIn("Não escalar", texto_decisao(decisao_fake(NAO_ESCALAR, None)))

    def test_texto_decisao_desconhecido_aborta(self):
        with self.assertRaises(ValueError):
            texto_decisao(decisao_fake("TIPO_INVALIDO", None))


if __name__ == "__main__":
    unittest.main()
