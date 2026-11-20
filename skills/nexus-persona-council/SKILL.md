---
name: nexus-persona-council
description: "Judgment and perspective from expert personas on a real situation, in four modes — `solo` (1 persona, concrete decision), `counsel` (panel of 3-5 with a blind round and an arbiter outside the panel, concrete decision), `battle` (adversarial pre-mortem against an already-decided plan), `lens` (see a situation, project or phase through the eyes of 1 or more personas — open exploration / coaching, no decision or numbers required). One parameterised skill: the first argument is always the mode. USE solo/counsel/battle when there is a concrete decision with facts and numbers on the table and you want the verdict of a specific person (e.g. Hormozi, Munger, Voss), or when you want to attack an already-written plan. USE lens to see a situation through one or more personas' eyes, or to have a conversation in their register, without a formal decision or numbers. DO NOT USE for knowledge questions about what an expert thinks (that is just reading their material) or for writing content in someone's voice. Requires a folder of personas, each with a LENS.md (format in references/lens-format.md); the skill ships no personas."
---

# nexus-persona-council — motor de juizo por persona

Modo obrigatorio como 1.o argumento: `solo` | `counsel` | `battle` | `lens`. Sem modo, PARA e pergunta.
Uma skill, quatro modos. As regras abaixo sao inviolaveis; perante ambiguidade fora delas, **PARA e pergunta.**

Invocacao: `nexus-persona-council <modo> <persona|painel> — <caso>`.

---

## 0. Configuracao (corre uma vez por sessao)

- **Pasta de personas** (`<PERSONAS>`): onde estao os `LENS.md`. Usa, por ordem: a pasta indicada no pedido; a variavel de ambiente `PERSONAS_DIR`; uma pasta `personas/` na raiz do projecto actual; por fim, a pasta `personas/` desta skill (24 personas incluidas, ver `personas/README.md`). Se o utilizador pedir uma persona que nao existe em nenhuma, PARA e pergunta: nao inventes personas.
- **Pasta de saida** (`<SAIDA>`): por omissao `./persona-council-output/` no directorio de trabalho do projecto actual (nunca dentro da pasta da skill instalada; ou outra indicada pelo utilizador). Contem `Pareceres/` e `Perspetivas/`.
- Formato dos `LENS.md`: `references/lens-format.md`. Termos desta skill (type-1/type-2, RPD, STOP, cue, ledger, Tiger/Paper Tiger/Elephant, teste Ohio): `references/glossary.md`.

---

## 1. Resolucao da persona

Nao existe indice de personas. Um nome resolve-se por caminho:

```
<PERSONAS>/[<Area>/]<Nome-Com-Hifens>/LENS.md
```

`<Nome-Com-Hifens>` = nome proprio em ASCII sem acentos, palavras ligadas por `-`: `Alex-Hormozi`, `Charlie-Munger`, `Chris-Voss`.
A `<Area>` (subpasta tematica) e opcional e normalmente nao vem no pedido. Resolve-se assim, por ordem:

1. Se a area for conhecida, testa directamente o caminho acima.
2. Senao, procura em `<PERSONAS>/` (ate 2 niveis; ignora o que comeca por `_` ou `.`) o directorio cujo nome bate com o nome pedido.
3. Zero correspondencias -> nao ha persona com esse nome; diz-lo e para. Mais de uma -> PARA e pergunta qual.

**Persona nao indicada em `solo`:** PARA e pergunta qual, listando as que tem `LENS.md` e o que cada uma decide primeiro (uma linha do bloco 1 de cada). Nao escolhas tu — a escolha da lente e metade do veredicto.

**Gate duro:** se o directorio existir mas **`LENS.md` nao existir**, PARA e responde literalmente que *essa persona ainda nao tem motor de julgamento — so tem banco de citacoes*. Nao produzas parecer. Ao PARAR, oferece duas saidas explicitas:
(i) correr com uma das que tem `LENS.md`, nomeando-as;
(ii) ler o `PERSONA.md` dela (se existir) como **banco de citacoes**, declarando no output que isso **nao e parecer** e nao passa gate nenhum.
Nunca apresentes (ii) como opiniao dela.

Nunca substituas o `LENS.md` em falta pelo `PERSONA.md`: um ficheiro de persona dominado por citacoes e sem regras condicionais produz caricatura com sotaque, nao juizo.

**Quem tem LENS descobre-se em runtime**, nunca de memoria nem desta pagina: procura `LENS.md` em `<PERSONAS>/*/` e `<PERSONAS>/*/*/`. Um eventual `ROSTER.md` e pista opcional para desambiguar nomes, **nunca autoridade** sobre quem tem motor de julgamento.

**Banco de casos (opcional).** Se existir `<PERSONAS>/CASOS.md` (casos por id), a invocacao por id le os factos de la em vez de os pedir. Casos marcados `held-out` NAO se correm fora do gate de validacao a que estao reservados — corre-los queima a atribuicao cega.

