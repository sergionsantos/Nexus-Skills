# Fresh-Context Verifier Protocol (Rule 0 operacionalizada)

> Princípio: uma lente fresca só apanha os teus blind spots se **não partilhar os teus assumptos**. O revisor recebe SPEC + OUTPUT. Nunca o teu raciocínio.

## INCLUIR no prompt do revisor

1. **Spec/ISA** — o que o deliverable DEVIA fazer (ISCs, behavior spec do step, requisitos verbatim).
2. **Output** — o código/artefacto em si (paths para ler, ou diff `git diff sha..sha`).
3. **Comando de verify do projecto** — como correr o check real (test/build/lint) e o expected.
4. **Critério de aceitação** — "findings com severidade; zero findings = APPROVE".

## EXCLUIR (contamina a lente)

- O teu raciocínio, justificações, trade-offs que consideraste.
- "Tentei X mas não funcionou porque Y" — o revisor deve REDESCOBRIR Y sozinho.
- O histórico da conversa.
- A tua auto-avaliação ("acho que está sólido excepto...").

## Template literal de dispatch

```python
Agent(subagent_type="oh-my-claudecode:code-reviewer",  # ex.: só se tiveres esse plugin; usa o teu subagente de review. Código
      # ex.: subagent_type="critic" / "oh-my-claudecode:critic" (se existirem) — planos/docs
      prompt="""REVIEW INDEPENDENTE — adversarial, tenta REFUTAR que está correcto.

SPEC (o que deve fazer):
<ISCs/behavior spec verbatim — sem comentário teu>

OUTPUT a rever:
<paths exactos para leres | diff>

VERIFY do projecto:
<comando + expected>

FORMATO DE RESPOSTA (obrigatório):
- findings APENAS: `path:linha · SEVERIDADE (BLOCKER/HIGH/MED/LOW) · problema · fix proposto`
- zero prosa, zero elogios, zero resumo do que o código faz
- se zero findings: exactamente `APPROVE — zero findings`
""")
```

## Loop

1. Dispatch → findings.
2. Corrige BLOCKER/HIGH → **re-verifica os fixes** (fixes regridem à mesma taxa de código novo).
3. Re-dispatch **só do diff** dos fixes (não o deliverable inteiro).
4. Repete até `APPROVE — zero findings`. Converge em 1-2 rondas; 3+ = o deliverable tem problema estrutural, pára e repensa.

## Armadilhas conhecidas

- **Idle ≠ done** (multi-agent): pede sempre o relatório explícito; notificação de idle não é entrega.
- Revisor devolve prosa simpática → re-dispatch com "FORMATO DE RESPOSTA obrigatório" reforçado.
- Auto-review disfarçada: passar o teu raciocínio "para contexto" = contaminar. Não.
- Review de doc/skill (não-código): mesma estrutura, lente = "um modelo médio consegue executar isto sem adivinhar?"
