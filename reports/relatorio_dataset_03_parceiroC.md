# Cashback Parceiro C — jul a ago/2011
- **Descrição:** 2 variantes de taxa de cashback (5% e 7% do GMV)
- **Parceiro:** Parceiro C
- **Período:** 2011-07-01 a 2011-08-14 (45 dias por variante)
- **Variantes:** 2 (Grupo 1, Grupo 2)
- **Fonte:** `data/dataset_03_parceiroC.csv`
- **Análise gerada em:** 2026-08-14

## Decisão

> **ESCALAR: Grupo 1**
>
> Grupo 1 tem o maior líquido médio diário (R$ 773/dia) e a vantagem é estatisticamente significativa contra todas as demais variantes (p < 0,050 e IC95% da diferença acima de zero).

## Métricas por variante (médias diárias)

| Variante | Taxa de cashback | Compradores/dia | GMV/dia | Comissão/dia | Cashback/dia | Líquido/dia | Margem |
|---|---|---|---|---|---|---|---|
| Grupo 1 | 5,0% | 101 | R$ 38.632 | R$ 2.704 | R$ 1.932 | **R$ 773** | 28,6% |
| Grupo 2 | 7,0% | 100 | R$ 37.450 | R$ 2.621 | R$ 2.621 | **R$ 0** | 0,0% |

## Comparações estatísticas (líquido diário)

Líder vs. cada adversária. Significância: p < 0,050 (α = 5% com correção de Bonferroni) e IC95% bootstrap da diferença acima de zero. Quando as variantes rodam nas mesmas datas, o teste é o t pareado por dia — que remove o ruído de calendário comum a todas; caso contrário, Welch não pareado.

| Comparação | Diferença líquida/dia | IC95% bootstrap | p-valor | Teste | Significante? |
|---|---|---|---|---|---|
| Líder − Grupo 2 | R$ 773 | [R$ 717, R$ 832] | < 0,0001 | t pareado por dia | Sim |

## Qualidade dos dados — alertas

- Grupo 2: margem não positiva (0,0%) — cashback consome toda a comissão; variante economicamente inviável

## Premissas e limitações

- **Sem contagem de visitantes por grupo:** o dataset não traz a exposição de cada variante, então assumimos split de tráfego equivalente entre os grupos e comparamos **médias diárias** — não é possível calcular taxa de conversão.
- **Pareamento por data:** como as variantes rodam em paralelo nas mesmas datas, a significância é avaliada com teste t pareado nas diferenças diárias, o que controla choques de calendário (fins de semana, promoções) que afetam todas as variantes ao mesmo tempo.
- **Líquido = comissão − cashback:** resultado do Méliuz antes de custos operacionais. É a métrica de decisão porque a pergunta do teste é qual variante escalar para 100% do tráfego.
- **Comissão assumida estável:** a análise confere a taxa de comissão por variante (ver tabela de métricas); diferenças de comissão entre grupos contaminariam a comparação.
- **Efeitos temporais:** sazonalidade de curto prazo (dia da semana, datas comemorativas) não é controlada; períodos longos e simétricos entre grupos mitigam o risco.

## Próximos passos

1. Escalar **Grupo 1** para 100% do tráfego.
2. Monitorar o líquido diário nas primeiras 2 semanas para confirmar que a margem se sustenta fora do período de teste.
3. Avaliar novo teste com taxas intermediárias se houver espaço de margem.
