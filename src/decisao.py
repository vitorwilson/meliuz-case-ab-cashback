"""Regras determinísticas de decisão do teste A/B.

Decisão sempre pela mesma régua, independente de quem roda a análise:
a candidata é a variante de maior líquido médio diário (comissão − cashback);
ela só é recomendada se tiver margem positiva e vantagem estatisticamente
significativa contra TODAS as demais (α com correção de Bonferroni).
"""
from __future__ import annotations

from dataclasses import dataclass

from estatistica import (
    ic_bootstrap_diferenca,
    ic_bootstrap_media,
    t_pareado_pvalor,
    welch_pvalor,
)
from formatacao import fmt_pct, fmt_pvalor, fmt_real
from metricas import MetricasGrupo

ALFA = 0.05  # nível de significância base, dividido pelo nº de comparações
MIN_DIAS_PAREADOS = 8      # abaixo disso o pareamento não tem poder; cai para Welch
MIN_SOBREPOSICAO = 0.8     # fração mínima de datas em comum para parear

ESCALAR = "ESCALAR"
INCONCLUSIVO = "INCONCLUSIVO"
NAO_ESCALAR = "NAO_ESCALAR"

TESTE_PAREADO = "t pareado por dia"
TESTE_WELCH = "Welch (não pareado)"


@dataclass(frozen=True)
class Comparacao:
    """Candidata vs. uma variante adversária, no líquido diário."""
    adversario: str
    diferenca_liquido_dia: float
    p_valor: float
    ic95: tuple[float, float]
    teste: str  # TESTE_PAREADO | TESTE_WELCH


@dataclass(frozen=True)
class Decisao:
    tipo: str  # ESCALAR | INCONCLUSIVO | NAO_ESCALAR
    variante: str | None
    justificativa: str
    alfa_ajustado: float
    comparacoes: list[Comparacao]


def decidir(metricas: list[MetricasGrupo]) -> Decisao:
    """Aplica as regras de decisão sobre as métricas das variantes.

    Ex.: decisao = decidir(resumir_grupos(dataset.observacoes))
    """
    if len(metricas) < 2:
        raise ValueError(
            f"decisão exige pelo menos 2 grupos; recebido: "
            f"{[m.grupo for m in metricas]}"
        )
    ordenados = sorted(metricas, key=lambda m: m.liquido_dia, reverse=True)
    candidata = ordenados[0]
    comparacoes = [_comparar(candidata, outro) for outro in ordenados[1:]]
    alfa = ALFA / len(comparacoes)  # Bonferroni
    if candidata.margem <= 0:
        return Decisao(NAO_ESCALAR, None, _texto_nao_escalar(candidata), alfa, comparacoes)
    if _vantagem_significativa(comparacoes, alfa):
        return Decisao(
            ESCALAR, candidata.grupo, _texto_escalar(candidata, alfa), alfa, comparacoes
        )
    return Decisao(
        INCONCLUSIVO, candidata.grupo,
        _texto_inconclusivo(candidata, comparacoes, alfa), alfa, comparacoes,
    )


def _comparar(candidata: MetricasGrupo, outro: MetricasGrupo) -> Comparacao:
    diferencas = _diferencas_pareadas(candidata, outro)
    if diferencas is not None:
        return Comparacao(
            adversario=outro.grupo,
            diferenca_liquido_dia=candidata.liquido_dia - outro.liquido_dia,
            p_valor=t_pareado_pvalor(diferencas),
            ic95=ic_bootstrap_media(diferencas),
            teste=TESTE_PAREADO,
        )
    x = [v for _, v in candidata.serie_liquido]
    y = [v for _, v in outro.serie_liquido]
    return Comparacao(
        adversario=outro.grupo,
        diferenca_liquido_dia=candidata.liquido_dia - outro.liquido_dia,
        p_valor=welch_pvalor(x, y),
        ic95=ic_bootstrap_diferenca(x, y),
        teste=TESTE_WELCH,
    )


def _diferencas_pareadas(
    candidata: MetricasGrupo, outro: MetricasGrupo
) -> list[float] | None:
    """Diferenças diárias nas datas comuns; None se não dá para parear."""
    por_data_a = dict(candidata.serie_liquido)
    por_data_b = dict(outro.serie_liquido)
    comuns = sorted(set(por_data_a) & set(por_data_b))
    maior_serie = max(len(por_data_a), len(por_data_b))
    if len(comuns) < MIN_DIAS_PAREADOS or len(comuns) < MIN_SOBREPOSICAO * maior_serie:
        return None
    return [por_data_a[d] - por_data_b[d] for d in comuns]


def _vantagem_significativa(comparacoes: list[Comparacao], alfa: float) -> bool:
    return all(c.p_valor < alfa and c.ic95[0] > 0 for c in comparacoes)


def _texto_escalar(candidata: MetricasGrupo, alfa: float) -> str:
    return (
        f"{candidata.grupo} tem o maior líquido médio diário "
        f"({fmt_real(candidata.liquido_dia)}/dia) e a vantagem é estatisticamente "
        f"significativa contra todas as demais variantes "
        f"(p < {_fmt_alfa(alfa)} e IC95% da diferença acima de zero)."
    )


def _texto_inconclusivo(
    candidata: MetricasGrupo, comparacoes: list[Comparacao], alfa: float
) -> str:
    pior = max(comparacoes, key=lambda c: c.p_valor)
    return (
        f"{candidata.grupo} lidera o líquido médio diário "
        f"({fmt_real(candidata.liquido_dia)}/dia), mas a vantagem não é "
        f"estatisticamente significativa contra {pior.adversario} "
        f"(p = {fmt_pvalor(pior.p_valor)} vs. α = {_fmt_alfa(alfa)}; IC95% "
        f"[{fmt_real(pior.ic95[0])}, {fmt_real(pior.ic95[1])}]). "
        f"Recomenda-se manter a variante atual e estender o teste."
    )


def _texto_nao_escalar(candidata: MetricasGrupo) -> str:
    return (
        f"nenhuma variante gera margem positiva: a melhor ({candidata.grupo}) "
        f"tem margem de {fmt_pct(candidata.margem)} "
        f"(líquido {fmt_real(candidata.liquido_dia)}/dia). Escalar qualquer "
        f"variante destrói valor — renegociar comissão ou redesenhar o teste."
    )


def _fmt_alfa(alfa: float) -> str:
    return f"{alfa:.3f}".replace(".", ",")
