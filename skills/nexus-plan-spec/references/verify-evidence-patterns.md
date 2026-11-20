# Padrões de evidência — "verify literal fresh" e verify ad-hoc

Quando o contexto exige "verify real corrido neste turno + exit code visível", só conta **evidência real de comandos corridos neste turno**: nada de caches, paráfrases ou "PASS" nu.

## A. Evidência canónica (3 comandos)

### 1. `pytest --junitxml` (testes)

```bash
cd <worktree> && pytest --junitxml=/tmp/<id>.xml -q 2>&1 | tail -3
echo "PYTEST_EXIT=${PIPESTATUS[0]}"
python - <<'EOF'
import xml.etree.ElementTree as ET
root = ET.parse('/tmp/<id>.xml').getroot()
for ts in root.iter('testsuite'):
    print(f"tests={ts.attrib['tests']} failures={ts.attrib['failures']} errors={ts.attrib['errors']}")
    break
EOF
```

Esperado: `PYTEST_EXIT=0` (número, não texto) e `tests=<n> failures=0 errors=0`, com `n` = a contagem canónica do repo. Atenção a `tests=3 errors=3` vindo de um subprocesso sem `cwd` correcto: NÃO é falha real (ver `execution-subroutines.md` §1). `failed=1` com exit 2 = falha real: diagnostica com `--tb=line`.

### 2. `git merge-base --is-ancestor` (prova que o merge aconteceu)

```bash
git merge-base --is-ancestor <branch> main && echo "is-ancestor: YES" || echo "is-ancestor: NO"
```

### 3. `git ls-remote origin <branch>` (prova que o push chegou)

```bash
git ls-remote origin main | head -1     # <sha>\trefs/heads/main
```

O SHA tem de coincidir com `git rev-parse HEAD`; se não, o push não chegou.

**Bloco de 4 verificações para "merge para main":** `git log --oneline --graph -8` · `git rev-parse HEAD` · is-ancestor · `git ls-remote origin main` · testes com exit code — numa só chamada, reportando cada exit code e cada linha.

## B. Anti-padrões

- ❌ Reciclar evidência de outro dia quando se pediu probe nova (usa o timestamp de hoje).
- ❌ `tests=3 errors=3` reportado como "suite verde" por não ter lido os contadores (lê sempre failures/errors do junit).
- ❌ "PASS" nu (sem dump, exit code ou SHA).
- ❌ Verify em cache: se o estado pode ter mudado (ficheiros, daemon, DB), re-corre.

## C. Template de reporte honesto quando o verify está bloqueado

```
@@BLOCKED — <artefacto> verify (turno N+1)

Verificado (neste turno):
- <A>: exit=0, evidência <…>
- <B>: count=N, evidência <…>

Não verificado neste turno (dependente de estado):
- <C>: verificado no turno N; para re-correr precisa de <…>
```

Não declares "done" quando o único verify é mais antigo que o turno actual: re-corre ou declara BLOCKED.

## D. Verify ad-hoc em turnos "só emissão" (planeamento, sem execução)

Num turno que só emite artefactos (o plano, ficheiros do executor, validador), o sistema pode reportar "unverified" porque o validador falha pré-execução (a infra que o plano cria ainda não existe) — **é por desenho**. Verifica o que é verificável com um script temporário e reporta honestamente.

Receita:

```bash
V=$(mktemp -t verify-<contexto>-XXXX.sh)
cat > "$V" <<'EOF'
# asserts aqui; imprime PASS/FAIL por check
EOF
bash "$V"; rm -f "$V"        # auto-limpeza
```

Invariantes do script:
1. Caminho seguro do SO (`mktemp`/`tempfile.gettempdir()`), nunca `/tmp` fixo.
2. Auto-limpeza no fim (e limpa também as probes ad-hoc da fase de ground-truth).
3. Categorias de assert: (a) artefactos existem, não vazios, com tamanho; (b) parsáveis (`ast.parse`, `node -c`, `bash -n`); (c) identificadores críticos presentes; (d) invariantes de conteúdo (pin certo; pins errados = 0).
4. **Símbolo → ficheiro-dono:** faz grep de cada símbolo no ficheiro onde vive (não procures `BASE_URL` num validador se vive no `.ts`) — o grep com âmbito errado é uma causa frequente de falso FAIL.
5. Em Python, não uses backslash dentro de f-strings (erro de sintaxe); constrói a string com `r'''...'''`.
6. **Reporte honesto:** se deu 21 PASS / 1 FAIL, diz ambos.
7. Declara explicitamente o que NÃO verificaste (ex.: não executei o milestone 0, não corri a suite e2e, não corri lint/build sobre markdown, não toquei em `.env`, não fiz commits).

Num caso real este verify ad-hoc apanhou um bug no próprio validador (procurava `**Goal**` sem dois-pontos, mas os steps usavam `**Goal:**`), corrigido no próprio turno.

Mensagem-tipo após o verify:

```
Verify ad-hoc — resumo (NÃO é suite verde)
Script temporário: <caminho> (criado, corrido, limpo).
N PASS, M FAIL.
Verifiquei: <lista>
Não verifiquei (e não vou fingir): <lista>
Bloqueador concreto: <o que impede suite verde>
Próximo passo canónico: <sessão seguinte arranca em M-X.1>
```
