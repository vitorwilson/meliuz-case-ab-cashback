"""Ponto de entrada da solução: analisa um CSV de teste A/B de cashback.

Uso típico (via ferramenta de IA ou direto no terminal):

    python3 src/analisar_teste.py data/dataset_01_parceiroA.csv \
        --nome "Cashback Parceiro A — jan/abr" \
        --descricao "3 variantes de taxa de cashback"

Saídas: JSON no stdout (para a IA interpretar), relatório em Markdown
(--relatorio) e linha na planilha de acompanhamento (--sem-registro pula).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from decisao import Decisao, decidir
from leitura_csv import Dataset, carregar_dataset
from metricas import (
    MetricasGrupo,
    alertas_margem_nao_positiva,
    alertas_outliers_liquido,
    alertas_taxa_instavel,
    resumir_grupos,
)
from registro import montar_registro, registrar
from relatorio import gerar_relatorio


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    dataset = carregar_dataset(args.csv)
    metricas = resumir_grupos(dataset.observacoes)
    decisao = decidir(metricas)
    alertas = _todos_alertas(dataset, metricas)
    hoje = date.today()
    caminho_relatorio = _escrever_relatorio(args, dataset, metricas, decisao, alertas, hoje)
    if not args.sem_registro:
        _registrar_na_planilha(args, dataset, metricas, decisao, hoje, caminho_relatorio)
    print(_para_json(args, dataset, metricas, decisao, alertas, caminho_relatorio))
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analisa um teste A/B de cashback e recomenda a variante a escalar."
    )
    parser.add_argument("csv", help="caminho do CSV do teste (schema do case)")
    parser.add_argument("--nome", default=None, help="nome do teste (default: nome do arquivo)")
    parser.add_argument("--descricao", default="", help="descrição curta do teste")
    parser.add_argument("--relatorio", default=None, help="caminho do relatório .md")
    parser.add_argument("--planilha", default="planilha/registro_testes.csv")
    parser.add_argument("--sem-registro", action="store_true",
                        help="não registrar na planilha de acompanhamento")
    return parser.parse_args(argv)


def _todos_alertas(dataset: Dataset, metricas: list[MetricasGrupo]) -> list[str]:
    alertas = list(dataset.alertas)
    alertas += alertas_taxa_instavel(dataset.observacoes)
    alertas += alertas_outliers_liquido(dataset.observacoes)
    alertas += alertas_margem_nao_positiva(metricas)
    return alertas


def _escrever_relatorio(
    args: argparse.Namespace,
    dataset: Dataset,
    metricas: list[MetricasGrupo],
    decisao: Decisao,
    alertas: list[str],
    hoje: date,
) -> str:
    caminho = args.relatorio or _relatorio_default(args.csv)
    texto = gerar_relatorio(
        _nome_teste(args), args.descricao, args.csv,
        dataset.observacoes, metricas, decisao, alertas, hoje,
    )
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    Path(caminho).write_text(texto, encoding="utf-8")
    return caminho


def _registrar_na_planilha(
    args: argparse.Namespace,
    dataset: Dataset,
    metricas: list[MetricasGrupo],
    decisao: Decisao,
    hoje: date,
    caminho_relatorio: str,
) -> None:
    datas = [o.data for o in dataset.observacoes]
    registro = montar_registro(
        _nome_teste(args), args.descricao, _parceiro(dataset), metricas, decisao,
        min(datas), max(datas), hoje, caminho_relatorio,
    )
    registrar(args.planilha, registro)


def _para_json(
    args: argparse.Namespace,
    dataset: Dataset,
    metricas: list[MetricasGrupo],
    decisao: Decisao,
    alertas: list[str],
    caminho_relatorio: str,
) -> str:
    datas = [o.data for o in dataset.observacoes]
    resultado = {
        "teste": _nome_teste(args),
        "parceiro": _parceiro(dataset),
        "periodo": {"inicio": str(min(datas)), "fim": str(max(datas))},
        "variantes": [_metricas_json(m) for m in metricas],
        "comparacoes": [
            {
                "adversario": c.adversario,
                "diferenca_liquido_dia": round(c.diferenca_liquido_dia, 2),
                "p_valor": round(c.p_valor, 4),
                "ic95": [round(c.ic95[0], 2), round(c.ic95[1], 2)],
                "teste": c.teste,
            }
            for c in decisao.comparacoes
        ],
        "decisao": {
            "tipo": decisao.tipo,
            "variante": decisao.variante,
            "justificativa": decisao.justificativa,
        },
        "alertas": alertas,
        "relatorio": caminho_relatorio,
    }
    return json.dumps(resultado, ensure_ascii=False, indent=2)


def _metricas_json(m: MetricasGrupo) -> dict[str, object]:
    return {
        "grupo": m.grupo,
        "dias": m.dias,
        "taxa_cashback": round(m.taxa_cashback, 4),
        "taxa_comissao": round(m.taxa_comissao, 4),
        "compradores_dia": round(m.compradores_dia, 1),
        "gmv_dia": round(m.gmv_dia, 2),
        "comissao_dia": round(m.comissao_dia, 2),
        "cashback_dia": round(m.cashback_dia, 2),
        "liquido_dia": round(m.liquido_dia, 2),
        "margem": round(m.margem, 4),
    }


def _nome_teste(args: argparse.Namespace) -> str:
    return args.nome or Path(args.csv).stem


def _parceiro(dataset: Dataset) -> str:
    return ", ".join(sorted({o.parceiro for o in dataset.observacoes}))


def _relatorio_default(csv_path: str) -> str:
    return str(Path("reports") / f"relatorio_{Path(csv_path).stem}.md")


if __name__ == "__main__":
    sys.exit(main())
