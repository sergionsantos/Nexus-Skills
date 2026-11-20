#!/usr/bin/env python3
"""Self-check for fact_check.py. Includes negative controls: an invented quote
and an invented number MUST be reported, so a pass proves the check can fail.

Run:  python3 scripts/test_fact_check.py      Exit 0 = every assertion held.
"""
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).parent / "fact_check.py"
spec = importlib.util.spec_from_file_location("fc", SCRIPT)
fc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fc)

TRANSCRIPT = """[0:01] So seven of the nine did no better than the dummy.
[0:09] Finding eight details hidden in the context scored 93 percent when you had
[0:13] two hundred and fifty thousand tokens in and 76% at a million tokens.
[0:20] It took almost twice as long, and it was 5.5 not five.
[0:25] There are twenty five new things from the last 10 months that people missed.
[0:31] A skill isn't that standard operating procedure anymore, it's a list of corrections.
"""


def run(draft, transcript=TRANSCRIPT):
    return fc.check(draft, transcript)


def statuses(items):
    return [i["status"] for i in items]


def main():
    # 1. Verbatim quote passes whatever the case, punctuation or apostrophe.
    q, _ = run('"A SKILL ISNT that standard operating procedure anymore; it\'s a list of corrections."')
    assert statuses(q) == ["exact"], f"[1] {q}"
    print("ok 1  verbatim quote passes despite case/punctuation/apostrophes")

    # 2. NEGATIVE CONTROL: an invented quote is reported missing.
    q, _ = run('"Claude can now write every skill for you without any instructions at all."')
    assert statuses(q) == ["missing"], f"[2] {q}"
    print("ok 2  invented quote -> missing")

    # 3. One drifted word in a long quote is `near`, not missing and not exact.
    q, _ = run('"Finding eight details hidden in the context scored 93 percent when you had two hundred and fifteen thousand tokens"')
    assert statuses(q) == ["near"], f"[3] {q}"
    print("ok 3  one drifted word -> near")

    # 4. Ellipsis: fragments are checked independently, in either direction.
    q, _ = run('"So seven of the nine did no better ... it was 5.5 not five"')
    assert statuses(q) == ["exact"], f"[4a] {q}"
    q, _ = run('"So seven of the nine did no better ... and then the model rewrote everything itself"')
    assert statuses(q) == ["missing"], f"[4b] {q}"
    print("ok 4  ellipsis fragments checked independently (real+real passes, real+invented fails)")

    # 5. Bracketed editorial insertions and short scare quotes are ignored.
    q, _ = run('"Finding eight [detalhes] details hidden in the context scored 93 percent" e o "dummy file".')
    assert statuses(q) == ["exact"], f"[5] {q}"
    print("ok 5  [insertions] ignored; quotes under 4 words are not checked")

    # 6. Numbers are compared by value across notations.
    ok = ("A: 93% e 76%. B: 250k tokens. C: 250.000 tokens. D: 250 mil tokens. E: 1M tokens. "
          "F: 1 milhão. G: 5,5. H: 25 coisas. I: 10 meses.")
    _, n = run(ok)
    bad = [x for x in n if x["status"] == "unmatched"]
    assert not bad, f"[6] false alarms: {bad}"
    print(f"ok 6  93%/93 percent, 250k=250,000=250.000=250 mil, 1M=a million, 5,5=5.5, 25=twenty five ({len(n)} distinct)")

    # 7. NEGATIVE CONTROL: an invented figure is reported, and so is a wrong unit.
    _, n = run("Subiu 47% e custou $300 por mês, com 9000 tokens.")
    assert [x["status"] for x in n] == ["unmatched"] * 3, f"[7] {n}"
    _, n = run("Chegou a 76 mil tokens.")  # transcript has 76%, not 76 thousand
    assert statuses(n) == ["unmatched"], f"[7b] {n}"
    print("ok 7  invented 47%, $300, 9000 and 76-thousand-vs-76% all unmatched")

    # 8. Structure is not claims: frontmatter, headings, list numbers, timestamps,
    #    single digits, version strings and the bookkeeping sections are skipped.
    draft = """---
date: "2026-10-17"
duration: "00:19:15"
---
# Doc 2026
### 12. Concept
1. Primeiro passo (veja [3:41–4:56])
- 2. Segundo
Fala-se de 3 coisas e da versão 2.1.302.

## Estrutura por Capítulo
| 18:22 | 99 coisas |

## Metadados Internos
- Qualidade 87/100, 4321 palavras
"""
    q, n = run(draft)
    assert q == [] and n == [], f"[8] structural numbers leaked: {q} {n}"
    print("ok 8  frontmatter, headings, list numbering, timestamps, 1-digit, versions, bookkeeping sections skipped")

    # 9. A number inside a quote is judged by the quote, not counted twice.
    q, n = run('Disse: "scored 93 percent when you had two hundred and fifty thousand tokens in".')
    assert statuses(q) == ["exact"] and n == [], f"[9] {q} {n}"
    print("ok 9  numbers inside a checked quote are not double-counted")

    # 10. CLI: exit 0 when clean, 1 on a finding (listed with its draft line), 2 on bad input.
    with tempfile.TemporaryDirectory() as d:
        t = Path(d, "t.txt"); t.write_text(TRANSCRIPT)
        good = Path(d, "good.md"); good.write_text('---\nx: y\n---\n\n"So seven of the nine did no better than the dummy."\n')
        badf = Path(d, "bad.md"); badf.write_text('---\nx: y\n---\n\n"Nothing like this was ever said in the video at all."\nVale 47%.\n')
        rep = Path(d, "r.json")

        def cli(*a):
            return subprocess.run([sys.executable, str(SCRIPT), *a], capture_output=True, text=True)

        p = cli("--draft", str(good), "--cleaned-transcript", str(t), "--report", str(rep))
        assert p.returncode == 0 and "0 MISSING" in p.stdout and rep.exists(), f"[10a] {p.returncode}\n{p.stdout}{p.stderr}"
        p = cli("--draft", str(badf), "--cleaned-transcript", str(t))
        assert p.returncode == 1, f"[10b] {p.returncode}"
        assert "MISSING quote (draft line 5)" in p.stdout and "UNMATCHED number '47%' (draft line 6)" in p.stdout, \
            f"[10b] findings not listed with their draft line:\n{p.stdout}"
        assert cli("--draft", str(d) + "/nope.md", "--cleaned-transcript", str(t)).returncode == 2, "[10c]"
        empty = Path(d, "e.txt"); empty.write_text("  \n")
        assert cli("--draft", str(good), "--cleaned-transcript", str(empty)).returncode == 2, "[10d]"
    print("ok 10 CLI exit codes 0/1/2, findings reported with draft line numbers, JSON report written")

    print("\nALL OK")


if __name__ == "__main__":
    main()
