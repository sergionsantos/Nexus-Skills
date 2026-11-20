#!/usr/bin/env python3
"""
sweep-draft-skills.py — lista skills com `status: draft` e ha quantos dias estagnam.

Um skill draft que nunca disparou em semanas ou (mais comum) disparou mas ninguem
actualizou o status e uma folha desactualizada a mentir com autoridade — caso real:
session-resume ficou `draft` 15 dias com uso real confirmado (2026-07-18).

Uso: sweep-draft-skills.py [--days N] [--skills-dir PASTA]   (default: só drafts com >=7 dias;
SKILLS_DIR=pasta de skills, default ~/.claude/skills; para skills de projecto usa
--skills-dir <proj>/.claude/skills)
Accao por linha: promover (uso real houve) ou fundir/apagar (nunca disparou).
"""
import os
import pathlib
import re
import sys
import time

ROOT = pathlib.Path(os.environ.get("SKILLS_DIR") or (pathlib.Path.home() / ".claude" / "skills"))
if "--skills-dir" in sys.argv:
    try:
        ROOT = pathlib.Path(sys.argv[sys.argv.index("--skills-dir") + 1])
    except IndexError:
        sys.exit("usage: sweep-draft-skills.py [--days N] [--skills-dir PASTA]")
try:
    min_days = int(sys.argv[sys.argv.index("--days") + 1]) if "--days" in sys.argv else 7
except (IndexError, ValueError):
    sys.exit("usage: sweep-draft-skills.py [--days N] [--skills-dir PASTA]")

rows = []
for md in ROOT.rglob("*.md"):
    try:
        head = md.read_text(encoding="utf-8")[:2000]
    except (OSError, UnicodeDecodeError):
        continue
    if not re.search(r"^status:\s*draft", head, re.M):
        continue
    age = (time.time() - md.stat().st_mtime) / 86400
    if age >= min_days:
        rows.append((age, md.relative_to(ROOT)))

for age, rel in sorted(rows, reverse=True):
    print(f"{age:5.0f}d  {rel}")
print(f"\n{len(rows)} draft(s) estagnado(s) >= {min_days}d. Por skill: promover ou fundir/apagar.")
