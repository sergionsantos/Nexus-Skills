# Formato do `LENS.md` (motor de julgamento de uma persona)

A skill `nexus-persona-council` so funciona com personas que tenham um `LENS.md`. Esta pagina descreve o formato esperado. A skill **nao traz personas**: tu escreves (ou geras) os `LENS.md` das pessoas cujo juizo queres usar, com base em material real (livros, transcricoes, entrevistas).

## O que e

Motor de julgamento de **uma pessoa concreta** sobre **casos concretos**. Nao e resumo, bio nem lista de frameworks. Teste de existencia: se uma linha continuar verdadeira depois de trocares o nome da persona por outra do painel, essa linha nao pertence ao LENS. Limite duro: 8000 caracteres (tem de caber inteiro em contexto).

## Estrutura (headings, por esta ordem)

```
# LENS — <Nome>
## 1. Cues e pesos
## 2. Padroes -> accao
## 3. Criterios de rejeicao
## 4. Epistemologia
## 5. Voz
## Ordem de ataque
## Casos trabalhados
## Lacunas          (opcional; obrigatorio se alguma quota ficar abaixo do minimo)
```

Quotas minimas sugeridas: >=8 pares no bloco 2, >=3 criterios no bloco 3, 3-5 perguntas na ordem de ataque, >=2 casos trabalhados. Se o material nao chega, declara em `Lacunas` em vez de inventar.

## Os blocos

1. **Cues e pesos** — o que a pessoa olha primeiro num caso novo, por que ordem, e o que ignora de proposito. Mau: "foca-se nos numeros" (serve a qualquer analista).
2. **Padroes -> accao** — pares condicionais: `Quando <padrao observavel> -> <accao executavel>, porque <razao>.`
3. **Criterios de rejeicao** — quando diz NAO e com que mecanismo (numero, limiar, facto que dispara o nao).
4. **Epistemologia** — que prova aceita, que erro teme mais, em que horizonte julga o resultado.
5. **Voz** — curto, no fim: marcadores de registo e vocabulario. Nao e o produto.

**Ordem de ataque** — 3-5 perguntas numeradas, pela ordem em que a pessoa as faz. Os criterios de paragem escrevem-se com o token literal `STOP:` (maiusculas, dois pontos). Um `STOP:` autonomo escreve-se sem bullet e sem numero.

**Casos trabalhados** — >=2 casos reais do material, cada um sob um sub-heading `###`, com factos, o que a pessoa perguntou, `**Veredicto**` direccional e a condicao que o inverteria.

## Ancoras (obrigatorias)

Cada linha dos blocos 1-4 tem de levar uma ancora para o material de origem:

```
- <afirmacao numa frase>. [ancora: <ficheiro>.md#<heading> | "<citacao verbatim de 5 a 15 palavras>"]
```

A citacao tem de conter a clausula que sustenta a afirmacao (limiar, verbo de rejeicao, condicao) — nao basta a parafrase de um resumo. Nao ancores em listas de frases-assinatura soltas, sem contexto de decisao: uma linha sem ancora valida nao conta como linha do LENS. A clausula decisoria tem de estar dentro das aspas. Uma linha `Lacunas` so e valida se disser o bloco, o numero da linha e o porque. O limite de 8000 caracteres e estrito: abaixo de 8000, nao igual.

## Estrutura de pastas

```
<pasta-de-personas>/
  <Area>/                 (opcional; ex.: Negocios, Investimento, Negociacao)
    <Nome-Com-Hifens>/    (ASCII sem acentos: Alex-Hormozi)
      LENS.md             (obrigatorio)
      PERSONA.md          (opcional, banco de citacoes/evidencia, nunca lido inteiro)
      DIGESTS/ SOURCES/   (opcionais, consulta dirigida)
```
