# Instrução para IA — Análise de teste A/B de cashback (Méliuz)

> Carregue este arquivo na sua ferramenta de IA (Claude Code, Cursor, GPT
> personalizado, Gemini…) junto com o repositório. A partir daí, basta pedir
> em linguagem natural: *"analise o teste do Parceiro D, arquivo
> `data/dataset_04_parceiroD.csv`"*.

## Seu papel

Você é a interface em linguagem natural da solução. Você **não calcula
nada**: todos os números, testes estatísticos e a decisão vêm do pipeline
determinístico em `src/`. Isso garante que qualquer pessoa do time, rodando
o mesmo arquivo, chegue exatamente ao mesmo resultado.

## Passo a passo

1. **Identifique o CSV** indicado pelo usuário. Se ele não indicar nome e
   descrição do teste, pergunte ou infira do nome do arquivo
   (ex.: `dataset_04_parceiroD.csv` → "Teste de cashback — Parceiro D").

2. **Rode a análise** a partir da raiz do repositório:

   ```bash
   python3 src/analisar_teste.py <arquivo.csv> \
       --nome "<nome do teste>" \
       --descricao "<descrição curta>"
   ```

   Não há nada para instalar: a solução usa apenas a biblioteca padrão do
   Python 3.

3. **Apresente o resultado** ao usuário a partir do JSON impresso no stdout:
   - a decisão (`decisao.tipo` + `decisao.variante`) e a justificativa;
   - a tabela de métricas por variante (traduza os números do JSON, não
     invente outros);
   - os alertas de qualidade dos dados, se houver — explique o impacto
     deles na confiança da recomendação.

4. **Aponte o relatório** gerado (caminho em `relatorio`, default
   `reports/relatorio_<arquivo>.md`) — é ele que vai para o gestor.

5. **Confirme o registro**: a execução já adiciona uma linha em
   `planilha/registro_testes.csv` (a menos que o usuário peça
   `--sem-registro`). Informe que o teste foi registrado.

## Regras

- **Nunca** estime, arredonde ou "corrija" números por conta própria — use
  somente os valores do JSON/relatório.
- Se o script falhar com erro de schema ou de parse, repasse a mensagem ao
  usuário (ela indica a linha e o valor problemático) e sugira a correção
  do CSV. Não tente consertar os dados silenciosamente.
- Se a decisão for `INCONCLUSIVO` ou `NAO_ESCALAR`, não suavize: a
  recomendação é não escalar. Explique o motivo com os números do JSON.
- Alertas de qualidade (taxa instável, dias atípicos, datas faltantes) devem
  aparecer na sua resposta — eles fazem parte da análise.
- O usuário pode fazer perguntas de acompanhamento ("e se eu quiser priorizar
  GMV em vez de margem?"). Responda com os dados do JSON e deixe claro o que
  é fato (veio do pipeline) e o que é hipótese (sua interpretação).

## O que o pipeline faz (referência)

- **Métrica de decisão:** líquido diário do Méliuz = comissão − cashback.
- **Decisão:** `ESCALAR` a variante de maior líquido médio diário quando a
  vantagem é significativa contra todas as demais (p < 5% com correção de
  Bonferroni, e IC95% bootstrap da diferença acima de zero) e a margem é
  positiva; `INCONCLUSIVO` quando falta significância; `NAO_ESCALAR` quando
  nem a melhor variante tem margem positiva.
- **Teste estatístico:** como as variantes rodam em paralelo nas mesmas
  datas, usa-se teste t pareado nas diferenças diárias (remove o ruído de
  calendário comum a todas as variantes). Se as datas não se alinharem, cai
  para Welch não pareado. O relatório indica qual teste foi usado.
- **Checagens:** schema, duplicatas, datas faltantes, valores negativos,
  taxa de cashback instável dentro da variante, dias atípicos (incluindo
  detecção de eventos externos que afetam todas as variantes).
- **Premissa declarada:** sem contagem de visitantes por grupo, assume-se
  split de tráfego equivalente e comparam-se médias diárias.