**Casos sinteticos ou de teste** levam aviso na primeira linha do parecer (`AVISO: caso sintetico, nao e decisao real`) e sufixo `-smoke` no nome do ficheiro, para nao se confundirem com pareceres reais.

Esta skill **nunca escreve dentro de `<PERSONAS>/`**: so leitura.

---

## 2. Carregamento de contexto

- **`LENS.md` — sempre, inteiro, em contexto.** Cabe: limite duro de 8000 caracteres.
- **`PERSONA.md` (grande), `FRAMEWORKS/`, `DIGESTS/`, `SOURCES/` — nunca inteiros.** Os loaders truncam; um ficheiro truncado a meio da frase e pior que ficheiro nenhum.
- Le-se material extra **so on-demand e por procura dirigida**: quando o caso exige um detalhe concreto que o LENS nao cobre, procura-se o termo especifico nesses ficheiros e le-se **a passagem**, nao o ficheiro. Justifica em uma linha do parecer o que foste buscar e porque.
- Se o LENS nao cobre e a procura dirigida nao devolve nada, isso e **lacuna declarada** no parecer, nao licenca para preencher com conhecimento geral do modelo.

---

## 3. Gate de convocacao — corre ANTES de tudo (excepto modo `lens`, ver §4.4)

Aplica-se a `solo`/`counsel`/`battle`. O modo `lens` nao classifica type-1/type-2: nao ha decisao formal a convocar. Para os outros tres, classifica a decisao antes de escolher o modo:

- **Type-1** — irreversivel ou caro de reverter: capital comprometido, contrato assinado, despedimento, publico irreversivel, reputacao, mudanca estrutural.
- **Type-2** — porta de duas vias: reversivel em dias/semanas com custo pequeno; testavel; desfazivel sem terceiros.

**Type-2 -> modo `solo`, sempre**, mesmo que tenham pedido `counsel` ou `battle`. Diz porque, numa linha, em linguagem simples: uma mesa de 3-5 pareceres nao se paga numa decisao que se desfaz na semana seguinte — o custo de deliberar excede o custo de errar e corrigir. (Um agente com bom prompt iguala quase o melhor protocolo de discussao multi-agente.)

`counsel` e `battle` **recusam** type-2: emitem a classificacao, a razao, e o ponteiro `usa: nexus-persona-council solo <persona> — <caso>`. Nao produzem mesa.

**Excepcao de reenquadramento:** se o que chega ao `battle` e um plano **ja decidido** mas type-2, o ponteiro para `solo` vem com a decisao reformulada — `usa: nexus-persona-council solo <persona> — manter ou reverter <plano>, com estes factos: <...>`. Nunca devolvas um ponteiro para um modo que recusaria o input tal como esta.

Duvida genuina entre type-1 e type-2: trata como type-1 e diz que o fizeste.

---

## 4. Os quatro modos

Regra transversal — **aplica-se a solo/counsel/battle; `lens` (§4.4) corre so a passagem A, ver ali**: **nunca menos de 2 passagens**, e a passagem critica corre **contra a constituicao da propria persona** — pega nos cues (bloco 1), criterios de rejeicao (bloco 3) e epistemologia (bloco 4) DELA e pergunta *"o juizo A respeita isto?"*. **Nunca** "isto esta bom?" — auto-critica sem sinal externo degrada o output.

### 4.1 `solo` — uma persona

1. **Passagem A — juizo.** Corre a `## Ordem de ataque` do LENS pela ordem escrita. Aplica blocos 1-4: cue dominante -> padrao reconhecido -> accao -> teste dos criterios de rejeicao -> que prova a epistemologia dela exige.

   As linhas `STOP:` **autonomas** (sem numero) sao **pre-condicoes do caso**: avaliam-se **antes da pergunta 1**, nao em ultimo. As `STOP:` dentro de pergunta numerada avaliam-se ao responder essa pergunta.
   Se disparar, o caso fecha ai: `## Veredicto` = `NAO HA CASO — <STOP literal>`, e o cheque (a) do §6 incide sobre o facto que o fez disparar. **Nao fabriques veredicto por cima de um STOP.**

   **Quando o STOP e sobre outra decisao que nao a que esta em mesa** (ex.: o STOP fecha "contratar" e o caso pergunta "aceito este contrato?"), o STOP fecha **a sub-decisao**, nao o caso: regista-o como restricao herdada e prossegue com a decisao em mesa. Diz no parecer que o fizeste.

