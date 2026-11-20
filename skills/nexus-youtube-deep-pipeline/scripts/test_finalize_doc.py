#!/usr/bin/env python3
"""Self-check for finalize_doc.py and generate_deep_doc._extract_document.
Run: python3 test_finalize_doc.py   (prints OK, exits 1 on failure)"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import generate_deep_doc as g

BODY = "# Title — Knowledge Document\n\n## Sumário\n\nPrimeira frase do sumário. Segunda.\n\n## Citações Relevantes\n\n> \"hello world again\"\n"
FM = '---\ntitle: Windows: Oito ferramentas\ntema_principal: Um tema: com dois pontos\ntags:\n  - a\n  - b\n---\n\n'


def finalize(draft, meta, fc="pass"):
    d = tempfile.mkdtemp()
    dp, op = os.path.join(d, "d.md"), os.path.join(d, "o.md")
    open(dp, "w", encoding="utf-8").write(draft)
    env = dict(os.environ, PYTHONUTF8="1")
    r = subprocess.run([sys.executable, os.path.join(HERE, "finalize_doc.py"), "--draft", dp, "--video-meta",
                        json.dumps(meta), "--fact-check", fc, "--output", op], capture_output=True, text=True, env=env)
    return r, (open(op, encoding="utf-8").read() if os.path.exists(op) else None)


META = {"url": "https://www.youtube.com/watch?v=ABCDEFGHIJK", "title": "My: Video", "channel": "Some Channel",
        "date": "20261001", "duration": "00:16:27"}

# 1. model frontmatter with an unquoted colon is replaced by valid, ordered frontmatter
r, out = finalize(FM + BODY, META)
assert r.returncode == 0, r.stderr
head = out.split("\n---\n")[0]
assert 'title: "My: Video"' in head and 'duration: "16:27"' in head and 'date: "2026-10-01"' in head
assert 'video_id: "ABCDEFGHIJK"' in head and 'channel: "[[People/Some-Channel]]"' in head
assert 'tema_principal: "Um tema: com dois pontos"' in head and "has_quotes: true" in head
assert "pipeline: nexus-youtube-deep-pipeline" in head and 'fact_check: "pass"' in head
# 2. no frontmatter at all: tema falls back to the first sentence of Sumário
r, out = finalize(BODY, META)
assert r.returncode == 0 and 'tema_principal: "Primeira frase do sumário."' in out
# 3. leftover wrapper fence in the body is a schema violation
r, out = finalize(FM + BODY + "\n```markdown\nx\n```\n", META)
assert r.returncode == 1 and out is None
# 4. extraction: preamble + fenced doc + closing offer
wrapped = "Não tenho ferramenta de escrita, aqui vai.\n\n```markdown\n" + FM + BODY + "```\n\nSe quiser, guardo.\n"
doc = g._extract_document(wrapped)
assert doc.startswith("---\n") and "de escrita" not in doc and "Se quiser" not in doc and "```" not in doc, doc
# 5. extraction: H1 then ```yaml frontmatter fence (closed right after FM) is left for _strip_wrapping_fence
v = "# T\n\n```yaml\n" + FM.strip() + "\n```\n\n" + BODY
out = g._strip_wrapping_fence(g._extract_document(v))
assert out.startswith("---\n") and "```" not in out, out
# 6. clean document is unchanged; a refusal is rejected
assert g._extract_document(FM + BODY) == FM + BODY
try:
    g._finish_completion("Não consegui gravar o ficheiro. " * 40, "stop")
    raise SystemExit("refusal was accepted")
except g.ProviderOutputError:
    pass
print("OK")
# 7. a real ```yaml code block that starts with a comment inside a clean document is NOT a wrapper
clean = FM + BODY + "\n```yaml\n# Cada entrada define:\nname: x\n```\n"
assert g._extract_document(clean) == clean, g._extract_document(clean)
print("OK 7")
