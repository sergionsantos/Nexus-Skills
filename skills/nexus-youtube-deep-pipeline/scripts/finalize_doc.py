#!/usr/bin/env python3
"""Write the final knowledge document with a DETERMINISTIC frontmatter.

The model's frontmatter is untrusted: across 48 runs it varied in quoting (title
with and without quotes), duration format ("16:27" vs "00:16:27"), and sometimes
was not valid YAML (an unquoted colon). So only the semantic fields are taken
from it (tema_principal, tags, topics); every other field comes from the video
metadata or from this script, in fixed order and format. The body is untouched.

Usage:
  finalize_doc.py --draft DRAFT.md --video-meta '{"url","title","channel","date","duration"}' \
      --fact-check pass|exceptions:N --output FINAL.md \
      [--content-type ai-tech] [--language EN] [--generator claude-sonnet] [--people-dir PEOPLE_DIR]

Exit 0 = written and schema-valid; exit 1 = schema violation (message on stderr).
Schema: references/frontmatter-schema.md
"""
import argparse, datetime, json, os, re, sys

YT = re.compile(r"(?:youtu\.be/|[?&]v=)([A-Za-z0-9_-]{11})")
FM = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def q(s):
    """Double-quoted YAML scalar (JSON string syntax is valid YAML)."""
    return json.dumps(str(s), ensure_ascii=False)


def norm_duration(d):
    """'16:27' -> '16:27'; '00:16:27' -> '16:27'; '1:54:47' stays; seconds -> mm:ss."""
    d = str(d or "").strip()
    if re.fullmatch(r"\d+(\.\d+)?", d):
        s = int(float(d))
        h, r = divmod(s, 3600)
        m, s = divmod(r, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
    m = re.fullmatch(r"(\d+):(\d{2}):(\d{2})", d)
    if m:
        h, mi, se = int(m.group(1)), m.group(2), m.group(3)
        return f"{h}:{mi}:{se}" if h else f"{int(mi)}:{se}"
    if re.fullmatch(r"\d+:\d{2}", d):
        return d
    return d


def norm_date(d):
    d = str(d or "").strip()
    if re.fullmatch(r"\d{8}", d):
        d = f"{d[:4]}-{d[4:6]}-{d[6:]}"
    return d


def model_fields(draft):
    """Pull tema_principal / tags / topics out of the model's frontmatter, tolerantly."""
    m = FM.match(draft)
    if not m:
        return {}, draft
    fm, body = m.group(1), draft[m.end():]
    out, cur = {}, None
    for line in fm.split("\n"):
        km = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if km:
            cur = km.group(1)
            val = km.group(2).strip()
            if val.startswith("[") and val.endswith("]"):
                out[cur] = [x.strip().strip("\"'") for x in val[1:-1].split(",") if x.strip()]
            elif val:
                out[cur] = val.strip("\"'") if cur not in ("tags", "topics") else [val.strip("\"'")]
            else:
                out[cur] = []
        elif cur and re.match(r"^\s+-\s+", line) and isinstance(out.get(cur), list):
            out[cur].append(re.sub(r"^\s+-\s+", "", line).strip().strip("\"'"))
    return out, body


def slug_name(channel):
    return re.sub(r"[\\/:*?\"<>|\[\]]", "", str(channel)).strip().replace(" ", "-")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft", required=True)
    ap.add_argument("--video-meta", required=True)
    ap.add_argument("--fact-check", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--content-type", default="ai-tech")
    ap.add_argument("--language", default="EN")
    ap.add_argument("--generator", default="claude-sonnet")
    ap.add_argument("--people-dir", help="optional folder for channel pages: create a stub [[People/<channel>]] note if missing")
    a = ap.parse_args()
    meta = json.loads(a.video_meta)
    draft = open(a.draft, encoding="utf-8").read().strip() + "\n"
    mf, body = model_fields(draft)
    body = body.lstrip("\n").rstrip() + "\n"
    url = meta.get("url", "")
    um = YT.search(url)
    video_id = meta.get("video_id") or (um.group(1) if um else "")
    chan_name = meta.get("channel_name") or re.sub(r"^\[\[(?:People/)?|\]\]$", "", str(meta.get("channel", "")))
    chan_link = f"[[People/{meta.get('channel_slug') or slug_name(chan_name)}]]"
    tema = mf.get("tema_principal")
    if isinstance(tema, list):
        tema = " ".join(tema)
    if not tema:
        sm = re.search(r"^#{1,3}\s*Sum[aá]rio\s*\n+(.+?)\n", body, re.M)
        tema = re.split(r"(?<=[.!?])\s", sm.group(1).strip())[0][:300] if sm else ""
    tags = mf.get("tags") or [a.content_type, slug_name(chan_name).lower(), "youtube"]
    topics = mf.get("topics") or []
    has_quotes = bool(re.search(r"^#{1,3}\s*Cita", body, re.M))
    lines = [
        "---",
        f"title: {q(meta.get('title', ''))}",
        f"channel: {q(chan_link)}",
        f"source: {q(chan_name)}",
        f"date: {q(norm_date(meta.get('date')))}",
        f"url: {q(url)}",
        f"video_id: {q(video_id)}",
        f"language: {q(a.language)}",
        f"duration: {q(norm_duration(meta.get('duration')))}",
        f"content_type: {q(a.content_type)}",
        f"tema_principal: {q(tema)}",
        "tags:",
        *[f"  - {x}" for x in tags],
    ]
    if topics:
        lines += ["topics:", *[f"  - {q(x) if re.search(r'[:#]', x) else x}" for x in topics]]
    lines += [
        f"has_quotes: {'true' if has_quotes else 'false'}",
        "pipeline: nexus-youtube-deep-pipeline",
        f"pipeline_run: {q(datetime.date.today().isoformat())}",
        f"pipeline_generator: {q(a.generator)}",
        f"fact_check: {q(a.fact_check)}",
        "---",
        "",
    ]
    problems = []
    for k, v in (("title", meta.get("title")), ("date", norm_date(meta.get("date"))), ("url", url),
                 ("video_id", video_id), ("channel", chan_name), ("tema_principal", tema)):
        if not v:
            problems.append(f"missing {k}")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", norm_date(meta.get("date"))):
        problems.append("date is not YYYY-MM-DD")
    if not re.search(r"^# ", body, re.M):
        problems.append("body has no H1")
    if re.search(r"^```(?:yaml|markdown|md)\s*$", body, re.M):
        problems.append("body still contains a wrapper fence")
    if problems:
        print("finalize_doc: " + "; ".join(problems), file=sys.stderr)
        return 1
    os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
    with open(a.output, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n" + body)
    if a.people_dir:
        page = os.path.join(a.people_dir, slug_name(chan_name) + ".md")
        if not os.path.exists(page):
            with open(page, "w", encoding="utf-8", newline="\n") as f:
                f.write(f'---\ntype: channel\nname: {q(chan_name)}\nplatform: YouTube\nstub: true\ntags:\n  - channel\n---\n\n# {chan_name}\n\nPágina criada por finalize_doc: completar URL e descrição.\n')
    print(f"wrote {a.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