2. **Passagem B — critica contra a constituicao + revisao.** Percorre linha a linha os blocos 1, 3 e 4. Para cada: *o juizo A contradiz esta linha? ignorou este cue? passou por cima deste criterio de rejeicao? aceitou prova que esta epistemologia rejeita?* Cada violacao encontrada corrige o juizo.
   Reporta no ficheiro: **quantas linhas dos blocos 1/3/4 percorreste** (a contagem tem de bater com o LENS), **quantas violacoes** apanhaste, e **o que mudou**. Zero violacoes e resultado legitimo **se e so se** a contagem de linhas estiver la e bater com o LENS — sem contagem, a passagem B nao correu. Nao ha quota de violacoes: fabricar violacoes cosmeticas para encher e a mesma falha ao contrario.
3. Aplica o gate de qualidade (§6). So depois escreve.

### 4.2 `counsel` — 3 a 5 personas, tres tempos

**Seleccao antes de emitir posicoes.** Descobre as personas com `LENS.md` pelo §1; disponibilidade nao significa convocacao. O painel tem **3 personas por defeito, minimo 3 e maximo 5**.

- **Painel explicito:** resolve nomes, elimina duplicados e valida cada LENS. Mantem a escolha do utilizador se houver 3-5 nomes validos. Nome ambiguo, LENS em falta, menos de 3 ou mais de 5 -> nao lances a ronda; apresenta o problema e pede a composicao corrigida. Nao substituas nem cortes nomes silenciosamente. Com 1-2 personas, oferece `solo` a uma persona escolhida pelo utilizador ou `lens` exploratorio ao painel.
- **Painel nao indicado:** le os blocos 1, 3 e 4 das LENS candidatas e escolhe **3 criterios diferentes aplicaveis aos factos do caso**: o que cada uma examina primeiro, o que a faria rejeitar e que prova exige. Relevancia por titulo ou notoriedade nao basta. Acrescenta uma 4.a ou 5.a apenas quando cobre uma restricao concreta do caso que as anteriores nao cobrem; justifica cada adicao. Se nao houver 3 LENS adequadas, nao completes por quota: explica a lacuna e oferece `solo`, sem escolher a persona pelo utilizador.
- **Registo obrigatorio:** antes da ronda cega, fixa `Painel: <nomes>` e uma linha por persona com `<facto do caso> -> <criterio distinto, bloco e path da LENS>`. O tamanho do roster nunca aumenta automaticamente o painel. Divergencia de criterios pode terminar em concordancia; nao implica fabricar votos contrarios.

**Tempo 1 — ronda cega.** Cada persona emite veredicto + **confianca (inteiro 1-5**; 1 = "so decido com dados que nao estao na mesa", 3 = "decido, mas um facto plausivel vira-me", 5 = "os criterios dela fecham o caso sem margem"**)** **sem ver** as outras.

Cego significa cego: cada juizo produz-se num **contexto que nunca viu os outros juizos**.
Mecanismos admissiveis, so estes dois:
(i) N invocacoes independentes de subagente/sessao, uma por persona, cada uma a receber
    apenas `<LENS da sua persona>` + `<caso>`;
(ii) N processos/sessoes novos em serie, cada um arrancado de raiz, a ler LENS e caso de
     ficheiro e a escrever o seu juizo em ficheiro; o seguinte nao recebe os anteriores.

**Escrever os juizos em serie dentro do mesmo contexto NAO e ronda cega.** Se o runtime so permitir isso, `counsel` **NAO corre**: declara `ronda cega: nao garantida pelo runtime`, PARA e pergunta se se corre `solo` a cada persona.

Declara no ficheiro qual dos dois mecanismos correu, nomeando o meio concreto — nao a intencao.

**Cada juizo da ronda cega corre as duas passagens do `solo` (§4.1) por dentro do seu contexto isolado, antes de ser selado.** O tempo 2 e sinal externo adicional e **nao substitui** a passagem B.

**Tempo 2 — exposicao anonimizada e revisao.** Cada persona ve as posicoes das outras **sem nomes** e revê ou mantem, com razao. O **delta pre/pos e output de primeira classe**, nao nota de rodape: tabela com persona · veredicto t1 · confianca t1 · veredicto t2 · confianca t2 · o que a fez mudar. Ninguem mudou -> escreve-se "ninguem mudou" **com a razao** (posicoes assentes em cues distintos que nao se contradizem, etc.).

**Tempo 3 — sintese por arbitro.** O arbitro **nao participou** na mesa — nunca uma das personas presentes, e nunca a lente que faz a revisao independente do gate (§6). E um juizo neutro sem LENS carregado; nomeia-se no parecer. Recebe as posicoes **anonimizadas**, em **ordem randomizada**. Regras do arbitro: exige a evidencia antes de dar peso a uma posicao; **penaliza comprimento** (resposta longa nao vale mais); **nomeia o cue que gera cada conflito** — a mesa diverge porque a persona X pesa primeiro o cue A e a persona Y o cue B, e o caso decide qual manda.

**Estado terminal explicito e obrigatorio.** Uma de duas:
- `CONSENSO: <decisao>` — com a condicao partilhada que o sustenta.
- `SEM CONSENSO. Decisao: <X>. Dissidentes: <posicao anonima> porque <razao>.` Dissidencia registada, nao dissolvida.

