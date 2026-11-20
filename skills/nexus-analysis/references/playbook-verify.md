# Playbook VERIFY — mecânico + independente

> Objectivo da fase: só chamar o relatório "final" depois de (a) um check mecânico que PODE falhar dizer PASS e (b) uma lente fresca confirmar os claims contra a realidade. O autor a reler o próprio relatório NÃO é verificação — é a mesma lente que deixou passar o erro.

## Parte A — Check mecânico (com predição escrita ANTES)

Escreve primeiro: "espero secs=N+3, estado=1, ordem=1, verif=1, exit=0". Depois corre `scripts/verify-report.sh <relatorio> <N>` (versão empacotada e testada deste check, com dump por campo) — ou inline:

```bash
R=relatorio.md; N=7   # ajusta N ao número real de melhorias do TEU relatório
secs=$(grep -c "^## " $R)
estado=$(grep -c "^## Estado real verificado" $R)
ordem=$(grep -c "^## Ordem" $R)
verif=$(grep -c "^## Verificação independente" $R)
probs=$(grep -c "^\*\*Problema:" $R); accs=$(grep -c "^\*\*Acção:" $R); imps=$(grep -c "^\*\*Impacto:" $R)
echo "secs=$secs (esperado $((N+3))) estado=$estado ordem=$ordem verif=$verif probs=$probs accs=$accs imps=$imps"
[ "$secs" -eq $((N+3)) ] && [ "$estado" -eq 1 ] && [ "$ordem" -eq 1 ] && [ "$verif" -eq 1 ] \
  && [ "$probs" -eq $N ] && [ "$accs" -eq $N ] && [ "$imps" -eq $N ]; echo "exit=$?"
```

**Negative control (1ª vez que usas o script):** copia o relatório para a tua pasta de trabalho (não uses `/tmp` à mão: no Git Bash do Windows `/tmp` não coincide com a pasta temporária do sistema — usa `"${TMPDIR:-.}"` ou a pasta do projecto), remove da CÓPIA uma secção obrigatória (ou muda N para N+1) e confirma que o check dá exit=1. Ex.: `grep -v "^## Ordem" relatorio.md > "${TMPDIR:-.}/neg.md"; scripts/verify-report.sh "${TMPDIR:-.}/neg.md" 7` → exit=1. Check que nunca viste falhar não prova nada. Apaga a cópia e re-corre no original.

## Parte B — Review independente (regra de revisão independente)

### O que CONTA como independente
**NÃO contam:** os agentes de exploração da fase 2 (são os finders — re-usá-los é auto-confirmação), spot-checks feitos por ti (lente do autor), ou qualquer agente que recebeu o teu raciocínio. **Conta:** um agente NOVO, lançado DEPOIS do relatório escrito, que recebe só relatório+código. Tickar "zero findings" com auto-verificação foi o único desvio sistémico do 1º teste com modelo médio — o modelo fez tudo o resto bem e falhou exactamente aqui.

**Porque é que isto importa (caso interno do autor, não incluído):** o autor (modelo médio) auto-certificou "20 claims spot-checked, zero findings, FINAL". Um subagente fresh (mesmo modelo, prompt limpo) sobre os mesmos 2 relatórios encontrou **2 MAJOR + 12 MINOR** — sobretudo contagens erradas por 2× ou mais. Confirmado por spot-check terceiro: o revisor tinha razão em 4/4. **Lição dupla:** (1) o self-cert do autor não vale nada, mesmo com "20 claims verificados"; (2) um subagente fresh do MESMO modelo médio APANHA os erros do autor — a independência do contexto basta, não é preciso modelo mais forte.

### Mecânica: subagente na MESMA sessão chega — não precisas de outra sessão nem de outro modelo
Independência = **contexto fresh + prompt limpo + timing pós-relatório**, não "sessão diferente". Um subagente nasce sem a tua conversa — se lançaste agentes na fase EXPLORE, tens a capacidade; usa-a outra vez com um agente NOVO:
1. Relatório terminado → lança 1 subagente com o prompt da secção seguinte, **verbatim** — sem acrescentar contexto, explicações, ou "o autor concluiu X".
2. Mesmo modelo serve (os claims são mecânicos: greps, ficheiro:linha, contagens). Modelo mais forte só para claims de julgamento (arquitectura, risco).
3. **Teste de contaminação no output:** revisor que refere coisas que só o autor viu (raciocínio, descartes, nomes de fases internas) = contaminado → repete com prompt limpo.
4. **Sem subagentes no teu runtime?** Dois caminhos, por ordem: (a) **sessão nova / segundo modelo** — abre uma conversa limpa (outra janela, outro modelo ou outra pessoa), dá-lhe SÓ o relatório + acesso ao código e cola VERBATIM o prompt da secção «Prompt pronto para o revisor» abaixo; traz a lista de findings de volta e segue o loop de convergência. (b) **Se nenhuma sessão fresca é possível:** NÃO tiques o ISC de review; marca o relatório `mechanically-verified` (taxonomia no fim deste playbook), escreve na secção `## Verificação independente` «por rever — pedir review independente» (a secção tem de existir para o `verify-report.sh` passar) e di-lo no fecho. Nunca lhe chames `final`.

