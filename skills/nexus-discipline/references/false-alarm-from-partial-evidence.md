# Falso alarme a partir de evidência parcial

**Classe:** simétrica da armadilha nº1 do `P3`. Essa é o falso **negativo** — ler para confirmar
e perder a má notícia. Esta é o falso **positivo**: ler metade e gritar. Em trabalho single-agent
custa embaraço; em multi-agente custa uma **ordem errada a um executor** que estava certo, e
gasta a confiança que se precisa quando o alarme for real.

## Detector

Estás a um passo desta armadilha quando as três condições se juntam:

1. Vais escrever uma frase de emergência — *"PARA TUDO"*, *"isto é grave"*, *"encontrei um bug
   crítico"*.
2. A conclusão vem de uma **vista derivada** e não do estado: linhas `-` de um diff, uma
   projecção SQL, um `grep -c`, um screenshot parcial.
3. Não corriste ainda o comando que **falsificaria** o alarme.

## Anti-pattern

O instinto é bom: detectaste algo que contradiz uma assunção, e a doutrina manda replanear
**antes** da próxima tool call. Parece rigor. O erro é replanear a partir de uma leitura que
ainda não está fechada — e a urgência sentida ("isto pode destruir dados") é exactamente o que
suprime o passo de fecho.

## Forma correcta

Antes de alarmar, fecha a leitura — três regras concretas:

- **Diff:** emparelha cada `-` com o `+` correspondente. Uma linha removida e re-adicionada com
  comentário diferente aparece como remoção se só olhares para o `-`.
- **Query:** confirma que a projecção inclui a coluna que **discrimina** (chave, id, tenant)
  antes de concluir duplicação ou não-determinismo. `ORDER BY version LIMIT 3` sem a chave não
  distingue "duas versões da mesma linha" de "duas linhas diferentes".
- **Sempre:** escreve o comando que provaria que estás errado, e corre-o. Se não consegues
  formular esse comando, não tens alarme — tens suspeita, e diz-se como suspeita.

Depois, se o alarme se confirmar, ele vale muito mais: chega com o dump que o sustenta.

## Evidência (sessão 2026-08-31)

**Instância 1 — o `-` sem o `+`.** Escrevi: *"**PARA TUDO.** Encontrei o que a diagnose dele não
viu, e é grave: o diff de `prisma/schema.prisma` **remove `progress Json`** — isso é a fase 2
(M2.6), o step irreversível."* Base: só as linhas `-` do diff.

Falsificação, 1 comando:

```
$ grep -c 'progress    Json' prisma/schema.prisma
1
```

O diff tinha **as duas** linhas:
`-  progress    Json  // { current: 3, target: 5 }` e
`+  progress    Json  // { current: 3, target: 5 } — DROPPED in M2 step 6`.
Não havia remoção: mudou o comentário. Se tivesse agido, teria mandado o executor "restaurar"
uma coluna que nunca saiu, a meio de uma migração em 2 fases.

**Instância 2 — a projecção sem a chave.** Dez minutos depois, na mesma sessão:
*"o dump revela **duas linhas com `version: 1`**, uma delas com `levelCurve: null`. Se o
`ConfigService` escolher por versão, a escolha é não-determinística."*

```
$ SELECT version, value->'levelCurve' ... ORDER BY version DESC LIMIT 3
[{"version":1,"levelCurve":{"base":100,"multiplier":1.5}},{"version":1,"levelCurve":null}]
```

Falsificação: acrescentar a coluna discriminante e reler o selector do código
(`prisma.remoteConfig.upsert({ where: { key: 'gamification' } })`):

```
$ SELECT key, version, value->'levelCurve' ...
[{"key":"gamification","version":1,"levelCurve":{...multiplier:1.5}},
 {"key":"features","version":1,"levelCurve":null}]
```

Chaves **diferentes**, não versões concorrentes. Zero não-determinismo. O `levelCurve: null` da
segunda linha é simplesmente uma chave que não tem esse campo.

**Passing check (critério a):** ambos os alarmes foram fechados com um comando de exit 0 e output
citável — `grep -c` → `1`, e a query com `key` → duas chaves distintas. Em nenhum dos casos foi
preciso opinião para resolver: faltava uma coluna e um emparelhamento.

## O que não funcionou

- **Hipótese descartada 1:** *"a edição de schema da fase 1 contém uma remoção da fase 2"*.
  Eliminada pelo `grep -c` acima. O que a gerou: ler o output de `git diff | grep -E '^[-+]'`
  **filtrado só pelos `-`** durante a leitura mental, apesar de os `+` estarem no mesmo output.
- **Hipótese descartada 2:** *"o `ConfigService` escolhe a linha por `version DESC`, logo com
  duas linhas empatadas a escolha é não-determinística"*. Eliminada por ler o selector real —
  `upsert` por `key`, com unique nessa coluna. O que a gerou: escrever a sonda com as colunas que
  me interessavam (`version`, `levelCurve`) em vez das colunas que **distinguem linhas**.
- **Não funcionou também** a auto-correcção tardia: nas duas vezes retractei-me no mesmo turno,
  o que limita o dano mas não o elimina — o dono já tinha lido o alarme. A correcção tem de ser
  *antes* de escrever, não depois.

## Scope

**Aplica-se** a: leitura de diffs, projecções SQL/JSON, contagens de `grep`, e qualquer vista
derivada usada para justificar uma acção urgente — especialmente quando há um executor a quem
se pode dar uma ordem errada.

**Não se aplica** a: alarmes de ferramenta com output completo e inequívoco (exit code + erro
verbatim de um comando que corri agora), nem a suspeitas comunicadas **como** suspeitas
("isto merece verificação, ainda não confirmei"). Esta última forma é sempre legítima e é a
saída correcta quando não consegues formular o comando falsificador.
