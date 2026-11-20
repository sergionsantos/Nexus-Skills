# Checklists EXPLORE por stack — greps e comandos prontos

> Complemento do `playbook-explore.md`: cola a checklist da stack no prompt do agente da lente respectiva. São greps concretos — adapta paths, mantém a lógica. Marcação: tudo aqui é adição de método (generalizado do traço Next/Supabase + prática; só a stack A vem directamente do traço).

## Stack A — Next.js + Supabase (traço-fonte: um gestor de tarefas web)

**Arquitectura/código**
- Testes vs camadas críticas: `find src -name "*.test.*"` e cruza com `src/lib/sync|hooks/*mutations*|lib/api` — gap = finding
- Invalidação: `grep -rn "invalidateQueries\|qk\." src` — keys de escrita vs keys das queries activas batem?
- Optimistic updates com rollback? `grep -rn "onMutate\|onError" src/hooks`
- Remendos: `grep -rnE "FIX|HACK|TODO|D[0-9]{2,}" src --include="*.ts*" | wc -l` por dir — densidade = fragilidade
**Infra/segurança**
- JWTs no `.env*`: descodifica payload (`cut -d. -f2 | base64 -d`) — `iss: supabase-demo` = demo keys = finding CRÍTICO
- `grep -rn "service_role" app` fora de código server-only = bypass RLS
- RLS: por tabela do schema, existe policy? (`grep -rhi "create policy" migrations | wc -l` vs nº de tabelas — `-i` obrigatório: SQL real mistura maiúsculas/minúsculas; sem ele, falso-zero fabrica um finding "sem RLS")
- Persistência: launchd/pm2/systemd presente? O que acontece num reboot?
**Gap funcional (a query de ouro)**
- Por coluna do schema: `grep -rn "<coluna>" src/components src/app` — 0 hits em coluna mutável/filtrável = valor latente
- Por tabela: tabela com migração+RLS e `grep -rln "<tabela>" src/components` = 0 → feature inteira enterrada
**UX/robustez**
- `find src/app -name "error.tsx" -o -name "loading.tsx" -o -name "not-found.tsx"` — vazio = sem fallbacks
- `grep -rn "isError" src/components src/hooks` — 0 = erros silenciosos
- `grep -rn "navigator.onLine\|offline" src` — 0 = sem tratamento offline
- Virtualização: `grep -rn "react-window\|react-virtual\|virtuoso" src` vs listas `.map` grandes
- `grep -rho "md:\|lg:\|sm:" src/components | wc -l` (total de ocorrências) baixo = mobile por fazer

## Stack B — API Python (FastAPI/Flask)

