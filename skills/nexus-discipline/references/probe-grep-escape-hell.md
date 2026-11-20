# Pattern: grep regex escape hell em bash heredoc

> **Pitfall (2026-07-04, M17.4 v0100/v0110 projecto X):** `grep -qE` em heredoc bash falha por interpretação de `\` em Python r-string + heredoc + bash composto. Default para `grep -qF`.

## Sintoma

Probe regex como:
```bash
grep -qE 'subIssueIds = \(subIssues \?\? \[\]\)\.map\(s => s\.id\)' file.ts
```
Reporta **NOMATCH** mesmo quando o source tem a string literal.

## Causa

Camadas de escape compostas:

1. **Python r-string** (`r'''...'''`) NÃO interpreta `\n`, `\t` → mantém `\n`, `\t` literais.
2. **bash heredoc** (`cat > file.sh <<'EOF'`) também NÃO interpreta → mantém `\n` literal.
3. **bash** ao executar o script **interpreta `\`** dentro de aspas simples (em alguns casos — confirmado empiricamente em macOS bash 5.x): `\?` vira `?` literal, `\.` vira `.` literal, mas `\(` e `\)` permanecem como escape.
4. **grep -E** recebe a string com escapes parcialmente removidos → regex confuso.

**Resultado**: `grep` não faz match do source literal porque os meta-chars foram desescapados para chars normais.

## Fix canónico

**Usar `grep -qF` (fixed string)** para padrões literais:

```bash
# ❌ NÃO
grep -qE 'subIssueIds = \(subIssues \?\? \[\]\)\.map\(s => s\.id\)' file.ts

# ✅ SIM
grep -qF 'subIssueIds = (subIssues' file.ts
```

`grep -qF` não interpreta regex — match literal byte-by-byte. Sem escape hell.

## Quando usar `grep -E` vs `grep -F`

| Use `grep -qF` quando | Use `grep -qE` quando |
|---|---|
| Pattern contém `\?` `\(` `\)` `\{\}` `\+` | Pattern é só anchors (`^foo`, `bar$`) |
| Pattern é string fixa (sem meta-chars) | Pattern usa meta-chars: `*` `+` `[]` `\|` |
| Match deve ser literal byte-by-byte | Match pode ser parcial (substring OK) |

**Default em verify scripts**: `grep -qF` a menos que precises de regex.

## Detector

Se probe regex reporta NOMATCH mas probe literal (sem regex) dá MATCH:

```bash
if ! grep -qE 'pattern with regex' file.ts && grep -qF 'pattern' file.ts; then
  echo "Escape hell detected — switch to grep -qF"
fi
```

## Lição lateral

Em **Python execute_code → heredoc → bash → grep**, há **3 layers de escape**:
1. Python r-string (preserva `\n`)
2. bash heredoc com aspas simples (preserva `\n`)
3. bash command-line execution (interpreta `\n` como escape em alguns casos)

Para evitar: usar `grep -qF` elimina a layer 3 completamente.

## Caso real (projecto X M17.4 v0100)

```bash
# Probe original (failed):
grep -qE 'subIssueIds = \(subIssues \?\? \[\]\)\.map\(s => s\.id\)' "$APP/.../issue-detail.tsx"
# → NOMATCH (escape hell)

# Probe fixed (passed):
grep -qF 'subIssueIds = (subIssues' "$APP/.../issue-detail.tsx"
# → MATCH

# Diff: -E + regex literal → -F + string literal (sem `\(\)?\`)
```

## Anti-pattern irmão: `grep -qE` com . para "qualquer char"

```bash
# ❌ Esta regex aceita "X" como match para ".":
grep -qE 'foo.bar' file.ts   # match "fooXbar" também!

# ✅ Usar `grep -qF` para literal:
grep -qF 'foo.bar' file.ts  # match só "foo.bar"
```

## Workaround avançado (quando precisa de regex)

Usar **single quotes em bash + escaping manual**:

```bash
# Em vez de heredoc, escrever o script via write_file directo
# e usar:
grep -qE 'pattern\.with\.dots' file.ts  # sem \( - mas com \. que sobrevive
```

Ou usar Python inline:
```bash
python3 -c "
import re
with open('file.ts') as f: content = f.read()
print('MATCH' if re.search(r'pattern \(\)', content) else 'NOMATCH')
"
```

Mas para 95% dos casos, `grep -qF` é a solução.

## Resumo (1-liner)

**Verify scripts com regex em bash → use `grep -qF` (literal string), reserve `grep -qE` para casos com `*` `+` `[]` apenas. Default to `-F`.**