### O que dar ao revisor — e o que NÃO dar
- DAR: o relatório + acesso ao código/sistema + a instrução abaixo.
- NÃO DAR: o teu raciocínio, os reports dos agentes de exploração, a tua lista de descartes. Revisor contaminado com as tuas conclusões confirma-as em vez de as testar.

### Prompt pronto para o revisor (agente/sessão fresh, lente ≠ autor)

```
És um revisor independente. Recebes um relatório de análise (<path>) que afirma factos
sobre <sistema> com evidência ficheiro:linha. NÃO recebes o raciocínio do autor.

Spot-checka os claims contra a realidade:
1. Escolhe 10-15 claims: os mais citados na argumentação, os mais fortes (CRÍTICO,
   "zero", "nunca"), e TODOS os grep-zero (ausências são os mais fáceis de errar).
2. Por claim: verifica ficheiro:linha existe e diz o que o relatório afirma; re-corre
   os greps; confirma estado vivo (portas, processos) com comandos.
3. Procura também o que o relatório NÃO diz: 1-2 factos relevantes que faltem.

Output: por claim, CONFIRMADO / DIVERGENTE (com o valor real) / NÃO-VERIFICÁVEL.
Severidade nos divergentes: MAJOR (muda uma recomendação) / MINOR (detalhe).
Zero elogios; se tudo confirma, di-lo em 1 linha.
```

### Loop de convergência

**Conta os findings, nunca confies no rótulo do revisor** (exemplo observado: um passe fresh terminou com "ZERO FINDINGS" no veredicto... listando 3 MINOR factuais no corpo). MINOR ≠ zero; o executor lê a lista, conta, e decide — o rótulo do revisor é claim, a lista é a evidência.

1. Findings do revisor → corrige o relatório → **re-corre a Parte A** (fixes partem contagens).
2. MAJOR corrigido → 2º passe fresh (pode ser outro agente) confirma o fix — os teus fixes também podem introduzir erros (já aconteceu: a review apanhou 1 MAJOR + 1 MINOR, correcção, passe 2 confirmou zero).
3. Pára em **zero findings num passe completo** — tipicamente 1-2 rondas, mas em relatórios densos-em-contagens (UX/a11y com dezenas de greps) espera mais: num caso interno do autor (não incluído) levaram **7 passes** até zero. Os 2 primeiros passes trouxeram os 4 MAJOR (2 cada); os 4 seguintes trouxeram só MINOR novo (nenhum MAJOR); o 7º confirmou zero. Não é o mesmo erro a repetir-se, é cobertura incompleta por passe — mesmo depois de zero MAJOR, MINORs continuam a aparecer até ao 6º passe. Não é regresso infinito: relatório factual converge (ao contrário de re-audits semânticos de KB, que assimptotam) — mas orçamenta pelo relatório, não por um número fixo de rondas.
4. **Se tens vários canais de delegação (vários agentes/personas nomeados), usa identidades DIFERENTES por passe, não o mesmo revisor repetido.** No caso dos 7 passes, cada um foi um agente diferente, com identidade/persona própria. Nota honesta sobre o que os dados mostram: os MAJOR concentraram-se nos 2 primeiros passes (retornos decrescentes depois disso para MAJOR) — mas 4 das 5 identidades seguintes trouxeram MINOR novo que as anteriores tinham deixado passar, até ao passe 6. O mesmo revisor repetido tende a confirmar o que já confirmou (ponto cego estável); uma identidade nova traz um ângulo novo, tal como as lentes do EXPLORE — a evidência real suporta isto para MINOR de forma mais forte que para MAJOR. Se só tens 1 canal, repetir é melhor que nada — mas se tens vários, roda-os.
5. Regista o resultado na secção "Verificação independente" do relatório: claims checados, CONFIRMADO/CORRIGIDO um por linha, + factos novos que o revisor trouxe.

### DONE-language — taxonomia de estados (usa-a no checklist e no relatório)
1. `draft` — relatório escrito, nada verificado.
2. `mechanically-verified` — Parte A PASS com dump; review por correr → linguagem: "**por rever**".
3. `review-blocked-infra` — a infra de review está temporariamente indisponível (serviço de delegação saturado, sem runtime para agente fresh AGORA mas haverá). Regista a CAUSA + o **comando exacto de retoma** (prompt do revisor + path do relatório) no checklist — distingue-se de "runtime sem subagentes de todo" (esse fica `por rever` até alguém correr a review noutra sessão).
4. `final` — review fresh convergiu a zero findings num passe completo.
- Nunca: "análise completa" com review por correr.
- Fecho para o dono: além do ficheiro, entrega no chat um **resumo ordenado por importância** (1 linha por melhoria) — o dono decide em 30s sem abrir o relatório.
- **Commit+push no fecho**: só quando a política do workspace/utilizador o permite — política local proíbe commits não pedidos → regista "commit pendente de autorização" em vez de violar a política.

## Erros típicos

| Erro | Correcção |
|---|---|
| Autor relê e declara "verificado" | Parte B — lente fresh obrigatória |
| Dar ao revisor os reports dos agentes | Só relatório+código; contaminação confirma em vez de testar |
| Corrigir findings e não re-correr Parte A | Fixes partem contagens; re-corre sempre |
| Check mecânico nunca visto a falhar | Negative control na 1ª utilização |
| "PASS" sem valores | Dump por campo (secs=10 probs=7 ...) + exit code visível |
