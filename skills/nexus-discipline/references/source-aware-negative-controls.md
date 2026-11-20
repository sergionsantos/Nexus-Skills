# Source-Aware Negative Controls

> **Pitfall datado (2026-07-02, M10 projecto X).** Lição transversal a qualquer verify script: negative controls de "absence" precisam de **scope** (quais ficheiros iterar) — não apenas de um predicate (string a procurar). Probe source-blind apanha signal de outro owner (shadcn, third-party, código pré-existente) e reporta um fail que não é fail do change-set.

## O caso M10 v2025

O probe N3 da `v2025-fresh-20260702-2025.sh` era:

```bash
TW_HITS=0
for f in $CSS_FILES; do
  grep -qE "\.text-white\b" "$f" 2>/dev/null && TW_HITS=$((TW_HITS+1))
done
[[ "$TW_HITS" == "0" ]] && neg "N3: .text-white AINDA no build CSS (Tailwind purges unused)" || negbad "N3: .text-white em $TW_HITS files"
```

**Problema**: o probe iterava **todos os CSS files do build output** (1 file de ~68KB minificado com todos os utilities Tailwind). Match: 1 file (o CSS global). Real: o `.text-white` matched era do **shadcn primitive** `components/ui/button.tsx` (linha 14: `"bg-destructive text-white hover:bg-destructive/90"`), não do M10 work.

**Custo**: 1 round-trip extra do user + tempo a explicar que o `text-white` é "feature, not bug" do shadcn destructive button.

## Forma concreta da correcção (v2025p1)

O probe foi refinado para iterar **só pelos ficheiros que o change-set tocou**:

```bash
M10_FILES="$APP/src/app/globals.css $APP/src/app/layout.tsx $APP/src/app/w/[wsSlug]/layout.tsx $APP/src/components/command/command-palette.tsx $APP/src/components/inbox/inbox-view.tsx $APP/src/components/issues/issue-detail.tsx $APP/src/components/issues/issue-row.tsx $APP/src/components/issues/team-issues-view.tsx $APP/src/components/layout/sidebar.tsx"
TW_M10=0
for f in $M10_FILES; do
  grep -q "text-white" "$f" 2>/dev/null && TW_M10=$((TW_M10+1))
done
[[ "$TW_M10" == "0" ]] && neg "B3: text-white REMOVIDO de ficheiros M10-tocados" || negbad "B3: text-white em $TW_M10 ficheiros M10"
```

E shadcn primitives ficam como **B4 (info)**, não como fail:

```bash
TW_SHADCN=$(grep -l "text-white" "$APP/src/components/ui/"*.tsx 2>/dev/null | wc -l | tr -d ' \t')
ok "B4 (info): text-white em $TW_SHADCN shadcn primitives (esperado, botão destructive)"
```

## Lição meta (generalizável)

**"Absence" probes precisam de scope, não só predicate.**

```text
WRONG: "this string should not be anywhere in the repo"
       → apanha signal de outros owners; reporta fail espúrio

RIGHT: "this string should not be in MY change-set"
       → scope explícito (lista de ficheiros que o work tocou)
       → signal de outros owners tratado como [info] ou excluded
       → fail só quando o signal está onde o autor é responsável
```

## Decision tree (para futuros verify scripts)

1. **O que estou a provar com este negative control?**
   - "M10 não introduziu X" → scope = ficheiros M10-tocados
   - "X não existe em parte alguma" → scope = repo inteiro, mas documentar quem são os outros owners
2. **Pode o signal existir noutro owner?** (shadcn, third-party, lib externa, código pré-existente)
   - **Sim** → probe itera só pelo scope, ou trata os outros owners como `[info]` explícito
   - **Não** → probe repo-inteiro é seguro (e mais forte)
3. **O signal esperado está no source file OU no build output?**
   - **Build output** (CSS minificado, JS bundle) → Tailwind/esbuild remove espaços, comprime cores — o probe pode falhar por minification, não por regressão
   - **Source file** → probe mais fiável, mas exclui work pré-existente

## Detector de trigger (quando suspeitar)

Recebeste um fail num negative control que diz "X está presente em N files" mas o **source** desses files não é teu? Antes de declarar regressão, faz 1 grep source-only:

```bash
# Se o probe reports fail no build output:
grep -r "X" "$MY_TOUCHED_FILES"  # source-only, scoped ao change-set
```

