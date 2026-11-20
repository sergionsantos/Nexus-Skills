#!/usr/bin/env python3
"""Self-check for generate_deep_doc.py: retry/fallback, background default,
wrapper-fence stripping, status file, and the bundled poller.

Run:  python3 scripts/test_generate_deep_doc.py
Exit 0 = all assertions held. Includes the negative controls (forced 429
cascade, budget exhaustion, 401 not retried), so a passing run proves the
check can fail.

ponytail: stdlib http.server stub + asserts. No pytest, no mocks library.
The stub dispatches on the "model" field of the request body, because both
stub links share one base URL.

The script's own PROVIDERS is claude-only (no HTTP link configured). The
retry/fallback machinery is still exercised: build_sandbox()
copies the script (and its templates) into the temp dir with two stub HTTP links
(stub-a, stub-b) in front of the real claude link. Test 34 runs the UNPATCHED
script and proves the real chain is claude-sonnet alone.
"""
import importlib.util
import json
import os
import signal
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REAL_SCRIPT = Path(__file__).parent / "generate_deep_doc.py"
SCRIPT = REAL_SCRIPT  # main() repoints this at the sandbox copy (stub HTTP links)
WAITER = Path(__file__).parent / "wait_for_status.sh"

# By default the claude link points at a binary that does not exist, so no test
# can reach a real, billed `claude`. Tests 29-33 override it with a fake.
MISSING_CLAUDE = "/nonexistent/claude"

M3 = "stub-a"
M27 = "stub-b"

# Two stub HTTP links injected in front of the real claude link: one base URL,
# one key, dispatch on the model id. Source text, not data: base_url must be
# read from STUB_BASE_URL when the sandbox script is imported/run, not here.
STUB_LINKS_SRC = """
PROVIDERS[:0] = [
    {"name": _n, "key_envs": ("STUB_API_KEY",),
     "base_url": os.environ.get("STUB_BASE_URL", ""),
     "model": _n, "temperature": 1, "extra_headers": {}}
    for _n in ("stub-a", "stub-b")
]
"""


def build_sandbox(tmp):
    """Copy generate_deep_doc.py + templates under tmp with the stub links
    prepended to PROVIDERS. Returns the sandbox script path."""
    box = tmp / "sandbox"
    (box / "scripts").mkdir(parents=True, exist_ok=True)
    (box / "templates").mkdir(exist_ok=True)
    for t in (REAL_SCRIPT.parent.parent / "templates").iterdir():
        if t.is_file():
            (box / "templates" / t.name).write_bytes(t.read_bytes())
    src = REAL_SCRIPT.read_text(encoding="utf-8")
    marker = "\n\ndef load_template("
    assert src.count(marker) == 1, "build_sandbox: load_template anchor moved"
    out = box / "scripts" / "generate_deep_doc.py"
    out.write_text(src.replace(marker, "\n" + STUB_LINKS_SRC + marker, 1), encoding="utf-8")
    return out

# model -> list of responses, consumed in order; the last one repeats.
# Each response: int status | "slow" | (status, retry_after_header_value)
RESPONSES = {}
HITS = []


class _Stub(BaseHTTPRequestHandler):
    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        model = json.loads(raw).get("model", "?")
        HITS.append(model)
        seq = RESPONSES.get(model) or [500]
        spec = seq.pop(0) if len(seq) > 1 else seq[0]

        if spec == "slow":  # never answers within the test's lifetime
            time.sleep(300)
            return
        retry_after = None
        # Long enough and varied enough to be a plausible document: the
        # detector now rejects near-empty and self-repeating completions.
        content = f"# doc from {model}\n\n## Sumário\n\nResumo de teste.\n\n" + "\n".join(
            f"Linha {i} de conteudo generico do documento de teste." for i in range(20)) + "\n"
        finish_reason = "stop"
        if isinstance(spec, tuple):
            spec, retry_after = spec
        elif isinstance(spec, dict):  # full control over the 200 body
            content = spec.get("content", content)
            finish_reason = spec.get("finish_reason", "stop")
            spec = spec.get("code", 200)

        if spec == 200:
            body = json.dumps({"choices": [{
                "message": {"content": content},
                "finish_reason": finish_reason}]}).encode()
        else:
            body = json.dumps({"error": {
                "message": "Token Plan usage limit reached"}}).encode()
        self.send_response(spec)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if retry_after is not None:
            self.send_header("Retry-After", str(retry_after))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def start_stub():
    # Threading: the "slow" response holds a request open for the whole run.
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Stub)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def run_script(tmp, port, keys, extra=(), env_extra=None, timeout=120):
    """Run the sandbox generate_deep_doc.py with the stub standing in for an HTTP vendor."""
    env = dict(os.environ)
    env.update({
        "STUB_BASE_URL": f"http://127.0.0.1:{port}",
        "STUB_API_KEY": "",
        "YTDEEP_CLAUDE_BIN": MISSING_CLAUDE,
        # Small budget so the retry paths are testable in seconds, not minutes.
        "LLM_MAX_RETRY_SECS": "3", "LLM_RETRY_BASE_SECS": "1", "LLM_RETRY_MAX_SLEEP": "2",
    })
    env.update(keys)
    env.update(env_extra or {})
    out = tmp / "draft.md"
    extra = list(extra)
    if "--model" not in extra:
        # The script's default is claude-sonnet; put the stub links first so the
        # HTTP retry/fallback paths stay under test.
        extra += ["--model", M3]
    cmd = [sys.executable, str(SCRIPT),
           "--cleaned-transcript", str(tmp / "t.txt"),
           "--video-meta", '{"title": "T", "url": "U"}',
           "--output", str(out), *extra]
    p = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=timeout)
    return p, out


