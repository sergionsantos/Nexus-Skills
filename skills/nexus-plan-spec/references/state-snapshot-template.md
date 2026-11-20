# state-snapshot — template por milestone (§0.3 / §7 da skill nexus-plan-spec)

Um `state-snapshot.md` por milestone, escrito no fim do pass que emite esse milestone. Externaliza a simulação mental do §0.3: o estado ACUMULADO contra o qual o próximo milestone vai ser escrito. Sem snapshot, o autor escreve steps contra o estado imaginado — a classe de erro que o §0.3 existe para matar.

## Localização

`<plano>/state-snapshots/state-M<nn>.md` (sibling dos ficheiros de milestone). O snapshot de M(n) é input obrigatório do pass que escreve M(n+1).

## Template

```markdown
# State snapshot — após M<nn> (<título do milestone>)
data: <YYYY-MM-DD> · pass: <n> · autor: <modelo>

## Ficheiros existentes (só os tocados até aqui)
| Path | Criado em | Último edit | Âncoras vivas (para edits futuros) |
|---|---|---|---|
| src/lib/auth.ts | M2.1 | M4.3 | `export async function login` · `// ROUTES-END` |

<!-- Ficheiro editado >=3x: âncoras de prosa deixam de ser fiáveis — o próximo
     step que o toca deve usar listagem integral (regra §7). Marcar com ⚠️. -->

## Estado do DB
- Migrations aplicadas: 001..0<nn> (última: `0<nn>_<slug>.sql`)
- Tabelas/constraints relevantes p/ próximos milestones: <lista>
- Dados de teste pinados: <ex.: issue ITEM-7 status=Backlog, criada em M3.2>

## Ambiente / processos
- Serviços up esperados: <containers, portas>
- Env vars introduzidas até aqui: <nome=valor VERIFICADO>

## Decisões consumidas / novas
- Consumidas neste milestone: D<##>, D<##>
- Novas registadas: D<##> (<1 linha do porquê>)

## Pendentes que atravessam a fronteira
- <verify adiado, GATE por aprovar, Open Question em aberto — com pointer>
```

## Regras de uso

1. **Escrever no momento** (write-as-you-go, §5) — snapshot reconstruído depois é ficção com formato de facto.
2. Cada linha de "Ficheiros existentes" tem de ser derivável dos steps emitidos — o snapshot não inventa estado.
3. Divergência detectada entre snapshot e realidade na execução → executor PÁRA (VERIFY-PREFLIGHT-GATE, skill nexus-discipline).
4. Plano ≤10 steps: snapshot único no fim dispensa a cadência por milestone.
