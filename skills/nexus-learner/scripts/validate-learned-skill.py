#!/usr/bin/env python3
"""
validate-learned-skill.py <path.md> — verify mecânico pós-extracção (nexus-learner passo 5).

Checks (exit 1 em qualquer falha, com lista):
  1. frontmatter presente e parseável (key: value)
  2. naming rules: kebab-case, sem acentos, sem sufixo duplicado -expertise-expertise
  3. secções obrigatórias: Detector, Anti-pattern, Forma correcta, Evidência (≥3 de 4)
  4. secção Evidência não-vazia (≥1 bullet com conteúdo)
  5. trigger collision: triggers do novo vs skills existentes (aviso, não falha)
  6. secção "O que não funcionou" presente (erro; --legacy degrada para aviso —
     usar só ao re-validar skills anteriores a 2026-07-18)

Uso: validate-learned-skill.py [--legacy] [--skills-dir PASTA] <path.md>

Pastas consideradas no check de triggers: SKILLS_DIR (ou ~/.claude/skills por omissão),
cada --skills-dir dado, e a pasta `.claude/skills` ancestral do skill validado (skills de
projecto: <proj>/.claude/skills/learned/<slug>/SKILL.md).
"""
import os
import pathlib
import re
import sys
import unicodedata

# root por omissão (learned/ é subdir); rglob apanha SKILL.md em subdirectorias
DEFAULT_SKILLS_DIR = pathlib.Path(os.environ.get("SKILLS_DIR") or (pathlib.Path.home() / ".claude" / "skills"))


def ancestor_skills_dir(path):
    """Pasta `.claude/skills` que contém `path` (skills de projecto), ou None."""
    parts = path.resolve().parts
    for i in range(len(parts) - 1, 0, -1):
        if parts[i] == "skills" and parts[i - 1] == ".claude":
            return pathlib.Path(*parts[: i + 1])
    return None


def skills_dirs_for(path, extra=()):
    dirs = [DEFAULT_SKILLS_DIR, *map(pathlib.Path, extra)]
    anc = ancestor_skills_dir(path)
    if anc is not None:
        dirs.append(anc)
    seen, out = set(), []
    for d in dirs:
        k = d.resolve()
        if k not in seen:
            seen.add(k)
            out.append(d)
    return out
REQUIRED_SECTIONS = ["detector", "anti-pattern", "forma correcta", "evid"]


def parse_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---(?:\n|$)", text, re.S)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        km = re.match(r"^(\w[\w-]*):\s*(.*)$", line)
        if km:
            fm[km.group(1)] = km.group(2)
    return fm