Se o **source-only grep** também falha mas o **build output grep** passa, é **minification artifact**, não regressão.

## Caso de estudo adicional (visual design upgrade)

Mesmo padrão aconteceu com `oklch(0.66% 0.165 47)` (terracotta accent) — probe esperava `oklch(0.66 0.165 47)` (com espaço) mas o CSS minificado tem `oklch(66% .165 47` (sem espaço — Tailwind/PostCSS comprime). Source-only grep no `globals.css` confirma o OKLCH correcto; build output é uma variante minificada do mesmo value.

## Anti-pattern correlacionado

**Probe source-blind em `**/build/**` ou `**/.next/**`**: por mais tentador que seja, **NUNCA** seja o primeiro a iterar sobre o build output para provar o teu change-set. O build output é a manifestação minificada, optimizada, versionada pelo bundler — não é a source of truth. Se o teu probe está a iterar o build output, é porque (a) queres runtime prove (legítimo), ou (b) estás a contornar uma limitação da tua source-of-truth (suspeito). Opte por (a) e trata minification artifacts como `falso-falho` por defeito.

## Mutation checks de lógica temporal e janelas

1. **Estabelece uma baseline limpa:** executa a suite original no mesmo ambiente e com os mesmos imports que os mutantes; exige exit 0 antes de interpretar qualquer falha como detecção de regressão.
2. **Isola cada mutante numa cópia em scratch:** preserva os originais e regista os respectivos SHA-256 antes/depois. Confirma que a suite importa a cópia mutada, não o módulo original que ficou no caminho de imports.
3. **Confirma a aplicação da alteração antes de correr:** exige correspondência única do trecho alterado e diff esperado. Uma substituição sem efeito não testa a hipótese.
4. **Muda uma regra por execução:** para janelas temporais, cobre tamanho N−1/N+1, inclusão indevida do retorno actual, perda de cada intervalo adjacente e uso de dias civis em vez de sessões. Define antecipadamente qual comportamento cada mutante viola.
5. **Conta apenas falhas comportamentais relevantes como detecção:** erro de sintaxe, importação, preparação de fixtures ou timeout torna a execução inválida, não um mutante morto. Regista por mutante a alteração, o teste/assert que falhou e o exit.
6. **Expõe sobreviventes antes de reforçar a suite:** conserva o resultado inicial, acrescenta o teste em falta e volta a executar baseline e mutante; assim não se apresenta cobertura acrescentada depois como cobertura original.
7. **Separa evidência de dados de evidência de sensibilidade:** um oracle independente pode confirmar todas as linhas dos outputs sem demonstrar que a suite detecta mutações. Reporta essas duas verificações separadamente e mantém pendente o critério que não foi executado.

### Oracle independente para intervalos entre sessões

- Deriva a marca própria por intersecção entre as datas flagadas e os dois endpoints de cada par de sessões consecutivas; não copies o mapa de índices da implementação revista.
- Para o retorno na posição i, deriva as dependências pela união das marcas próprias nos N retornos anteriores, excluindo i. Compara as datas de origem completas, além dos booleanos, para detectar atribuições incorrectas com contagens totais iguais.
- Compara todas as linhas: endpoints, chaves únicas, estado de warm-up, motivos e conjuntos de flags. Contagens agregadas são resumo, não substituto da comparação.
- Distingue granularidades: intervalos identificados por flag/papel podem partilhar o mesmo retorno. Não exijas que o número de intervalos seja igual ao de retornos únicos marcados.
- Trata marca temporal como incerteza de alinhamento, não como invalidade automática de preço; mantém explícito que vazio não certifica os restantes timestamps.

### Execução anteriormente bloqueada

Recupera o comando e a decisão de aprovação do registo antes de explicar o bloqueio. Se o comando não ficou preservado, declara a lacuna; prepara um novo comando explícito e submete-o ao mecanismo normal de aprovação, sem o apresentar como reconstrução exacta nem contornar o bloqueio anterior. Uma proposta de mutation check ainda não executada continua proposta, não método validado.

## Resumo operacional

| Probe intent | Scope | Verdict do "fail" |
|---|---|---|
| "X não existe no source do change-set" | source files do change-set | Fail = regressão confirmada |
| "X não existe no build output do change-set" | build output, com minification-aware regex | Fail = regressão provada (cuidado com minify) |
| "X não existe em TODO O REPO" | repo inteiro | Fail = regression OR signal de outro owner — **investigar antes** |