### 4.3 `battle` — pre-mortem contra plano ou decisao ja tomada

So corre sobre algo **ja decidido ou ja escrito**. Sobre uma decisao ainda em aberto, usa `solo`/`counsel`.

**Quem ataca:** as objeccoes emitem-se sempre **de dentro de um LENS**, nunca em voz neutra. Uma persona explicitamente indicada corre sozinha; um painel explicito admite 1-5 personas distintas com LENS valida, sem substituir ou cortar nomes silenciosamente. Sem nomes, aplica a seleccao limitada e justificada do §4.2 (3 por defeito, ate 5 apenas por criterio adicional). Objeccao sem persona por tras e conselho generico com fato de red team.

**Fonte congelada e revisao independente.** Identifica o caso canonico antes das passagens. Separa factos com localizador, calculos derivados e hipoteses; um parecer anterior nao substitui o caso. Antes de concluir, prepara o pacote de revisao com caso, LENS, argumentos completos e regras do gate, sem sugerir resultado nem instruir o juiz a declarar sobrevivencia/morte. O juiz escolhe o alvo de swap dentro das restricoes do §6. Nao anuncies o resultado independente antes de o receber.

**Nunca instancies "o advogado do diabo".** Dissidencia atribuida por papel entrincheira mais na crenca original. O enquadramento e sempre: *"Assume que este plano foi seguido tal como esta e falhou aos 12 meses. Lista as razoes pelas quais falhou."* — passado, nao condicional.

**Standard probatorio.** Toda objeccao nomeia:
(a) **o facto deste caso** que a sustenta (numero, prazo, dependencia, pessoa — nao "em geral acontece");
(b) **o falsificador** — o que teria de ser verdade para a objeccao morrer;
(c) **o sinal de deteccao** — o que se observa, e quando, para saber que esta a acontecer.
Objeccao sem falsificador **e cortada**, e o **numero de cortes reporta-se**. Conserva um ledger de todas as candidatas com identificador, persona, texto original, facto/localizador, falsificador e disposicao final (retida, mitigada, refutada ou cortada com motivo). Mede cortes e sobrevivencia sobre o conjunto original, nunca so sobre as retidas. Nao inventes candidatas para cumprir uma quota. (Um red team sem standard probatorio gera muito mais "riscos" do que os que se vem a verificar.)
Separa **origem textual** (recuperada ou derivada, data e caminho) de **validade factual** (facto canonico, inferencia ou dado ausente). Recuperar uma objecao antiga nao prova que seja verdadeira. Preserva variantes com mecanismos diferentes no mesmo agrupamento; portabilidade nao refuta um facto.

**Classificacao** de cada sobrevivente:
- **Tiger** — plausivel, alto impacto, e ha um movimento a fazer agora.
- **Paper Tiger** — assusta, mas o falsificador ja esta satisfeito pelos factos do caso.
- **Elephant** — real, grande, e ninguem na mesa quer nomear.
Cada ID tem uma disposicao e classe actuais unicas em ledger e parecer. Facilidade de mitigacao nao basta para Paper Tiger; Elephant exige evidencia de que o risco nao esta a ser nomeado. Sem suporte, regista a lacuna sem impor classe.

**Tres passagens:** draft -> critica-contra-constituicao (as objeccoes respeitam os criterios de rejeicao e a epistemologia da persona que as emite?) -> **contra-movimento por movimento** (para cada objeccao sobrevivente: que mitigacao concreta, a custo de que).

**STOP e contas nao sao intercambiaveis.** Se invocares um STOP da LENS, transcreve a condicao literal e demonstra a sua aplicabilidade com factos do caso. O falsificador de uma objeccao financeira nao prova nem refuta automaticamente outro STOP. Distingue receita, caixa incremental, custos e activos ja existentes; depois de corrigir uma conta, reavalia explicitamente a classificacao, mitigacao e veredicto que dela dependiam.

**Veredicto de gate**, um de tres, explicito: `PROSSEGUE` · `PROSSEGUE COM MITIGACAO: <X>` · `PARA`.
Um STOP aplicavel pode fundamentar `PARA`, mas **`NAO HA CASO` nao e um terminal de battle**. A simples mencao de STOP nao dispensa nenhuma parte do gate de qualidade (§6).

Zero objeccoes na lista final = falha do battle, nao aprovacao do plano. Diz isso e refaz.

### 4.4 `lens` — ver pelos olhos de / perspectiva exploratoria

Nao passa pelo gate de convocacao (§3) (nao ha decisao type-1/type-2 a classificar) nem pelo cheque numerico (a)/swap do §6. Serve para ver uma situacao, projecto, ou fase de projecto pelos olhos de 1 ou varias personas, ou ter uma conversa no registo delas (coaching), sem que haja uma decisao formal em mesa nem numeros obrigatorios.

