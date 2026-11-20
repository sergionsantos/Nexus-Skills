---
name: structured-ask-owner-for-secret
description: "Quando precisas de N valores secretos curtos (chaves, tokens, IDs) que o owner tem num sítio a que não chegas, pergunta de forma estruturada com opções de entrega em vez de inventar placeholders ou repetir tentativas de acesso."
trigger: "precisas de valores secretos que o owner tem num host inacessível; sem rota SSH/rede; sem fonte pública"
---

# Structured ask — owner tem o segredo, tu não consegues chegar a ele

## Quando se aplica

- Precisas de valores literais curtos (chaves de API, tokens, IDs) que vivem num ficheiro `.env`/gestor de segredos num host a que o teu ambiente não tem rota (sem SSH configurado, sem VPN, sem credenciais).
- Já tentaste os caminhos óbvios e falharam (ssh time-out / sem rota / identidade errada / sem chave).

## Anti-patterns

- Escrever um placeholder (`service-key-here`) e declarar o step «done». O literal não tem valor real: qualquer teste que o use falha mais tarde, longe da causa.
- Repetir tentativas de acesso (`ssh`, `ping`, `ls ~/.ssh`) depois de saberes que não há rota.
- Procurar o segredo em sítios não autorizados (keychains, histórico de shell, ficheiros de outros projectos).

## Procedimento

1. Prova uma vez que não consegues chegar aos valores (1 comando, resultado citado).
2. Pára e escreve `STATUS=need` (ver `done-language-and-status-vocabulary.md`).
3. Pergunta ao owner com **opções de entrega concretas** e uma recomendada:
   - (a) cola os valores no chat de confiança;
   - (b) cria um ficheiro local fora do repo (ex.: `~/.keys.env`) e indica o path;
   - (c) dá-me acesso (alias SSH / rota) ao host;
   - (d) outra via que prefiras.
   Nunca copies valores secretos para ficheiros commitados, logs ou mensagens.
4. Diz o que fazes quando os valores chegarem (que ficheiro preenches, que verificação corres) — para o owner saber o que esperar.
5. Quando chegarem, verifica sem expor: `grep -c "NOME_VAR" .env.local` e comprimento/forma dos valores, não os valores. Só então confirmas a integração real (ex.: um pedido autenticado que devolve 200).

## Exemplo de mensagem

> @@NEED bloqueado: preciso de 6 chaves `<nome>-key` para preencher `X_<PERFIL>_KEY` em `.env.local`. Não tenho rota nem credenciais para o host onde estão. Como preferes entregar: (a) coles aqui; (b) ficheiro local + path; (c) alias SSH para este worker; (d) outra? Recomendo (b). Quando chegarem: preencho `.env.local`, confirmo `grep -c` e faço um pedido autenticado por perfil.

## Verificação

Depois da entrega: contagem de linhas esperadas no ficheiro, comprimento/forma dos valores (nunca o valor), e um pedido real autenticado por cada chave.
