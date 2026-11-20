# Glossário (definições tiradas desta skill)

- **Rule 0** — revisão independente para código não-trivial (não-negociável): author-pass ≠ done; revisor diferente do autor (SKILL.md §1).
- **Rule 1** — live-probe de artefactos user-facing: "should work" sem output real não é evidência (§1).
- **ISA** — Ideal State Artifact: ficheiro de spec/estado de uma tarefa por fases (`.isa/ISA-<nome>.md`, `templates/ISA.md`).
- **ISC** — critério de aceitação binário `- [ ]` dentro de um ISA; só se marca com evidência no mesmo bloco (§3).
- **E1-E5** — níveis de esforço (E1 trivial … E5 multi-fase) que decidem se há ISA e que verificação aplicar (`references/effort-and-process.md`).
- **STATUS=need / @@DONE** — no status file do agente: `STATUS=working|done|blocked|need`, com sentinela `@@DONE`/`@@BLOCKED`/`@@NEED` (§3). `need` = pára e pede decisão/escalada ao orquestrador ou owner (§4).
- **owner** — o humano que pede o trabalho e decide o que é seu (segurança, acesso, scope, dados).
- **failure-tree** — secção "If verify fails" de um step de plano: sintomas esperados e a acção prescrita para cada um (§4).
- **blast radius** — alcance do dano de uma acção; num step irreversível sem prova, só se pode confinar (§1).
- **MILESTONE-CADENCE** — checklist no fecho de cada milestone: verifies PASS com dumps, state-snapshot, checks mecânicos, review forte se correctness-oculta (§5).
- **VERIFY-PREFLIGHT-GATE** — antes de um verify, confirmar expected concreto + failure-tree; se o resultado não bate com nenhuma entrada, PÁRA com dump tabular (§4).
