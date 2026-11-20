# Playbook GROUND — estado real vs estado documentado

> Objectivo da fase: chegar ao fim com uma secção "Estado real verificado" onde CADA linha tem um comando+resultado por trás. Num caso real (app de tarefas web), esta fase sozinha produziu a melhoria #1 inteira (app down + JWT mismatch) antes de qualquer agente de exploração arrancar. Não é burocracia — é onde os findings mais críticos vivem.

## Passo 1 — Inventário de fontes documentadas (10 min)

Lista o que o projecto AFIRMA sobre si próprio. Fontes típicas, por ordem:
1. `LOG.md` / journal do projecto — estado operacional, landmines conhecidas, backlog
2. `README` / docs de arranque — como supostamente corre
3. checklists/wraps recentes (ex.: `.analysis/`, `Wraps/`) — último estado conhecido
4. Configs (`.env*`, `docker-compose`, `*.plist`, `gateway.yml`, etc.) — o que DEVIA estar configurado
5. Migrações/schema — o que a base de dados DEVIA ter

Enquanto lês, extrai **claims verificáveis** para uma tabela de trabalho:

| Claim documentado | Fonte | Como verificar ao vivo |
|---|---|---|
| "app live em :<porta>" | LOG | `lsof -i :<porta>` |
| "gateway.yml revertido no disco" | LOG landmine | `diff` config actual vs versão preparada |
| "backlog: bulk-toolbar por fazer" | LOG | grep do componente no código |

Regra: se um claim não tem forma de verificação, escreve "NÃO-VERIFICÁVEL" — não o promovas a facto.

**Amostragem quando o corpus de claims explode** (projecto com centenas de reports/checklists históricos — calibração num projecto de trading, 2026-07-20): não confirmes literalmente tudo; prioriza por ordem: (1) claims que bloqueiam operação hoje, (2) claims canónicos (protocolo/CLAUDE.md do projecto), (3) claims mais recentes, (4) claims que as tuas recomendações vão citar. O resto fica fora do GROUND — não é dívida, é scope.

**Gates de domínio do projecto**: procura no `CLAUDE.md`/protocolo local gates obrigatórios próprios (selftest, calibradores, validadores) — corre-os no GROUND e adiciona-os como ISC do relatório. O gate do próprio projecto encontra findings que a checklist genérica nunca vê (caso real: calibrador com veredicto FAIL e exit 0).

## Passo 2 — Verificação viva, claim a claim

Comandos típicos por tipo de claim (adapta à stack):

- **Processo/serviço a correr?** `lsof -i :<porta>`, `ps aux | grep <nome>`, `launchctl list | grep <label>` (macOS), `systemctl status` (Linux)
- **Endpoint responde?** `curl -s -o /dev/null -w "%{http_code}" http://<host>:<porta>/<path>` — e **confirma a IDENTIDADE**: 200 não prova que é o serviço certo; lê o payload + processo dono da porta (`lsof -iTCP:<porta>`). (Caso real 2026-07-20: porta respondia 200... de OUTRO serviço.)
- **Gate/verificador "passou"?** Compara o veredicto IMPRESSO com o exit code real (`cmd; echo rc=$?`) — "FAIL ... rc=0" = falso-verde, e é finding. Aplica-se a qualquer stack, não só trading.
- **Config no disco = config documentada?** `diff` ou grep das chaves críticas; para JWT: descodifica o payload (`echo <token> | cut -d. -f2 | base64 -d`) e compara `iss`/assinatura com o secret actual
- **Schema real?** ficheiro de migração é evidência aceitável de que o schema *suporta* X (o traço citou `0003_issues.sql` e passou review limpa). Introspection viva (`information_schema.columns`, `\d tabela`) só quando a pergunta aberta é "a migração correu mesmo / correu diferente?" — isso sim é um check de divergência do GROUND
- **Feature existe no código?** `grep -rn "<símbolo>" <dir>` — **zero hits é resultado válido e citável**
- **Automação reporta sucesso?** Log `[OK]`/exit 0 NÃO é evidência de que o artefacto de output existe — `ls`/`stat` no output esperado. (Calibração 2026-07-20: script gravava `[OK] updated` 3× num log enquanto o ficheiro de destino nem existia no disco — o log de sucesso era o próprio bug.)

Predict-then-run: antes de cada comando escreve o esperado ("espero listener em :<porta>"). Divergência esperado-vs-real = candidato a finding.

## Passo 3 — Classificar as divergências

Cada divergência doc-vs-realidade cai numa de 3 classes, e cada classe tem destino diferente:

1. **Doc stale, realidade melhor** — o LOG diz partido mas já foi corrigido (traço: "gateway.yml revertido" já não era verdade). Destino: nota na secção Estado real + acção "actualizar LOG" dentro de uma melhoria.
2. **Doc stale, realidade pior** — algo que o doc dá como feito não está. Destino: candidato a melhoria.
3. **Divergência crítica nova** — nada no doc a prevê (traço: `.env.local` com demo keys vs `JWT_SECRET` rotacionado → app vai falhar auth ao arrancar). Destino: quase sempre melhoria #1 ou #2; é o tipo de finding que só o GROUND apanha porque nenhuma lente de exploração olha para o cruzamento config-app × config-infra.

## Passo 4 — Escrever a secção "Estado real verificado"

3-6 bullets, cada um no formato: afirmação + evidência entre parênteses. Exemplo real:
> - **App PARADA.** `lsof -i :<porta>` = nada; sem processo next; sem launchd `<label-do-serviço>`. Backend (gateway :<porta-backend>) está up.

**Live-probe bloqueado (app não arranca, falta `.env`/secret) NÃO cancela o GROUND — muda a etiqueta.** Caso real (app CRM, análise de UX, 2026-07-20): API recusou arrancar (`JWT_SECRET or NEXTAUTH_SECRET must be set`), sem `.env` de runtime no checkout. Regra: não gerar secrets nem alterar config só para observar; os findings de UX/UI continuam a existir via leitura de código — mas marca-os **explicitamente "estático"** (lido no código) em oposição a **"observado"** (visto a correr no browser/runtime), e nunca promove um ao outro. Um finding estático é tão citável como um observado (tem `ficheiro:linha`) — só o nível de confiança na experiência real do utilizador é menor, e o relatório tem de o dizer.

**Nota (fronteira com nexus-discipline):** a 1ª sonda read-only num sistema de outro dono/projecto pode bater num gate de aprovação (timeout de consentimento) — é espírito de `nexus-discipline` (escalar o que é do dono, esperar a aprovação explícita do dono), não doutrina específica deste skill; espera pela aprovação explícita antes de repetir a sonda.

## Erros típicos de modelo fraco nesta fase

| Erro | Correcção |
|---|---|
| Copiar o estado do LOG para o relatório sem verificar | Cada linha da secção exige comando+resultado |
| Verificar só o que é fácil (portas) e saltar configs | A tabela do passo 1 é o contrato — todos os claims marcados verificáveis são verificados |
| Assumir que a migração correu quando há sinais de divergência | Introspection viva quando a pergunta é "correu mesmo?"; migração no disco chega para "o schema suporta X" |
| Descartar divergência "porque não é pedida" | Divergência crítica é SEMPRE finding, mesmo fora do scope pedido |
