---
name: session-resume
description: "Re-entry protocol for long-running work picked up mid-way — a fresh session resumes a project (build plan, KB expansion, migration, research) in ≤2 min without rediscovery or wrong assumptions. Use when the user says 'resume project X', 'continue where we left off', 'go back to <project>', or when a session opens in a project that has re-entry artifacts (README-EXECUTOR, wrap LOG, ISA in a non-complete phase, a status file). Also load when the agent is about to say 'done', 'fixed', 'implemented', 'verified', 'ready to merge', or 'approved by the owner' without a matching verification command run in the same turn — this skill carries the done-language discipline (no completion claim without fresh verify evidence). Portuguese/English."
version: 1.0.0
status: active
category: nexus
tags: [nexus, resume, reentry, long-horizon, handoff, verify]
linked_files:
  templates:
    - "templates/reentry-readme.md"
  scripts:
    - "scripts/recover-from-failed-patch.sh"  # diagnoses an edit tool that reported success but did not persist; exit 1 = not persisted, exit 0 = applied
  references:
    - "references/pitfalls-avancados.md"
    - "references/self-report-fabrication.md"  # case study: fabricated 'reviewed by the owner' claim
---

# session-resume — retomar sem redescobrir nem assumir

> **Contrato:** cada sessão nasce em branco; trabalho longo sobrevive em estado EXTERNO (ficheiros, git, issue tracker). Este skill garante que a re-entrada lê esse estado em vez de o reinventar — e que detecta quando a realidade divergiu do que ficou escrito. Custo: ~2 min de checklist antes de tocar em qualquer coisa. Caso real do custo de não o fazer: sessão assumiu "M0 já executado" quando estava a 3/14 — quase re-executou trabalho e propôs gates errados.

Glossário mínimo: **ISC** = critério de aceitação binário (`- [ ]`) dentro de um ISA, ticado só com evidência. **ISA** = ficheiro de especificação/estado de uma tarefa (`.isa/ISA-<nome>.md`, com campo `phase:` e registo de execução); pode ser produzido pela skill opcional `nexus-discipline`. **Folha de re-entrada** = README-EXECUTOR: documento de passagem de turno de um projecto. **ISA-Lite** = versão reduzida de um ISA, para um passo ou fase (os intermédios ficam superseded pelo mais recente). **pane** = painel/terminal onde uma sessão de agente corre; **orquestrador** = agente ou sessão que coordena outros e/ou escreve o ficheiro de estado; **hook** = script que o ambiente corre automaticamente em certos eventos (ex.: aviso de verificação stale). **Contrato `STATUS=…@@DONE`** = formato de estado descrito no passo 1.0.

`nexus-discipline` é uma skill irmã deste repositório (`../nexus-discipline`) e é **opcional**: sem ela, o ISA é qualquer ficheiro de estado/especificação do teu projecto (com fase e registo do que foi feito). Nada disto é obrigatório: se o teu projecto usa outros nomes, aplica o mesmo princípio.

## Workflow — checklist de entrada (ordem fixa)

### 1. LOCALIZAR os artefactos de re-entrada (por ordem de autoridade)

0. **Ficheiro de estado activo** (se o projecto usar um: ex. `STATUS`, `state.md`, ficheiro escrito por um orquestrador/pane): é o indicador mais fresco do ponto de pausa real; o ISA mestre pode estar vários milestones atrás. Ler PRIMEIRO.
   - Contrato típico: uma linha por turno `STATUS=working|done|blocked|need SUMMARY="≤12 palavras" FILES=... VERIFY=pass|fail|n/a` + terminador `@@DONE`/`@@BLOCKED`/`@@NEED` + uma linha com o que o dono tem de fazer. Sem narrativa livre.
   - **Só o último bloco completo conta.** Se o ficheiro foi sobrescrito/truncado a meio, o último terminador completo (`@@...`) é a verdade, não a chave `STATUS=` do cabeçalho (`STATUS=working` + último terminador `@@DONE` = overwrite parcial; escrever um `STATUS=done` explícito na próxima sessão em vez de deixar o resíduo).
   - **`@@NEED` com acção do dono** (clicar, responder, aprovar): não tentar exercitar a acção — é intervenção humana. Apresentar menu compacto (já fiz / lembra-me onde / encerrar tema / outro foco) e parar.
