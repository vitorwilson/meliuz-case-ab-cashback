"""Teste de ponta a ponta: CSV -> JSON + relatório + linha na planilha."""
import contextlib
import csv
import io
import json
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from analisar_teste import main

CABECALHO = "Data,Grupos de usuários,Parceiro,compradores,comissão,cashback,vendas totais"


def gerar_csv_teste(caminho: str) -> None:
    """Grupo 1 com líquido claramente maior que Grupo 2 (cashback menor)."""
    linhas = []
    for grupo, taxa in [("Grupo 1", 0.04), ("Grupo 2", 0.09)]:
        for i in range(30):
            dia = date(2011, 1, 1) + timedelta(days=i)
            vendas = 50000 + (i * 137) % 8000
            linhas.append(
                f"{dia},{grupo},Parceiro X,{vendas // 500},"
                f"{_brl(vendas * 0.11)},{_brl(vendas * taxa)},{_brl(vendas)}"
            )
    Path(caminho).write_text(CABECALHO + "\n" + "\n".join(linhas) + "\n", encoding="utf-8")


def _brl(valor: float) -> str:
    """5500.0 -> 'R$ 5.500' (formato do schema do case)."""
    return "R$ " + f"{valor:,.0f}".replace(",", ".")


class FluxoCompletoTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        base = Path(self.dir.name)
        self.csv = str(base / "teste.csv")
        self.relatorio = str(base / "relatorio.md")
        self.planilha = str(base / "planilha" / "registro_testes.csv")
        gerar_csv_teste(self.csv)

    def tearDown(self):
        self.dir.cleanup()

    def _rodar(self) -> dict:
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            codigo = main([
                self.csv, "--nome", "Teste E2E", "--descricao", "sintético",
                "--relatorio", self.relatorio, "--planilha", self.planilha,
            ])
        self.assertEqual(codigo, 0)
        return json.loads(saida.getvalue())

    def test_json_no_stdout(self):
        resultado = self._rodar()
        self.assertEqual(resultado["decisao"]["tipo"], "ESCALAR")
        self.assertEqual(resultado["decisao"]["variante"], "Grupo 1")
        self.assertEqual(len(resultado["variantes"]), 2)

    def test_relatorio_gerado(self):
        self._rodar()
        texto = Path(self.relatorio).read_text(encoding="utf-8")
        self.assertIn("# Teste E2E", texto)
        self.assertIn("## Decisão", texto)
        self.assertIn("ESCALAR: Grupo 1", texto)

    def test_linha_na_planilha(self):
        self._rodar()
        with open(self.planilha, encoding="utf-8") as arq:
            linhas = list(csv.DictReader(arq))
        self.assertEqual(len(linhas), 1)
        self.assertEqual(linhas[0]["Nome do teste"], "Teste E2E")
        self.assertEqual(linhas[0]["Relatório"], self.relatorio)

    def test_sem_registro_nao_cria_planilha(self):
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            main([self.csv, "--relatorio", self.relatorio,
                  "--planilha", self.planilha, "--sem-registro"])
        self.assertFalse(Path(self.planilha).exists())


if __name__ == "__main__":
    unittest.main()
