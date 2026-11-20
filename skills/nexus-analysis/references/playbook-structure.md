# Playbook STRUCTURE — escrever o relatório

> Objectivo da fase: relatório onde um leitor decide em 2 min (tabela de ordem) e um executor arranca sem re-investigar (evidência + acção concreta). Usa `templates/report-template.md`; este playbook ensina a PREENCHÊ-LO bem.

## Anatomia de um item exemplar (anotado; abreviado de uma análise real de um gestor de tarefas web)

```
## 2. Expor os metadados que o schema já suporta — due dates, estimates, templates, initiatives
   └─ título = acção+objecto, não "Problema com X"; sub-itens do cluster visíveis já no título

**Problema:** é um *gestor de tarefas* onde não se consegue marcar uma data de entrega. O backend está pronto; falta só UI:
   └─ 1ª frase = a dor em linguagem de utilizador; 2ª = o diagnóstico em 1 linha
- `issues.due_date` (`0003_issues.sql`) — filtrável (`lib/filters.ts`) e mutável, mas issue-detail.tsx tem **0 hits** de `due_date` — sem picker.
   └─ cada bullet: facto + evidência ficheiro:linha; grep-zero citado como prova
- Menores: cycle settings, snooze de triage, `previous_identifiers`.
   └─ cauda do cluster comprimida numa linha "Menores:" — presente mas sem inchar

**Acção:** due-date picker (`<input type="date">` chega) + estimate selector → templates UI → initiatives page. Ordenado por rácio ganho/diff.
   └─ sequência interna explícita; A OPÇÃO MÍNIMA NOMEADA ("<input type=date> chega") — trava o executor de over-engineering

**Impacto:** maior ganho funcional por linha de código em todo o backlog; transforma o uso diário. Esforço: 1-3 dias.
   └─ impacto = 1 frase comparativa (porquê ESTE e não outro); esforço sempre em horas/dias
```

## Regras de escrita por campo

- **Problema:** 1 frase de dor + bullets de evidência. Nunca prosa corrida; nunca bullet sem evidência.
- **Acção:** passos numerados/encadeados, ordenados por ganho/diff. Nomeia a opção mínima E a recomendada quando diferem ("Alternativa mínima: route handlers /api/agent/*; recomendado: MCP server"). Não detalhes steps de build — isso é /nexus-plan-spec.
- **Impacto:** porquê importa NO CONTEXTO REAL do dono (não "best practice diz"). Se precisa de parágrafo, a melhoria é fraca. Fecha sempre com `Esforço: X`.
- **Marcador (CRÍTICO):** só no item que bloqueia tudo o resto; 2 "CRÍTICO" = nenhum é.

## Tabela de ordem — heurísticas por ordem de aplicação

Aplica por esta ordem; a primeira que decidir a posição, decide:
1. **Pré-condição** primeiro — sem isto nada existe (app tem de correr)
2. **Maior ganho/diff** cedo — vitórias visíveis criam tracção
3. **Seguro de vida** antes de mexer na camada que ele protege (testes do sync antes de features que tocam sync)
4. **Transformação** depois do núcleo seguro (a API herda um núcleo testado)
5. **Escala** quando o volume vem a caminho
6. **Coerência/QoL** no fim — não bloqueia

Cada linha da tabela: `# · nome curto · porquê nesta posição (1 linha)`. Depois: **sequência prática** ("1 → 2 → 3 → 4 antes de 5/6; 7 em paralelo") com **cross-refs por número** ("#5 herda núcleo testado por #4").

## Trade-off deliberado = nota explícita

Se a ordem sacrifica rigor por pragmatismo, di-lo E dá a alternativa. Exemplo real: "#4 argumenta 'testar antes de mexer', mas #2/#3 vêm antes — diffs pequenos, aditivos, risco baixo no sync; quem preferir rigor máximo troca #4 para segundo lugar." Mostrar o julgamento é o que torna a ordem confiável; escondê-lo torna-a arbitrária.

## Resumo executivo (opcional)

Incluir quando o dono decide prioridades sem ler os 20 achados técnicos (relatório vai para alguém que não vai executar). 3-6 bullets em linguagem de negócio — zero paths, zero greps; por bullet: o que ganha + custo aproximado; fecho com "se só houver tempo para uma: #{X}, porque {razão}". Escreve-o em ÚLTIMO (depois da ordem fechada — é destilação, não rascunho). Não substitui a tabela de ordem: o resumo diz "o quê e porquê importa", a tabela diz "em que sequência e porquê essa". Formato no `templates/report-template.md`.

## Erros típicos

| Erro | Correcção |
|---|---|
| Título "Problema com testes" | Título = acção+objecto ("Testar o sync layer + corrigir bugs de invalidação") |
| Resumo executivo com paths/greps | Linguagem de negócio; a evidência fica nas secções técnicas |
| Acção vaga ("melhorar error handling") | Passos concretos + opção mínima nomeada |
| Impacto genérico ("aumenta qualidade") | 1 frase comparativa ancorada no contexto do dono |
| Contagem citada sem o comando que a gerou | Regista comando exacto (corpus+padrão) junto ao número — a review re-conta e diverge se o padrão for ambíguo (caso interno do autor, não incluído: rondas evitáveis) |
| Ordem sem racional visível | Tabela posição→porquê + trade-offs por extenso |
| Relatório vira spec de implementação | Acção pára no "o quê + por onde começar"; steps → /nexus-plan-spec |
