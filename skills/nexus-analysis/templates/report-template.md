# {Sistema} — {N} Melhorias Substanciais

> Análise: {agente}, {data}. Método: {X} agentes de exploração paralelos ({lentes}) sobre {superfície: dirs, linhas, ficheiros}, {docs/LOGs consultados}. Cada recomendação tem evidência ficheiro:linha.

## Resumo executivo (opcional — incluir quando o dono decide prioridades sem ler os detalhes técnicos)

{3-6 bullets, linguagem de negócio, zero paths/greps. Por bullet: o que ganha + custo aproximado. Ex.: "A app está em baixo — meio dia de trabalho recupera-a (nº1)." Fechar com 1 linha de recomendação: "Se só houver tempo para uma: #{X}, porque {razão de negócio}."}

## Estado real verificado ({data})

- {o que está de facto a correr / parado — com comando+resultado}
- {onde os docs/LOGs estão desactualizados}
- {divergências críticas novas descobertas no grounding}

---

## 1. {Título da melhoria} ({CRÍTICO se aplicável})

**Problema:** {frase}
- {facto com evidência ficheiro:linha ou comando}
- {grep-zero conta como evidência de ausência}

**Acção:** {passos numerados, ordenados por rácio ganho/diff; nomear a opção mínima que chega}

**Impacto:** {porquê importa no contexto real do dono}. Esforço: {horas|N dias}.

## 2..N. {idem — garantir ≥1 de cada fonte: partido / latente / transformação}

---

## Ordem e racional

| # | Melhoria | Porquê nesta posição |
|---|---|---|
| 1 | {nome curto} | {1 linha: pré-condição / maior ganho por diff / seguro de vida / transformação / coerência} |

Sequência prática sugerida: {encadeamento + paralelismos, ligando melhorias por número: "#5 herda núcleo testado por #4"}.

---

## Verificação independente (sessão 2, {data})

Revisão por lente fresh ({método}): {claims spot-checked com resultado CONFIRMADO/CORRIGIDO, um por linha}

{Zero findings → análise final | findings corrigidos → re-verificado}

{Nota de trade-off deliberado, se a ordem sacrifica rigor por pragmatismo — explicitar e dar a alternativa.}
