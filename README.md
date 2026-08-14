# Análise automatizada de testes A/B de cashback — Méliuz

Analisar um teste A/B de cashback hoje leva de 2 a 4 horas e o resultado
depende de quem está olhando. Esta solução padroniza a análise: qualquer
pessoa do time aponta o CSV do teste — direto no terminal ou pedindo em
linguagem natural para uma ferramenta de IA — e recebe a mesma análise, com
a mesma régua de decisão: **qual variante escalar para 100% do tráfego**.

## Quickstart

Não há nada para instalar: só Python 3 (biblioteca padrão, sem dependências).

```bash
python3 src/analisar_teste.py data/dataset_01_parceiroA.csv \
    --nome "Cashback Parceiro A — jan a abr/2011" \
    --descricao "3 variantes de taxa de cashback"
```

Isso gera três saídas:

1. **Relatório gerencial** em Markdown (`reports/relatorio_<dataset>.md`);
2. **JSON no stdout** com todas as métricas, testes estatísticos e a decisão;
3. **Linha na planilha de acompanhamento** (`planilha/registro_testes.csv`).

## Uso com IA (o fluxo pensado)

A solução foi desenhada para ser acionada por linguagem natural. Carregue o
arquivo [`prompts/analise_teste.md`](prompts/analise_teste.md) na sua
ferramenta de IA (Claude Code, Cursor, GPT personalizado, Gemini…) junto com
este repositório e peça, por exemplo:

> "Analise o teste novo do Parceiro D, o arquivo é `data/dataset_04_parceiroD.csv`"

A IA roda o pipeline determinístico, apresenta a decisão e os alertas, e
confirma o registro na planilha. Ela **não calcula nada** — todos os números
vêm do script, então o resultado não depende de quem (ou qual IA) rodou.

## Como a decisão é tomada

- **Métrica de decisão:** líquido diário do Méliuz = comissão − cashback. É
  o que sobra de receita depois de pagar o cashback — escalar uma variante
  que maximiza outra coisa destrói margem.
- **Regra:** escalar a variante de maior líquido médio diário somente se a
  vantagem for estatisticamente significativa contra **todas** as demais
  (p < 5% com correção de Bonferroni e IC95% bootstrap da diferença acima de
  zero) e a margem for positiva. Caso contrário: `INCONCLUSIVO` (manter o
  teste) ou `NAO_ESCALAR` (nenhuma variante viável).
- **Teste estatístico:** como as variantes rodam em paralelo nas mesmas
  datas, usa-se teste t pareado nas diferenças diárias — isso remove o ruído
  de calendário que afeta todas as variantes ao mesmo tempo. Se as datas não
  se alinharem, cai para Welch não pareado. O relatório indica qual foi usado.
- **Robustez a dados ruins:** schema inválido ou valor malformado aborta com
  mensagem indicando a linha; problemas não fatais (datas faltantes,
  duplicatas, taxa de cashback instável dentro da variante, dias atípicos,
  margem não positiva) viram **alertas** no relatório.

## Resultados dos 3 testes fornecidos

| Teste | Variantes | Decisão | Líquido/dia da vencedora | Relatório |
|---|---|---|---|---|
| Parceiro A (jan–abr/2011) | 3 (~4%, ~6%, ~7%) | Escalar Grupo 1 | R$ 4.399 | [link](reports/relatorio_dataset_01_parceiroA.md) |
| Parceiro B (mai–jun/2011) | 3 (4%, 6%, 9%) | Escalar Grupo 1 | R$ 4.698 | [link](reports/relatorio_dataset_02_parceiroB.md) |
| Parceiro C (jul–ago/2011) | 2 (5%, 7%) | Escalar Grupo 1 | R$ 773 | [link](reports/relatorio_dataset_03_parceiroC.md) |

Leituras que a análise traz automaticamente:

- **A:** as taxas de cashback variam muito de dia para dia dentro de cada
  grupo (3%–10%) — implementação ruidosa das variantes. A vantagem do Grupo 1
  sobre o Grupo 2 (R$ 513/dia) só é significativa porque o teste pareado por
  dia desconta o ruído de calendário.
- **B:** cashback maior não comprou volume — o Grupo 1 (4%) teve mais
  compradores/dia que as variantes de 6% e 9%, então o cashback adicional foi
  custo puro; Grupo 1 vence de lavada.
- **C:** o Grupo 2 (7%) entrega todo o retorno ao usuário — cashback =
  comissão, margem zero. Inválido por construção; Grupo 1 é a única variante
  viável.

## Planilha de acompanhamento

Cada análise registra automaticamente uma linha em
[`planilha/registro_testes.csv`](planilha/registro_testes.csv) com nome,
descrição, resultado e decisão (mínimo exigido pelo case) mais parceiro,
período e link do relatório.

**Versão pública no Google Sheets:** https://docs.google.com/spreadsheets/d/10IcpBJzlmp_XDhu0X15QPE6L4p-lXIScjJ5Wkp27bWo/edit?usp=sharing

## Schema esperado de novos datasets

Mesmo schema dos CSVs em `data/` — uma linha por variante por dia:

| Coluna | Tipo | Descrição |
|---|---|---|
| `Data` | YYYY-MM-DD | Data da observação |
| `Grupos de usuários` | string | Variante do teste (Grupo 1, Grupo 2, …) |
| `Parceiro` | string | Parceiro do teste |
| `compradores` | int | Usuários únicos que compraram no dia |
| `comissão` | string (R$) | Comissão paga pelo parceiro ao Méliuz no dia |
| `cashback` | string (R$) | Cashback distribuído aos usuários no dia |
| `vendas totais` | string (R$) | GMV no dia |

Valores monetários no formato `"R$ 10.273"` (também aceita `"R$ 1.234,56"`).
Número de variantes e período são livres — nada no código é específico de um
parceiro.

## Testes

```bash
python3 -m unittest discover -s tests
```

## Estrutura

```
├── prompts/analise_teste.md   # instrução que transforma qualquer IA em interface da solução
├── src/
│   ├── analisar_teste.py      # CLI / ponto de entrada
│   ├── leitura_csv.py         # parse e validação do schema
│   ├── metricas.py            # métricas por variante + alertas de qualidade
│   ├── estatistica.py         # t pareado / Welch / bootstrap (stdlib puro)
│   ├── decisao.py             # regras de decisão (ESCALAR / INCONCLUSIVO / NAO_ESCALAR)
│   ├── relatorio.py           # relatório gerencial em Markdown
│   ├── registro.py            # linha na planilha de acompanhamento
│   └── formatacao.py          # números em pt-BR
├── tests/                     # python3 -m unittest discover -s tests
├── data/                      # datasets de entrada
├── reports/                   # relatórios gerados
└── planilha/                  # registro consolidado dos testes
```

## Premissas e limitações

- O dataset não traz visitantes/exposição por grupo: assume-se split de
  tráfego equivalente entre variantes e comparam-se médias diárias (não há
  como calcular taxa de conversão).
- Líquido = comissão − cashback, antes de custos operacionais.
- Sazonalidade de curto prazo não é modelada; o pareamento por dia e os
  períodos simétricos entre grupos mitigam o efeito.
