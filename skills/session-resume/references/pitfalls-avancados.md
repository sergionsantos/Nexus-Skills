# Pitfalls avançados (específicos de certos tipos de projecto)

Extensão de `SKILL.md`. O `SKILL.md` funciona sozinho; isto cobre casos mais específicos (ISA/ficheiros de estado, serviços web, SQLite, gates).

**⚠️ Pitfall "ISAs untracked = re-entrada a meio, não começo do zero":** uma sessão interrompida pode deixar 5–10 ISAs untracked (`git status --short`) sem nenhum commitado. Não é rascunho a limpar — é o working state de ontem. Lê o ISA mestre (mais antigo, com o tracker de fases completo) para a timeline; o ISA-Lite mais recente para o passo actual; o ficheiro de estado para o ponto de pausa. Os Lite intermédios estão superseded.

## Anti-padrões específicos

| Anti-padrão | Correcção |
|---|---|
| "Foi entregue" baseado na tabela do emissor (`delivered_at`, audit row) | Verifica no sistema de DESTINO (API do canal, IMAP, DB do destinatário). "Hand-off OK" ≠ "chegou ao destino" |
| Gates adicionados endpoint a endpoint ("whack-a-mole") | Um chokepoint central (middleware / guard de router) com política declarativa; cada ronda de review que acha um endpoint novo é sinal de que falta o chokepoint |
| Chokepoint só cobre leituras (GET/HEAD) | Cobre também escritas (POST/PATCH/DELETE) — ex.: `Depends(require_user_actor)` em cada write |
| Fechar uma porta que o spec deixou aberta de propósito (ex.: agente pode criar `candidate`, só o utilizador promove) | Lê a docstring/spec do state machine antes de "corrigir" um suposto bypass |
| Asserção de filtro/scrub só com ausência (`assert canary not in body`) | Trivialmente verde com body vazio. Junta controlos positivos (`len(body) >= 2`, chave esperada presente) |
| Camada superior chama a camada abaixo em vez do orquestrador (side-effects a jusante nunca correm) | Reproduz com `git stash` + teste de regressão que falha na 1.ª asserção pós-side-effect; encaminha tudo pelo orquestrador |
| Gate rejeita honestamente uma nova identidade/artefacto (drift, segurança, conteúdo) | Não alargues o threshold nem metas override: actualiza a REFERÊNCIA aprovada (baseline/blocklist) e re-corre o gate; assim continua a defender de drift futuro. Se há UNIQUE(name), usa nome novo por versão |
| "Que corpo é este?" num promote com `new_body` | O corpo antigo está no artefacto activo; o novo no draft que acabaste de escrever — lê da fonte que escreveste, não da linha "active" da DB |
| Pytest/fixture web com SQLite: `ProgrammingError` cross-thread | Abre uma ligação nova (`sqlite3.connect(<db_path>)`) em vez de reutilizar a do lifespan |