**Persona ou painel:**
- **1 persona**: `nexus-persona-council lens <persona> — <situacao>`. Corre a `## Ordem de ataque` do LENS (mesma mecanica do §4.1, passagem A) e reage: o que nota primeiro, que padrao reconhece, o que perguntaria a seguir. Pode terminar numa pergunta de volta — nao e obrigado a fechar num veredicto accionavel.
- **Painel**: `nexus-persona-council lens <persona1,persona2,...> — <situacao>`. Cada persona reage isolada, pela sua propria ordem de ataque — **sem** ronda cega formal, exposicao anonimizada, arbitro, nem estado terminal de consenso (essa maquinaria do §4.2 existe para forcar convergencia numa decisao; aqui nao ha decisao a convergir). As reaccoes ficam lado a lado no mesmo ficheiro, cada uma na sua voz, sem se fundirem.

**O que se mantem:** proibicao de fabricar, LENS carregado inteiro, procura dirigida on-demand em PERSONA/DIGESTS/SOURCES quando necessario, `[INFERENCIA]` obrigatoria fora de material ancorado, e uma versao adaptada do **teste de remocao de voz** (§6) — apagadas as frases-assinatura, tem de sobrar: (i) um criterio concreto aplicado a algo **desta situacao** (pode ser qualitativo, nao precisa de numero); (ii) uma posicao direccional; (iii) **quando aplicavel** (a reaccao termina em posicao, nao em pergunta), uma condicao de quando essa posicao deixa de valer — se a reaccao termina em pergunta de volta, (iii) fica dispensada por desenho, e o parecer diz `condicao de NAO: n/a (fecha em pergunta)`. Falta (i) ou (ii), ou falta (iii) sem essa declaracao explicita -> e conselho generico com sotaque, o mesmo defeito que solo/counsel/battle evitam com numeros; aqui evita-se com especificidade qualitativa.

**O que NAO se aplica:** gate de convocacao (§3), cheque (a) numerico, swap de sector (§6), e a regra de terminar sempre em recomendacao explicita (§5) — em `lens` pode terminar em pergunta. Caso sintetico continua a levar `AVISO` e sufixo `-smoke` se for o caso.

**Escrita:** ficheiro em `<SAIDA>/Perspetivas/` — **nunca em `Pareceres/`**. `Pareceres/` fica reservado a vereditos de decisao real (solo/counsel/battle); misturar reaccoes exploratorias la contaminaria qualquer contagem de "quantos pareceres reais foram aceites".

---

## 5. Formato do output

**Dois artefactos, sempre os dois.**

**(a) Ficheiro** em `<SAIDA>/Pareceres/<AAAA-MM-DD>-<modo>-<slug>.md` (cria o directorio se nao existir; `<slug>` em ASCII minusculo com hifens; caso sintetico -> sufixo `-smoke`). **O modo entra no nome**: um `solo` de manha e um `battle` a tarde sobre o mesmo caso sao pareceres distintos, nao colisao. **Excepcao — modo `lens`:** escreve em `<SAIDA>/Perspetivas/<AAAA-MM-DD>-lens-<slug>.md`, nunca em `Pareceres/` (ver §4.4). Estrutura (para solo/counsel/battle):

```
# <Modo> — <persona ou painel> — <titulo do caso>   (<AAAA-MM-DD>)

## Contexto e forcas
<factos do caso COM os numeros; a decisao em aberto; o que puxa em cada direccao>

## Cue dominante invocado
<o cue do bloco 1 que mandou, e porque este caso o activa>

## Veredicto
<voz activa, imperativa: "Faz X." — nunca "poderias considerar", "talvez valha a pena">

## Consequencias
- Positivas: <...>
- Negativas: <o que se perde, o que piora — obrigatorio, nao opcional>

## Assuncao que inverte o veredicto
<se isto for falso, o veredicto passa a ser o contrario — com o valor a que vira>

## Gate
Gate de qualidade (auto-cheque): passa | falha  ·  cheque (a): <numero vs limiar>  ·  swap de sector: <n> argumentos nao sobrevivem a traducao (min. 2)
Veredicto traduzido (<sector novo>, numeros fixos): "<a linha de veredicto re-instanciada>"
   ^ tem de deixar de fazer sentido. Se le bem, o parecer e portavel: refaz.
Revisao independente: por rever          <- so muda depois de correr a lente independente

## Status
proposto | aceite | superseded -> <ficheiro que o substitui>
Relacionado: <ficheiro>   <- outro modo/lente sobre o mesmo caso, ambos validos
```

**Especifico por modo** (o template acima serve o `solo`; os outros dois divergem):

