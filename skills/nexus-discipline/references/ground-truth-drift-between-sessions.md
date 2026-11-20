# Ground truth drift between execution windows — when yesterday's "verified ✅" is today's empty

> **Pitfall class:** executar probes / passos de um plano (ver `nexus-plan-spec`) cujo **ground truth (DB / KB / config / lista) era válido numa janela de execução anterior mas está diferente (vazio, parcial ou re-seedado) na janela actual**. O plano continua "correcto" contra o spec; o spec está stale contra a realidade actual.

## Variante «sessão retomada»

Numa janela anterior o trabalho deixou a base de dados num estado específico (utilizador de teste, dezenas de registos de exemplo, milhares de linhas). Na sessão seguinte (outro turno, às vezes outro agente) a mesma BD está **vazia ou diferente**, mas o recap, o caderno e o LOG continuam a descrever o estado antigo.

**A armadilha:** confiar no recap/LOG e correr os probes → a maioria falha ou dá resultados enganadores (ex.: zero linhas de auditoria porque o próprio escritor de auditoria precisa de um utilizador-alvo que já não existe).

## Diagnóstico de 3 nós (quando algo "devia funcionar" e não funciona)

Antes de declarar "o código está partido" ou "o plano está errado", corre isto **contra o sistema vivo**, não contra o LOG:

1. **O alvo existe?** `select count(*) from <tabela>` (ou equivalente para KB/config). Se 0 mas o plano assume N → drift.
2. **O estado de interesse foi escrito?** `select count(*) from <audit_table> where action like '<prefix>%' and created_at > now() - interval '1 hour'`. Se 0 mas o LOG diz que escreveu → drift (ou o caminho de escrita está partido).
3. **O processo em execução é o que o LOG descreve?** `ps` + health-check do serviço, ou `git log -1 --oneline`. Se o processo/commit mudou em silêncio, o LOG descreve a instância anterior.

Se **qualquer** nó devolver algo diferente do recap → **PÁRA, mostra o dump dos 3 nós ao owner** e pergunta qual de 3 caminhos tomar: **A** re-seed mínimo para acabar os probes actuais · **B** adiar os probes restantes e commitar só o verificado · **C** investigar primeiro a causa.

## Porque é que recap/caderno/LOG não são ground truth

1. **Re-seed entre sessões** — outro agente, um script de seed acidental, um reset de ingest, um watch-mode que perde estado em memória.
2. **Migrações** — podem apagar e recriar tabelas (schema intacto, dados desaparecidos).
3. **Mudança de ambiente** — túnel caiu, servidor reiniciado noutra porta, token expirou.

Em todos os casos: **confia no `select count(*)` vivo, não no recap.** O recap é o que o owner acha que é verdade; o count é o que lá está.

## Custos

| Escolha | Custo se certa | Custo se errada |
|---|---|---|
| Check de 3 nós antes de re-correr | 30-60 s + 1 turno | 30-60 s (barato) |
| Re-correr probes contra recap stale | 0 | 5-15 min de output lixo + owner confuso |
| Inserir seed ad-hoc para os probes passarem | 0 | commits a reverter + viola invariantes do projecto + esconde a causa |

## O que registar depois de resolver o drift

1. **Entrada `Drift detected` no topo do LOG** com: timestamp, dump dos 3 nós, caminho escolhido pelo owner, novo ground truth.
2. **Caminho A (re-seed):** marca as linhas inseridas com um padrão único (ex.: `%@recovery.example`) para a sessão seguinte as poder apagar limpamente.
3. **Caminho B (adiar):** a entrada do LOG passa a ser o registo de «ISCs bloqueados». Não finjas que o milestone está feito.
4. **Caminho C (investigar):** a investigação é o trabalho; o dump é o ponto de entrada. Não a misturar com os probes.

## Relacionado

- `nexus-discipline` (reflexo de re-avaliar depois de cada lote de resultados): o «lote» aqui é o início da sessão seguinte.
