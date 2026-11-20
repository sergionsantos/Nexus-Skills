#!/usr/bin/env python3
"""
nexus-discipline — ISA Creator
Creates ISA artifacts at the contract-frozen path: {project}/.isa/ISA-[slug].md

Usage:
    python isa-create.py "task name" [--template ISA-Lite.md] [--project .] [--phase observe]

Phase 0 invariant honored:
    - Path shape:  .isa/ISA-<slug>.md  (matched by _ISA_PATH_RE in gate hooks)
    - Frontmatter: `phase: observe` (gap #1 fix — gates read this field; missing = fail-open)
    - Phase names: observe→think→plan→build→execute→verify→learn→complete (verbatim)
    - ISC format:  ### ISC-[CATEGORIA]-[N]: with - [ ] / - [x] checkboxes (contract dialect)
    - 12-section skeleton matching ISA-Full spec (templates/ISA-Full.md)
"""

import argparse
import re
import sys
from pathlib import Path
from datetime import datetime


# ---------------------------------------------------------------------------
# Slugify
# ---------------------------------------------------------------------------

def slugify(name: str) -> str:
    """Convert task name to a safe ASCII slug.

    Word-boundary safety: the replacement pipeline operates on the full string
    (not word-by-word), so there is no risk of mutilating composites like
    'Ledger' when replacing 'edge', or 'PostgreSQL' when replacing 'post'.
    The regex anchors used in nexus-discipline (\\bword\\b) are not needed here because
    we are *transforming* the whole string, not doing find-and-replace of a
    specific word inside prose — no false-positive risk applies.
    """
    name = name.lower()
    # Basic accent removal (Portuguese + common European)
    name = re.sub(r'[áàãâä]', 'a', name)
    name = re.sub(r'[éèêë]', 'e', name)
    name = re.sub(r'[íìîï]', 'i', name)
    name = re.sub(r'[óòõôö]', 'o', name)
    name = re.sub(r'[úùûü]', 'u', name)
    name = re.sub(r'[ç]', 'c', name)
    name = re.sub(r'[ñ]', 'n', name)
    # Collapse any non-alphanumeric run to a single hyphen
    name = re.sub(r'[^a-z0-9]+', '-', name)
    # Strip leading/trailing hyphens and collapse internal runs
    name = re.sub(r'-+', '-', name).strip('-')
    return name


# ---------------------------------------------------------------------------
# Valid phase names (contract-frozen — do NOT change without re-freezing contract)
# ---------------------------------------------------------------------------

VALID_PHASES = [
    "observe", "think", "plan", "build", "execute", "verify", "learn", "complete"
]


# ---------------------------------------------------------------------------
# 12-section ISA-Full skeleton
# ---------------------------------------------------------------------------

def build_isa_content(name: str, slug: str, filename: str, phase: str) -> str:
    """Build the full 12-section ISA skeleton with `phase:` frontmatter.

    Sections follow ISA-Full spec (templates/ISA-Full.md):
      1. Problem  2. Vision  3. Out-of-Scope  4. Principles  5. Constraints
      6. Goal  7. Criteria (ISC)  8. Test Strategy  9. Features
      10. Decisions  11. Changelog  12. Verification
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    return f"""---
title: "ISA: {name}"
description: "Ideal State Artifact para {name}"
date: {date_str}
path: ".isa/{filename}"
status: draft
phase: {phase}
---

# ISA: {name}

> **Phase:** `{phase}` — avança para `think` ao iniciar análise de risco.
> Edita o campo `phase:` no frontmatter conforme progredes (observe→think→plan→build→execute→verify→learn→complete).
> (Opcional: só se tiveres hooks/gates que leiam `phase:`, mantê-lo actualizado é o que os faz funcionar.)

---

## 1. Problem

[Descrever o problema ou necessidade que este ISA resolve. Ser específico e factual.]

## 2. Vision

[Descrever o estado ideal após execução bem-sucedida. O que o sucesso *parece* em concreto.]

## 3. Out of Scope

- [O que NÃO está incluído nesta iteração]
- [Adicionar mais itens conforme necessário]

## 4. Principles

1. [Princípio orientador 1 — ex: simplicidade antes de optimização]
2. [Princípio orientador 2]

## 5. Constraints

- **Tempo**: [X horas/dias]
- **Recursos**: [ferramentas/APIs disponíveis]
- **Dependências**: [o que tem de estar feito antes]

## 6. Goal

[Mensurável, específico, com deadline. Ex: "Entregar X funcional e verificado até YYYY-MM-DD."]

## 7. Criteria (ISC)

> Cada critério deve ser: **binário** (sim/não) · **testável** (verificável objectivamente) · **granular** · **independente**.
> Mínimo 5, ideal 10-15. Ao verificar: troca `- [ ]` por `- [x]` e anexa evidência no mesmo bloco.

