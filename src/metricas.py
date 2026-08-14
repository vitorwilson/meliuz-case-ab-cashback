"""Métricas por variante do teste e checagens de qualidade específicas.

A métrica de decisão é o líquido diário do Méliuz (comissão − cashback):
quanto sobra de receita depois de pagar o cashback aos usuários.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import date

from formatacao import fmt_pct
from leitura_csv import Observacao

LIMIAR_CV_TAXA = 0.15  # coef. de variação da taxa diária acima disso = variante instável
FATOR_OUTLIER_IQR = 1.5


@dataclass(frozen=True)
class MetricasGrupo:
    """Agregados de uma variante; séries diárias alimentam os testes estatísticos."""
    grupo: str
    dias: int
    compradores_dia: float
    gmv_dia: float
    comissao_dia: float
    cashback_dia: float
    liquido_dia: float
    taxa_cashback: float  # cashback total / GMV total
    taxa_comissao: float  # comissão total / GMV total
    margem: float         # líquido total / comissão total
    serie_liquido: tuple[tuple[date, float], ...]  # (data, líquido) diário


def agrupar(observacoes: list[Observacao]) -> dict[str, list[Observacao]]:
    """Agrupa observações por variante, preservando a ordem do arquivo.

    Ex.: grupos = agrupar(dataset.observacoes); grupos["Grupo 1"]
    """
    grupos: dict[str, list[Observacao]] = {}
    for obs in observacoes:
        grupos.setdefault(obs.grupo, []).append(obs)
    return grupos


def resumir_grupos(observacoes: list[Observacao]) -> list[MetricasGrupo]:
    """Calcula as métricas de cada variante, ordenadas pelo nome do grupo."""
    return [
        calcular_metricas(grupo, obs)
        for grupo, obs in sorted(agrupar(observacoes).items())
    ]


def calcular_metricas(grupo: str, observacoes: list[Observacao]) -> MetricasGrupo:
    n = len(observacoes)
    comissao = sum(o.comissao for o in observacoes)
    cashback = sum(o.cashback for o in observacoes)
    vendas = sum(o.vendas for o in observacoes)
    compradores = sum(o.compradores for o in observacoes)
    liquido = comissao - cashback
    return MetricasGrupo(
        grupo=grupo,
        dias=n,
        compradores_dia=compradores / n,
        gmv_dia=vendas / n,
        comissao_dia=comissao / n,
        cashback_dia=cashback / n,
        liquido_dia=liquido / n,
        taxa_cashback=cashback / vendas if vendas else 0.0,
        taxa_comissao=comissao / vendas if vendas else 0.0,
        margem=liquido / comissao if comissao else 0.0,
        serie_liquido=tuple((o.data, o.comissao - o.cashback) for o in observacoes),
    )


def alertas_taxa_instavel(observacoes: list[Observacao]) -> list[str]:
    """Flag: taxa de cashback diária muito variável dentro da mesma variante.

    Indica implementação ruidosa do teste (ex.: usuários do mesmo grupo
    recebendo taxas diferentes ao longo dos dias).
    """
    alertas = []
    for grupo, obs in sorted(agrupar(observacoes).items()):
        taxas = [o.cashback / o.vendas for o in obs if o.vendas > 0]
        if len(taxas) < 2:
            continue
        media = statistics.mean(taxas)
        if media <= 0:
            continue
        cv = statistics.stdev(taxas) / media
        if cv > LIMIAR_CV_TAXA:
            alertas.append(
                f"{grupo}: taxa de cashback diária instável — média {fmt_pct(media)}, "
                f"variação {fmt_pct(min(taxas))}–{fmt_pct(max(taxas))} "
                f"(CV {fmt_pct(cv)}). Possível implementação ruidosa da variante."
            )
    return alertas


def alertas_margem_nao_positiva(metricas: list[MetricasGrupo]) -> list[str]:
    """Flag: variante com margem ≤ 0 (cashback consome toda a comissão ou mais).

    Independente da decisão final, essa variante é economicamente inviável.
    """
    return [
        f"{m.grupo}: margem não positiva ({fmt_pct(m.margem)}) — cashback "
        f"consome toda a comissão; variante economicamente inviável"
        for m in metricas
        if m.margem <= 0
    ]


def alertas_outliers_liquido(observacoes: list[Observacao]) -> list[str]:
    """Flag: dias com líquido fora de Q1 − 1,5·IIQ / Q3 + 1,5·IIQ.

    Dias atípicos em TODAS as variantes indicam evento externo (promoção,
    data comemorativa), não problema do teste — são reportados agrupados.
    """
    outliers = _outliers_por_grupo(observacoes)
    if not outliers:
        return []
    comuns = set.intersection(*(set(v) for v in outliers.values()))
    alertas = [
        f"dia {dia} com líquido atípico em todas as variantes — "
        f"possível evento externo (promoção ou data comemorativa)"
        for dia in sorted(comuns)
    ]
    for grupo in sorted(outliers):
        for dia in sorted(set(outliers[grupo]) - comuns):
            alertas.append(f"{grupo}: dia {dia} com líquido atípico")
    return alertas


def _outliers_por_grupo(
    observacoes: list[Observacao],
) -> dict[str, list[date]]:
    """Datas atípicas por grupo; grupos sem outlier aparecem com lista vazia."""
    resultado: dict[str, list[date]] = {}
    for grupo, obs in agrupar(observacoes).items():
        pontos = [(o.comissao - o.cashback, o.data) for o in obs]
        if len(pontos) < 4:
            resultado[grupo] = []
            continue
        q1, _, q3 = statistics.quantiles([p[0] for p in pontos], n=4)
        iiq = q3 - q1
        resultado[grupo] = [
            dia for valor, dia in pontos if _eh_outlier(valor, q1, q3, iiq)
        ]
    return resultado


def _eh_outlier(valor: float, q1: float, q3: float, iiq: float) -> bool:
    return (
        valor < q1 - FATOR_OUTLIER_IQR * iiq
        or valor > q3 + FATOR_OUTLIER_IQR * iiq
    )
