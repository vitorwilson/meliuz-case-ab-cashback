"""Geração do relatório gerencial em Markdown.

O relatório é determinístico: os números vêm do pipeline, não da
interpretação de quem rodou. A camada de IA apresenta e explica o
resultado, mas não altera valores.
"""
from __future__ import annotations

from datetime import date

from decisao import ESCALAR, INCONCLUSIVO, NAO_ESCALAR, Decisao
from formatacao import fmt_pct, fmt_pvalor, fmt_real
from leitura_csv import Observacao
from metricas import MetricasGrupo


def gerar_relatorio(
    nome: str,
    descricao: str,
    arquivo: str,
    observacoes: list[Observacao],
    metricas: list[MetricasGrupo],
    decisao: Decisao,
    alertas: list[str],
    data_analise: date,
) -> str:
    """Monta o relatório completo em Markdown, pronto para um gestor ler."""
    secoes = [
        _cabecalho(nome, descricao, arquivo, observacoes, metricas, data_analise),
        _secao_decisao(decisao),
        _secao_metricas(metricas),
        _secao_comparacoes(decisao),
        _secao_alertas(alertas),
        _SECAO_PREMISSAS,
        _secao_proximos_passos(decisao),
    ]
    return "\n\n".join(secoes) + "\n"


def _cabecalho(
    nome: str,
    descricao: str,
    arquivo: str,
    observacoes: list[Observacao],
    metricas: list[MetricasGrupo],
    data_analise: date,
) -> str:
    datas = [o.data for o in observacoes]
    parceiros = sorted({o.parceiro for o in observacoes})
    linhas = [
        f"# {nome}",
        "",
        f"- **Descrição:** {descricao}" if descricao else "",
        f"- **Parceiro:** {', '.join(parceiros)}",
        f"- **Período:** {min(datas)} a {max(datas)} ({max(metricas, key=lambda m: m.dias).dias} dias por variante)",
        f"- **Variantes:** {len(metricas)} ({', '.join(m.grupo for m in metricas)})",
        f"- **Fonte:** `{arquivo}`",
        f"- **Análise gerada em:** {data_analise}",
    ]
    return "\n".join(l for l in linhas if l)


def _secao_decisao(decisao: Decisao) -> str:
    rotulo = {
        ESCALAR: f"ESCALAR: {decisao.variante}",
        INCONCLUSIVO: f"INCONCLUSIVO (líder provisório: {decisao.variante})",
        NAO_ESCALAR: "NÃO ESCALAR NENHUMA VARIANTE",
    }[decisao.tipo]
    return f"## Decisão\n\n> **{rotulo}**\n>\n> {decisao.justificativa}"


def _secao_metricas(metricas: list[MetricasGrupo]) -> str:
    linhas = [
        "## Métricas por variante (médias diárias)",
        "",
        "| Variante | Taxa de cashback | Compradores/dia | GMV/dia | Comissão/dia | Cashback/dia | Líquido/dia | Margem |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for m in metricas:
        linhas.append(
            f"| {m.grupo} | {fmt_pct(m.taxa_cashback)} | {m.compradores_dia:.0f} "
            f"| {fmt_real(m.gmv_dia)} | {fmt_real(m.comissao_dia)} "
            f"| {fmt_real(m.cashback_dia)} | **{fmt_real(m.liquido_dia)}** "
            f"| {fmt_pct(m.margem)} |"
        )
    return "\n".join(linhas)


def _fmt_alfa(alfa: float) -> str:
    return f"{alfa:.3f}".replace(".", ",")


def _secao_comparacoes(decisao: Decisao) -> str:
    linhas = [
        "## Comparações estatísticas (líquido diário)",
        "",
        f"Líder vs. cada adversária. Significância: p < {_fmt_alfa(decisao.alfa_ajustado)} "
        "(α = 5% com correção de Bonferroni) e IC95% bootstrap da diferença acima de zero. "
        "Quando as variantes rodam nas mesmas datas, o teste é o t pareado por dia — "
        "que remove o ruído de calendário comum a todas; caso contrário, Welch não pareado.",
        "",
        "| Comparação | Diferença líquida/dia | IC95% bootstrap | p-valor | Teste | Significante? |",
        "|---|---|---|---|---|---|",
    ]
    for c in decisao.comparacoes:
        significante = "Sim" if c.p_valor < decisao.alfa_ajustado and c.ic95[0] > 0 else "Não"
        linhas.append(
            f"| Líder − {c.adversario} | {fmt_real(c.diferenca_liquido_dia)} "
            f"| [{fmt_real(c.ic95[0])}, {fmt_real(c.ic95[1])}] "
            f"| {fmt_pvalor(c.p_valor)} | {c.teste} | {significante} |"
        )
    return "\n".join(linhas)


def _secao_alertas(alertas: list[str]) -> str:
    if not alertas:
        return "## Qualidade dos dados\n\nNenhum problema detectado."
    itens = "\n".join(f"- {a}" for a in alertas)
    return f"## Qualidade dos dados — alertas\n\n{itens}"


_SECAO_PREMISSAS = """## Premissas e limitações

- **Sem contagem de visitantes por grupo:** o dataset não traz a exposição de cada variante, então assumimos split de tráfego equivalente entre os grupos e comparamos **médias diárias** — não é possível calcular taxa de conversão.
- **Pareamento por data:** como as variantes rodam em paralelo nas mesmas datas, a significância é avaliada com teste t pareado nas diferenças diárias, o que controla choques de calendário (fins de semana, promoções) que afetam todas as variantes ao mesmo tempo.
- **Líquido = comissão − cashback:** resultado do Méliuz antes de custos operacionais. É a métrica de decisão porque a pergunta do teste é qual variante escalar para 100% do tráfego.
- **Comissão assumida estável:** a análise confere a taxa de comissão por variante (ver tabela de métricas); diferenças de comissão entre grupos contaminariam a comparação.
- **Efeitos temporais:** sazonalidade de curto prazo (dia da semana, datas comemorativas) não é controlada; períodos longos e simétricos entre grupos mitigam o risco."""


def _secao_proximos_passos(decisao: Decisao) -> str:
    passos = {
        ESCALAR: (
            f"1. Escalar **{decisao.variante}** para 100% do tráfego.\n"
            "2. Monitorar o líquido diário nas primeiras 2 semanas para confirmar "
            "que a margem se sustenta fora do período de teste.\n"
            "3. Avaliar novo teste com taxas intermediárias se houver espaço de margem."
        ),
        INCONCLUSIVO: (
            "1. Manter o split atual de tráfego — não escalar nenhuma variante ainda.\n"
            "2. Estender o teste para acumular mais dias e repetir esta análise.\n"
            "3. Se a liderança se mantiver sem significância, avaliar se a diferença "
            "prática justifica a decisão mesmo sem certeza estatística."
        ),
        NAO_ESCALAR: (
            "1. Não escalar nenhuma variante — todas destroem valor no nível atual.\n"
            "2. Renegociar a comissão com o parceiro ou reduzir as taxas de cashback testadas.\n"
            "3. Redesenhar o teste com taxas que preservem margem positiva."
        ),
    }
    return f"## Próximos passos\n\n{passos[decisao.tipo]}"
