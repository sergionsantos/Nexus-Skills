# PLAN — CLI Python `hello` com teste (exemplo mínimo)

> Exemplo completo e pequeno no formato do §6 do SKILL.md. Passa `bash scripts/validate-plan-spec.sh references/example-mini-plan.md`. Um plano real tem mais milestones, reality-check do ambiente e red-team; aqui o objectivo é só mostrar a forma.

## §0 Facts do ambiente (verificados)

- Python 3 disponível (`python --version`); sem dependências externas. Ver nota do shell abaixo.
- Shell: os comandos usam sintaxe bash (Git Bash no Windows). Em Windows o Python do venv é `.venv/Scripts/python`; em Linux/macOS é `.venv/bin/python`. Este exemplo não usa venv e usa `python`.

## §0.5 Locked Decisions Register

| ID | Decisão | Porquê |
|---|---|---|
| D01 | Pasta de trabalho `hello-cli/` com `hello.py` e `test_hello.py` | Um módulo e um teste bastam |
| D02 | Testes com `unittest` da stdlib (`python -m unittest`) | Zero dependências a instalar |
| D03 | `greet(name)` devolve `Hello, <name>!`; sem argumento a CLI usa `world` | Comportamento fixo, sem decisões ao executor |

## Milestone M1 — Núcleo

### Step M1.1 — Criar a função greet

**Goal:** existir `hello-cli/hello.py` com `greet(name)` (D03).
**Depends on:** nenhum.
**Files touched:** `hello-cli/hello.py` (novo).
**Behavior spec:** `greet("Ana")` devolve `Hello, Ana!`.
**Implementation:**

```python
def greet(name):
    return "Hello, " + name + "!"
```

**Commands:**

```bash
mkdir -p hello-cli
# colar o código acima em hello-cli/hello.py
```

**Verify:**

```bash
cd hello-cli && python -c "from hello import greet; print(greet('Ana'))"
```

Expected: `Hello, Ana!`

**If verify fails:** `ModuleNotFoundError: hello` → o comando não correu dentro de `hello-cli/` ou o ficheiro tem outro nome; confirma com `ls hello-cli`. `SyntaxError` → o código colado diverge do bloco acima; volta a colar.
**Done when:** o Verify imprime exactamente `Hello, Ana!`.

### Step M1.2 — Teste unitário de greet

**Goal:** teste automático do comportamento D03.
**Depends on:** M1.1.
**Files touched:** `hello-cli/test_hello.py` (novo).
**Behavior spec:** o teste passa quando `greet("Ana") == "Hello, Ana!"`.
**Implementation:**

```python
import unittest
from hello import greet


class TestGreet(unittest.TestCase):
    def test_greet(self):
        self.assertEqual(greet("Ana"), "Hello, Ana!")


if __name__ == "__main__":
    unittest.main()
```

**Commands:**

```bash
# colar o código acima em hello-cli/test_hello.py
```

**Verify:**

```bash
cd hello-cli && python -m unittest -v
```

Expected: última linha `OK` e `Ran 1 test`.

**If verify fails:** `ModuleNotFoundError: hello` → corre de dentro de `hello-cli/`. `AssertionError` → `greet` devolve texto diferente; compara com M1.1.
**Done when:** `python -m unittest` termina com `OK` (exit code 0).

## Milestone M2 — CLI

### Step M2.1 — Ponto de entrada da linha de comandos

**Goal:** `python hello.py [nome]` imprime a saudação (D03).
**Depends on:** M1.2.
**Files touched:** `hello-cli/hello.py` (editado: acrescenta no fim).
**Behavior spec:** sem argumento imprime `Hello, world!`; com argumento `Ana` imprime `Hello, Ana!`.
**Implementation:**

```python


if __name__ == "__main__":
    import sys
    print(greet(sys.argv[1] if len(sys.argv) > 1 else "world"))
```

**Commands:**

```bash
# acrescentar o bloco acima ao FIM de hello-cli/hello.py
```

**Verify:**

```bash
cd hello-cli && python hello.py && python hello.py Ana
```

Expected: duas linhas, `Hello, world!` e `Hello, Ana!`.

**If verify fails:** nenhuma saída → o bloco ficou dentro de `greet` (indentação); tem de estar na coluna 0. `NameError: greet` → o bloco foi colado antes da função.
**Done when:** as duas linhas esperadas aparecem e o exit code é 0.

### Step M2.2 — Reverificar o teste após a edição

**Goal:** confirmar que M2.1 não partiu o teste de M1.2.
**Depends on:** M2.1.
**Files touched:** nenhum.
**Behavior spec:** a suite continua verde.
**Implementation:** sem código novo.
**Commands:**

```bash
cd hello-cli && python -m unittest
```

**Verify:**

```bash
cd hello-cli && python -m unittest -v
```

Expected: `Ran 1 test` e `OK`.

**If verify fails:** `FAILED` → lê o traceback; a causa provável é M2.1 ter alterado `greet`; repõe o bloco de M1.1 e repete M2.1.
**Done when:** `OK` e exit code 0.
