"""Registro do teste na planilha de acompanhamento.

Fonte de verdade local: planilha/registro_testes.csv, com uma linha por
teste — o mínimo aceito pelo case. Esse CSV é importado para o Google
Sheets público de acompanhamento (passo manual descrito no README).
"""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from decisao import ESCALAR, INCONCLUSIVO, NAO_ESCALAR, Decisao
from formatacao import fmt_real
from metricas import MetricasGrupo

COLUNAS_REGISTRO = [
    "Nome do teste", "Descrição", "Parceiro", "Início", "Fim", "Dias",
    "Nº de variantes", "Resultado", "Decisão", "Data da análise", "Relatório",
]


def registrar(planilha: str, registro: dict[str, str]) -> None:
    """Appenda uma linha na planilha CSV, criando o cabeçalho se necessário.

    Ex.: registrar("planilha/registro_testes.csv", montar_registro(...))
    """
    caminho = Path(planilha)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    novo = not caminho.exists()
    with caminho.open("a", encoding="utf-8", newline="") as arq:
        escritor = csv.DictWriter(arq, fieldnames=COLUNAS_REGISTRO)
        if novo:
            escritor.writeheader()
        escritor.writerow(registro)


def montar_registro(
    nome: str,
    descricao: str,
    parceiro: str,
    metricas: list[MetricasGrupo],
    decisao: Decisao,
    inicio: date,
    fim: date,
    data_analise: date,
    relatorio: str,
) -> dict[str, str]:
    """Monta a linha da planilha no formato das colunas de acompanhamento."""
    return {
        "Nome do teste": nome,
        "Descrição": descricao,
        "Parceiro": parceiro,
        "Início": str(inicio),
        "Fim": str(fim),
        "Dias": str(max(m.dias for m in metricas)),
        "Nº de variantes": str(len(metricas)),
        "Resultado": resumo_resultado(metricas, decisao),
        "Decisão": texto_decisao(decisao),
        "Data da análise": str(data_analise),
        "Relatório": relatorio,
    }


def resumo_resultado(metricas: list[MetricasGrupo], decisao: Decisao) -> str:
    """Uma linha com o líquido/dia de cada variante, líder primeiro."""
    ordenados = sorted(metricas, key=lambda m: m.liquido_dia, reverse=True)
    partes = [f"{m.grupo}: {fmt_real(m.liquido_dia)}/dia" for m in ordenados]
    return "Líquido diário — " + " vs. ".join(partes)


def texto_decisao(decisao: Decisao) -> str:
    """Decisão curta para a célula da planilha."""
    if decisao.tipo == ESCALAR:
        return f"Escalar {decisao.variante} para 100% do tráfego"
    if decisao.tipo == INCONCLUSIVO:
        return f"Inconclusivo — manter split e estender o teste (líder: {decisao.variante})"
    if decisao.tipo == NAO_ESCALAR:
        return "Não escalar nenhuma variante — margem não positiva"
    raise ValueError(f"tipo de decisão desconhecido: {decisao.tipo!r}")