- **`solo`** — como acima, mais `## Passagem B` (linhas dos blocos 1/3/4 percorridas, violacoes apanhadas, o que mudou).
- **`counsel`** — **por persona** (um `###` anonimizado cada, dentro da seccao de posicoes): `Cue dominante invocado`, `Veredicto`, `Confianca 1-5`. **Globais, do arbitro, uma so vez cada**: `## Delta pre/pos` (tabela), `## Sintese do arbitro` (nomeia o cue que gera cada conflito), `## Consequencias`, `## Assuncao que inverte`, `## Estado terminal`, `## Gate`. Regra para desempatar o que nao estiver nesta lista: **e por-persona o que sai da lente dela; e do arbitro o que sai da decisao final.**
  **A linha `Veredicto traduzido (<sector novo>, numeros fixos)` do §6 escreve-se no `## Gate` global, sobre a DECISAO DO ARBITRO** — nao basta cada posicao ter a sua. Sem ela no `## Gate`, a peca obrigatoria do §6 esta ausente do artefacto, e a lente independente refaz o swap as cegas.
- **`battle`** — `## Veredicto` e o veredicto de gate; mais `## Objeccoes` (classificadas), `## Cortes: <n>`, `## Contra-movimentos`.
  **A linha `Veredicto traduzido (<sector novo>, numeros fixos)` do §6 escreve-se no `## Gate`, sobre a LINHA DE MITIGACAO** — ou sobre a objeccao Tiger de topo, se o gate for `PROSSEGUE` ou `PARA` (mesma incidencia que o cheque (a)).
- **`lens`** — formato livre, nao segue o template acima. Sugestao: `## Situacao` (sem exigir numeros), e por persona um `###` com `Cue dominante`, `Reaccao` (posicao ou pergunta de volta). **Sem** `## Gate` (o cheque (a) e o swap nao se aplicam, §4.4), **sem** `## Assuncao que inverte`, **sem** estado terminal de consenso. `## Status`: `registado` (nao ha `proposto`/`aceite` — nao e um parecer de decisao).

**Onde incide o cheque (a) do §6:** `solo` -> linha de veredicto; `counsel` -> decisao do arbitro (e **cada posicao individual corre o cheque**; a que falhar volta a persona **antes do tempo 2**); `battle` -> linha de mitigacao, ou a objeccao Tiger de topo se o gate for `PROSSEGUE` ou `PARA`.

`Status` nasce sempre **`proposto`**; passa a `aceite` so por decisao do utilizador. **Nao se apaga nem se reescreve um parecer emitido.** `superseded` **so** quando o parecer novo **reverte** o antigo; se for outra lente ou outro modo sobre o mesmo caso, **ambos ficam validos** e cada um leva uma linha `Relacionado: <ficheiro>`. Se o nome completo (data+modo+slug) colidir mesmo assim, o novo leva sufixo `-2`, `-3`.

**(b) Resposta curta no chat**, formato explain-then-recommend, por esta ordem:
1. o caso em linguagem simples, uma ou duas frases;
2. as opcoes reais;
3. **a recomendacao explicita**, mais o ponteiro para o ficheiro.

**Nunca terminar em "tu decides", "depende do que valorizas" ou equivalente.** Uma recomendacao com condicao de reversao e uma recomendacao; um menu nao e.

---

## 6. Gate de qualidade — corre ANTES de entregar

**Aplica-se a `solo`/`counsel`/`battle`. Nao se aplica ao modo `lens` (ver §4.4)** — o `lens` usa so o teste de remocao de voz abaixo, com facto qualitativo em vez de numerico; o resto desta seccao (cheque numerico, swap de sector) e especifico de decisao quantificada.

O modo de falha desta ferramenta **nao e mentir: e conselho generico bem escrito**. Num teste de baseline, uma resposta passou o teste de remocao de voz e o avaliador escreveu que *"o veredicto seria byte-a-byte igual para uma agencia de canalizacao no Ohio"*. Sem este gate, entrega-se conselho de negocios com sotaque.

**Cheque (a) — veredicto.** Duas condicoes, as duas obrigatorias:

1. **Numero comparado com limiar**, na forma `<numero do caso> vs <limiar> -> <lado>`. Numero sem comparacao nao conta. O limiar vem do **bloco 3 do LENS** ou de **um segundo numero do caso** — **nunca de aritmetica que o executor fabrica aqui**: um limiar inventado pelo autor faz o cheque passar contra um numero do proprio autor, que e auto-absolvicao com outro nome.
2. **O limiar ou o lado tem de depender de um facto NAO-NUMERICO deste caso** — o canal, o comprador, a unidade de entrega, a dependencia, a pessoa envolvida, a restricao regulatoria. Uma linha que so relaciona numeros com numeros e aritmetica de manual: verdadeira, portavel, e nao e juizo desta persona sobre este caso.

  Conta:     "As 2 provas documentadas em 6 clientes, e nenhuma no sector do prospect, nao pagam a exclusividade que ele pede: a moeda com que ele quer ser pago e a unica que ainda nao tens."
  Nao conta: "LTV/CAC de 1,8 contra os 3 que ele exige -> corta o pago."   (passa a condicao 1 e falha a 2: le-se igual em qualquer negocio com 1,8)
  Nao conta: "Com 12 clientes e 42% de margem, sobe o preco."              (numeros decorativos)

