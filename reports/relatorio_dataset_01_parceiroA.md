# Cashback Parceiro A — jan a abr/2011
- **Descrição:** 3 variantes de taxa de cashback (taxas médias: 4,2%, 5,8% e 7,4% do GMV)
- **Parceiro:** Parceiro A
- **Período:** 2011-01-01 a 2011-04-02 (92 dias por variante)
- **Variantes:** 3 (Grupo 1, Grupo 2, Grupo 3)
- **Fonte:** `data/dataset_01_parceiroA.csv`
- **Análise gerada em:** 2026-08-14

## Decisão

> **ESCALAR: Grupo 1**
>
> Grupo 1 tem o maior líquido médio diário (R$ 4.399/dia) e a vantagem é estatisticamente significativa contra todas as demais variantes (p < 0,025 e IC95% da diferença acima de zero).

## Métricas por variante (médias diárias)

| Variante | Taxa de cashback | Compradores/dia | GMV/dia | Comissão/dia | Cashback/dia | Líquido/dia | Margem |
|---|---|---|---|---|---|---|---|
| Grupo 1 | 4,2% | 105 | R$ 60.926 | R$ 6.936 | R$ 2.537 | **R$ 4.399** | 63,4% |
| Grupo 2 | 5,8% | 118 | R$ 69.816 | R$ 7.915 | R$ 4.029 | **R$ 3.886** | 49,1% |
| Grupo 3 | 7,4% | 124 | R$ 73.759 | R$ 8.347 | R$ 5.474 | **R$ 2.873** | 34,4% |

## Comparações estatísticas (líquido diário)

Líder vs. cada adversária. Significância: p < 0,025 (α = 5% com correção de Bonferroni) e IC95% bootstrap da diferença acima de zero. Quando as variantes rodam nas mesmas datas, o teste é o t pareado por dia — que remove o ruído de calendário comum a todas; caso contrário, Welch não pareado.

| Comparação | Diferença líquida/dia | IC95% bootstrap | p-valor | Teste | Significante? |
|---|---|---|---|---|---|
| Líder − Grupo 2 | R$ 513 | [R$ 287, R$ 737] | < 0,0001 | t pareado por dia | Sim |
| Líder − Grupo 3 | R$ 1.526 | [R$ 1.146, R$ 1.916] | < 0,0001 | t pareado por dia | Sim |

## Qualidade dos dados — alertas

- Grupo 1: taxa de cashback diária instável — média 4,1%, variação 3,0%–10,0% (CV 38,8%). Possível implementação ruidosa da variante.
- Grupo 2: taxa de cashback diária instável — média 5,6%, variação 5,0%–10,0% (CV 17,2%). Possível implementação ruidosa da variante.
- Grupo 3: taxa de cashback diária instável — média 6,8%, variação 4,0%–10,0% (CV 26,1%). Possível implementação ruidosa da variante.
- dia 2011-01-08 com líquido atípico em todas as variantes — possível evento externo (promoção ou data comemorativa)
- dia 2011-01-13 com líquido atípico em todas as variantes — possível evento externo (promoção ou data comemorativa)
- Grupo 1: dia 2011-01-14 com líquido atípico
- Grupo 2: dia 2011-01-14 com líquido atípico
- Grupo 2: dia 2011-02-16 com líquido atípico
- Grupo 2: dia 2011-03-12 com líquido atípico
- Grupo 3: dia 2011-03-11 com líquido atípico
- Grupo 3: dia 2011-03-12 com líquido atípico
- Grupo 3: dia 2011-03-13 com líquido atípico

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