### ISC-FUNC-01: [Funcionalidade principal]
- [ ] [Critério binário — ex: endpoint POST /api/x retorna 201 com payload válido]

### ISC-FUNC-02: [Funcionalidade secundária]
- [ ] [Critério binário]

### ISC-QUAL-01: [Qualidade de código/output]
- [ ] [Critério binário — ex: sem erros de lint; testes passam]

### ISC-PERF-01: [Performance]
- [ ] [Critério binário — ex: p95 < 200ms em carga de X req/s]

### ISC-DOC-01: [Documentação]
- [ ] [Critério binário — ex: README actualizado com instruções de setup]

## 8. Test Strategy

[Como os critérios acima serão verificados. Ferramentas, comandos, ambiente.]

```bash
# Exemplo de comando de verificação
# pytest tests/ -v
# curl -s http://localhost:3000/health | jq .
```

## 9. Features

[Lista de funcionalidades ou sub-tarefas que compõem este ISA. Pode ser vazio se o Goal já é atómico.]

- [ ] [Feature/sub-tarefa 1]
- [ ] [Feature/sub-tarefa 2]

## 10. Decisions

| Decisão | Alternativas consideradas | Racional |
|---|---|---|
| [Decisão técnica/design] | [Alternativa A, B] | [Porquê esta] |

## 11. Changelog

| Data | Fase | Nota |
|---|---|---|
| {date_str} | observe | ISA criado |

## 12. Verification

> Preencher ao entrar na fase `verify`. Cada item exige evidência de tool (não "parece certo").

- [ ] Todos os ISC verificados com evidência de tool capturada?
- [ ] Goal atingido (mensurável)?
- [ ] Revisão independente concluída (Rule 0, SKILL.md §1 — obrigatória para código não-trivial/unattended)?
- [ ] Sem findings bloqueantes no diff revisto?

---
**Status**: Draft
**Criado**: {date_str}
**Fase actual**: {phase}
"""


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def create_isa(name: str, template: str = "ISA-Lite.md",
               project_dir: str = ".", phase: str = "observe") -> Path:
    """Create ISA at {project}/.isa/ISA-<slug>.md with phase: frontmatter."""
    if phase not in VALID_PHASES:
        print(f"ERROR: Invalid phase '{phase}'. Must be one of: {', '.join(VALID_PHASES)}",
              file=sys.stderr)
        sys.exit(1)

    project = Path(project_dir).resolve()
    isa_dir = project / ".isa"

    # 1. Create .isa/ directory (honored contract path)
    isa_dir.mkdir(parents=True, exist_ok=True)

    # 2. Build filename
    slug = slugify(name)
    if not slug:
        print("ERROR: Task name produced an empty slug. Provide a non-empty ASCII name.",
              file=sys.stderr)
        sys.exit(1)
    filename = f"ISA-{slug}.md"
    filepath = isa_dir / filename

    # 3. Guard: do not overwrite
    if filepath.exists():
        print(f"WARNING: ISA already exists: {filepath}")
        print("Delete it manually if you want to recreate it.")
        return filepath

    # 4. Write ISA with phase: frontmatter (gap #1 fix)
    content = build_isa_content(name, slug, filename, phase)
    filepath.write_text(content, encoding="utf-8")

    print(f"ISA created:  {filepath}")
    print(f"Directory:    {isa_dir}")
    print(f"Phase:        {phase}")
    print(f"\nNext steps:")
    print(f"  1. Fill sections 1-6 (Problem → Goal)")
    print(f"  2. Write ISC criteria in section 7 (min 5, binary+testable)")
    print(f"  3. Update frontmatter `phase:` as you progress")
    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="nexus-discipline — Create ISA artifacts at .isa/ISA-<slug>.md",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python isa-create.py "API REST Tarefas"
  python isa-create.py "Migração DB" --project /path/to/project --phase think
  python isa-create.py "Landing Page Acme" --phase observe

Phase values (in order):
  observe → think → plan → build → execute → verify → learn → complete
""",
    )
    parser.add_argument("name", help="Task name (e.g. 'API REST Tarefas')")
    parser.add_argument(
        "--template", default="ISA-Lite.md",
        help="Template hint (informational; skeleton is always ISA-Full). Default: ISA-Lite.md"
    )
    parser.add_argument(
        "--project", default=".",
        help="Project root directory (default: current directory)"
    )
    parser.add_argument(
        "--phase", default="observe",
        choices=VALID_PHASES,
        help="Initial phase value for frontmatter (default: observe)"
    )
    args = parser.parse_args()

    create_isa(args.name, args.template, args.project, args.phase)


if __name__ == "__main__":
    main()
