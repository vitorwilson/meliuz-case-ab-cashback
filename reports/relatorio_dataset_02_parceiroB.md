# Cashback Parceiro B — mai a jun/2011
- **Descrição:** 3 variantes de taxa de cashback (4%, 6% e 9% do GMV)
- **Parceiro:** Parceiro B
- **Período:** 2011-05-01 a 2011-06-30 (61 dias por variante)
- **Variantes:** 3 (Grupo 1, Grupo 2, Grupo 3)
- **Fonte:** `data/dataset_02_parceiroB.csv`
- **Análise gerada em:** 2026-08-14

## Decisão

> **ESCALAR: Grupo 1**
>
> Grupo 1 tem o maior líquido médio diário (R$ 4.698/dia) e a vantagem é estatisticamente significativa contra todas as demais variantes (p < 0,025 e IC95% da diferença acima de zero).

## Métricas por variante (médias diárias)

| Variante | Taxa de cashback | Compradores/dia | GMV/dia | Comissão/dia | Cashback/dia | Líquido/dia | Margem |
|---|---|---|---|---|---|---|---|
| Grupo 1 | 4,0% | 131 | R$ 67.112 | R$ 7.382 | R$ 2.684 | **R$ 4.698** | 63,6% |
| Grupo 2 | 6,0% | 89 | R$ 46.935 | R$ 5.163 | R$ 2.816 | **R$ 2.347** | 45,5% |
| Grupo 3 | 9,0% | 82 | R$ 43.114 | R$ 4.742 | R$ 3.880 | **R$ 862** | 18,2% |

## Comparações estatísticas (líquido diário)

Líder vs. cada adversária. Significância: p < 0,025 (α = 5% com correção de Bonferroni) e IC95% bootstrap da diferença acima de zero. Quando as variantes rodam nas mesmas datas, o teste é o t pareado por dia — que remove o ruído de calendário comum a todas; caso contrário, Welch não pareado.

| Comparação | Diferença líquida/dia | IC95% bootstrap | p-valor | Teste | Significante? |
|---|---|---|---|---|---|
| Líder − Grupo 2 | R$ 2.351 | [R$ 2.066, R$ 2.660] | < 0,0001 | t pareado por dia | Sim |
| Líder − Grupo 3 | R$ 3.836 | [R$ 3.461, R$ 4.277] | < 0,0001 | t pareado por dia | Sim |

## Qualidade dos dados — alertas

- dia 2011-05-15 com líquido atípico em todas as variantes — possível evento externo (promoção ou data comemorativa)
- dia 2011-05-22 com líquido atípico em todas as variantes — possível evento externo (promoção ou data comemorativa)

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