def main():
    tmp = Path(os.environ.get("TMPDIR", "/tmp")) / f"ytdeep-selftest-{os.getpid()}"
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "t.txt").write_text("\n".join(f"sentence {i}" for i in range(40)))
    global SCRIPT
    SCRIPT = build_sandbox(tmp)
    srv, port = start_stub()
    keyed = {"STUB_API_KEY": "k1"}

    # 1. NEGATIVE CONTROL: m3 429 -> the next MODEL answers, in the same round,
    #    with no waiting (a model-specific failure must not cost a backoff).
    RESPONSES.clear(); HITS.clear()
    RESPONSES.update({M3: [429], M27: [200]})
    t0 = time.time()
    p, out = run_script(tmp, port, keyed, extra=["--foreground"])
    elapsed = time.time() - t0
    assert p.returncode == 0, f"[1] expected exit 0, got {p.returncode}\n{p.stderr}"
    assert HITS == [M3, M27], f"[1] expected m3 then m2.7, hit {HITS}"
    assert "FAIL provider=stub-a: HTTP 429" in p.stderr, f"[1] no 429 log line:\n{p.stderr}"
    assert "next=stub-b" in p.stderr, f"[1] next link not named:\n{p.stderr}"
    # "no RETRY line" is the deterministic form of "it did not wait". A wall
    # clock bound here would fire on a loaded machine and blame the wrong thing.
    assert "RETRY" not in p.stderr, f"[1] should not have waited before falling over:\n{p.stderr}"
    assert f"from {M27}" in out.read_text(), "[1] output not written by the second link"
    print(f"ok 1  429 on stub-a falls to stub-b in the same round, no backoff paid ({elapsed:.1f}s)")

    # 2. NEGATIVE CONTROL: every link 429 forever -> retries, then gives up at
    #    the budget with an aggregated error. (Budget = 3s via run_script env.)
    RESPONSES.clear(); HITS.clear()
    RESPONSES.update({M3: [429], M27: [429]})
    out.unlink(missing_ok=True)
    p, out = run_script(tmp, port, keyed, extra=["--foreground"])
    assert p.returncode == 2, f"[2] expected exit 2, got {p.returncode}\n{p.stderr}"
    assert len(HITS) > 2, f"[2] gave up without retrying a single round: {HITS}"
    assert "RETRY round 2" in p.stderr, f"[2] no retry log line:\n{p.stderr}"
    assert "GIVE UP" in p.stderr, f"[2] no give-up line:\n{p.stderr}"
    assert "all LLM providers failed after" in p.stderr, f"[2] no aggregated error:\n{p.stderr}"
    assert not out.exists(), "[2] output file must not be written on total failure"
    status = json.loads((tmp / "draft.md.status.json").read_text())
    assert status["state"] == "error", f"[2] status not error: {status}"
    print(f"ok 2  persistent 429 retries then gives up at the budget ({len(HITS)} calls, exit 2)")

    # 3. No API key: both links skip, and skipping is NOT transient — it must
    #    fail immediately rather than burn the retry budget on a missing key.
    RESPONSES.clear(); HITS.clear()
    RESPONSES.update({M3: [200], M27: [200]})
    t0 = time.time()
    p, out = run_script(tmp, port, {"STUB_API_KEY": ""}, extra=["--foreground"])
    assert p.returncode == 2, f"[3] expected exit 2, got {p.returncode}\n{p.stderr}"
    assert HITS == [], f"[3] should not have called anything: {HITS}"
    assert "SKIP provider=stub-a: no API key" in p.stderr, f"[3] no skip line:\n{p.stderr}"
    assert "RETRY" not in p.stderr, f"[3] retried a missing key:\n{p.stderr}"
    print(f"ok 3  missing key skips both links and fails fast, no retry ({time.time() - t0:.1f}s)")

    # 4. Background is the DEFAULT: parent returns fast, child finishes later.
    RESPONSES.clear(); HITS.clear()
    RESPONSES.update({M3: [200]})
    out.unlink(missing_ok=True)
    (tmp / "draft.md.status.json").unlink(missing_ok=True)
    t0 = time.time()
    p, out = run_script(tmp, port, keyed)  # no --foreground
    elapsed = time.time() - t0
    assert p.returncode == 0, f"[4] expected exit 0, got {p.returncode}\n{p.stderr}"
    assert elapsed < 10, f"[4] parent blocked {elapsed:.1f}s — not detached"
    assert "Started in background" in p.stdout, f"[4] no bg banner:\n{p.stdout}"
    status_file = tmp / "draft.md.status.json"
    for _ in range(100):
        st = json.loads(status_file.read_text())
        if st["state"] in ("done", "error"):
            break
        time.sleep(0.2)
    assert st["state"] == "done", f"[4] background run did not finish clean: {st}"
    assert out.read_text().startswith(f"# doc from {M3}"), "[4] bg child wrote no output"
    assert st["bytes"] == out.stat().st_size, f"[4] status bytes mismatch: {st}"
    print(f"ok 4  background default: parent returned in {elapsed:.2f}s, child state=done")

    # 5. --model moves its link to the FRONT and the rest still follows.
    RESPONSES.clear(); HITS.clear()
    RESPONSES.update({M27: [429], M3: [200]})
    out.unlink(missing_ok=True)
    p, out = run_script(tmp, port, keyed, extra=["--foreground", "--model", "stub-b"])
    assert p.returncode == 0, f"[5] expected exit 0, got {p.returncode}\n{p.stderr}"
    assert HITS == [M27, M3], f"[5] expected m2.7 first then m3, hit {HITS}"
    assert f"from {M3}" in out.read_text(), "[5] wrong link produced the doc"
    print("ok 5  --model stub-b puts it first, round continues into stub-a")

    # 6. Wrapper-fence stripping, incl. the ```markdown whole-document wrap that
    #    a real reasoning-model run emitted (even fence count disarmed the old guard).
    spec = importlib.util.spec_from_file_location("gdd", SCRIPT)
    gdd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gdd)
    strip = gdd._strip_wrapping_fence
    fm = "---\ntitle: T\n---\n"
    cases = [
        ("markdown wrap closed at EOF", "```markdown\n" + fm + "# H1\nbody\n```\n", False),
        ("md wrap closed at EOF", "```md\n" + fm + "# H1\nbody\n```\n", False),
        ("yaml wrap closed after frontmatter", "```yaml\n" + fm + "```\n# H1\nbody\n", False),
        ("yaml wrap never closed", "```yaml\n" + fm + "# H1\nbody\n", False),
        ("markdown wrap around a real code block",
         "```markdown\n" + fm + "# H1\n```python\nx = 1\n```\nafter\n```\n", True),
    ]
    for label, raw, keeps_inner in cases:
        got = strip(raw)
        assert not got.lstrip().startswith("```"), f"[6] {label}: opening fence survived:\n{got!r}"
        assert got.rstrip().splitlines()[-1].strip() != "```", \
            f"[6] {label}: trailing wrapper fence survived:\n{got!r}"
        assert "title: T" in got, f"[6] {label}: frontmatter lost:\n{got!r}"
        if keeps_inner:
            assert "```python" in got and "x = 1" in got, f"[6] {label}: ate the real code block:\n{got!r}"
    # Must NOT touch a clean doc whose last line is a legit code fence.
    clean = fm + "# H1\n```python\nx = 1\n```\n"
    assert strip(clean) == clean, f"[6] mangled a clean doc:\n{strip(clean)!r}"
    print(f"ok 6  wrapper fences stripped ({len(cases)} variants), clean doc untouched")

    # 7. A SIGKILLed worker must not hang the documented poll for ever.
    RESPONSES.clear(); HITS.clear()
    RESPONSES.update({M3: ["slow"]})
    out.unlink(missing_ok=True)
    status_file.unlink(missing_ok=True)
    p, out = run_script(tmp, port, keyed)  # background
    assert p.returncode == 0, f"[7] spawn failed: {p.stderr}"
    for _ in range(100):
        st = json.loads(status_file.read_text())
        if st.get("state") == "running":
            break
        time.sleep(0.1)
    assert st["state"] == "running", f"[7] worker never reached running: {st}"
    os.kill(st["pid"], signal.SIGKILL)
    time.sleep(0.5)
    t0 = time.time()
    w = subprocess.run([str(WAITER), str(status_file), "10", "1"],
                       capture_output=True, text=True, timeout=60)
    assert w.returncode == 2, f"[7] waiter should report a dead worker (2), got {w.returncode}: {w.stderr}"
    assert time.time() - t0 < 15, "[7] waiter did not bail out promptly"
    assert json.loads(status_file.read_text())["state"] == "running", \
        "[7] precondition lost: status should still be frozen at running"
    print("ok 7  SIGKILLed worker -> wait_for_status.sh exits 2 instead of looping for ever")

    # 8. --output into a missing dir must not kill the parent before any status
    #    exists (that left the poll with no file to read).
    RESPONSES.clear(); HITS.clear()
    RESPONSES.update({M3: [200]})
    deep = tmp / "missing-a" / "missing-b"
    p2 = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--cleaned-transcript", str(tmp / "t.txt"),
         "--video-meta", '{"title": "T"}',
         "--output", str(deep / "draft.md"), "--model", M3],
        capture_output=True, text=True, timeout=60,
        env={**os.environ, "STUB_BASE_URL": f"http://127.0.0.1:{port}",
             "STUB_API_KEY": "k1", "YTDEEP_CLAUDE_BIN": MISSING_CLAUDE})
    assert p2.returncode == 0, f"[8] expected exit 0, got {p2.returncode}\n{p2.stderr}"
    w = subprocess.run([str(WAITER), str(deep / "draft.md.status.json"), "60", "1"],
                       capture_output=True, text=True, timeout=120)
    assert w.returncode == 0, f"[8] waiter did not see done: rc={w.returncode} {w.stdout}{w.stderr}"
    assert (deep / "draft.md").exists(), "[8] output not written into the created dir"
    print("ok 8  missing output dir is created, run completes, waiter exits 0")

    # 9. Concurrent readers never observe a torn status file.
    stop = threading.Event()
    bad = []

    def reader():
        while not stop.is_set():
            try:
                json.loads(status_file.read_text())
            except FileNotFoundError:
                pass
            except ValueError as e:
                bad.append(str(e))

    th = [threading.Thread(target=reader, daemon=True) for _ in range(4)]
    [t.start() for t in th]
    for i in range(300):
        gdd._write_status(str(status_file), state="running", pid=os.getpid(), n=i)
    stop.set()
    [t.join(timeout=5) for t in th]
    assert not bad, f"[9] torn reads observed: {bad[:3]}"
    # These writes claim state=running with THIS process's pid. Leave that
    # behind and the one-run-per-output lock will (correctly) refuse every
    # later run on this --output.
    status_file.unlink(missing_ok=True)
    print("ok 9  300 status writes under 4 concurrent readers, zero torn reads")

    # 10. A bad numeric argument must never be able to produce exit 0.
    (tmp / "st-running.json").write_text(json.dumps({"state": "running", "pid": os.getpid()}))
    # NB: an empty argument is NOT in this list — "${2:-90}" substitutes the
    # default for empty as well as unset, so "" is a valid "use the default",
    # not a bad argument. The '' arm of the guard only covers direct sourcing.
    for args_ in (["abc", "20"], ["90", "abc"], ["-5", "20"], ["9 0", "20"], ["9.5", "20"]):
        w = subprocess.run([str(WAITER), str(tmp / "st-running.json"), *args_],
                           capture_output=True, text=True, timeout=30)
        assert w.returncode == 3, f"[10] args {args_}: expected exit 3, got {w.returncode}"
        # Assert the REASON, not just the code: the counting loop also exits 3
        # on a bad argument (via a shell arithmetic error), so exit 3 alone no
        # longer distinguishes "rejected the argument" from "fell through".
        assert "must be a non-negative integer" in w.stderr, \
            f"[10] args {args_}: rejected without saying why:\n{w.stderr}"
    print("ok 10 non-numeric max_polls/interval -> exit 3 with a stated reason")

    # 11. The pid must be in the status from the "starting" write on, otherwise
    #     a child that dies during interpreter startup is invisible.
    dead = subprocess.Popen([sys.executable, "-c", "pass"])
    dead.wait()
    (tmp / "st-starting.json").write_text(
        json.dumps({"state": "starting", "pid": dead.pid, "output": "x", "log": "y"}))
    w = subprocess.run([str(WAITER), str(tmp / "st-starting.json"), "5", "1"],
                       capture_output=True, text=True, timeout=30)
    assert w.returncode == 2, f"[11] dead worker in 'starting' should be 2, got {w.returncode}"
    RESPONSES.clear(); HITS.clear()
    RESPONSES.update({M3: ["slow"]})
    out.unlink(missing_ok=True); status_file.unlink(missing_ok=True)
    p, out = run_script(tmp, port, keyed)  # background
    st = json.loads(status_file.read_text())
    assert "pid" in st, f"[11] status has no pid right after the parent returned: {st}"
    os.kill(st["pid"], signal.SIGKILL)
    print("ok 11 'starting' status carries the pid -> death before 'running' is detectable")

    # 12. --status-file in a missing dir must not kill the parent either.
    RESPONSES.clear(); HITS.clear()
    RESPONSES.update({M3: [200]})
    sf = tmp / "sf-missing" / "st.json"
    p2 = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--cleaned-transcript", str(tmp / "t.txt"), "--video-meta", '{"title": "T"}',
         "--output", str(tmp / "draft12.md"), "--status-file", str(sf), "--model", M3],
        capture_output=True, text=True, timeout=60,
        env={**os.environ, "STUB_BASE_URL": f"http://127.0.0.1:{port}",
             "STUB_API_KEY": "k1", "YTDEEP_CLAUDE_BIN": MISSING_CLAUDE})
    assert p2.returncode == 0, f"[12] expected exit 0, got {p2.returncode}\n{p2.stderr}"
    assert sf.exists(), "[12] status file not created in the missing dir"
    w = subprocess.run([str(WAITER), str(sf), "60", "1"], capture_output=True, text=True, timeout=120)
    assert w.returncode == 0, f"[12] waiter rc={w.returncode}: {w.stdout}{w.stderr}"
    print("ok 12 --status-file in a missing dir is created, run completes, waiter exits 0")

    # 13. The anti-race re-read. The worker can write `done` and exit in the
    #     ~20ms between the waiter's snapshot and its `kill -0`; without the
    #     re-read that finished run is reported as death (exit 2). Sequenced
    #     deterministically by stubbing `cat` (the waiter's only way of reading
    #     the file): 1st read -> running + dead pid, 2nd -> done.
    stub = tmp / "stub-bin"
    stub.mkdir(exist_ok=True)
    (stub / "n").unlink(missing_ok=True)
    (stub / "cat").write_text(
        "#!/bin/sh\n"
        f'c="{stub}/n"\n'
        "n=0; [ -f \"$c\" ] && read n < \"$c\"\n"
        "n=$((n+1)); echo \"$n\" > \"$c\"\n"
        f'if [ "$n" -eq 1 ]; then echo \'{{"state": "running", "pid": {dead.pid}}}\'\n'
        f'else echo \'{{"state": "done", "pid": {dead.pid}, "bytes": 7}}\'; fi\n')
    (stub / "cat").chmod(0o755)
    w = subprocess.run([str(WAITER), str(tmp / "st-running.json"), "3", "1"],
                       capture_output=True, text=True, timeout=30,
                       env={**os.environ, "PATH": f"{stub}:{os.environ['PATH']}"})
    assert (stub / "n").read_text().strip() == "2", \
        f"[13] expected exactly 2 reads (snapshot + re-read), got {(stub / 'n').read_text().strip()}"
    assert w.returncode == 0, \
        f"[13] worker that finished in the race window must be 'done', got {w.returncode}: {w.stderr}"
    print("ok 13 worker finishing inside the snapshot->kill -0 window reads as done, not death")

    # 14. An unclosed fence inside a wrapped body makes the count even again;
    #     the wrapper's trailing fence must still go.
    unclosed = "```markdown\n" + fm + "# H1\n```python\nx = 1\nafter\n```\n"
    got = strip(unclosed)
    assert not got.lstrip().startswith("```markdown"), f"[14] opener survived:\n{got!r}"
    assert got.rstrip().splitlines()[-1].strip() != "```", \
        f"[14] wrapper fence survived an unclosed inner block:\n{got!r}"
    assert "```python" in got and "x = 1" in got, f"[14] ate the inner block:\n{got!r}"
    print("ok 14 unclosed inner fence no longer strands the wrapper's closing fence")

    # 15. Two runs sharing one --output must not raise inside _write_status.
    errs = []

    def writer():
        try:
            for i in range(200):
                gdd._write_status(str(status_file), state="running", pid=os.getpid(), n=i)
        except Exception as e:
            errs.append(f"{type(e).__name__}: {e}")

    ws = [threading.Thread(target=writer) for _ in range(3)]
    [t.start() for t in ws]
    [t.join(timeout=30) for t in ws]
    assert not errs, f"[15] concurrent status writers raised: {errs[:3]}"
    leftovers = [q.name for q in status_file.parent.glob(status_file.name + ".*") if q.name.endswith(".tmp")]
    assert not leftovers, f"[15] temp files left behind: {leftovers[:3]}"
    status_file.unlink(missing_ok=True)  # same reason as [9]
    print("ok 15 3 concurrent writers on one status file: no exception, no temp left behind")

    # 16. Retry-After is obeyed: the server's number sets the wait, not backoff.
    #     Budget 30s here so a 2s wait fits; base backoff 1s so that if the
    #     header were ignored the wait would be visibly shorter.
    RESPONSES.clear(); HITS.clear()
    RESPONSES.update({M3: [(429, "2"), 200], M27: [429]})
    out.unlink(missing_ok=True)
    t0 = time.time()
    p, out = run_script(tmp, port, keyed, extra=["--foreground"],
                        env_extra={"LLM_MAX_RETRY_SECS": "30", "LLM_RETRY_BASE_SECS": "1"})
    waited = time.time() - t0
    assert p.returncode == 0, f"[16] expected exit 0, got {p.returncode}\n{p.stderr}"
    assert "RETRY round 2 in 2s (Retry-After)" in p.stderr, \
        f"[16] Retry-After not honoured (backoff would say 1s):\n{p.stderr}"
    # Assert the shape, not the wall clock: elapsed here also carries whatever
    # the rest of the suite left running, so it is only a floor.
    assert len([l for l in p.stderr.splitlines() if "RETRY" in l]) == 1, \
        f"[16] expected exactly one retry round:\n{p.stderr}"
    assert HITS == [M3, M27, M3], f"[16] expected one full round then a retry of m3, hit {HITS}"
    assert waited >= 2, f"[16] returned in {waited:.2f}s — it did not actually sleep"
    assert f"from {M3}" in out.read_text(), "[16] retry did not land on the first link"
    print(f"ok 16 Retry-After: 2 honoured over the 1s backoff (slept {waited:.1f}s), then succeeded")

    # 17. NEGATIVE CONTROL: 401 is not transient. Retrying a bad key only burns
    #     the budget, so it must fail after exactly one round.
    RESPONSES.clear(); HITS.clear()
    RESPONSES.update({M3: [401], M27: [401]})
    out.unlink(missing_ok=True)
    t0 = time.time()
    p, out = run_script(tmp, port, keyed, extra=["--foreground"],
                        env_extra={"LLM_MAX_RETRY_SECS": "30", "LLM_RETRY_BASE_SECS": "1"})
    fast = time.time() - t0
    assert p.returncode == 2, f"[17] expected exit 2, got {p.returncode}\n{p.stderr}"
    assert HITS == [M3, M27], f"[17] 401 was retried: {HITS}"
    assert "RETRY" not in p.stderr, f"[17] retried a 401:\n{p.stderr}"
    print(f"ok 17 401 fails after one round, never retried ({fast:.1f}s)")

    # 18. 5xx without a Retry-After header falls back to exponential backoff.
    RESPONSES.clear(); HITS.clear()
    RESPONSES.update({M3: [503, 503, 200], M27: [503]})
    out.unlink(missing_ok=True)
    p, out = run_script(tmp, port, keyed, extra=["--foreground"],
                        env_extra={"LLM_MAX_RETRY_SECS": "30", "LLM_RETRY_BASE_SECS": "1"})
    assert p.returncode == 0, f"[18] expected exit 0, got {p.returncode}\n{p.stderr}"
    assert "RETRY round 2 in 1s (backoff)" in p.stderr, f"[18] no backoff line:\n{p.stderr}"
    assert "RETRY round 3 in 2s (backoff)" in p.stderr, f"[18] backoff did not double:\n{p.stderr}"
    print("ok 18 5xx with no Retry-After backs off exponentially (1s, 2s) and recovers")

    # 19. A 200 OK carrying a truncated completion is a PROVIDER FAILURE, not a
    #     document. Real damage this prevents: a run on 2026-08-10 wrote a doc
    #     that stopped at 7 of 13 sections and every downstream check passed it.
    RESPONSES.clear(); HITS.clear()
    RESPONSES.update({M3: [{"code": 200, "content": "# half a doc\n", "finish_reason": "length"}],
                      M27: [200]})
    out.unlink(missing_ok=True)
    p, out = run_script(tmp, port, keyed, extra=["--foreground"])
    assert p.returncode == 0, f"[19] expected exit 0, got {p.returncode}\n{p.stderr}"
    assert HITS == [M3, M27], f"[19] truncation did not fall to the next link: {HITS}"
    assert "finish_reason='length'" in p.stderr, f"[19] finish_reason not reported:\n{p.stderr}"
    assert f"from {M27}" in out.read_text(), "[19] truncated content was written to the doc"
    print("ok 19 finish_reason != stop is a provider failure -> next link, not a document")

    # 20. Same for a repeat loop, the other half of the real failure: the doc's
    #     last line was 20342 chars of one ideograph and nothing noticed.
    RESPONSES.clear(); HITS.clear()
    loop_line = "  *Contexto:*" + ("底" * 20328)
    RESPONSES.update({M3: [{"code": 200, "content": f"---\ntitle: T\n---\n# H1\n{loop_line}\n"}],
                      M27: [200]})
    out.unlink(missing_ok=True)
    p, out = run_script(tmp, port, keyed, extra=["--foreground"])
    assert p.returncode == 0, f"[20] expected exit 0, got {p.returncode}\n{p.stderr}"
    assert HITS == [M3, M27], f"[20] degenerate output did not fall to the next link: {HITS}"
    assert "repeat loop on line" in p.stderr, f"[20] loop not reported:\n{p.stderr}"
    assert "底" not in out.read_text(), "[20] degenerate content reached the doc"
    print("ok 20 repeat loop -> next link")

    # 21. One run per --output. A second run must refuse rather than overwrite
    #     the first one's status slot (a poller on run A would otherwise get run
    #     B's "done", while A rewrites the output afterwards).
    RESPONSES.clear(); HITS.clear()
    RESPONSES.update({M3: ["slow"]})
    out.unlink(missing_ok=True); status_file.unlink(missing_ok=True)
    p, out = run_script(tmp, port, keyed)  # A: background, will hang on the stub
    assert p.returncode == 0, f"[21] first run failed to start: {p.stderr}"
    first = json.loads(status_file.read_text())
    p2, _ = run_script(tmp, port, keyed)   # B: same --output
    assert p2.returncode == 3, f"[21] second run should refuse with 3, got {p2.returncode}\n{p2.stderr}"
    assert "another run" in p2.stderr, f"[21] no explanation given:\n{p2.stderr}"
    still = json.loads(status_file.read_text())
    assert still.get("pid") == first.get("pid"), \
        f"[21] second run overwrote the first run's status: {first} -> {still}"
    os.kill(first["pid"], signal.SIGKILL)
    # A finished/failed run in the slot must NOT block a re-run.
    gdd._write_status(str(status_file), state="error", pid=first["pid"], error="x")
    RESPONSES.clear(); RESPONSES.update({M3: [200]})
    p3, _ = run_script(tmp, port, keyed)
    assert p3.returncode == 0, f"[21] a finished run must not block a re-run: {p3.stderr}"
    # Wait for it: this one is in the background, and leaving it running would
    # make the lock (correctly) refuse every later test on this --output.
    w = subprocess.run([str(WAITER), str(status_file), "60", "1"],
                       capture_output=True, text=True, timeout=120)
    assert w.returncode == 0, f"[21] re-run did not finish: rc={w.returncode} {w.stdout}{w.stderr}"
    print("ok 21 second run on a live --output refuses (exit 3); a finished one does not block")

    # 22. The parent must not push a state the child already advanced back to
    #     "starting" — a poller would read a finished run as dead.
    guard = tmp / "guard.json"
    for state, expect_pid in (("starting", 4242), ("running", 111), ("done", 111)):
        gdd._write_status(str(guard), state=state, pid=111, output="o", log="l")
        gdd._adopt_child_pid(str(guard), 4242, "o", "l")
        after = json.loads(guard.read_text())
        assert after["pid"] == expect_pid, \
            f"[22] state={state}: expected pid {expect_pid}, got {after}"
        assert after["state"] == state, f"[22] state={state} was changed to {after['state']}"
    print("ok 22 child pid adopted only while 'starting', never over a newer state")

    # 23. A failed status write must not leave its temp file behind.
    orphan_dir = tmp / "orphan"
    orphan_dir.mkdir(exist_ok=True)
    st = orphan_dir / "st.json"
    try:
        gdd._write_status(str(st), state="running", bad=object())  # not serialisable
        raise AssertionError("[23] expected _write_status to raise on a bad field")
    except TypeError:
        pass
    left = [f.name for f in orphan_dir.iterdir()]
    assert left == [], f"[23] temp file left behind after a failed write: {left}"
    print("ok 23 a failed status write cleans up its temp file")

    # 24. The detector's WINDOW, not one artefact's signature. t20 pins a
    #     20342-char line at ratio 0.999; that leaves every threshold between
    #     200/0.5 and 20342/0.999 free to drift without a test noticing.
    # Every case except the two length ones must be comfortably longer than
    # _MIN_DOC_CHARS: otherwise the length guard rejects them first and masks
    # the property under test. (Mutations Y1/Y3 survived exactly that mistake.)
    varied = "\n".join(f"Linha {i} com conteudo variado e util." for i in range(80))
    reject = [
        ("250-char line at ratio 0.6", "x" * 150 + "abcdefghij" * 10 + "\n" + varied),
        ("200-char line at ratio 1.0 (the floor)", "y" * 200 + "\n" + varied),
        ("empty document", ""),
        ("whitespace-only document", "   \n\n  \n"),
        ("document of duplicate lines", "\n".join(["a repeated line here"] * 80)),
    ]
    for label, bad in reject:
        try:
            gdd._reject_bad_completion(bad, "stop")
            raise AssertionError(f"[24] accepted {label}: {bad[:60]!r}")
        except gdd.ProviderOutputError:
            pass
    # ...and the other side of each boundary must still pass.
    accept = [
        ("250 chars at ratio 0.25", "abcd" * 62 + "\n" + varied),
        ("199-char degenerate line (below the floor, declared ceiling)", "z" * 199 + "\n" + varied),
        ("wide aligned markdown table", "\n".join(
            ["| " + " | ".join(f"col{c} value padded out".ljust(40) for c in range(6)) + " |",
             "|" + "|".join(["-" * 42] * 6) + "|"] + [varied])),
        ("long indented code block", " " * 250 + "x = 1\n" + varied),
    ]
    for label, good in accept:
        gdd._reject_bad_completion(good, "stop")  # raises if it regresses
    print(f"ok 24 detector window pinned: {len(reject)} rejected, {len(accept)} accepted at the boundaries")

    # 25. Degeneration is NOT transient: every link returning junk must fail
    #     after ONE round, never burn the retry budget on a deterministic fault.
    RESPONSES.clear(); HITS.clear()
    junk = {"code": 200, "content": "---\nt: T\n---\n# H1\n" + "底" * 5000}
    RESPONSES.update({M3: [junk], M27: [junk]})
    out.unlink(missing_ok=True)
    p, out = run_script(tmp, port, keyed, extra=["--foreground"],
                        env_extra={"LLM_MAX_RETRY_SECS": "30", "LLM_RETRY_BASE_SECS": "1"})
    assert p.returncode == 2, f"[25] expected exit 2, got {p.returncode}\n{p.stderr}"
    assert HITS == [M3, M27], f"[25] degeneration was retried: {HITS}"
    assert "RETRY" not in p.stderr, f"[25] burned retry budget on a deterministic fault:\n{p.stderr}"
    assert not out.exists(), "[25] degenerate content was written to disk"
    print("ok 25 all links degenerate -> one round, exit 2, no retry, nothing written")

    # 26. A completion that is all reasoning strips to "" — the strip of
    #     <think> blocks can empty it out — and an absent finish_reason must not
    #     silently disarm the check.
    for label, spec in (("all <think>", {"code": 200, "content": "<think>reasoning only"}),
                        ("no finish_reason", {"code": 200, "content": "---\nt: x\n---\n# H1\ncut",
                                              "finish_reason": None})):
        RESPONSES.clear(); HITS.clear()
        RESPONSES.update({M3: [spec], M27: [200]})
        out.unlink(missing_ok=True)
        p, out = run_script(tmp, port, keyed, extra=["--foreground"])
        assert p.returncode == 0, f"[26] {label}: expected exit 0, got {p.returncode}\n{p.stderr}"
        assert HITS == [M3, M27], f"[26] {label}: did not fall to the next link: {HITS}"
        assert out.stat().st_size > 100, f"[26] {label}: wrote an empty doc"
    print("ok 26 empty completion and absent finish_reason both fail over instead of shipping")

    # 27. Retry-After: 0 must not turn the backoff into a tight loop.
    RESPONSES.clear(); HITS.clear()
    RESPONSES.update({M3: [(429, "0")], M27: [(429, "0")]})
    out.unlink(missing_ok=True)
    p, out = run_script(tmp, port, keyed, extra=["--foreground"],
                        env_extra={"LLM_MAX_RETRY_SECS": "6", "LLM_RETRY_BASE_SECS": "2"})
    assert p.returncode == 2, f"[27] expected exit 2, got {p.returncode}\n{p.stderr}"
    assert "in 2s" in p.stderr, f"[27] zero was not floored to the base backoff:\n{p.stderr}"
    assert len(HITS) <= 8, f"[27] flooded the provider: {len(HITS)} calls in a 6s budget"
    # A malformed header must degrade to backoff, never kill a retryable 429:
    # int(float("inf")) raises OverflowError from inside the HTTPError handler.
    for bad_header in ("inf", "-inf", "nan", "soon", ""):
        assert gdd._retry_after_secs({"Retry-After": bad_header}) in (None, 0), \
            f"[27] Retry-After {bad_header!r} did not degrade cleanly"
    print(f"ok 27 Retry-After: 0 floored to the base backoff ({len(HITS)} calls); inf/nan degrade to backoff")

    # 28. Oversized waiter arguments are rejected by us, not by shell arithmetic.
    w = subprocess.run([str(WAITER), str(tmp / "st-running.json"), "99999999999999999999", "20"],
                       capture_output=True, text=True, timeout=30)
    assert w.returncode == 3, f"[28] expected exit 3, got {w.returncode}"
    assert "at most 9 digits" in w.stderr, f"[28] rejected for the wrong reason:\n{w.stderr}"
    print("ok 28 max_polls above 2^63 rejected with our message, not a shell error")

    # 29-33: the local `claude -p` link, driven by a fake binary that records
    # what it was given and answers according to FAKE_CLAUDE_MODE.
    fake = tmp / "fake-claude"
    fake.write_text(f'''#!{sys.executable}
import json, os, sys
mode = os.environ.get("FAKE_CLAUDE_MODE", "ok")
prompt = sys.stdin.read()
open(os.environ["FAKE_CLAUDE_LOG"], "w").write(json.dumps({{"argv": sys.argv[1:], "prompt": prompt}}))
doc = "# doc from claude\\n\\n## Sumário\\n\\nResumo de teste.\\n\\n" + "\\n".join("Linha %d de conteudo generico do documento de teste." % i for i in range(20)) + "\\n"
if mode == "auth":
    print(json.dumps({{"is_error": True, "result": "Failed to authenticate: OAuth session expired"}}))
    sys.exit(1)
if mode == "overloaded":
    print(json.dumps({{"is_error": True, "result": "API Error: 529 overloaded_error"}}))
    sys.exit(1)
print(json.dumps({{"result": doc, "stop_reason": "max_tokens" if mode == "truncated" else "end_turn", "is_error": False}}))
''')
    fake.chmod(0o755)
    flog = tmp / "fake-claude.log"

    def claude_env(mode):
        return {"YTDEEP_CLAUDE_BIN": str(fake), "FAKE_CLAUDE_MODE": mode, "FAKE_CLAUDE_LOG": str(flog)}

    # 29. No HTTP key: both stub links SKIP and claude
    #     writes the doc. The prompt must carry the template STRUCTURE and the
    #     SIZING block, and the CLI must run with tools off.
    RESPONSES.clear(); HITS.clear()
    flog.unlink(missing_ok=True)
    out.unlink(missing_ok=True)
    p, out = run_script(tmp, port, {}, extra=["--foreground"], env_extra=claude_env("ok"))
    assert p.returncode == 0, f"[29] expected exit 0, got {p.returncode}\n{p.stderr}"
    assert HITS == [], f"[29] an HTTP link was contacted without a key: {HITS}"
    assert "SKIP provider=stub-a" in p.stderr and "TRY provider=claude-sonnet" in p.stderr, \
        f"[29] chain did not fall through to claude:\n{p.stderr}"
    assert "from claude" in out.read_text(), "[29] output not written by the claude link"
    seen = json.loads(flog.read_text())
    assert seen["argv"][:1] == ["-p"] and "--tools" in seen["argv"], f"[29] bad argv {seen['argv']}"
    assert seen["argv"][seen["argv"].index("--tools") + 1] == "", "[29] tools were not disabled"
    assert "--strict-mcp-config" in seen["argv"] and "--disable-slash-commands" in seen["argv"], \
        f"[29] MCP connectors / slash commands not disabled: {seen['argv']}"
    assert seen["argv"][seen["argv"].index("--setting-sources") + 1] == "project", \
        f"[29] user hooks/settings not excluded: {seen['argv']}"
    assert "OUTPUT CONTRACT" in seen["prompt"], "[29] output contract missing from the prompt"
    assert "SIZING" in seen["prompt"], "[29] sizing block missing from the prompt"
    assert "## Output structure" in seen["prompt"], "[29] template structure missing from the prompt"
    print("ok 29 no stub key -> claude -p writes the doc, tools off, structure + sizing in the prompt")

    # 30. --model claude-sonnet puts claude first: the HTTP links are never touched.
    RESPONSES.clear(); HITS.clear()
    RESPONSES.update({M3: [200], M27: [200]})
    out.unlink(missing_ok=True)
    p, out = run_script(tmp, port, keyed, extra=["--foreground", "--model", "claude-sonnet"],
                        env_extra=claude_env("ok"))
    assert p.returncode == 0 and HITS == [], f"[30] claude not first: rc={p.returncode} hits={HITS}\n{p.stderr}"
    print("ok 30 --model claude-sonnet runs claude first, HTTP links untouched")

    # 31. NEGATIVE CONTROL: a claude completion cut at max_tokens is rejected
    #     and the next link answers — truncation must not ship as a document.
    RESPONSES.clear(); HITS.clear()
    RESPONSES.update({M3: [200], M27: [200]})
    out.unlink(missing_ok=True)
    p, out = run_script(tmp, port, keyed, extra=["--foreground", "--model", "claude-sonnet"],
                        env_extra=claude_env("truncated"))
    assert p.returncode == 0 and HITS == [M3], f"[31] expected fall to m3: rc={p.returncode} hits={HITS}\n{p.stderr}"
    assert "FAIL provider=claude-sonnet" in p.stderr and "max_tokens" in p.stderr, \
        f"[31] truncation not reported:\n{p.stderr}"
    assert f"from {M3}" in out.read_text(), "[31] truncated claude output was written"
    print("ok 31 claude stop_reason=max_tokens rejected, next link answers")

    # 32. NEGATIVE CONTROL: an expired login is not transient (no retry, one
    #     round, real reason surfaced), a 529 overload is (retry round logged).
    RESPONSES.clear(); HITS.clear()
    out.unlink(missing_ok=True)
    p, out = run_script(tmp, port, {}, extra=["--foreground"], env_extra=claude_env("auth"))
    assert p.returncode == 2, f"[32] expected exit 2, got {p.returncode}\n{p.stderr}"
    assert "RETRY" not in p.stderr, f"[32] retried a dead login:\n{p.stderr}"
    assert "OAuth session expired" in p.stderr and not out.exists(), f"[32] bad failure report:\n{p.stderr}"
    p, out = run_script(tmp, port, {}, extra=["--foreground"], env_extra=claude_env("overloaded"))
    assert p.returncode == 2 and "RETRY round 2" in p.stderr, f"[32] overload not retried:\n{p.stderr}"
    print("ok 32 expired login fails fast; 529 overload is retried")

    # 33. Depth is the caller's choice, size follows the source: a short video
    #     gets a small budget, a long one reaches the old ceilings, never more.
    short, mid, long_ = gdd.size_profile(5_000), gdd.size_profile(26_000), gdd.size_profile(500_000)
    assert long_ == {"doc_kb": 100, "concepts": 15, "frameworks": 5, "traps": 13, "tools": 11,
                     "quotes": 40, "rows": 25, "timeline": 15, "links": 20}, f"[33] ceilings: {long_}"
    assert all(short[k] <= mid[k] <= long_[k] for k in short), f"[33] not monotonic: {short} {mid} {long_}"
    assert short["doc_kb"] == 12 and short["concepts"] == 5, f"[33] floors: {short}"
    assert "50-100KB" not in gdd.sizing_block(5_000) and "about 12KB" in gdd.sizing_block(5_000)
    print(f"ok 33 size_profile: 5KB -> {short['doc_kb']}KB/{short['concepts']} concepts, "
          f"26KB -> {mid['doc_kb']}KB/{mid['concepts']}, 500KB -> ceilings")

    # 34. The REAL (unpatched) chain is claude-sonnet alone, and a key +
    #     endpoint of some other provider left in the environment change nothing: no call, no log line.
    real_spec = importlib.util.spec_from_file_location("gdd_real", REAL_SCRIPT)
    gdd_real = importlib.util.module_from_spec(real_spec)
    real_spec.loader.exec_module(gdd_real)
    names = [pr["name"] for pr in gdd_real.PROVIDERS]
    assert names == ["claude-sonnet"], f"[34] real chain is not claude-sonnet alone: {names}"
    assert [pr["name"] for pr in gdd_real._provider_chain(None)] == names, "[34] default order changed"
    RESPONSES.clear(); HITS.clear()
    flog.unlink(missing_ok=True)
    out34 = tmp / "draft34.md"
    p = subprocess.run(
        [sys.executable, str(REAL_SCRIPT), "--cleaned-transcript", str(tmp / "t.txt"),
         "--video-meta", '{"title": "T", "url": "U"}', "--output", str(out34), "--foreground"],
        capture_output=True, text=True, timeout=120,
        env={**os.environ, "EXTRA_PROVIDER_API_KEY": "k1", "EXTRA_PROVIDER_BASE_URL": f"http://127.0.0.1:{port}",
             "STUB_API_KEY": "k1", "STUB_BASE_URL": f"http://127.0.0.1:{port}",
             "LLM_MAX_RETRY_SECS": "3", "LLM_RETRY_BASE_SECS": "1", **claude_env("ok")})
    assert p.returncode == 0, f"[34] expected exit 0, got {p.returncode}\n{p.stderr}"
    assert HITS == [], f"[34] an HTTP endpoint was contacted: {HITS}"
    tries = [l for l in p.stderr.splitlines() if l.startswith(("TRY", "SKIP", "FAIL"))]
    assert tries == ["TRY provider=claude-sonnet model=sonnet"], f"[34] chain trace: {tries}"
    assert "extra_provider" not in p.stderr.lower(), f"[34] extra provider mentioned at run time:\n{p.stderr}"
    assert "from claude" in out34.read_text(), "[34] real chain did not write via claude"
    print("ok 34 real chain = claude-sonnet only; extra provider env present, zero HTTP calls, first TRY is claude-sonnet")

    srv.shutdown()
    print("\nALL OK")


if __name__ == "__main__":
    main()