1. `<projecto>/plan/00-README-EXECUTOR.md` ou `<projecto>/README-EXECUTOR.md` — folha de turno canónica (se existe, é a autoridade documental).
2. `<projecto>/.isa/ISA-*.md` — campo `phase:` + registo de execução = onde a execução está exactamente.
3. `<projecto>/LOG.md`, `CHANGELOG.md` ou o último "wrap" do tema (ver skill `session-wrap`).
4. **Memória persistente, se existir** (ferramenta de memória do agente, notas, wiki): pesquisar "<projecto> wrap re-entrada" para achar o LOG quando o caminho não é óbvio. Se não tens memória persistente, salta este passo: `README`, `LOG` e `git log` chegam.

Nenhum encontrado → não há folha de turno: reconstrói a partir de `git log` + ficheiros, e **cria a folha** com `templates/reentry-readme.md` antes de começar.

**⚠️ Pitfall "issue tracker é fonte canónica, ficheiros locais são reflexo":** se o projecto usa um issue tracker (GitHub Issues, Linear, Jira, …), consulta o estado oficial das issues ANTES de tratar artefactos locais. `README-EXECUTOR`/`plan.json` ficam obsoletos no momento em que outro agente fecha/move uma issue sem actualizar a folha. Procedimento:
1. Identifica o tracker (procura `#123`, `ABC-123`, URLs nos `plan/*`, README, `*.md`: `grep -rE '[A-Z]+-[0-9]+' <projecto>/plan/ <projecto>/*.md | head`).
2. Lista as issues que te tocam (ex.: `gh issue list --assignee @me`) e abre as relevantes (`gh issue view N`).
3. Se o working tree diverge do tracker (passos "todo" local mas "done" no tracker, ou o inverso) → **autoridade é o tracker**; rectifica a folha local.

**⚠️ Pitfall "tracker offline ≠ credenciais erradas":** erros de rede (`fetch failed`) e de credenciais (`missing credentials`) parecem-se. Antes de pedires ao utilizador para rever passwords, faz um probe TCP/HTTP ao serviço: `curl -sS -m 3 -o /dev/null -w '%{http_code}\n' "$URL/health"` — `000` = serviço offline (parado, IP/porta errados, firewall); `200` = serviço up, o problema é auth; `401` = up mas precisa de token.

**⚠️ Pitfall "ferramenta de pesquisa falha em ficheiros untracked":** ferramentas de search/grep do agente podem ignorar ficheiros untracked ou ignorados. Para inventariar artefactos de re-entrada usa SEMPRE `git status --short` primeiro, depois `ls -la` nas localizações canónicas, e só depois a pesquisa de conteúdo.

**⚠️ Pitfall "path do template ≠ path da instância":** ao criar o ISA da nova fase, não escrevas no caminho do template (read-only, às vezes protegido por guard). Instâncias vão em `<project-root>/.isa/ISA-<nome>.md` (`mkdir -p .isa/`).

### 2. ESTADO — extrair 3 factos antes de agir

