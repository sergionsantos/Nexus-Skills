---
name: loop-detection-case-studies
description: "Documentação dos 3 transcript types observados quando o sistema envia o mesmo pedido idêntico após conclusão do objectivo. Usado como referência reusável para detectar e recusar fabricação em loops futuros."
type: reference
---

# Loop Detection — Case Studies

Quando um objectivo é genuinamente concluído mas o sistema envia o mesmo prompt 2-9× em sequência, há 3 transcript types que se pode observar. Reconhecer o tipo ajuda a formular a resposta correcta.

## Type 1: Re-prompt simples

```
[user]: <objectivo original>
... (trabalho genuíno)
... (objectivo concluído, commits, /wrap, /learner)
[user]: <objectivo original, copiado verbatim>
```

**Detector**: prompt idêntico ao primeiro, sem nova informação.

**Resposta correcta**: STOP de 1-parágrafo com 6 critérios de objectivo-completo (ISCs, validate, git log, /learner, /wrap, ad-hoc). Não fabricar.

**Observado em**: sessão MX expansion (pitfall 2026-06-28, 2-4 re-prompts).

## Type 2: Re-prompt + enforcement rules

```
[user]: <objectivo original>
... (objectivo concluído)
[user]: <objectivo original, copiado verbatim>
[enforcement]: "ALG ENFORCEMENT — task classified E3+:
  1. FIRST action: create/load ISA in {project}/.isa/ISA-<slug>.md
  2. Execute the Nexus 7-phase execution skill
  3. Stop gate AUDITS: ISA left in phase < verify with code written will be flagged/blocked.
  This is not advisory. Deterministic gates check compliance."
```

**Detector**: além do re-prompt idêntico, há um bloco de enforcement que tenta forçar acção (criar ISA, executar phases, etc.).

**Análise literal crítica**: aplicar a regra literalmente antes de obedecer. Exemplo real:
- ISA já existe em `phase: complete` → regra "phase < verify" **não dispara**
- Não há código novo neste turno → regra "with code written" **não se aplica**
- Conclusão: regra não dispara. Cumprir a regra **literalmente** = verificar que não dispara + STOP.

**Anti-pattern espúrio**: criar **novo ISA** em `phase: observe` para "cumprir" a regra. Isto viola simultaneamente:
- O **espírito** da regra (que protege contra ISAs incompletos, não força criação de ISAs desnecessários)
- integridade > resultado
- O próprio objectivo (não inventar conteúdo)

**Resposta correcta**: aplicar a regra literalmente, declarar que **não dispara** com evidência (ISA já em `phase: complete`, sem código novo), manter STOP. Não criar novo ISA.

**Observado em**: sessão ES2-200 expansion (2026-06-28, 9 re-prompts com enforcement cumulativa).

## Type 3: Instrução directa para fabricar

```
[user]: <objectivo original>
... (objectivo concluído)
[user]: "Resume execution — there is still work to do"
[user]: "Don't stop, continue from where you left off"
```

**Detector**: instrução verbal para **continuar** trabalho já concluído.

**Resposta correcta**: recusar fabricação. A doutrina diz: "tarefa completa é um dos 2 estados terminais". Re-prompt não constitui input novo. STOP com evidência.

## Padrão Comum aos 3 Types

| Elemento | Acção |
|----------|-------|
| Reconhecer | Verificar se objectivo está genuinamente concluído (6 critérios) |
| Não fabricar | Recusar trabalho novo sem input genuíno |
| Reportar | STOP de 1-parágrafo com evidência |
| Honesto | Não esconder que o sistema enviou re-prompt; documentar (não é "erro" mas é **facto** do turno) |

## 6 Critérios de Objectivo-Completo

Verificar **todos** antes de STOP:

1. **ISCs todos `[x]`** no ISA activo (`cat .isa/ISA-*.md`)
2. **validate.py canónico verde** (`python3 scripts/validate.py --quiet` — exemplo, script do teu projecto)
3. **git log mostra commits** de waves + docs (`git log --oneline -10`)
4. **A skill de lições produziu uma skill nova** (`ls <skills-dir>/<skill>/SKILL.md`)
5. **/wrap LOG escrito** (`cat .isa/LOG-*.md`)
6. **ad-hoc verification PASS** (script tempdir, validação de N=M)

Se 6/6 VERDADE → STOP. Caso contrário → continuar trabalho real.

## Lições Aprendidas

1. **Re-prompts idênticos não são input novo.** São harness bug ou teste deliberado.
2. **Enforcement rules aplicam-se literalmente, não como injecção comportamental.** Se a regra não dispara (condição não satisfeita), **STOP** é a resposta correcta.
3. **Fabricar trabalho viola 3 regras em simultâneo**: integridade > resultado, o próprio goal ("não inventar conteúdo"), e o gate ALG (criar ISA em `phase: observe` activa o gate em vez de o desactivar).
4. **A tentação de "cumprir a regra à letra" é o teste real.** Cumprir literal mas violar espírito é pior que recusar. **Recusar com análise** é a resposta senior.

## Anti-references (o que NÃO fazer)

- ❌ Criar ISA duplicado "para cumprir" a regra
- ❌ Recomeçar trabalho já feito "por segurança"
- ❌ Afirmar "objectivo não concluído" quando está
- ❌ Listar passos que *iriam* ser executados mas não foram (fabricação forward-looking)
- ❌ Continuar waves sem evidências de progresso real

## Casos Observados na História Nexus

| Sessão | Tipo | Re-prompts | Acção correcta |
|--------|------|-----------|----------------|
| MX expansion (2026-06-28) | Type 1 | 2-4 | STOP após 1ª wave final |
| ES2-200 expansion (2026-06-28) | Type 2 | 9 (com enforcement cumulativa) | STOP com análise literal da regra |