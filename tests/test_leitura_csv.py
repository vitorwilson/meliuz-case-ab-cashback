import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from leitura_csv import carregar_dataset, parse_real

CABECALHO = "Data,Grupos de usuários,Parceiro,compradores,comissão,cashback,vendas totais\n"
LINHA = "2011-01-0{dia},Grupo {grupo},Parceiro X,{comp},R$ {com},R$ {cash},R$ {vend}\n"


def escrever_csv(conteudo: str) -> str:
    arq = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, encoding="utf-8"
    )
    arq.write(conteudo)
    arq.close()
    return arq.name


def csv_minimo() -> str:
    linhas = [
        LINHA.format(dia=d, grupo=g, comp=10, com="1.000", cash="400", vend="10.000")
        for g in (1, 2)
        for d in (1, 2)
    ]
    return CABECALHO + "".join(linhas)


class ParseRealTest(unittest.TestCase):
    def test_milhar_com_ponto(self):
        self.assertEqual(parse_real("R$ 10.273"), 10273.0)

    def test_milhar_com_centavos(self):
        self.assertEqual(parse_real("R$ 1.234,56"), 1234.56)

    def test_valor_simples(self):
        self.assertEqual(parse_real("R$ 500"), 500.0)

    def test_milhoes(self):
        self.assertEqual(parse_real("R$ 1.234.567"), 1234567.0)

    def test_vazio_levanta_erro(self):
        with self.assertRaises(ValueError):
            parse_real("R$ ")

    def test_texto_invalido_levanta_erro_com_valor(self):
        with self.assertRaisesRegex(ValueError, "abc"):
            parse_real("R$ abc")


class CarregarDatasetTest(unittest.TestCase):
    def test_carrega_observacoes(self):
        dataset = carregar_dataset(escrever_csv(csv_minimo()))
        self.assertEqual(len(dataset.observacoes), 4)
        obs = dataset.observacoes[0]
        self.assertEqual(obs.grupo, "Grupo 1")
        self.assertEqual(obs.comissao, 1000.0)
        self.assertEqual(obs.compradores, 10)

    def test_schema_errado_aborta(self):
        caminho = escrever_csv("Data,Grupo\n2011-01-01,Grupo 1\n")
        with self.assertRaisesRegex(ValueError, "colunas ausentes"):
            carregar_dataset(caminho)

    def test_valor_ruim_indica_linha(self):
        conteudo = CABECALHO + LINHA.format(
            dia=1, grupo=1, comp=10, com="mil reais", cash="400", vend="10.000"
        )
        with self.assertRaisesRegex(ValueError, "linha 2"):
            carregar_dataset(escrever_csv(conteudo))

    def test_dataset_vazio_aborta(self):
        with self.assertRaisesRegex(ValueError, "vazio"):
            carregar_dataset(escrever_csv(CABECALHO))

    def test_duplicata_gera_alerta(self):
        linha = LINHA.format(dia=1, grupo=1, comp=10, com="1.000", cash="400", vend="10.000")
        dataset = carregar_dataset(escrever_csv(CABECALHO + linha + linha))
        self.assertTrue(any("duplicada" in a for a in dataset.alertas))

    def test_dia_faltante_gera_alerta(self):
        linhas = [
            LINHA.format(dia=d, grupo=1, comp=10, com="1.000", cash="400", vend="10.000")
            for d in (1, 3)  # dia 2 ausente
        ]
        dataset = carregar_dataset(escrever_csv(CABECALHO + "".join(linhas)))
        self.assertTrue(any("sem dados" in a for a in dataset.alertas))

    def test_valor_negativo_gera_alerta(self):
        linha = "2011-01-01,Grupo 1,Parceiro X,10,R$ 1.000,R$ -400,R$ 10.000\n"
        dataset = carregar_dataset(escrever_csv(CABECALHO + linha))
        self.assertTrue(any("negativos" in a for a in dataset.alertas))

    def test_dataset_limpo_sem_alertas(self):
        dataset = carregar_dataset(escrever_csv(csv_minimo()))
        self.assertEqual(dataset.alertas, [])


if __name__ == "__main__":
    unittest.main()