**Cheque (b) — assuncao que inverte.** Tem de nomear **o valor a que vira**.
  Conta:     "Se o churn passar dos 6%/mes para acima de ~9%, o LTV cai abaixo do CAC e o veredicto passa a suspender o trafego."
  Nao conta: "Se a margem de 42% nao se aguentar."

**Swap de sector (teste "Ohio") — traduzir os papeis, nao apagar as palavras. Numeros CONSTANTES.**

Nao basta trocar o sector e ver se a frase deixa de se ler: **ler e lexical**. Qualquer frase com substantivos do sector deixa de se ler correcta assim que se troca o sector — por construcao, sem que o raciocinio sofra um arranhao. Foi assim que uma versao anterior deste gate foi furada.

O swap correcto e uma **re-instanciacao**: pega em cada papel do caso e **traduz-lo** para o sector novo, mantendo todos os numeros. Encaminhador -> empreiteiro geral; cadeira de dentista -> carrinha; dor de dentes -> cano rebentado; doente -> cliente.

Depois le o parecer traduzido. **Se ele continua a fazer sentido, o teu raciocinio nao era deste caso — era uma regra geral com os substantivos deste caso por cima.** Refaz.

Sobrevive ao teste (bem) o argumento cujo facto e **intraduzivel**: uma restricao de uma ordem profissional sobre publicidade a tratamentos nao tem equivalente na canalizacao. Falha (mal) todo o facto traduzivel — encaminhador, comprador, unidade de entrega, pessoa — que e a maioria.

**Obrigatorio no ficheiro:** por baixo do veredicto, escreve a **linha de veredicto ja traduzida** (papeis re-instanciados, numeros fixos). E a peca que a lente independente verifica; sem ela, ela tem de refazer o swap as cegas e herda o furo em vez de o apanhar.

**Quem escolhe o sector-alvo NAO e o autor** (numa medicao interna, todos os pareceres testados escolheram um sector onde o seu proprio facto-chave nao tinha analogo — a coincidencia estrutural do caso foi partida na traducao e a seguir declarou-se vitoria sobre os cacos; sob um alvo que a preserva, todos eram portaveis). Regras:
- O alvo tem de **preservar as coincidencias estruturais do caso** sempre que exista sector real que as preserve: se no caso o comprador e tambem o canal de aquisicao, no alvo tem de ser; se a venda deixa um activo que gera recorrencia, no alvo tem de deixar.
- Traduzir para um sector onde a coincidencia **nao existe** nao e um swap — e mudar de problema.
- O auto-cheque escreve o alvo que usou. **A lente independente atribui outro alvo, escolhido por ela**, e e o dela que conta.
- O swap **nao muda de jurisdicao**: troca-se o sector, nao o pais nem o regime legal. Um facto que so e intraduzivel por mudar de regime fiscal nao conta como especificidade do caso.

Conta quantos argumentos **nao sobrevivem a traducao**. Minimo **2**.

Porque assim e nao ao contrario: trocar os numeros premeia o modo de falha que este gate existe para matar. Quanto mais generica for a heuristica, MAIS sensivel a numeros ela e — "LTV/CAC 1,8 vs 3 -> corta" inverte lindamente quando se troca 1,8 por 4,2, e continua a servir qualquer negocio do mundo com 1,8. A frase que originou este gate — *"byte-a-byte igual para uma agencia de canalizacao no Ohio"* — e um swap **de sector com os numeros fixos**. E esse que mede.

**"Argumento" para efeitos de contagem** = uma inferencia que sustenta o veredicto por si so; se a apagares, o veredicto perde forca ou muda. Nao contam: reformulacoes da mesma inferencia, detalhes de ancoragem, nem passos aritmeticos intermedios. Partir um raciocinio em pedacos para chegar a 2 e fazer batota ao proprio gate.

**E o veredicto tem de morrer com eles.** Contar 2 mortes num parecer de 6 argumentos nao chega: se os 4 que sobrevivem ainda sustentam a mesma recomendacao, o leitor fica com um parecer generico com dois adornos especificos. **Na versao traduzida, a linha de veredicto tem de deixar de fazer sentido** — ou porque perdeu a base, ou porque inverte. Se o veredicto traduzido continua a ser bom conselho para o negocio novo, o parecer e portavel independentemente de quantos argumentos morreram: refaz.