- **Último passo VERIFICADO** (não "último tocado" — só conta com verify/dump registado)
- **Próximo passo** + as suas dependências
- **Decisões travadas** que o próximo passo consome (D##, versões, portas, paths)

### 3. DIVERGÊNCIA — re-verificar o ambiente (o passo que salva)

Os factos do README têm DATA. Ambiente é estado vivo, não pressuposto:

```bash
# exemplos — adapta ao projecto:
docker ps --format '{{.Names}} {{.Status}}'     # containers do README ainda up?
git -C <repo> log --oneline -3                   # commits de OUTRA sessão entretanto?
git -C <repo> status --short                     # working tree como esperado? (untracked + modified)
node -v                                          # versões ainda as travadas?
```

**Sinal de mão paralela:** ficheiros `*.bak.<ferramenta>` na raiz de paths de infra (ex.: `docker-compose.yml.bak.x`) = outra sessão editou + fez backup. Investigar SEM tocar até perceber o quê; nunca apagar como "lixo".

**Regra de decisão:**
- Tudo bate → continua para o próximo passo.
- **Divergência encontrada** (container morto, commits novos, versões mudadas, ficheiros alterados) → **PÁRA**: dump tabular (Esperado do README vs Real), actualiza a folha, e reporta ao utilizador se a divergência muda o plano. Trabalho paralelo de outra sessão é a causa nº1.
- **Divergência sem explicação** → NÃO avançar. Apresentar 3 opções: (a) commitar agora em commit separado, (b) reverter para o estado do último wrap, (c) investigar antes de decidir. Não escolher pelo utilizador.
- **Snapshots stale:** uma lista automática de "ficheiros alterados" pode citar um ficheiro que já não existe — confirma com `find <path> -name '<basename>'` antes de mexer.
- **Pointer files envelhecem** (ficheiros de "estado de fecho" escritos uma vez): byte-counts e contagens neles NUNCA são ground-truth, mesmo com <48h. `wc -c <ficheiro real>` e uma asserção por conteúdo (`grep -c`) antes de confirmar paridade.

### 4. ANUNCIAR a re-entrada (1 marco, compacto)

`Retomado <projecto>: último verificado = <X>, próximo = <Y>, ambiente ✅ (ou ⚠️ divergências: ...)` — e só então trabalhar.

### 5. À SAÍDA — manter a folha viva

Antes de fechar a sessão: actualizar "Estado actual" da folha (último verificado, próximo passo, data) + `session-wrap` se o tema fecha. Faz commit do ISA que sustenta o trabalho (um `.isa/ISA-*.md` untracked no fecho é história perdida). Folha desactualizada é pior que folha nenhuma — mente com autoridade.

## Done-language: nada de "done" sem verify deste turno

Regra de ouro durante e depois da retoma:
- **"Done/verificado/implementado" exige verify real corrido NESTE turno**, com evidência visível: comando + exit code + output literal. Senão, linguagem honesta: "implementado, happy-path testado, por rever" / "testes unitários OK, end-to-end não corrido".
- `STATUS=done` / `@@DONE` proibidos enquanto houver critério (ISC, ver glossário) aberto ou revisão pendente — usa `STATUS=working` + `@@NEED`.
- A regra é estrutural, não semântica: qualquer adjectivo que qualifique o trabalho como final dispara-a, mesmo se for verdade. Pós-edit, responde com output literal de tool ("pytest: 5 passed, exit 0"), sem adjectivos sobre o trabalho.
- **Nunca fabricar a aprovação de outrem.** "Revisto/aprovado pelo dono" só vale com a frase do dono citada verbatim; sem ela é "pendente de revisão" ou "revisto por subagente independente". Ver `references/self-report-fabrication.md`.
- **Exit code literal:** se o verify é um pipe (`pytest ... | tail`), o exit code que o shell devolve é o do `tail`, não o do teste. Usa `set -o pipefail` ou lê `${PIPESTATUS[0]}` logo a seguir (`pytest -q 2>&1 | tail -5; echo "exit=${PIPESTATUS[0]}"`) e cita esse valor.
- Se o teu ambiente ou um hook avisar que a verificação está desactualizada ("verification status: stale"), corre os testes + lint outra vez neste turno e mostra o exit code antes de declarar progresso.

## Quando NÃO usar

- **Fechar/arrumar um tema** → `session-wrap` (lado de saída; este skill é a entrada)
- **Tarefa nova** sem histórico de execução → começa normal
- **Build plan determinístico já em execução** com o seu próprio executor → a checklist desse executor é a versão especializada desta; usa-a
- **Relembrar decisões/conversas** sem projecto estruturado → pesquisa na memória/histórico, se tiveres

## Verificação (como sabes que funcionou)

- A sessão declara o marco do passo 4 em ≤2 min com ponteiros concretos (ficheiro:secção), não vagos.
- Check falível: "qual foi o último passo verificado e onde está registado?" — a resposta aponta para um artefacto, não para memória.
- Uma divergência plantada (ex.: parar um container esperado) é apanhada no passo 3, não a meio do trabalho.

## Anti-padrões

| Anti-padrão | Correcção |
|---|---|
| "Lembro-me de onde ficámos" (memória > artefacto) | Passos 1-2 — o artefacto é a autoridade |
| Confiar em facto de ambiente com 3 dias | Passo 3 — re-verificar sempre |
| Assumir que és a única sessão no projecto | Passo 3 — `git log` apanha mãos paralelas |
| Retomar do "último tocado" em vez do "último verificado" | Passo 2 — só verify conta |
| Folha de turno que ninguém actualiza | Passo 5 — actualizar à saída é parte do custo |
| Reconstruir contexto e não deixar folha | Passo 1 — cria com o template |
| Inventariar a working tree com a pesquisa do agente | Começa por `git status --short` |
| Mexer em ficheiros divergentes sem perguntar | Passo 3 — divergência não explicada = PÁRA + 3 opções |
| Escrever o ISA novo no path do template | Instâncias em `<project-root>/.isa/` |
| ISA em `phase=observe` tratado como "em curso" | É um draft sem execução; pergunta qual é o próximo passo real |
| Validator "9/9 PASS" lido como "suite verde" | Valida a forma, não o runtime; completa com um smoke test de runtime (porta, env, processos) |
| Tratar ficheiros locais como canónicos quando há tracker | Consulta o tracker primeiro |
| `fetch failed` → pedir ao utilizador para rever credenciais | Probe `curl -m 3` primeiro (`000` = offline) |
| `git status` como prova do estado das tarefas | Em trabalho multi-agente diverge do tracker; o tracker é a verdade |
| Varrer um directório de repos inteiro com `find` para achar um projecto | Itera repo a repo (`for d in */; do test -e "$d/<feature>"; done`); se não encontra, PÁRA e pergunta o caminho |
| "Arranca X na porta Y" sem caminho/comando | Não é divergência, é input incompleto: declara o bloqueador numa mensagem curta em vez de varrer o disco |
| `@@NEED` com acção do dono | Menu compacto e parar (passo 1.0) |
| `lint` exit ≠ 0 lido como "introduzi erros" (ou exit 0 como "limpo") | Mede delta: `git stash` → erros N0; `git stash pop` → M; delta M−N0 = 0 é o que se reporta |
| Auto-aprovação ("owner-applied") sem frase do dono | Spawn de reviewer independente; ver done-language |
| Daemon que renasce sozinho depois de `pkill` (watcher externo) | Mata 1×, arranca 1×, regista PID/porta; não entres em loop kill→spawn; reporta a causa externa. Pidfiles podem ficar stale |
| edit tool devolve `success` mas o ficheiro não mudou | Após cada edição de código de produção confirma com `wc -l`/`grep <marcador>`/import smoke (`scripts/recover-from-failed-patch.sh`); se não persistiu, reescreve o ficheiro inteiro |
| Commit com resumo "1 file changed" sem confirmar QUE ficheiros | Antes do commit, `git diff --stat HEAD -- <ficheiros>`: cada ficheiro prometido tem de aparecer; se faltar → `git checkout HEAD -- <f>` + reescrever + novo diff |
| `replace_all` em padrões estruturais (`with`/`try`/`for`) | Só seguro para literais. Faz 1 substituição simples, confirma, e para >2 estruturais reescreve o ficheiro |
| Aplicar texto de um ficheiro de input que o dono pode ter mudado entretanto | `cat` + `sha256sum` imediatamente antes de aplicar e `diff` contra o que tens em memória |
| Feature com UI validada só com `curl` e screenshot | Protocolo 3 camadas: HTTP (`curl` + código + resposta crua), screenshot e reconstrução textual em `.md` (tabela + dumps). A reconstrução sobrevive a CORS/file:// e a daemons mortos |
| Screenshot de UI com tabela vazia lido como "feature partida" | Distingue CORS/harness de falha do servidor: `curl -H "Origin: x"`, chamada directa à função, screenshot same-origin |

## Mais pitfalls

Casos técnicos mais específicos (ISAs untracked, "foi entregue", chokepoints, SQLite cross-thread, UNIQUE(name), promote com `new_body`) estão em `references/pitfalls-avancados.md`.

## Changelog

- v1.0.0 — versão partilhável: genericizada a partir da v0.10.9 do skill original (dependências de memória, ficheiro de estado e tracker privados passam a opcionais; casos de projecto reduzidos à lição de classe).