def check(path_str, legacy=False, extra_dirs=()):
    errors, warnings = [], []
    path = pathlib.Path(path_str)
    if not path.is_file():
        return [f"ficheiro não existe: {path}"], []
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        return [f"ficheiro ilegível: {e}"], []

    # 1. frontmatter
    fm = parse_frontmatter(text)
    if fm is None:
        errors.append("frontmatter ausente ou malformado (bloco --- ... ---)")
        fm = {}

    # 2. naming
    slug = path.parent.name if path.name == "SKILL.md" else path.stem
    if slug != slug.lower() or " " in slug or "_" in slug:
        errors.append(f"slug não é kebab-case: {slug!r}")
    if unicodedata.normalize("NFKD", slug).encode("ascii", "ignore").decode() != slug:
        errors.append(f"slug tem acentos/não-ASCII: {slug!r}")
    if "-expertise-expertise" in re.sub(r"[_-]", "-", slug):
        errors.append(f"sufixo redundante -expertise-expertise: {slug!r}")

    # 3. secções (case-insensitive, headers ## ou ###)
    headers = [h.lower() for h in re.findall(r"^#{2,3}\s+(.+)$", text, re.M)]
    found = sum(1 for req in REQUIRED_SECTIONS if any(req in h for h in headers))
    if found < 3:
        errors.append(
            f"só {found}/4 secções obrigatórias (Detector/Anti-pattern/"
            f"Forma correcta/Evidência) — headers: {headers[:6]}"
        )
    # 3b. Detector é OBRIGATÓRIO por si (critério de promoção b: failure pattern nomeado
    # vive no Detector — 3/4 sem Detector contornava o gate; red-team 2026-07-18)
    if not any("detector" in h for h in headers):
        errors.append("secção Detector ausente (obrigatória — o failure pattern do gate (b) vive aqui)")

    def section_body(name_re):
        m = re.search(rf"^#{{2,3}}\s+[^\n]*{name_re}[^\n]*\n(.*?)(?=^#{{2,3}}\s|\Z)", text, re.M | re.S | re.I)
        return m.group(1) if m else None

    # 4. evidência não-vazia
    # header com [^\n]* — com re.S um .* atravessaria linhas e capturaria body vazio
    em = re.search(r"^#{2,3}\s+[^\n]*evid[^\n]*\n(.*?)(?=^#{2,3}\s|\Z)", text, re.M | re.S | re.I)
    if em:
        bullets = [l for l in em.group(1).splitlines() if re.match(r"^\s*[-*]\s+\S", l)]
        if not bullets:
            errors.append("secção Evidência sem bullets com conteúdo")
    elif found >= 3:
        errors.append("secção Evidência ausente")

    # 6. "O que não funcionou" — critério de promoção (c): >=1 beco sem saída COM CONTEÚDO
    # (header vazio contornava o gate — red-team 2026-07-18)
    nf_body = section_body(r"(?:não funcionou|nao funcionou|what didn't work)")
    if nf_body is None:
        msg = 'secção "O que não funcionou" ausente (critério de promoção c: >=1 beco sem saída)'
        (warnings if legacy else errors).append(msg)
    elif not [l for l in nf_body.splitlines() if re.match(r"^\s*[-*]\s+\S", l)]:
        msg = 'secção "O que não funcionou" sem bullets com conteúdo (beco sem saída tem de estar escrito)'
        (warnings if legacy else errors).append(msg)

    # 7. Evidência com marca de passing-check — critério de promoção (a): o check que provou
    # o caminho tem de estar citável (exit 0, PASS, repro, comando em backtick + resultado)
    ev_body = section_body(r"evid")
    if ev_body is not None:
        has_check = re.search(r"exit\s*=?\s*0|exit code 0|\bPASS\b|\bverde\b|\bgreen\b|\brepro\b|`[^`]{3,}`", ev_body, re.I)
        if not has_check:
            msg = "Evidência sem marca de passing-check (exit 0 / PASS / comando verbatim) — critério de promoção (a) não demonstrado"
            (warnings if legacy else errors).append(msg)

    # 5. trigger collision (aviso) — aceita inline [a, b] E block-list YAML (- a\n- b);
    # o regex só-inline saltava o check em silêncio no formato natural (red-team 2026-07-18)
    triggers = []
    trig_m = re.search(r'"?triggers"?:\s*\[(.*?)\]', text, re.S)
    if trig_m:
        triggers = [t.strip(' "\'') for t in trig_m.group(1).split(",") if t.strip(' "\'')]
    else:
        blk = re.search(r"^triggers:\s*\n((?:\s+-\s+.+\n)+)", text, re.M)
        if blk:
            triggers = [re.sub(r"^\s*-\s*", "", l).strip(' "\'') for l in blk.group(1).splitlines() if l.strip()]
    if triggers:
        for trig in triggers[:10]:
            if len(trig) < 4:
                warnings.append(f"trigger demasiado genérico: {trig!r}")
                continue
            for d in skills_dirs_for(path, extra_dirs):
                if not d.is_dir():
                    continue
                for other in d.rglob("*.md"):
                    if other.resolve() == path.resolve():
                        continue
                    try:
                        if trig.lower() in other.read_text(encoding="utf-8").lower():
                            warnings.append(f"trigger {trig!r} também em {other.name}")
                            break
                    except (OSError, UnicodeDecodeError):
                        continue
                else:
                    continue
                break
    return errors, warnings


def main():
    args = sys.argv[1:]
    legacy = "--legacy" in args
    args = [a for a in args if a != "--legacy"]
    extra = []
    while "--skills-dir" in args:
        i = args.index("--skills-dir")
        if i + 1 >= len(args):
            print(__doc__)
            return 2
        extra.append(args[i + 1])
        del args[i : i + 2]
    if len(args) != 1:
        print(__doc__)
        return 2
    errors, warnings = check(args[0], legacy=legacy, extra_dirs=extra)
    for w in warnings[:8]:
        print(f"⚠️  {w}")
    if errors:
        for e in errors:
            print(f"❌ {e}")
        print(f"\nFAIL — {len(errors)} erro(s)")
        return 1
    print("✅ PASS — skill mecanicamente válido" + (f" ({len(warnings)} avisos)" if warnings else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