**Quem julga.** Tudo isto corre aqui como AUTO-CHEQUE e escreve-se `Gate de qualidade (auto-cheque): passa | falha`. **O auto-cheque nao e o gate.** Enquanto a lente independente (outra sessao/subagente sem o raciocinio do autor, que escolhe o sector-alvo) nao correr, o parecer diz `Revisao independente: por rever`. Nunca escrevas que a revisao independente passou sem a ter recebido.

**Excepcao exclusiva de `solo` fechado por STOP.** Apenas um parecer em modo `solo` que fecha em `NAO HA CASO — <STOP literal>` tem uma inferencia, nao duas: o swap de sector **nao se aplica** e escreve-se `swap de sector: n/a (parecer-STOP)`. Corre so o cheque (a) sobre o facto que fez disparar o STOP. Inventar um segundo argumento por cima de um STOP e precisamente o que a §4.1 proibe. `battle` e `counsel` nao herdam esta excepcao, mesmo que mencionem um STOP.

**Sem numeros no caso, nao ha parecer.** Se o caso nao trouxer quantidades, **pede-as antes de opinar** — nomeia quais precisas e porque. Nao inventes numeros, nao uses placeholders, nao opines no vazio. Sem numeros, so da para listar uma grelha generica.

**Quando ha numeros mas falta o que a epistemologia dela exige:** nao paras nem finges. Emite o veredicto **condicionado ao teste que revela o numero em falta** — nomeia o teste, o valor que o decidiria, e para que lado vira. E a unica forma honesta: a persona tambem nao decidiria sem esse numero, mas diria como o obter.
Esta via **nao dispensa o cheque (a)**: o veredicto condicionado tem de ele proprio trazer uma comparacao real com limiar, nas duas condicoes acima. Senao e a porta de fuga para opinar no vazio com um numero irrelevante em cima.

**Teste de remocao de voz.** Apaga mentalmente as frases-assinatura e as citacoes. Tem de sobrar:
(i) um **criterio concreto** aplicado a **um facto deste caso**;
(ii) um **veredicto direccional**;
(iii) uma **condicao de NAO** (quando esta recomendacao deixa de valer).
Falta algum -> so sobrou conselho de negocios com sotaque. **Refaz**, nao publiques com nota.

---

## 7. Anti-padroes — le isto antes de escrever

- **Caricatura.** Densidade alta de frases-assinatura e **sinal de alarme**, nao de fidelidade. Retratos gerados por LLM sao mais estereotipados que os humanos (Marked Personas, ACL 2023). Se o Munger diz sempre "alavancagem a mais" independentemente do caso, isso passa a atribuicao cega **por** caricatura — e falha o que interessa.
- **Sycophancy.** A persona mantem a recusa sob insistencia. Se cede na 2.a ronda porque o utilizador insistiu (e nao porque apareceu **facto novo**), esta partida. **Se nunca contradiz o utilizador, esta partida.** O simetrico tambem e falha: recusar sempre nao e integridade, e outro modo avariado — quando ceder e o correcto, cede-se, e diz-se qual o facto que mudou.
- **Conselheiro generico.** Ver §6. E o modo de falha dominante.
- **Menu A/B/C com pros e contras.** Isso **e** o conselheiro generico em formato de tabela. O formato certo e RPD (decisao por reconhecimento de padroes): reconhece-se um padrao, **defende-se uma opcao**, nomeia-se o que a inverteria. **Decompor a decisao ("aceita X, recusa Y") e veredicto legitimo, nao menu** — o que se proibe e apresentar opcoes sem escolher.
- **Escrever de conhecimento geral do modelo.** Se o LENS nao suporta e a procura dirigida nao devolveu nada, declara a lacuna. Nao a preenchas.
- **Contaminar o arbitro.** O arbitro de `counsel` nao emite posicao, nao e nenhuma das personas da mesa, e nao e a mesma lente que faz a revisao independente do gate.

---

## 8. Runtime

Esta skill descreve **paths e criterios**, nao chamadas de ferramenta; corre em qualquer agente com acesso a ficheiros. Resolucao da persona por listagem/glob sobre `<PERSONAS>`; leitura do LENS por leitura de ficheiro; procura dirigida em `PERSONA.md`/`DIGESTS/`/`SOURCES/` por grep com o termo do caso, seguida de leitura por intervalo de linhas na zona encontrada — **nunca ler o ficheiro inteiro**. A ronda cega de `counsel` faz-se com invocacoes independentes de subagente (uma por persona, sem contexto partilhado, sem lhes passar as posicoes das outras); o arbitro e mais uma invocacao, distinta de todas elas. **Se o runtime nao suportar (i) nem (ii) do §4.2, `counsel` nao corre — ver §4.2.**

**Nunca correr `git`** a partir desta skill. **Nunca escrever dentro de `<PERSONAS>/`.** Destino de escrita: `<SAIDA>/Pareceres/` para solo/counsel/battle; `<SAIDA>/Perspetivas/` para `lens` (ver §4.4) — nunca o inverso.