- Rotas vs testes: `grep -rn "@app\.\|@router\." --include="*.py" . | wc -l` vs `find tests -name "test_*.py" | wc -l`
- Validação de input nos endpoints: modelos Pydantic em todos os POST/PUT? `grep -rn "def.*(request" sem schema = trust boundary aberta
- `grep -rn "except Exception\|except:" --include="*.py" .` — catch-all engole erros
- Secrets: `grep -rn "api_key\|password\|token" --include="*.py" . | grep -v environ` — hardcoded = finding
- Migrações: alembic/SQL corridas? introspection viva vs ficheiros
- Blocking em async: `grep -rn "requests\.\|time.sleep" --include="*.py" .` dentro de `async def`
- Deploy: como corre? (uvicorn manual = morre com o terminal)

## Stack C — Serviço Node / MCP server / CLI

- Entry points vs docs: `cat package.json | jq .bin,.scripts` — scripts documentados existem?
- Error handling no transport: `grep -rn "process.on('uncaughtException'\|unhandledRejection'" src` — 0 = crash silencioso
- Tools MCP: por tool registada, schema de input validado? handler com try/catch?
- **Query de ouro MCP** (equivalente da query de ouro da Stack A; encontrado em calibração real 2026-07-20, maior rácio ganho/diff do relatório): por handler/tool exportado em `src/tools/` (ou equivalente), existe registo no servidor (`srv.tool(`/`server.setRequestHandler`)? Contagem de exports vs contagem de registos no entry point — export sem registo = capacidade construída e invisível ao cliente = valor latente.
- Estado: onde persiste? ficheiro sem lock = corrupção com 2 instâncias
- Logging: PRIMEIRO verifica se existe logger estruturado próprio (grep por `logEvent`/`logger`/tabela de eventos) — se existir, contagem de `console.log` é proxy sem significado. Só na ausência: `grep -rn "console.log" src | wc -l` alto = debugging impossível em produção
- Versões: `npm outdated` — nota: com N pequeno quase nunca vira finding (majors atrás sem dor evidente = descarte); corre no fim, só se sobrar orçamento de lente

## Stack F — Sistema quantitativo / trading / data pipelines (calibração real 2026-07-20, pipeline de dados de mercado)

> Híbrido research+batch+market-data+registry+automação — nenhuma stack única encaixa; usa Stack B como base parcial + isto. Aqui o risco NÃO está em rotas-vs-testes: está em gates falso-verdes, harnesses re-derivados e claims históricos contraditórios.

- **Gates de domínio primeiro**: procura selftest/calibrators/known-answer tests/golden datasets no próprio projecto (`CLAUDE.md`/protocolo local costuma nomeá-los) — corre-os e adiciona-os como ISC. Foi o calibrador do próprio projecto (não a checklist genérica) que encontrou o finding nº1.
- **Falso-verde por exit code**: por cada gate/verificador, compara o veredicto IMPRESSO com o exit code real (`cmd; echo rc=$?`) — "FAIL ... exit 0" = o gate não protege nada = finding CRÍTICO.
- **Freshness triangulada** (mtime NÃO chega para market data): mtime + último timestamp DENTRO do feed + estado do scheduler (`launchctl list`/`crontab -l`) + conteúdo dos logs (`last_run.json`) + processo vivo. Qualquer perna a divergir = pipeline morto que parece vivo.
- **Identidade de serviço, não só health**: HTTP 200 numa porta ≠ serviço certo — verifica payload identity + processo dono (`lsof -iTCP:<porta>`) + rotas declaradas no código. (Caso real: :<porta> respondia 200... de OUTRO serviço.)
- **Registry/state-machine consistency**: cruza os campos semânticos (state vs gates vs promotion vs fresh_last vs wiring) — contradições entre campos do mesmo registo são findings que nenhum grep isolado apanha.
- **Censo de adopção do núcleo canónico**: importadores do core/facade vs importadores do legacy que ele substitui — mede se a consolidação documentada aconteceu de facto (caso real: 13 vs 81).
- **Query de ouro research** (equivalente de "schema sem UI"): spec completa + implementação existente + wiring existente + **output stale ou não consumido** = capacidade pronta sem operação contínua = valor latente nº1.
- **Segredo em traceback**: além de hardcodes, procura SDKs que serializam credenciais dentro de excepções gravadas em logs — credencial em log = comprometida, recomenda rotação; NUNCA a copies para o relatório.
- **Scheduler + watchdog**: automação crítica tem watchdog? `last_run` antigo com zero alertas a chegar ao dono = watchdog em falta.
- Contagens brutas (`except Exception`, nº de testes) são MAPA, não finding — em pipelines best-effort o catch-all é deliberado; o finding é onde a falha é engolida sem mudar exit code nem chegar ao operador.

## Stack E — Notas pessoais (Obsidian ou similar) / PKM / gestão pessoal (calibração real 2026-07-20, non-code)

> Unidade de evidência aqui NÃO é `ficheiro:linha` — é **ficheiro + secção/mtime/contagem** (uma daily note não tem "linha" relevante; tem secção vazia/não-vazia e blocos repetidos). O resto do operating mode aplica-se igual (grep-zero conta, predict-then-run, etc.).

- **"Tocado ≠ editado"** (a técnica que mais rendeu na calibração — 2 findings independentes): `stat -f "%Sm"` dá o tocado; `git log -1 --format=%ci -- <ficheiro>` + leitura do conteúdo (datas dos itens) dá o editado. Mtime recente com conteúdo congelado há meses = sistema morto que parece vivo = finding.
- **"Log de sucesso ≠ artefacto no disco"** (automação de notas — cron/hook/script): quando um log diz `[OK] X updated`, `ls`/`stat` no X. Ausência com log verde = pipeline a mentir = finding CRÍTICO. Cadeia completa: `crontab -l`/`launchctl list` → ler o script fonte (`grep -n` aos paths hardcoded) → verificar cada output esperado existe.
- **Fill-rate de secções-com-propósito** (equivalente PKM de "cobertura de testes"): últimas 2-4 semanas de daily notes, por secção do template: quantas vezes preenchida? 0/10 = secção morta no template = candidato a corte ou a automação.
- **Query de ouro PKM** (equivalente da query de ouro Stack A): por skill/pipeline/agente disponível no sistema, existe backlog de input correspondente INTOCADO? (`mtime` do backlog vs data de criação do skill). Pipeline pronto + fila parada = valor latente nº1.
- **Duplicados por convenção de nome**: variantes do mesmo ficheiro (`_Task List_.md` vs `Task List.md`, acento vs sem-acento) — `diff` entre eles; estruturas divergentes nunca reconciliadas = fricção do dono.
- **Doc-canónico vs uso real** (substitui o "standard de comparação externo", que em PKM raramente existe): o que documento canónico do sistema AFIRMA vs o que os ficheiros mostram — grep dos nomes de features/workflows documentados nos ficheiros operacionais; 0 hits = doc e prática divorciados.
- Processo "vivo"?: não há porta para lsof — usa frequência real de escrita (`ls -lt` no dir, gaps no histórico) + automação registada (`crontab -l`, `launchctl list`) vs automação documentada.

## Stack D — Operação macOS (launchd/serviços do dono)

- `launchctl list | grep <label>` vs plists em `~/Library/LaunchAgents` — serviço documentado sem plist = morre no reboot
- `lsof -i :<porta>` por porta documentada
- Logs: plist tem `StandardOutPath`/`StandardErrorPath`? sem logs = debugging cego
- `KeepAlive` presente? crash = morto até alguém reparar
- Paths no plist absolutos e existentes? (`~` não expande em launchd)
- TCC: serviço acede a `~/Documents`? cron/launchd bloqueado por TCC = falha silenciosa
