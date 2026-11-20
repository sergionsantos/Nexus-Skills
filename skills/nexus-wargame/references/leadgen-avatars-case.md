# Caso datado — projecto de lead-gen com personas virtuais (origem do skill)

Primeiro uso completo do processo, antes de existir o skill. (Nomes de clientes e caminhos removidos na partilha.)

## O que foi feito

Objectivo: capacidade genérica para criar "especialistas virtuais" (personas transparentes com presença social) para lead-gen em qualquer domínio.

- **Playbook genérico:** 7 fases, prompts, model routing.
- **Persona 1** (software B2B de nicho): spec + 5 missões + success + ledger 46 itens + 5 war-games red-teamed 3 rondas → STABLE. Fase 5 executada por modelo médio (bios, calendário, semana 1).
- **Persona 2** (turismo B2C): spec + 6 missões + success + ledger 48 itens + 6 war-games red-teamed 3 rondas → STABLE.

## Lições que moldaram o skill

1. **Modelo caro como parâmetro.** O processo não depende de um modelo concreto — qualquer modelo forte serve. Generalizado para `$STRONG`.
2. **Colisão de LEDGER-id em fan-out paralelo.** Na persona 1, 3 agentes usaram o mesmo id inicial ao mesmo tempo → renumeração manual pós-facto. Na persona 2, gamas pré-alocadas por missão (13-18, 19-24, …) → zero colisões. Virou regra da fase 3.
3. **Convergência real do red-team.** Ronda 1 fortalece tudo; ronda 2 apanha defeitos de COERÊNCIA entre as edições da ronda 1 (pointers partidos, contradições, dependências implícitas — não defeitos novos); ronda 3 = STABLE. Findings encolhem monotonicamente. Byte-idêntico + zero edições = fim.
4. **A tese valida-se na fase 5, não antes.** O executor de tier médio respeitou sozinho os gates escritos pelos war-games (pré-conta, visuais bloqueados, zero estatísticas inventadas). Os 2 findings que escaparam eram do tipo já previsto ("prometer o que não existe") e a revisão independente apanhou-os. O julgamento transferiu-se pelos ficheiros.
5. **War-game descobre o que o autor não sabia perguntar.** Surgiram: destinos em zona de conflito vendidos como paraíso na base de conhecimento; contas encobertas que afinal nunca foram criadas (risco menor); transferência de dados UE→país terceiro (RGPD); SLA de resposta (lead sem resposta em 24h é pior que não capturar); atribuição de conversões (sem prova, o projecto morre).
6. **Trust boundaries = abort duro.** Segurança de viagem, saúde, RGPD, pagamentos em DM — o red-team recusou qualquer contorno "esperto"; só orientar, escalar e citar fontes oficiais.

## Números

11 war-games, ~380K de conteúdo, 3 rondas de red-team por persona, ~40 invocações de subagente. Custo do modelo caro concentrado nas fases 1-4; fase 5+ toda em modelo médio.
